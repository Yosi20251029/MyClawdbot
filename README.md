專案總覽與近期變更

此 repo 為個人自動化通知與報表系統（Taipei weather / news / TOEIC practice）。下面紀錄近期完成的重要變更與實作細節，方便日後維護與追蹤。

主要功能
- 每 30 分鐘使用 GitHub Actions 自動執行並發送 Telegram 訊息（parse_mode=HTML）。
- 即時天氣（使用 Open‑Meteo），包含現在天氣、明天天氣概況、降雨機率、風速、最高/最低溫與穿衣建議。
- 新聞彙整（太子集團 / 台灣 / 國際）：抓取 Google News RSS，清理標題尾端的來源字樣，標題保留可點連結，並提供重點整理。
- 多益單字練習：每次隨機提供 5 個多益常考單字（中文釋義 + 例句），並用短期去重機制避免近期重複。
- 報表格式以 HTML 發送到 Telegram，並關閉網頁預覽（disable_web_page_preview=True）。

近期重要變更（時序）
1. 新增 GitHub Actions 排程（.github/workflows/taipei-weather.yml）
   - 現在以 cron: "*/30 * * * *" 每 30 分鐘執行。
   - Workflow 內容：checkout → 安裝系統 / pip 套件 → 執行 scripts/hourly_report.py --send。
   - 測試：已手動觸發並確認可以成功發送（action run 顯示步驟成功，腳本回傳 "sent"）。

2. scripts/hourly_report.py 的改善
   - fetch_weather(): 加入重試機制（預設最多 3 次），並將 timeout 延長為 60 秒，失敗時有退避等待（5s、10s、15s）並在 stderr 印出嘗試日誌。
   - 增加對 hourly: precipitation_probability 的請求，以計算降雨機率並在報表中顯示（若可得，會標示最高降雨機率 %）。
   - 新聞標題清理：使用正則與分割（re.split）移除標題尾端常見分隔符後的來源（例如 " - Yahoo新聞"、" | 華視新聞"、括號尾註），但仍保留可點連結的 href。
   - 農民曆移除：原本的農民曆欄位改為多益單字練習（5 字）— 每字附中文與例句。
   - 多益單字去重：實作短期去重（memory/toeic_history.json），預設記錄最近 k=10 個單字，從字庫排除最近出現過的單字再抽樣。若池內不足，才重置 recent。

3. 新增錯誤與穩定性處理
   - 在遇到 API 讀取超時（requests.exceptions.ReadTimeout）時會重試並記錄日誌；若全部重試失敗，腳本會拋出錯誤，Actions run 將顯示失敗，以便排查。

部署與注意事項
- Telegram Token 與 Chat ID：請在 GitHub repo 的 Settings → Secrets → Actions 新增 TELEGRAM_BOT_TOKEN 與 TELEGRAM_CHAT_ID（目前 Actions template 已設定使用這兩個 secret）。
- GitHub Actions 權限：若要把 image 推到 ghcr.io，請確保 repo 的 GITHUB_TOKEN 有 packages 權限（預設通常足夠）。
- memory/toeic_history.json：腳本會在 Actions runner 上將此檔案寫入 workspace，用於短期去重；目前不會自動 commit 回 repo（避免頻繁 commit）。

未來建議（可選）
- 加備援天氣來源（例如 OpenWeatherMap），在主 API 失敗時使用備援或發送上一次快照。這可進一步提升通知穩定性。
- 若要永續保存多益 history，可考慮將 history 存為 artifact 或推到私有 storage（避免在 repo 產生頻繁 commits）。
- 若需要我可以協助把服務容器化並部署到 Render / Fly（已準備 autoMoltbot scaffold，可依需求調整 Dockerfile 與 workflow）。

開發者備註
- 主要檔案：scripts/hourly_report.py、.github/workflows/taipei-weather.yml。請以這兩個檔案為主要維護目標。 

若你要我把這份變更同步到專案內其他 README（例如 docs/ 或 repo 內特定位置），或要我把這個 README 加到另一個 repo，告訴我我要放到哪裡我就去做。