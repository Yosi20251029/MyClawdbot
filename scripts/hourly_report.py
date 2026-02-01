#!/usr/bin/env python3
"""
hourly_report.py
- Fetch current Taipei weather
- Fetch news for three categories (太子集團, 台灣, 國際)
- Generate clothing advice for tomorrow
- Produce a simple lunar/farm calendar note (placeholder)
- Generate horoscope snippets for Taurus and Cancer (template)
- Format message as HTML and (by default) print (dry-run). Sending to Telegram occurs when --send is passed and TG_BOT_TOKEN env is set.
"""
import requests, os, sys, argparse
from datetime import datetime, timedelta

parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', action='store_true', help='Print the report instead of sending')
parser.add_argument('--send', action='store_true', help='Send report to Telegram using TG_BOT_TOKEN')
args = parser.parse_args()

TG_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TG_CHAT = os.environ.get('TELEGRAM_CHAT_ID','533375854')

# helpers
def fetch_openweathermap(api_key, retries=2, timeout=30):
    # Call OpenWeatherMap Current + OneCall API (OneCall requires lat/lon)
    ow_url = 'https://api.openweathermap.org/data/2.5/onecall'
    params = {'lat':25.0330, 'lon':121.5654, 'units':'metric', 'exclude':'minutely', 'appid': api_key}
    last_exc = None
    for attempt in range(1, retries+1):
        try:
            r = requests.get(ow_url, params=params, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            # normalize to our expected shape
            cur = data.get('current', {})
            daily = data.get('daily', [])
            hourly = data.get('hourly', [])
            out = {}
            out['current_weather'] = {
                'time': datetime.fromtimestamp(cur.get('dt', 0)).isoformat(),
                'temperature': cur.get('temp'),
                'windspeed': cur.get('wind_speed')
            }
            if daily:
                out['daily'] = {
                    'temperature_2m_max': [d.get('temp',{}).get('max') for d in daily][:1],
                    'temperature_2m_min': [d.get('temp',{}).get('min') for d in daily][:1],
                    'precipitation_sum': [ (d.get('rain',0) + d.get('snow',0)) for d in daily][:1]
                }
            else:
                out['daily'] = {'temperature_2m_max':[None], 'temperature_2m_min':[None], 'precipitation_sum':[0]}
            # hourly precipitation probability not provided by OWM; use pop if present
            pop_list = [int(h.get('pop',0)*100) for h in hourly]
            out['hourly'] = {'precipitation_probability': pop_list}
            out['_source'] = 'openweathermap'
            return out
        except Exception as e:
            last_exc = e
            wait = 3 * attempt
            print(f'fetch_openweathermap: attempt {attempt} failed: {e}; retrying in {wait}s', file=sys.stderr)
            try:
                import time
                time.sleep(wait)
            except Exception:
                pass
    raise last_exc


def fetch_weather(retries=3, timeout=60):
    url = 'https://api.open-meteo.com/v1/forecast'
    params = {'latitude':25.0330,'longitude':121.5654,'current_weather':'true','timezone':'Asia/Taipei','daily':'temperature_2m_max,temperature_2m_min,precipitation_sum','hourly':'precipitation_probability'}
    last_exc = None
    for attempt in range(1, retries+1):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            data['_source'] = 'open-meteo'
            return data
        except Exception as e:
            last_exc = e
            wait = 5 * attempt
            print(f'fetch_weather: attempt {attempt} failed: {e}; retrying in {wait}s', file=sys.stderr)
            try:
                import time
                time.sleep(wait)
            except Exception:
                pass
    # all retries failed for open-meteo — try OpenWeatherMap if key available
    owm_key = os.environ.get('OPENWEATHER_API_KEY')
    if owm_key:
        try:
            print('fetch_weather: primary API failed, attempting OpenWeatherMap fallback', file=sys.stderr)
            return fetch_openweathermap(owm_key)
        except Exception as e:
            print(f'fetch_weather: OpenWeatherMap fallback failed: {e}', file=sys.stderr)
    # if no fallback or fallback failed, raise original
    raise last_exc

def fetch_news(query, max_items=5):
    rss_url = f'https://news.google.com/rss/search?q={requests.utils.requote_uri(query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'
    r = requests.get(rss_url, timeout=20)
    r.raise_for_status()
    import xml.etree.ElementTree as ET
    root = ET.fromstring(r.content)
    items = root.findall('.//item')[:max_items]
    out = []
    for it in items:
        title = it.find('title').text if it.find('title') is not None else ''
        link = it.find('link').text if it.find('link') is not None else ''
        out.append({'title': title, 'link': link})
    return out

def clothing_advice(max_t, min_t, precip):
    adv = []
    avg = (max_t + min_t)/2
    if avg >= 28:
        adv.append('短袖/薄外套')
    elif avg >= 20:
        adv.append('長袖/薄外套')
    else:
        adv.append('外套/保暖衣物')
    if precip > 30:
        adv.append('帶傘或雨具')
    return '，'.join(adv)

def lunar_placeholder():
    try:
        from lunardate import LunarDate
        today = datetime.now()
        ld = LunarDate.fromSolarDate(today.year, today.month, today.day)
        return f'農曆：{ld.year}年{ld.month}月{ld.day}日'
    except Exception:
        today = datetime.now()
        return f'農曆：暫無（lunardate not available） - {today.strftime("%Y-%m-%d")}'

def horoscope_template(sign):
    # deterministic simple horoscope based on date
    day_seed = int(datetime.now().strftime('%Y%m%d'))
    messages = {
        'Taurus': '工作穩定，適合處理財務與細節。',
        'Cancer': '情感豐富，適合跟家人聯繫，注意休息。'
    }
    return messages.get(sign, '')

# build report
weather = fetch_weather()
cur = weather.get('current_weather',{})
daily = weather.get('daily',{})
now_time = cur.get('time')
now_temp = cur.get('temperature')
now_wind = cur.get('windspeed')
max_t = daily.get('temperature_2m_max',[None])[0]
min_t = daily.get('temperature_2m_min',[None])[0]
precip = daily.get('precipitation_sum',[0])[0]

# determine tomorrow weather summary and precipitation probability
weather_summary = '未知'
precip_prob = None
try:
    # use daily precipitation_sum to decide rain vs clear
    if precip is not None and precip > 0.1:
        weather_summary = '雨天'
    else:
        # check hourly precipitation_probability for tomorrow (if available)
        hourly = weather.get('hourly',{})
        probs = hourly.get('precipitation_probability', [])
        if probs:
            maxp = max(probs)
            precip_prob = maxp
            if maxp >= 60:
                weather_summary = '大雨機率高'
            elif maxp >= 30:
                weather_summary = '有雨機率'
            else:
                weather_summary = '晴到多雲'
except Exception:
    weather_summary = '未知'

# news
news_taizi = fetch_news('太子集團')
news_taiwan = fetch_news('台灣')
news_world = fetch_news('international OR world news')

# compose
lines = []
lines.append(f"<b>時間：</b>{now_time}")
# weather source annotation
weather_source = weather.get('_source','open-meteo')
if weather_source == 'openweathermap':
    src_label = 'OpenWeatherMap（備援）'
else:
    src_label = 'Open‑Meteo（主來源）'
lines.append(f"<b>資料來源：</b> {src_label}")
# if using backup source, add caution note
if weather_source == 'openweathermap':
    lines.append('<b>備註：</b> 本次資料為備援來源（OpenWeatherMap），數值可能與主來源略有差異，請以當地實際狀況為準。')
lines.append(f"<b>現在天氣：</b> 溫度 {now_temp}°C，風速 約{now_wind} km/h")
if precip_prob is not None:
    lines.append(f"<b>明天天氣概況：</b> {weather_summary}（降雨機率最高 {precip_prob}%）")
else:
    lines.append(f"<b>明天天氣概況：</b> {weather_summary}")
lines.append(f"<b>明天天氣與穿衣建議：</b> 最高 {max_t}°C / 最低 {min_t}°C；建議：{clothing_advice(max_t, min_t, precip)}")
# Replace lunar section with TOEIC vocabulary practice
def sample_toeic_words(n=5, history_k=10):
    import random, json
    words = [
        {'word':'acquire','chi':'獲得；取得','example':'The company plans to acquire new assets next quarter.'},
        {'word':'allocate','chi':'分配；撥出','example':'We need to allocate more funds to marketing.'},
        {'word':'annual','chi':'每年的；年度的','example':'The annual report will be released in March.'},
        {'word':'benefit','chi':'利益；好處','example':'Employees receive health benefits.'},
        {'word':'comply','chi':'遵守','example':'All contractors must comply with the safety regulations.'},
        {'word':'contribute','chi':'貢獻；捐助','example':'She contributed significantly to the project.'},
        {'word':'deliver','chi':'交付；傳遞','example':'The courier will deliver the package by noon.'},
        {'word':'efficient','chi':'有效率的','example':'An efficient workflow saves time.'},
        {'word':'estimate','chi':'估計；估算','example':'Please provide an estimate for the repair costs.'},
        {'word':'negotiate','chi':'談判；協商','example':'They will negotiate the contract terms next week.'},
        {'word':'priority','chi':'優先事項；優先權','example':'Customer satisfaction is our top priority.'},
        {'word':'proposal','chi':'提案；建議','example':'Submit your proposal by the end of the month.'},
        {'word':'revenue','chi':'收入；營收','example':'The company reported increased revenue this quarter.'},
        {'word':'schedule','chi':'時間表；安排','example':'The meeting is scheduled for Friday.'},
        {'word':'strategic','chi':'策略性的','example':'They developed a strategic plan for expansion.'}
    ]
    history_path = os.path.join('memory','toeic_history.json')
    recent = []
    try:
        if os.path.exists(history_path):
            with open(history_path,'r',encoding='utf-8') as f:
                recent = json.load(f)
    except Exception:
        recent = []
    # build pool excluding recent words
    recent_set = set(recent[-history_k:]) if recent else set()
    pool = [w for w in words if w['word'] not in recent_set]
    if len(pool) < n:
        # not enough unique words, reset recent
        pool = words.copy()
        recent = []
    chosen = random.sample(pool, min(n, len(pool)))
    # update history
    recent_words = [w['word'] for w in chosen]
    recent.extend(recent_words)
    # keep only last history_k entries
    recent = recent[-history_k:]
    try:
        os.makedirs('memory', exist_ok=True)
        with open(history_path,'w',encoding='utf-8') as f:
            json.dump(recent, f, ensure_ascii=False)
    except Exception:
        pass
    return chosen

toeic = sample_toeic_words(5)

lines.append(f"<b>多益常考單字（5）</b>")
for w in toeic:
    import html
    word = html.escape(w['word'])
    chi = html.escape(w['chi'])
    ex = html.escape(w['example'])
    lines.append(f"- {word}：{chi}；例句：{ex}")

lines.append(f"<b>今日運勢：</b> 金牛：{horoscope_template('Taurus')}  巨蟹：{horoscope_template('Cancer')}")

def format_news_section(title, items):
    s = [f"<b>{title}</b>"]
    if not items:
        s.append('無資料')
    else:
        import re, html
        def clean_title(raw):
            t = raw.strip()
            # split on common separators (dash, em-dash, pipe) regardless of spaces
            parts = re.split(r"\s*[-–—|]\s*", t)
            t = parts[0]
            # also remove any trailing parentheses content
            t = re.sub(r"\s*\（.*\）\s*$", "", t)
            return t
        for i,it in enumerate(items, start=1):
            raw = it.get('title','')
            link = it.get('link','')
            text = html.escape(clean_title(raw))
            href = html.escape(link)
            s.append(f"{i}. <a href=\"{href}\">{text}</a>")
        # concise summary (cleaned)
        summary = ' / '.join([ (clean_title(it['title'])[:80] + '...') if len(clean_title(it['title']))>80 else clean_title(it['title']) for it in items ])
        s.append(f"重點整理：{html.escape(summary)}")
    return '\n'.join(s)

lines.append(format_news_section('太子集團新聞重點', news_taizi))
lines.append(format_news_section('台灣新聞重點', news_taiwan))
lines.append(format_news_section('國際新聞重點', news_world))

message = '\n\n'.join(lines)

if args.dry_run:
    print('--- DRY RUN: hourly report ---')
    print(message)
    sys.exit(0)

# send
if args.send:
    if not TG_TOKEN:
        print('TG token not set; aborting send')
        sys.exit(1)
    send_url = f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage'
    res = requests.post(send_url, data={'chat_id': TG_CHAT, 'text': message, 'parse_mode':'HTML', 'disable_web_page_preview': True})
    res.raise_for_status()
    print('sent')
else:
    print('no action; use --send to deliver')
