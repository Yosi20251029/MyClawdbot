Release v0.1 — 2026-02-01

簡短說明
- 將天氣 / 新聞 / 多益練習的自動通知流程強化為穩定、可追蹤的排程系統，並加入備援、日誌摘要與 artifact 保存機制以提升可靠度與可審計性。

主要變更（重點摘要）

- 排程與執行
  - GitHub Actions：調整為每 30 分鐘執行（cron: "*/30 * * * *"），同時保留手動觸發（workflow_dispatch）。
  - Workflow：checkout → 安裝依賴 → 下載 TOEIC 歷史 artifact（若存在）→ 執行報表腳本 → 上傳更新後的 toeic_history.json 為 artifact。

- 天氣資料與穩定性
  - primary：維持使用 Open‑Meteo 取得即時天氣（含 current + daily + hourly 資料）。
  - retry & timeout：fetch_weather() 新增重試機制（預設最多 3 次），timeout 延長為 60s，並有退避等待與錯誤日誌。
  - fallback：若 Open‑Meteo 全部重試失敗且設定了 OPENWEATHER_API_KEY，會自動呼叫 OpenWeatherMap（OneCall）作為備援，並以統一格式回傳。
  - 訊息中顯示資料來源：會標註「Open‑Meteo（主來源）」或「OpenWeatherMap（備援）」，若為備援會額外顯示警示文字提醒可能有差異。

- 訊息內容格式（Telegram）
  - 時間、資料來源、現在天氣、明天天氣概況（含降雨機率）、穿衣建議、今日運勢（目前為模板）、多益單字練習、三類新聞（標題 + 重點整理）。
  - 新聞：保留可點連結的標題，並清理尾端媒體來源字樣（例如移除 " - Yahoo新聞"、" | 華視新聞" 等）。
  - 加入 JSON 摘要（summary）輸出到 Actions 日誌，包含 weather_time、weather_source、precip_prob、news_counts、toeic（本次單字）等，方便快速驗證每次為即時抓取。

- 多益單字（TOEIC）
  - 每次隨機抽樣 5 個常考單字（含中文意思與例句），非寫死。
  - 避免近期重複：實作短期去重（history_k=10），透過 memory/toeic_history.json 記錄最近出現單字。
  - Artifact 保存：workflow 會下載上一次的 toeic-history artifact（若存在），執行後再上傳新的 toeic-history artifact，避免在 repo 產生頻繁 commit。

- Artifact 與健全處理
  - 若無 toeic-history artifact，workflow 現在會容忍（continue-on-error）並在上傳前建立空的 memory/toeic_history.json（內容 []），確保第一次也能順利上傳 artifact。
  - 在上傳前會把檔案存在性、大小與內容列印到日誌便於除錯。

- 其他
  - README.md 已更新並記錄上述變更與部署/安全注意事項。
  - 已新增多個小改動的 commits（例如：新聞標題清理、TOEIC 去重、OpenWeatherMap fallback、summary 輸出、workflow artifact 處理等）。

部署 / 使用提醒
- 請在 GitHub Repo Secrets 設定： TELEGRAM_BOT_TOKEN、TELEGRAM_CHAT_ID；若要啟用備援請加 OPENWEATHER_API_KEY（OpenWeatherMap API key）。
- Artifact（toeic-history）會出現在每次 Actions run 的 Artifacts 區；預設 GitHub 保留期請參考帳號/組織設定。
- 若要我協助把備援 key 上傳為 secret、或進行 Render/Fly 的容器部署（v2），告訴我我會接續操作。

欲查詢的 commit 範例（可直接用這些關鍵訊息做 git log 過濾）
- feat(fetch): add retries and increased timeout for weather API
- fix(news): keep links, clean trailing source names from titles
- feat(report): replace lunar section with 5 TOEIC words (meaning + example)
- feat(toeic): avoid recent repeats using memory/toeic_history.json
- chore(workflow): run every 30 minutes; ensure checkout and deps
- feat: add OpenWeatherMap fallback and persist TOEIC history as artifact in workflow
- feat(report): annotate weather data source (主來源/備援) in message
- feat(report): add caution note when using OpenWeatherMap fallback
- ci(workflow): ensure toeic_history.json exists and print before upload
- chore(report): print JSON summary (weather_time, source, precip_prob, news_counts, toeic) to logs
