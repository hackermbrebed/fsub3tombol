import os
import json
import uuid
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Load .env
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

BOT_USERNAME = os.getenv("BOT_USERNAME")  # contoh: myfsubbot

CHANNELS = [
    {"id": int(os.getenv("CHANNEL_ID_1")), "link": os.getenv("CHANNEL_LINK_1")},
    {"id": int(os.getenv("CHANNEL_ID_2")), "link": os.getenv("CHANNEL_LINK_2")},
    {"id": int(os.getenv("CHANNEL_ID_3")), "link": os.getenv("CHANNEL_LINK_3")},
]

DB_FILE = "database.json"

# Load database
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        VIDEOS = json.load(f)
else:
    VIDEOS = {}

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(VIDEOS, f, indent=2)

app = Client(
    "fsub-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

def get_fsub_keyboard(video_id):
    buttons = [
        [InlineKeyboardButton(f"🔗 Join Channel {i+1}", url=ch["link"])]
        for i, ch in enumerate(CHANNELS)
    ]
    buttons.append(
        [InlineKeyboardButton("🔄 Coba Lagi", callback_data=f"retry:{video_id}")]
    )
    return InlineKeyboardMarkup(buttons)

# ✅ Check FSub
async def check_fsub(client, user_id):
    for ch in CHANNELS:
        try:
            member = await client.get_chat_member(ch["id"], user_id)
            print(f"[DEBUG] User {user_id} di {ch['id']} → {member.status}")
            if member.status in ["kicked", "left"]:
                return False, f"🖕🏻 Lu belum join channel nyet! {ch['link']}"
        except Exception as e:
            print(f"[DEBUG] ERROR cek channel {ch['id']} → {e}")
            return False, f"⚠️ Bot perlu jadi admin dulu di channel ini nyet {ch['link']}"
    return True, None

# Admin add video
@app.on_message(filters.command("addvideo") & filters.reply)
async def add_video(client, message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("🖕🏻 Goblog lu bukan admin!")

    if not message.reply_to_message.video:
        return await message.reply("🖕🏻 Goblog reply videonya nyet!")

    file_id = message.reply_to_message.video.file_id
    video_id = str(uuid.uuid4())[:8]

    VIDEOS[video_id] = file_id
    save_db()

    deep_link = f"https://t.me/{BOT_USERNAME}?start={video_id}"

    await message.reply(
        f"✅ Video disimpan jink!\nNih linknya:\n{deep_link}",
        quote=True,
        disable_web_page_preview=True
    )

# Start handler with deep link
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    args = message.text.split()
    if len(args) == 1:
        return await message.reply("👋 Halo nyet! Gunakan link yang dikirim admin untuk nonton videonya.")

    video_id = args[1]
    if video_id not in VIDEOS:
        return await message.reply("⚠️ Videonya ga ada nyet!")

    user_id = message.from_user.id
    ok, reason = await check_fsub(client, user_id)

    if not ok:
        await message.reply(
            reason or "🖕🏻 Join channelnya dulu nyet!",
            reply_markup=get_fsub_keyboard(video_id)
        )
    else:
        await client.send_video(
            user_id,
            VIDEOS[video_id],
            caption=f"🎥 Nih videonya, jangan lupa ngocok ya."
        )

# Callback coba lagi
@app.on_callback_query(filters.regex(r"retry:(\w+)"))
async def retry_fsub(client, callback_query):
    user_id = callback_query.from_user.id
    video_id = callback_query.matches[0].group(1)

    if video_id not in VIDEOS:
        return await client.send_message(user_id, "⚠️ Videonya ga ada nyet!")

    ok, reason = await check_fsub(client, user_id)

    if not ok:
        await client.send_message(
            user_id,
            reason or "🖕🏻 Join channelnya dulu nyet!",
            reply_markup=get_fsub_keyboard(video_id)
        )
    else:
        await client.send_video(
            user_id,
            VIDEOS[video_id],
            caption=f"🎥 Nih videonya, jangan lupa ngocok ya."
        )

    try:
        await callback_query.message.delete()
    except:
        pass

# List video
@app.on_message(filters.command("listvideo"))
async def list_video(client, message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("🖕🏻 Goblog lu bukan admin!")

    if not VIDEOS:
        return await message.reply("📂 Belum ada video tersimpan nyet.")

    text = "📋 Daftar Video:\n\n"
    for vid in VIDEOS:
        text += f"- {vid} → https://t.me/{BOT_USERNAME}?start={vid}\n"

    await message.reply(text, disable_web_page_preview=True)

print("🤖 Bot FSub aktif dengan deep link!")
app.run()
