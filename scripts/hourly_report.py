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
def fetch_weather():
    url = 'https://api.open-meteo.com/v1/forecast'
    params = {'latitude':25.0330,'longitude':121.5654,'current_weather':'true','timezone':'Asia/Taipei','daily':'temperature_2m_max,temperature_2m_min,precipitation_sum'}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

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

# news
news_taizi = fetch_news('太子集團')
news_taiwan = fetch_news('台灣')
news_world = fetch_news('international OR world news')

# compose
lines = []
lines.append(f"<b>時間：</b>{now_time}")
lines.append(f"<b>現在天氣：</b> 溫度 {now_temp}°C，風速 約{now_wind} km/h")
lines.append(f"<b>明天天氣與穿衣建議：</b> 最高 {max_t}°C / 最低 {min_t}°C；建議：{clothing_advice(max_t, min_t, precip)}")
lines.append(f"<b>農民曆：</b> {lunar_placeholder()}")
lines.append(f"<b>今日運勢：</b> 金牛：{horoscope_template('Taurus')}  巨蟹：{horoscope_template('Cancer')}")

def format_news_section(title, items):
    s = [f"<b>{title}</b>"]
    if not items:
        s.append('無資料')
    else:
        for i,it in enumerate(items, start=1):
            # use HTML link
            import html
            t = html.escape(it['title'])
            l = html.escape(it['link'])
            s.append(f"{i}. <a href=\"{l}\">{t}</a>")
        # concise summary
        summary = ' / '.join([ (it['title'][:80] + '...') if len(it['title'])>80 else it['title'] for it in items ])
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
