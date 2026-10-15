
import os
import json
import requests
from pathlib import Path

YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]
YOUTUBE_CHANNEL_ID = os.environ["YOUTUBE_CHANNEL_ID"]
FACEBOOK_PAGE_ID = os.environ["FACEBOOK_PAGE_ID"]
FACEBOOK_PAGE_ACCESS_TOKEN = os.environ["FACEBOOK_PAGE_ACCESS_TOKEN"]

STATE_FILE = Path("last_live.txt")


def check_response(response, service_name):
    """แสดงรายละเอียดข้อผิดพลาด โดยไม่เปิดเผย API key หรือ access token"""
    if not response.ok:
        print(f"{service_name} API Error: HTTP {response.status_code}")

        try:
            error_data = response.json()
            print(
                json.dumps(
                    error_data,
                    ensure_ascii=False,
                    indent=2
                )
            )
        except ValueError:
            print(response.text[:2000])

        response.raise_for_status()


def find_live():
    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "channelId": YOUTUBE_CHANNEL_ID,
        "eventType": "live",
        "type": "video",
        "maxResults": 5,
        "key": YOUTUBE_API_KEY,
    }

    response = requests.get(url, params=params, timeout=30)
    check_response(response, "YouTube")

    data = response.json()
    items = data.get("items", [])

    if not items:
        print("ยังไม่พบไลฟ์สด")
        return None

    video = items[0]
    video_id = video["id"]["videoId"]
    title = video["snippet"]["title"]

    live = {
        "id": video_id,
        "title": title,
        "url": f"https://www.youtube.com/watch?v={video_id}",
    }

    print("ตรวจพบไลฟ์ YouTube:", live["title"])
    print("ลิงก์ไลฟ์:", live["url"])

    return live


def post_to_facebook(live):
    url = (
        f"https://graph.facebook.com/"
        f"v23.0/{FACEBOOK_PAGE_ID}/feed"
    )

    message = (
        "🔴 DONJUSTPLAY กำลังไลฟ์สด!\n\n"
        f"{live['title']}\n"
        "เข้ามารับชมกันได้เลยครับ 🎮"
    )

    response = requests.post(
        url,
        data={
            "message": message,
            "link": live["url"],
            "access_token": FACEBOOK_PAGE_ACCESS_TOKEN,
        },
        timeout=30,
    )

    # ถ้า Facebook ปฏิเสธโพสต์ จะแสดงสาเหตุจริงจาก API
    check_response(response, "Facebook")

    result = response.json()
    print("โพสต์ Facebook สำเร็จ")
    print("Post ID:", result.get("id"))


def main():
    # ตรวจสอบการตั้งค่าโดยไม่แสดงค่าความลับ
    required_settings = {
        "YOUTUBE_API_KEY": YOUTUBE_API_KEY,
        "YOUTUBE_CHANNEL_ID": YOUTUBE_CHANNEL_ID,
        "FACEBOOK_PAGE_ID": FACEBOOK_PAGE_ID,
        "FACEBOOK_PAGE_ACCESS_TOKEN": FACEBOOK_PAGE_ACCESS_TOKEN,
    }

    missing = [
        name for name, value in required_settings.items()
        if not value.strip()
    ]

    if missing:
        raise ValueError(
            "GitHub Secrets มีค่าว่าง: " + ", ".join(missing)
        )

    live = find_live()

    if live is None:
        return

    last_id = (
        STATE_FILE.read_text().strip()
        if STATE_FILE.exists()
        else ""
    )

    if live["id"] == last_id:
        print("ไลฟ์นี้โพสต์ไปแล้ว ไม่โพสต์ซ้ำ")
        return

    # บันทึก ID เฉพาะเมื่อโพสต์ Facebook สำเร็จ
    post_to_facebook(live)
    STATE_FILE.write_text(live["id"])
    print("บันทึกสถานะไลฟ์แล้ว")


if __name__ == "__main__":
    main()
