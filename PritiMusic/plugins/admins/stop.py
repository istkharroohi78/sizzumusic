from pyrogram import filters, Client
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus 

import config 
from PritiMusic import app # 🟢 Main bot ko pehchanne ke liye zaroori import
from PritiMusic.core.call import Lucky
from PritiMusic.utils.database import set_loop
from PritiMusic.utils.inline import close_markup
from config import BANNED_USERS
from PritiMusic.misc import db

# ✅ IMPORT NEW ADMIN CHECKER (For Clone Support)
from PritiMusic.cplugin.utils.decorators.admins import AdminRightsCheck

@Client.on_message(
    filters.command(
        ["end", "stop", "cend", "cstop"],
        prefixes=["/", "!", "#"],
    )
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck 
async def stop_music(cli: Client, message: Message, _, chat_id):
    
    # 🛑 THE CLASH FIX (CLONE BOT): Agar command Main Bot pe aayi hai, toh Clone bot chup rahega!
    try:
        if cli.me.id == app.id:
            return
    except Exception:
        pass

    # 🟢 PURE GROUP ADMIN CHECK (No SUDOERS)
    try:
        member = await cli.get_chat_member(chat_id, message.from_user.id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply_text("❌ **Sirf Admins hi is command ko use kar sakte hain!**")
    except Exception:
        return await message.reply_text("❌ **Error: Admin rights verify nahi ho paye.**")

    if len(message.command) != 1:
        return
    
    # Stream Stop Karega
    await Lucky.stop_stream(chat_id)
    
    # Loop Reset Karega
    await set_loop(chat_id, 0)
    
    # Queue Empty (Safety Fix)
    try:
        db[chat_id] = []
    except Exception:
        pass
        
    await message.reply_text(
        _["admin_5"].format(message.from_user.mention), reply_markup=close_markup(_)
    )
