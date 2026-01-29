# MyClawdbot — Todo App

這個專案是一個用 Next.js + TypeScript + Tailwind CSS 建置的簡單 Todo List 應用，包含前端 UI、暗/亮模式切換（支援系統偏好與手動切換）、以及示範性的 CI workflow（使用 GitHub Actions）來發送台北天氣通知。

主要目標
- 提供一個乾淨、響應式的 Todo List UI（新增 / 編輯 / 刪除 / 標記完成 / 篩選）
- 支援系統預設與手動的亮暗模式切換（prefers-color-scheme + 手動切換）
- 示範如何使用 GitHub Actions 進行週期性任務（例如發送 Telegram 訊息）

專案架構

- pages/
  - _app.tsx — 全局 App，處理主題（系統優先、可手動切換）
  - index.tsx — Todo 應用的入口頁面
- components/
  - TodoApp.tsx — Todo 應用的主要元件，包含新增、刪除、標記、篩選與 localStorage 持久化
- scripts/
  - hourly_weather_bot.py — 備援的台北天氣推送程式（可在 VM 中背景運行）
  - minute_weather_test.py — 每分鐘測試腳本（用於快速測試通知）
- .github/workflows/taipei-weather.yml — GitHub Actions workflow（定時抓取天氣並發送 Telegram；需設定 repo secrets）
- styles/globals.css — 全局樣式與 CSS 變數（包含系統/手動主題支援）
- tailwind.config.js — Tailwind 設定（darkMode: 'class'）
- package.json / tsconfig.json / next.config.js — 專案設定與指令

使用技術
- Next.js 14 + React 18
- TypeScript
- Tailwind CSS（class-based dark mode，並支援 prefers-color-scheme）
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
- 頁面會先嘗試讀取 localStorage 的 user preference（如有設定則以此為準），否則會跟隨系統偏好（prefers-color-scheme）。
- 右上角也提供手動切換按鈕；手動切換會儲存於 localStorage 作為明確偏好，並覆蓋系統設定。

持久化
- Todo 資料以 localStorage 儲存在鍵 `todos` 中（方便快速測試與本地開發）。

自動發送天氣通知（使用 GitHub Actions）
1. 在 GitHub 倉庫設定 Secrets：
   - TELEGRAM_BOT_TOKEN — 你的 Telegram Bot token
   - TELEGRAM_CHAT_ID — 目標 chat id（此專案預設為 533375854）
2. Workflow `.github/workflows/taipei-weather.yml` 會定時呼叫 Open‑Meteo，並使用 Telegram Bot 發送格式化後的繁體中文天氣訊息。
3. 測試流程：先以每分鐘執行 10 次驗證通知，驗證完成後會切回每半小時執行。

部署與注意事項
- 若需要長期穩定推送，建議使用 GitHub Actions（已設定）或其他不會自動暫停的運行環境（例如小型 VPS）。
- 請勿在公開 repo 中硬編碼 Telegram token，使用 GitHub Secrets 保護憑證。

如何貢獻
- 歡迎 PR：Fork → 建立 feature branch（命名以 feature/ 或 fix/ 開頭）→ 完成後發 Pull Request 到 main。
- Issue：在 repository 的 Issues 裡提出 bug 或新功能建議。

Commit 規範
- 使用簡潔前綴：
  - feat: 新功能
  - fix: 錯誤修正
  - docs: 文件改動
  - chore: 重構/建構/依賴更新
  - test: 新增或修改測試
- 範例： `feat: add dark mode toggle`

CI / Badge
- 本專案使用 GitHub Actions 做定時任務（天氣通知）。
- 可加上 CI Badge（例如 workflow run 成功率）到 README，若要我幫你加 badge，我會把 badge 的 Markdown 插入最上方。

部署步驟（建議）
1. 使用 GitHub Actions：
   - 把 TELEGRAM_BOT_TOKEN 與 TELEGRAM_CHAT_ID 設成 Repository Secrets。
   - Workflow 已加入 `.github/workflows/taipei-weather.yml`，測試完成後會改為每 30 分鐘執行。
2. 若要部署網站到生產（例如 Vercel）：
   - 在 Vercel 建立專案並連結 GitHub 倉庫，Vercel 會自動部署 Next.js 專案。
   - 若使用 Vercel，請在 Vercel 的環境變數中加入 TELEGRAM_BOT_TOKEN（僅在你需要 server 端發送時使用）。

後續建議
- 增加後端 API（Next.js API routes 或簡單 SQLite）以支援多設備同步
- 新增使用者登入與多用戶資料隔離（如果需要共享）
- 擴充 Todo 欄位：提醒（reminders）、重複規則、排序與標籤管理

如果你要我把 README 再調整成更正式的格式（包含安裝截圖、CI badges、或更多使用範例），告訴我要加什麼內容，我會更新並 push。