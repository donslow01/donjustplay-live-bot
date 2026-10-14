
import os
import json
import requests
from pathlib import Path

YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]
YOUTUBE_CHANNEL_ID = os.environ["YOUTUBE_CHANNEL_ID"]
FACEBOOK_PAGE_ID = os.environ["FACEBOOK_PAGE_ID"]
FACEBOOK_PAGE_ACCESS_TOKEN = os.environ["FACEBOOK_PAGE_ACCESS_TOKEN"]

STATE_FILE = Path("last_live.txt")


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
    response.raise_for_status()
    data = response.json()

    items = data.get("items", [])
    if not items:
        print("ยังไม่พบไลฟ์สด")
        return None

    video = items[0]
    video_id = video["id"]["videoId"]
    title = video["snippet"]["title"]

    return {
        "id": video_id,
        "title": title,
        "url": f"https://www.youtube.com/watch?v={video_id}",
    }


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
    response.raise_for_status()
    print("โพสต์ Facebook สำเร็จ:", response.json())


def main():
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

    post_to_facebook(live)
    STATE_FILE.write_text(live["id"])
    print("บันทึกสถานะไลฟ์แล้ว")


if __name__ == "__main__":
    main()
