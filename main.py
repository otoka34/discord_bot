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
print("===== 48時間以内の課題 =====")

for component in calendar.walk():

    if component.name == "VEVENT":

        title = str(component.get("summary"))
        course = component.get("categories").cats[0].to_ical().decode()
        deadline = component.get("dtstart").dt

        if now <= deadline <= limit:
            deadline_jst = deadline.astimezone(
                ZoneInfo("Asia/Tokyo")
        )
            deadline_str = deadline_jst.strftime(
                "%m/%d %H:%M"
            )
            message = (
                f"【{course}】\n"
                f"{title}\n"
                f"締切: {deadline_str}"
            )
            messages.append(message)

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

if messages:
    content = (
        "⚠️ 48時間以内に締切の課題があります\n\n"
        + "\n\n".join(messages)
    )
else:
    content = (
        "✅ 48時間以内に締切の課題はありません"
    )

requests.post(
    WEBHOOK_URL,
    json={
        "content": content
    }
)

print("通知送信完了")