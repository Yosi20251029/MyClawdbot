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


def format_message(data):
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
    # next 12 hours — pick the first hourly time strictly after now in Asia/Taipei
    from datetime import datetime, timezone
    import pytz

    hourly = data.get('hourly',{})
    times = hourly.get('time',[])
    temps = hourly.get('temperature_2m',[])
    prec = hourly.get('precipitation_probability',[])
    winds = hourly.get('windspeed_10m',[])
    msg = cur_line + "\n未來 12 小時重點：\n"

    tz = pytz.timezone('Asia/Taipei')
    now_local = datetime.now(tz)

    # parse times into datetimes with timezone awareness
    time_objs = []
    for t in times:
        try:
            # fromisoformat works with offsets like +08:00; ensure UTC fallback
            dt = datetime.fromisoformat(t)
            if dt.tzinfo is None:
                # API should include timezone, but assume UTC if not
                dt = dt.replace(tzinfo=timezone.utc)
            # convert to local tz
            dt_local = dt.astimezone(tz)
            time_objs.append(dt_local)
        except Exception:
            time_objs.append(None)

    # find first index with time > now_local
    start_idx = None
    for i, dt in enumerate(time_objs):
        if dt is None:
            continue
        if dt > now_local:
            start_idx = i
            break
    if start_idx is None:
        # fallback: if no future times, start from end-12
        start_idx = max(0, len(times) - 12)

    for i in range(start_idx, min(len(times), start_idx + 12)):
        t = times[i]
        te = temps[i] if i < len(temps) else None
        pr = prec[i] if i < len(prec) else None
        wi = winds[i] if i < len(winds) else None
        if te is None:
            te_text = 'N/A'
        else:
            if TEMP_UNIT=='F': te = te*9/5+32
            te_text = f"{round(te,1)}°{TEMP_UNIT}"
        if pr is None:
            pr_text = 'N/A'
        else:
            pr_text = f"{pr}%"
        if wi is None:
            wi_text = 'N/A'
        else:
            if WIND_UNIT=='m/s': wi = round(wi/3.6,1)
            else: wi = round(wi,1)
            wi_text = f"{wi} {WIND_UNIT}"
        # format time for readability in local tz
        try:
            display_time = time_objs[i].strftime('%Y-%m-%d %H:%M') if time_objs[i] else t
        except Exception:
            display_time = t
        msg += f"- {display_time} — {te_text}，降雨機率 {pr_text}，風速 {wi_text}\n"
    msg += "\n（資料來源：Open-Meteo）"
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

if __name__=='__main__':
    logger.info('weather bot started')
    while True:
        try:
            data = fetch_weather()
            msg = format_message(data)
            send_telegram(msg)
        except Exception as e:
            logger.error(f'Error during weather fetch/send: {e}')
            # send minimal error notice (don't raise if sending fails)
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
