#!/usr/bin/env python3
import requests, time, os, logging
from requests.adapters import HTTPAdapter, Retry

# Configuration from env
TOKEN = os.environ.get('TG_BOT_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID','533375854')
WIND_UNIT = os.environ.get('WIND_UNIT','km/h')
TEMP_UNIT = os.environ.get('TEMP_UNIT','C')
TIMEOUT = int(os.environ.get('WEATHER_TIMEOUT', '20'))
RETRIES = int(os.environ.get('WEATHER_RETRIES', '3'))
BACKOFF_FACTOR = float(os.environ.get('WEATHER_BACKOFF', '1.0'))
LOG_PATH = os.environ.get('WEATHER_LOG', '/tmp/weather_bot.log')

# Test mode controls
TEST_MODE = os.environ.get('TEST_MODE','0') == '1'
TEST_INTERVAL = int(os.environ.get('TEST_INTERVAL', '60'))
TEST_COUNT = int(os.environ.get('TEST_COUNT', '10'))

# Setup logging
logging.basicConfig(level=logging.INFO, filename=LOG_PATH, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger('weatherbot')

# requests session with retries
session = requests.Session()
retries = Retry(total=RETRIES, backoff_factor=BACKOFF_FACTOR, status_forcelist=[429,500,502,503,504], allowed_methods=["GET", "POST"]) 
adapter = HTTPAdapter(max_retries=retries)
session.mount('https://', adapter)
session.mount('http://', adapter)


def fetch_weather():
    url = 'https://api.open-meteo.com/v1/forecast'
    params = {
        'latitude':25.0330,
        'longitude':121.5654,
        'hourly':'temperature_2m,precipitation_probability,windspeed_10m',
        'current_weather':'true',
        'timezone':'Asia/Taipei',
        'forecast_days':1,
    }
    try:
        r = session.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning(f'fetch_weather failed: {e}')
        raise


def fetch_news():
    # Fetch top news about 太子集團 via Google News RSS
    rss_url = 'https://news.google.com/rss/search?q=%E5%A4%AA%E5%AD%90%E9%9B%86%E5%9C%98&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'
    try:
        r = session.get(rss_url, timeout=TIMEOUT)
        r.raise_for_status()
        # parse basic XML titles
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.content)
        items = root.findall('.//item')[:5]
        news = []
        for it in items:
            title = it.find('title').text if it.find('title') is not None else ''
            link = it.find('link').text if it.find('link') is not None else ''
            news.append({'title': title, 'link': link})
        return news
    except Exception as e:
        logger.warning(f'fetch_news failed: {e}')
        return []


def format_message(data, news_items):
    cur = data.get('current_weather',{})
    time_str = cur.get('time','')
    temp = cur.get('temperature')
    wind = cur.get('windspeed')
    if temp is None:
        temp_text = 'N/A'
    else:
        if TEMP_UNIT=='F': temp = temp*9/5+32
        temp = round(temp,1)
        temp_text = f"{temp}°{TEMP_UNIT}"
    if wind is None:
        wind_text = 'N/A'
    else:
        if WIND_UNIT=='m/s': wind = round(wind/3.6,1)
        else: wind = round(wind,1)
        wind_text = f"約 {wind} {WIND_UNIT}"
    cur_line = f"現在天氣：\n- 時間：{time_str}\n- 溫度：{temp_text}\n- 風速：{wind_text}\n"

    # Build clickable links using HTML and a concise summary
    msg = cur_line + "\n最新五則太子集團新聞重點：\n"
    if not news_items:
        msg += "（取得新聞失敗或無相關新聞）\n"
    else:
        titles_for_summary = []
        for i,n in enumerate(news_items, start=1):
            title = (n.get('title') or '').strip()
            link = n.get('link') or ''
            # escape HTML characters in title
            import html
            safe_title = html.escape(title)
            safe_link = html.escape(link)
            msg += f"{i}. <a href=\"{safe_link}\">{safe_title}</a>\n"
            # prepare short title for summary
            short = title
            if len(short) > 80:
                short = short[:77] + '...'
            titles_for_summary.append(short)
        # concise summary line joining main topics
        summary = ' / '.join(titles_for_summary)
        msg += f"\n重點整理：{html.escape(summary)}\n"

    msg += "\n（資料來源：Open-Meteo / Google News RSS）"
    return msg


def send_telegram(text):
    token = TOKEN
    if not token:
        logger.error('TG_BOT_TOKEN not set')
        raise SystemExit('TG_BOT_TOKEN not set')
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {'chat_id': CHAT_ID, 'text': text}
    try:
        r = session.post(url, data=payload, timeout=TIMEOUT)
        r.raise_for_status()
        logger.info('Sent message to Telegram')
        return r.json()
    except Exception as e:
        logger.warning(f'send_telegram failed: {e}')
        raise


def run_once():
    data = fetch_weather()
    news = fetch_news()
    msg = format_message(data, news)
    resp = send_telegram(msg)
    return resp

if __name__=='__main__':
    logger.info('weather bot started')
    if TEST_MODE:
        logger.info(f'Running in TEST_MODE: interval={TEST_INTERVAL}s count={TEST_COUNT}')
        for i in range(TEST_COUNT):
            try:
                run_once()
                logger.info(f'Test send {i+1}/{TEST_COUNT} done')
            except Exception as e:
                logger.error(f'Error during test send: {e}')
            if i < TEST_COUNT-1:
                time.sleep(TEST_INTERVAL)
        logger.info('TEST_MODE completed')
        # after test mode, exit (we expect external scheduler for hourly runs)
        raise SystemExit('TEST_MODE finished')

    # Normal mode: send once per hour
    while True:
        try:
            run_once()
        except Exception as e:
            logger.error(f'Error during weather fetch/send: {e}')
            try:
                session.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage', data={'chat_id': CHAT_ID, 'text': f'天氣機器人發生錯誤：{e}'}, timeout=10)
            except Exception:
                logger.warning('Failed to send error message to Telegram')
        # sleep until next hour
        now = time.time()
        next_hour = ((int(now)//3600)+1)*3600
        sleep_seconds = max(60, next_hour - now)
        logger.info(f'sleeping for {sleep_seconds} seconds')
        time.sleep(sleep_seconds)
