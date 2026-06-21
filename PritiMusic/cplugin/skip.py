import random
from pyrogram import filters, Client
from pyrogram.types import Message

import config
from PritiMusic import app
from PritiMusic.core.call import Lucky
from PritiMusic.misc import db

# ✅ Jo zaroori hai wahi import kiya gaya hai
from PritiMusic.utils.database import get_loop
from PritiMusic.utils.decorators import AdminRightsCheck
from PritiMusic.utils.inline import close_markup
from PritiMusic.utils.stream.autoclear import auto_clean
from config import BANNED_USERS

# 🟢 THE FIX 1: @Client.on_message aur Prefixes add kiye for Main & Clone
@Client.on_message(
    filters.command(["skip", "cskip", "next", "cnext"], prefixes=["/", "!", "#"]) 
    & filters.group 
    & ~BANNED_USERS
)
@AdminRightsCheck
async def skip(cli: Client, message: Message, _, chat_id):
    
    # 🛑 YAHAN SE 'cli.me.id != app.id' WALA BLOCK HAMESHA KE LIYE HATA DIYA HAI 🛑

    # 1. Queue check karte hain
    check = db.get(chat_id)
    if not check:
        return await message.reply_text(_["queue_2"])
        
    # 2. Loop on/off check
    loop = await get_loop(chat_id)
    if loop != 0:
        return await message.reply_text(_["admin_8"])

    # 3. Multi-skip logic (jaise /skip 3)
    if len(message.command) > 1:
        state = message.text.split(None, 1)[1].strip()
        if state.isnumeric():
            state = int(state)
            count = len(check)
            if count > 2:
                count = int(count - 1)
                if 1 <= state <= count:
                    for x in range(state - 1): # (state-1) elements pop karenge
                        try:
                            popped = check.pop(0)
                            if popped:
                                await auto_clean(popped)
                        except:
                            pass
                else:
                    return await message.reply_text(_["admin_11"].format(count))
        else:
            return await message.reply_text(_["admin_10"])
    else:
        # Normal single skip ke case mein error avoid karne ke liye
        if len(check) == 1:
            pass # Aage badhne do, taaki aakhri track skip ho sake
        else:
            pass

    # 🟢 THE FIX 2: REAL FIX FOR CLONE & MAIN SYNC 🟢
    try:
        # 🔥 call.py ab khud automatic handle karega jab hum None pass karenge
        await Lucky.change_stream(None, chat_id)
        
    except Exception as e:
        # Agar koi internal error aata hai toh gracefully stop kar denge
        try:
            await message.reply_text(
                text=_["admin_6"].format(message.from_user.mention, message.chat.title),
                reply_markup=close_markup(_)
            )
            await Lucky.stop_stream(chat_id)
        except:
            pass
