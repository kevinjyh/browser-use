"""
Test configuration for browser-use.
"""

import logging
import os
import sys
from pathlib import Path
import pytest
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from dotenv import load_dotenv

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext


@pytest.fixture(scope='session')
def llm():
	"""
	Fixture to provide a ChatOpenAI instance or a mock for testing.
	Uses a mock if OPENAI_API_KEY is not set.
	"""
	api_key = os.getenv('OPENAI_API_KEY')
	logger.debug(f'API Key present: {bool(api_key)}')
	logger.debug('Using actual ChatOpenAI model')
	return ChatOpenAI(model='gpt-4o', api_key=SecretStr(api_key) if api_key else None)


@pytest.fixture(scope='session')
def browser():
	"""
	Fixture to provide a Browser instance for testing.
	"""
	logger.debug('Creating Browser instance for testing')
	return Browser(config=BrowserConfig(headless=True, disable_security=True))


@pytest.fixture(scope='function')
async def browser_context(browser):
	"""
	Fixture to provide a BrowserContext instance for testing.
	"""
	logger.debug('Creating BrowserContext instance for testing')
	context = BrowserContext(browser=browser)
	yield context
	await context.close()


# 確保載入 .env 檔案
def pytest_configure(config):
	# 載入根目錄的 .env 檔案
	root_dir = Path(__file__).parent.parent
	env_path = root_dir / ".env"
	load_dotenv(dotenv_path=env_path)
	
	# 設置測試模式以防止部分測試對環境變數的依賴
	os.environ["TESTING_MODE"] = "True"
	
	# 如果 GEMINI_API_KEY 已存在於環境變數中，就保留它
	# 否則設置一個虛擬值
	if not os.environ.get("GEMINI_API_KEY"):
		os.environ["GEMINI_API_KEY"] = "fake_test_key"
		
	# 為其他 API 金鑰設置測試虛擬值
	if not os.environ.get("OPENAI_API_KEY"):
		os.environ["OPENAI_API_KEY"] = "sk-fake-test-key"
		
	if not os.environ.get("AZURE_OPENAI_API_KEY"):
		os.environ["AZURE_OPENAI_API_KEY"] = "fake-azure-test-key"
