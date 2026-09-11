import os
import re
import json
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import ChannelPrivateError, UsernameInvalidError

CHANNELS_FILE = "channels.json"
OUTPUT_FILE = "sub.txt"

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]


def load_channels():
    try:
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                print(f"✅ {len(data)} کانال بارگذاری شد.")
                return data
            print("⚠️ فرمت channels.json باید لیست باشه.")
    except FileNotFoundError:
        print(f"❌ فایل {CHANNELS_FILE} پیدا نشد.")
    except json.JSONDecodeError as e:
        print(f"❌ خطا در JSON: {e}")
    return []


def extract_links(text):
    if not text:
        return []
    patterns = [
        r"vless://[^\s]+",
        r"vmess://[^\s]+",
        r"trojan://[^\s]+",
        r"ss://[^\s]+",
    ]
    links = []
    for p in patterns:
        links += re.findall(p, text)
    return links


async def main():
    channels = load_channels()
    if not channels:
        print("❌ هیچ کانالی برای بررسی نیست.")
        return

    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()
    print("✅ اتصال به تلگرام برقرار شد.")

    configs = set()

    for channel in channels:
        print(f"📡 بررسی: {channel}")
        try:
            async for msg in client.iter_messages(channel, limit=100):
                if msg.message:
                    found = extract_links(msg.message)
                    if found:
                        configs.update(found)
        except (ChannelPrivateError, UsernameInvalidError):
            print(f"⛔️ دسترسی به {channel} ممکن نیست.")
        except Exception as e:
            print(f"⚠️ خطا در {channel}: {type(e).__name__} - {e}")
        await asyncio.sleep(1)

    await client.disconnect()
    print("✅ اتصال تلگرام قطع شد.")

    if not configs:
        print("ℹ️ هیچ لینکی پیدا نشد.")
        return

    old = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            old = set(line.strip() for line in f if line.strip())

    merged = old | configs
    new_count = len(merged) - len(old)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(merged)))

    print(f"✅ ذخیره شد → {OUTPUT_FILE}")
    print(f"📊 کل: {len(merged)} | جدید: {new_count}")


if __name__ == "__main__":
    asyncio.run(main())
