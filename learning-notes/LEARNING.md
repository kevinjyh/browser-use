# browser-use 專案學習筆記

## 1. 專案功能梳理

Browser-use 是一個用於讓 AI 代理控制網頁瀏覽器的 Python 庫，它使 AI 可以像人類一樣與網頁進行互動。

### 核心功能

1. **瀏覽器自動化**
   - 控制瀏覽器進行網頁導航、點擊、輸入文字等基本操作
   - 支援多標籤頁管理
   - 支援視覺分析（截圖和頁面元素識別）
   - 可連接到真實 Chrome 瀏覽器 (包括用戶已登入的狀態)

2. **AI 代理能力**
   - 透過 LLM (大型語言模型) 來解讀網頁內容
   - 自主規劃和執行多步驟任務
   - 使用視覺能力理解網頁佈局和元素
   - 自主記憶和提取關鍵信息

3. **DOM 操作**
   - 提取和解析網頁 DOM 結構
   - 識別可交互元素（按鈕、輸入框等）
   - 支援複雜的 DOM 導航和搜索

4. **控制器模組**
   - 定義和管理 AI 可執行的動作
   - 提供擴展功能的接口
   - 處理錯誤和異常情況

### 組件間交互邏輯

1. **Agent (代理)**: 是核心協調者，負責管理任務執行流程
   - 接收用戶任務
   - 呼叫 LLM 進行決策
   - 管理瀏覽器狀態
   - 監控任務執行

2. **Browser (瀏覽器)**: 管理與實際瀏覽器的交互
   - 啟動和配置瀏覽器
   - 管理瀏覽器上下文和標籤頁
   - 提供頁面截圖和狀態信息

3. **Controller (控制器)**: 管理可執行的動作
   - 註冊和執行命令
   - 處理動作參數和結果
   - 提供擴展介面

4. **DOM Service**: 處理網頁結構和元素
   - 分析網頁 DOM
   - 識別和選擇元素
   - 處理頁面內容提取

## 2. 學習路線圖及時間期程表

### 第一階段：基礎理解（1-2週）

1. **環境設置與基本概念**（2-3天）
   - 安裝必要依賴
   - 瞭解基本的瀏覽器自動化概念
   - 熟悉 Playwright 基礎（Browser-use 底層使用的瀏覽器自動化工具）

2. **基本範例運行**（2-3天）
   - 運行簡單的 AI 瀏覽器任務
   - 分析執行過程和結果
   - 調試常見問題

3. **核心類別結構理解**（3-4天）
   - 梳理主要類別關係
   - 理解代碼結構和組織方式
   - 學習基本 API 用法

### 第二階段：深入探索（2-3週）

1. **代理（Agent）機制研究**（4-5天）
   - 分析代理決策過程
   - 理解 LLM 集成方式
   - 學習系統提示詞設計

2. **瀏覽器操作細節**（3-4天）
   - 學習瀏覽器配置選項
   - 理解上下文管理
   - 分析頁面狀態處理

3. **DOM 處理與頁面理解**（4-5天）
   - 深入 DOM 元素識別機制
   - 學習頁面解析和內容提取
   - 理解視覺處理流程

4. **控制器與動作系統**（3-4天）
   - 分析內置動作實現
   - 學習自定義動作開發
   - 理解動作過濾和優先級

### 第三階段：進階應用（2-3週）

1. **實際案例開發**（1週）
   - 開發簡單的自動化任務
   - 優化代理性能
   - 擴展基本功能

2. **自定義擴展開發**（1週）
   - 擴充額外動作
   - 集成外部服務
   - 優化特定任務效能

3. **項目總結與最佳實踐**（3-4天）
   - 總結學習經驗
   - 梳理常見問題和解決方案
   - 建立個人知識庫

## 3. 由淺入深的代碼檔案學習順序

### 入門文件

1. `browser_use/__init__.py` - 了解專案結構和主要組件
2. `README.md` - 專案介紹和基本用法
3. `examples/*.py` - 基本範例，了解使用方式

### 核心架構

1. `browser_use/agent/service.py` - Agent 類實現，了解核心工作流程
2. `browser_use/browser/browser.py` - 瀏覽器管理實現
3. `browser_use/controller/service.py` - 操作控制器實現
4. `browser_use/dom/service.py` - DOM 處理服務

### 進階組件

1. `browser_use/browser/context.py` - 瀏覽器上下文管理
2. `browser_use/agent/views.py` - 代理數據結構和模型
3. `browser_use/controller/registry/service.py` - 動作註冊系統
4. `browser_use/dom/views.py` - DOM 元素數據結構

### 深入細節

1. `browser_use/agent/prompts.py` - 系統提示詞設計
2. `browser_use/agent/memory.py` - 代理記憶系統
3. `browser_use/agent/message_manager.py` - 消息管理
4. `browser_use/utils.py` - 工具函數和輔助方法

## 4. 測試案例由淺入深的學習順序

### 基礎測試

1. `tests/test_browser_config_models.py` - 了解配置模型和選項
2. `tests/test_full_screen.py` - 簡單的功能測試
3. `tests/test_browser.py` - 瀏覽器基本功能測試
4. `tests/test_context.py` - 瀏覽器上下文測試

### 核心功能測試

1. `tests/test_service.py` - 代理服務核心功能測試
2. `tests/test_models.py` - 數據模型測試
3. `tests/test_core_functionality.py` - 整體核心功能測試
4. `tests/test_wait_for_element.py` - 等待元素功能測試

### 互動操作測試

1. `tests/test_dropdown.py` / `tests/test_dropdown_complex.py` - 下拉選單互動測試
2. `tests/test_react_dropdown.py` - React 框架下拉選單測試
3. `tests/test_mind2web.py` - Web 資料處理測試

### 進階功能測試

1. `tests/test_agent_actions.py` - 代理動作測試
2. `tests/test_action_filters.py` - 動作過濾系統測試
3. `tests/test_self_registered_actions.py` - 自註冊動作測試
4. `tests/test_vision.py` - 視覺處理功能測試
5. `tests/test_stress.py` - 壓力測試和性能邊界

### 整合測試

1. `tests/test_attach_chrome.py` - 連接真實 Chrome 瀏覽器測試
2. `tests/test_save_conversation.py` - 對話保存功能測試

透過按照這個順序學習測試案例，可以從基礎配置開始，逐步理解各個組件的功能和互動方式，最後掌握整體系統的工作原理。

---

此學習計劃旨在幫助一位自學的 Python 愛好者逐步理解 browser-use 專案。請根據個人學習進度和理解情況適當調整時間安排，也可以在學習過程中記錄問題和心得，形成自己的知識體系。
