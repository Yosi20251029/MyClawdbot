# MyClawdbot — Todo App

這個專案是一個用 Next.js + TypeScript + Tailwind CSS 建置的簡單 Todo List 應用，包含前端 UI、暗/亮模式切換、以及示範性的 CI workflow（使用 GitHub Actions）來發送台北天氣通知。

主要目標
- 提供一個乾淨、響應式的 Todo List UI（新增 / 編輯 / 刪除 / 標記完成 / 篩選）
- 支援亮暗模式切換（使用 Tailwind 的 class-based dark mode）
- 示範如何使用 GitHub Actions 進行周期性任務（例如發送 Telegram 訊息）

專案架構

- pages/
  - _app.tsx — 全局 App 包含主題（亮/暗）切換按鈕及主題設定
  - index.tsx — Todo 應用的入口頁面
- components/
  - TodoApp.tsx — Todo 應用的主要元件，包含新增、刪除、標記、篩選與 localStorage 持久化
- scripts/
  - hourly_weather_bot.py — 備援的台北天氣推送程式（背景運行）
  - minute_weather_test.py — 每分鐘測試腳本（用於快速測試通知）
- .github/workflows/taipei-weather.yml — GitHub Actions workflow，用於定時抓取天氣並發送 Telegram（需設定 repo secrets）
- styles/globals.css — 全局樣式與 CSS 變數（包含暗/亮主題變數）
- tailwind.config.js — Tailwind 設定（darkMode: 'class'）
- package.json / tsconfig.json / next.config.js — 專案設定與指令

使用技術
- Next.js 14 + React 18
- TypeScript
- Tailwind CSS（class-based dark mode）
- GitHub Actions（定時任務）
- Open-Meteo（公開天氣 API）
- Telegram Bot API（發送通知）

如何運作

本地運行
1. 安裝依賴：
   npm install
2. 開發模式啟動（預設使用 3001 端口以避免與 Codespace web port 衝突）：
   npm run dev
3. 打開瀏覽器訪問： http://localhost:3001

主題切換
- 頁面右上角有主題切換按鈕，會在 localStorage 儲存你的偏好（亮 / 暗），並以 class 對 documentElement 加上 `.dark` 來切換 Tailwind dark 模式。

持久化
- Todo 資料以 localStorage 儲存在鍵 `todos` 中（方便快速測試與本地開發）。

自動發送天氣通知（使用 GitHub Actions）
1. 在 GitHub 仓库設定 Secrets：
   - TELEGRAM_BOT_TOKEN — 你的 Telegram Bot token
   - TELEGRAM_CHAT_ID — 目標 chat id（此專案預設為 533375854）
2. Workflow `.github/workflows/taipei-weather.yml` 會定時呼叫 Open‑Meteo，並使用 Telegram Bot 發送格式化後的繁體中文天氣訊息。
3. 我們在測試階段會把排程設為每分鐘 10 次，測試完成後會改為每 30 分鐘。

部署與注意事項
- 若需要長期穩定推送，建議使用 GitHub Actions（已設定）或其他不會自動暫停的運行環境（例如小型 VPS）。
- 請勿在公開 repo 中硬編碼 Telegram token，使用 GitHub Secrets 保護憑證。

後續建議
- 增加後端 API（Next.js API routes 或簡單 SQLite）以支援多設備同步
- 新增使用者登入與多用戶資料隔離（如果需要共享）
- 擴充 Todo 欄位：提醒（reminders）、重複規則、排序與標籤管理

如果你要我把 README 再調整成更正式的格式（包含安裝截圖、CI badges、或更多使用範例），告訴我要加什麼內容，我會更新並 push。