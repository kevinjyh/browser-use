from __future__ import annotations

import logging
from typing import List, Optional
import os

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
	BaseMessage,
	HumanMessage,
)
from langchain_core.messages.utils import convert_to_openai_messages
from mem0 import Memory as Mem0Memory
from pydantic import BaseModel

from browser_use.agent.message_manager.service import MessageManager
from browser_use.agent.message_manager.views import ManagedMessage, MessageMetadata
from browser_use.utils import time_execution_sync

logger = logging.getLogger(__name__)


class MemorySettings(BaseModel):
	"""Settings for procedural memory."""

	agent_id: str
	interval: int = 10
	config: Optional[dict] | None = None


class Memory:
	"""
	Manages procedural memory for agents.

	This class implements a procedural memory management system using Mem0 that transforms agent interaction history
	into concise, structured representations at specified intervals. It serves to optimize context window
	utilization during extended task execution by converting verbose historical information into compact,
	yet comprehensive memory constructs that preserve essential operational knowledge.
	"""

	# Default configuration values as class constants
	DEFAULT_VECTOR_STORE = {'provider': 'faiss', 'config': {'embedding_model_dims': 384}}
	DEFAULT_EMBEDDER = {'provider': 'huggingface', 'config': {'model': 'all-MiniLM-L6-v2'}}

	def __init__(
		self,
		message_manager: MessageManager,
		llm: BaseChatModel,
		settings: MemorySettings,
	):
		self._memory_config = settings.config or self._get_default_config(llm)
		self._interval = settings.interval
		self._agent_id = settings.agent_id
		self._message_manager = message_manager
		self._llm = llm

		# 在測試模式下跳過初始化Mem0Memory，避免PyTorch相關錯誤
		if os.environ.get("TESTING_MODE") == "True":
			logger.info("Running in testing mode, skipping memory initialization")
			self.mem0 = None
		else:
			self.mem0 = Mem0Memory.from_config(config_dict=self._memory_config)

	@staticmethod
	def _get_default_config(llm: BaseChatModel) -> dict:
		"""Returns the default configuration for memory."""
		return {
			'vector_store': Memory.DEFAULT_VECTOR_STORE,
			'llm': {'provider': 'langchain', 'config': {'model': llm}},
			'embedder': Memory.DEFAULT_EMBEDDER,
		}

	@time_execution_sync('--create_procedural_memory')
	def create_procedural_memory(self, current_step: int) -> None:
		"""
		Create a procedural memory if needed based on the current step.

		Args:
		    current_step: The current step number of the agent
		"""
		logger.info(f'Creating procedural memory at step {current_step}')

		# Get all messages
		all_messages = self._message_manager.state.history.messages

		# Separate messages into those to keep as-is and those to process for memory
		new_messages = []
		messages_to_process = []

		for msg in all_messages:
			if isinstance(msg, ManagedMessage) and msg.metadata.message_type in {'init', 'memory'}:
				# Keep system and memory messages as they are
				new_messages.append(msg)
			else:
				if len(msg.message.content) > 0:
					messages_to_process.append(msg)

		# Need at least 2 messages to create a meaningful summary
		if len(messages_to_process) <= 1:
			logger.info('Not enough non-memory messages to summarize')
			return
		# Create a procedural memory
		memory_content = self._create([m.message for m in messages_to_process], current_step)

		if not memory_content:
			logger.warning('Failed to create procedural memory')
			return

		# Replace the processed messages with the consolidated memory
		memory_message = HumanMessage(content=memory_content)
		memory_tokens = self._message_manager._count_tokens(memory_message)
		memory_metadata = MessageMetadata(tokens=memory_tokens, message_type='memory')

		# Calculate the total tokens being removed
		removed_tokens = sum(m.metadata.tokens for m in messages_to_process)

		# Add the memory message
		new_messages.append(ManagedMessage(message=memory_message, metadata=memory_metadata))

		# Update the history
		self._message_manager.state.history.messages = new_messages
		self._message_manager.state.history.current_tokens -= removed_tokens
		self._message_manager.state.history.current_tokens += memory_tokens
		logger.info(f'Messages consolidated: {len(messages_to_process)} messages converted to procedural memory')

	def _create(self, messages: List[BaseMessage], current_step: int) -> Optional[str]:
		parsed_messages = convert_to_openai_messages(messages)
		try:
			results = self.mem0.add(
				messages=parsed_messages,
				agent_id=self._agent_id,
				memory_type='procedural_memory',
				metadata={'step': current_step},
			)
			if len(results.get('results', [])):
				return results.get('results', [])[0].get('memory')
			return None
		except Exception as e:
			logger.error(f'Error creating procedural memory: {e}')
			return None

	def add_messages(self, messages: List[BaseMessage], current_step: int) -> None:
		"""
		Add messages to the memory database.
		"""
		# Skip if no messages
		if not messages:
			return

		# 在測試模式下不執行記憶體相關操作
		if self.mem0 is None:
			logger.debug("Skipping memory operations in testing mode")
			return
			
		parsed_messages = []
		for message in messages:
			parsed_messages.append(
				{
					"role": message.type,
					"content": message.content,
					"metadata": getattr(message, "additional_kwargs", {}),
				}
			)

		if parsed_messages:
			results = self.mem0.add(
				messages=parsed_messages,
				agent_id=self._agent_id,
				memory_type='procedural_memory',
				metadata={'step': current_step},
			)
			logger.debug(f'Memory added: {len(results)} messages')
