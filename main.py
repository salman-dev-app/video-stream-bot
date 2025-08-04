# main.py - TEMPORARY TOKEN GENERATOR

import os
import dropbox
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# শুধু এই তিনটি টোকেন দরকার
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
DROPBOX_APP_KEY = os.environ['DROPBOX_APP_KEY']
DROPBOX_APP_SECRET = os.environ['DROPBOX_APP_SECRET']

# /start কমান্ডের জন্য ফাংশন
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    auth_flow = dropbox.DropboxOAuth2Flow(
        consumer_key=DROPBOX_APP_KEY,
        consumer_secret=DROPBOX_APP_SECRET,
        redirect_uri=None, 
        session=None,
        csrf_token_session_key=None,
        token_access_type='offline'
    )
    auth_url = auth_flow.start()
    
    await update.message.reply_html(
        f"Hello {user.mention_html()}!\n\n"
        f"We need to re-authenticate with Dropbox to get a new valid token.\n\n"
        f"1. Please go to this link: <a href='{auth_url}'>Generate Auth Code</a>\n"
        f"2. Click 'Allow' on the Dropbox page.\n"
        f"3. Copy the code that Dropbox gives you.\n"
        f"4. Send it back to me using the command: /auth YOUR_COPIED_CODE\n\n"
        f"Example: `/auth aBcDeFgHiJkLmNoPqRsTuVwXyZ`"
    )

# /auth কমান্ডের জন্য ফাংশন
async def auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        auth_code = context.args[0].strip()
        auth_flow = dropbox.DropboxOAuth2Flow(
            consumer_key=DROPBOX_APP_KEY,
            consumer_secret=DROPBOX_APP_SECRET,
            redirect_uri=None, session=None, csrf_token_session_key=None
        )
        oauth_result = auth_flow.finish(auth_code)
        
        refresh_token = oauth_result.refresh_token
        
        await update.message.reply_text(
            "✅ **SUCCESS!**\n\n"
            "Here is your new, valid Refresh Token. Copy it carefully.\n\n"
            "Now, go to your Render.com dashboard -> Environment tab, and update the value of `DROPBOX_REFRESH_TOKEN` with this new token.\n\n"
            "After updating, revert the `main.py` code back to the final video bot code and redeploy."
        )
        await update.message.reply_text(f"`{refresh_token}`", parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("auth", auth))
    application.run_polling()

if __name__ == '__main__':
    main()
