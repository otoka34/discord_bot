import os
import requests
from dotenv import load_dotenv
from icalendar import Calendar
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

load_dotenv()

ICAL_URL = os.getenv("ICAL_URL")
response = requests.get(ICAL_URL)
calendar = Calendar.from_ical(response.text)
now = datetime.now(timezone.utc)
limit = now + timedelta(hours=72)
messages = []
print("===== 72時間以内の課題 =====")

for component in calendar.walk():

    if component.name == "VEVENT":

        title = str(component.get("summary"))
        course = component.get("categories").cats[0].to_ical().decode()
        deadline = component.get("dtstart").dt

        if now <= deadline <= limit:
            deadline_jst = deadline.astimezone(
                ZoneInfo("Asia/Tokyo")
        )
            weekdays = ["月", "火", "水", "木", "金", "土", "日"]

            weekday = weekdays[deadline_jst.weekday()]

            deadline_str = deadline_jst.strftime(
                f"%m/%d({weekday}) %H:%M"
            )

            remaining = deadline_jst - datetime.now(
                ZoneInfo("Asia/Tokyo")
            )

            hours = int(remaining.total_seconds() // 3600)
            minutes = int(
                (remaining.total_seconds() % 3600) // 60
            )

            remaining_str = (
                f"あと {hours}時間{minutes}分"
            )

            if hours < 24:
                alert = "🔥"
            else:
                alert = ""

            message = (
                f"{alert}【{course}】\n"
                f"{title}\n"
                f"締切: {deadline_str}\n"
                f"{remaining_str}"
            )
            messages.append(message)

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

if messages:
    content = (
        "⚠️ 72時間以内に締切の課題があります\n\n"
        + "\n\n".join(messages)
    )
else:
    content = (
        "✅ 72時間以内に締切の課題はありません"
    )

requests.post(
    WEBHOOK_URL,
    json={
        "content": content
    }
)

print("通知送信完了")