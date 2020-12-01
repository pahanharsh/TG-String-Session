import asyncio

from bot import bot, HU_APP
from pyromod import listen
from asyncio.exceptions import TimeoutError

from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    SessionPasswordNeeded, FloodWait,
    PhoneNumberInvalid, ApiIdInvalid,
    PhoneCodeInvalid, PhoneCodeExpired
)

API_TEXT = """Hi, {}.
This is Pyrogram's String Session Generator Bot. I will generate String Session of your Telegram Account.

By @Discovery_Updates

`Send your `API_ID` same as `APP_ID`.`"""
HASH_TEXT = "`Now send your `API_HASH`.`\n\nPress /cancel to Cancel Task."
PHONE_NUMBER_TEXT = (
    "Now send your Telegram account's Phone number in International Format. \n"
    "Including Country code. Example: **+14154566376**\n\n"
    "Press /cancel to Cancel Task."
)

@bot.on_message(filters.private & filters.command("start"))
async def genStr(_, msg: Message):
    chat = msg.chat
    api = await bot.ask(
        chat.id, API_TEXT.format(msg.from_user.mention)
    )
    if await is_cancel(msg, api.text):
        return
    try:
        check_api = int(api.text)
    except Exception:
        await api.delete()
        await msg.reply("`API_ID` is Invalid.\nPress /start to Start again.")
        return
    api_id = api.text
    await api.delete()
    hash = await bot.ask(chat.id, HASH_TEXT)
    if await is_cancel(msg, hash.text):
        return
    if not len(hash.text) >= 30:
        await hash.delete()
        await msg.reply("`API_HASH` is Invalid.\nPress /start to Start again.")
        return
    api_hash = hash.text
    await hash.delete()
    while True:
        number = await bot.ask(chat.id, PHONE_NUMBER_TEXT)
        if not number.text:
            continue
        if await is_cancel(msg, number.text):
            return
        phone = number.text
        await number.delete()
        confirm = await bot.ask(chat.id, f'`Is "{phone}" correct? (y/n):` \n\nSend: `y` (If Yes)\nSend: `n` (If No)')
        if await is_cancel(msg, confirm.text):
            return
        if "y" in confirm.text:
            await confirm.delete()
            break
    try:
        client = Client("my_account", api_id=api_id, api_hash=api_hash)
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`\nPress /start to create again.")
        return
    try:
        await client.connect()
    except ConnectionError:
        await client.disconnect()
        await client.connect()
    try:
        code = await client.send_code(phone)
        await asyncio.sleep(1)
    except FloodWait as e:
        await msg.reply(f"`Yu have floodwait of {e.x} Seconds`")
        return
    except ApiIdInvalid:
        await msg.reply("`Api Id and Api Hash are Invalid.`\n\nPress /start to create again.")
        return
    except PhoneNumberInvalid:
        await msg.reply("`your Phone Number is Invalid.`\n\nPress /start to create again.")
        return
    try:
        otp = await bot.ask(
            chat.id, ("`An otp is sent to your phone number, "
                      "Please enter otp in `1 2 3 4 5` format.`\n\n"
                      "`If Bot not sending OTP then try` /restart `cmd and again` /start `the Bot.`\n"
                      "Press /cancel to Cancel."), timeout=300)
    except TimeoutError:
        await msg.reply("`Time limit reached of 5 min.\nPress /start to create again.`")
        return
    if await is_cancel(msg, otp.text):
        return
    otp_code = otp.text
    await otp.delete()
    try:
        await client.sign_in(phone, code.phone_code_hash, phone_code=' '.join(str(otp_code)))
    except PhoneCodeInvalid:
        await msg.reply("`Invalid Code.`\n\nPress /start to create again.")
        return
    except PhoneCodeExpired:
        await msg.reply("`Code is Expired.`\n\nPress /start to create again.")
        return
    except SessionPasswordNeeded:
        try:
            two_step_code = await bot.ask(
                chat.id, 
                "`This account have two-step verification code.\nPlease enter your second factor authentication code.`\nPress /cancel to Cancel.",
                timeout=300
            )
        except TimeoutError:
            await msg.reply("`Time limit reached of 5 min.\n\nPress /start to create again.`")
            return
        if await is_cancel(msg, two_step_code.text):
            return
        new_code = two_step_code.text
        await two_step_code.delete()
        try:
            await client.check_password(new_code)
        except Exception as e:
            await msg.reply(f"**ERROR:** `{str(e)}`")
            return
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`")
        return
    try:
        session_string = await client.export_session_string()
        await client.send_message("me", f"#PYROGRAM #HU_STRING_SESSION\n\n```{session_string}```")
        await client.disconnect()
        text = "`String Session is Successfully Generated.\nClick on Button Below.`"
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Click Me", url=f"tg://openmessage?user_id={chat.id}")]]
        )
        await bot.send_message(chat.id, text, reply_markup=reply_markup)
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`")
        return


@bot.on_message(filters.private & filters.command("restart"))
async def restart(_, msg: Message):
    await msg.reply("`Restarting`")
    HU_APP.restart()


@bot.on_message(filters.private & filters.command("help"))
async def restart(_, msg: Message):
    out = f"""
Hello {msg.from_user.mention}, this is Pyrogram Session String Generator Bot \
which gives you `HU_STRING_SESSION` for your UserBot.

It needs `API_ID` , `API_HASH` , `PHONE_NUMBER` and `One time Verification Code` \
which will send to your `PHONE_NUMBER`.
you have to put `OTP` in `1 2 3 4 5` this format.

**NOTE:** `If bot not Sending Otp to your PHONE_NUMBER then try` 
/restart `Command and again` /start `your Process.`

(C) Author: [Krishna Singhal](https://t.me/Krishna_Singhal) and \
[UsergeTeam](https://t.me/TheUserge)
Give a Star ⭐️ to [REPO](https://github.com/Krishna-Singhal/genStr) if you like this Bot.
"""
    await msg.reply(out, disable_web_page_preview=True)


async def is_cancel(msg: Message, text: str):
    if text.startswith("/cancel"):
        await msg.reply("`Process Cancelled.`")
        return True
    return False

if __name__ == "__main__":
    bot.run()
