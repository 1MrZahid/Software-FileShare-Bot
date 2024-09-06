from bot import Bot
from pyrogram.types import Message
from pyrogram import filters
from config import ADMINS, USER_REPLY_TEXT


@Bot.on_message(filters.private & filters.incoming)
async def useless(_,message: Message):
    if USER_REPLY_TEXT:
        await message.reply(USER_REPLY_TEXT)
