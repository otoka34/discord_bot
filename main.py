import os
import requests
from dotenv import load_dotenv
from icalendar import Calendar
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from dateutil.rrule import rrulestr

load_dotenv()

ICAL_URLS = [
    os.getenv("ICAL_URL_1"),
    os.getenv("ICAL_URL_2")
]

calendars = []

for url in ICAL_URLS:
    response = requests.get(url)
    calendars.append(Calendar.from_ical(response.text))

now = datetime.now(timezone.utc)
limit = now + timedelta(hours=168)
events = []

print("===== 1週間以内の課題 =====")

for calendar in calendars:
    for component in calendar.walk():
        if component.name == "VEVENT":
            title = str(component.get("summary"))
            categories = component.get("categories")

            if categories:
                course = categories.cats[0].to_ical().decode()
            else:
                course = ""

            dtstart = component.get("dtstart").dt
            
            # タイムゾーンをUTCに統一して計算するための準備
            if isinstance(dtstart, datetime):
                # タイムゾーンがない（naive）な場合はUTCにする
                if dtstart.tzinfo is None:
                    dtstart = dtstart.replace(tzinfo=timezone.utc)
                else:
                    dtstart = dtstart.astimezone(timezone.utc)
            else:
                # dtstart が date 型（終日予定）の場合、datetime に変換
                dtstart = datetime.combine(dtstart, datetime.min.time(), tzinfo=timezone.utc)

            # 繰り返しルールの解析
            rrule = component.get("rrule")
            deadlines = []

            if rrule:
                # 繰り返し予定の場合：指定期間内に発生する日時をすべてリストアップ
                # icalendarのrruleオブジェクトを文字列にしてdateutilに渡す
                rrule_str = f"DTSTART:{dtstart.strftime('%Y%m%dT%H%M%SZ')}\n" + rrule.to_ical().decode()
                try:
                    rule = rrulestr(rrule_str)
                    # now から limit までの間に発生する予定を抽出
                    for dt in rule.between(now, limit, inc=True):
                        deadlines.append(dt)
                except Exception as e:
                    print(f"繰り返し解析エラー ({title}): {e}")
            else:
                # 単発の予定の場合
                deadlines.append(dtstart)

            # 抽出したすべての締切日時について処理
            for deadline in deadlines:
                # 期間内かチェック (rrule.between を使っている場合は常にTrueになりますが念のため)
                if now <= deadline <= limit:
                    deadline_jst = deadline.astimezone(ZoneInfo("Asia/Tokyo"))
                    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
                    weekday = weekdays[deadline_jst.weekday()]

                    deadline_str = deadline_jst.strftime(f"%m/%d({weekday}) %H:%M")
                    remaining = deadline_jst - datetime.now(ZoneInfo("Asia/Tokyo"))

                    hours = int(remaining.total_seconds() // 3600)
                    minutes = int((remaining.total_seconds() % 3600) // 60)
                    remaining_str = f"あと {hours}時間{minutes}分"

                    if hours < 24:
                        alert = "🔥🔥🔥"
                    elif hours < 72:
                        alert = "🔥"
                    else:
                        alert = ""

                    if course:
                        message = f"{alert}【{course}】\n{title}\n締切: {deadline_str}\n{remaining_str}"
                    else:
                        message = f"{alert}{title}\n締切: {deadline_str}\n{remaining_str}"
                    
                    events.append((deadline_jst, message))

events.sort(key=lambda x: x[0])

messages = [
    message
    for _, message in events
]

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

if messages:
    content = (
        "⚠️ 1週間以内に締切の課題があります\n\n"
        + "\n\n".join(messages)
    )
else:
    content = (
        "✅ 1週間以内に締切の課題はありません"
    )

requests.post(
    WEBHOOK_URL,
    json={
        "content": content
    }
)

print("通知送信完了")