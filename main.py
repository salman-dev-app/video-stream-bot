# main.py - Enhanced for Video Streaming Links

import os
import dropbox
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Setup Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Load Secure Tokens from Environment Variables (The secure method) ---
try:
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    DROPBOX_APP_KEY = os.environ['DROPBOX_APP_KEY']
    DROPBOX_APP_SECRET = os.environ['DROPBOX_APP_SECRET']
    DROPBOX_REFRESH_TOKEN = os.environ['DROPBOX_REFRESH_TOKEN']
except KeyError as e:
    logging.critical(f"FATAL ERROR: A secret key is missing: {e}. Go to Render.com -> Environment and add it.")
    exit()

# --- Flask Web Server to keep the bot alive on Render ---
app = Flask('')

@app.route('/')
def home():
    return "Streaming Bot is alive and running!"

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- Core Telegram Bot Logic ---

# Handles the /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello! I'm ready to work. Send or forward me any video or file.")

# This function now handles both videos and general files
async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    file_to_process = None
    original_file_name = None

    # Check if the message contains a video or a document
    if update.message.video:
        file_to_process = update.message.video
        original_file_name = file_to_process.file_name or f"telegram_video_{file_to_process.file_unique_id}.mp4"
    elif update.message.document:
        file_to_process = update.message.document
        original_file_name = file_to_process.file_name
    else:
        await update.message.reply_text("This doesn't seem to be a video or a file I can handle.")
        return

    # Let the user know the process has started
    msg = await update.message.reply_text(f"Processing '{original_file_name}'...")

    try:
        # Download the file into memory
        file_object = await file_to_process.get_file()
        file_content_bytes = await file_object.download_as_bytearray()
        
        await msg.edit_text("File downloaded. Uploading to Dropbox...")

        # Create a Dropbox client using the secure refresh token
        with dropbox.Dropbox(
            app_key=DROPBOX_APP_KEY,
            app_secret=DROPBOX_APP_SECRET,
            oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
        ) as dbx:
            # Define the path in your Dropbox
            dropbox_path = f'/Telegram Videos/{original_file_name}'
            
            # Upload the file
            dbx.files_upload(bytes(file_content_bytes), dropbox_path, mode=dropbox.files.WriteMode('overwrite'))
            
            await msg.edit_text("Upload complete! Generating a shareable link...")
            
            # --- Generate and Convert the Link ---
            # 1. Create a standard shareable link
            shared_link_metadata = dbx.sharing_create_shared_link_with_settings(dropbox_path)
            shared_link = shared_link_metadata.url
            
            # 2. Convert it to a direct, streamable link by replacing '?dl=0' with '?raw=1'
            # This is the magic trick you asked for!
            direct_stream_link = shared_link.replace('?dl=0', '?raw=1')
            
            # Send the final link to the user
            await msg.edit_text(
                f"✅ **Success!**\n\n"
                f"Your direct streamable link for **{original_file_name}** is ready:\n\n"
                f"`{direct_stream_link}`",
                parse_mode='Markdown'
            )

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        await msg.edit_text(f"❌ **Error:** Something went wrong. The developers have been notified.")

# --- Main function to start everything ---
def main():
    # Build the Telegram bot application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    # This single handler now triggers for both videos and documents
    application.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, media_handler))
    
    # Start the bot by polling for new messages
    application.run_polling()

if __name__ == '__main__':
    logging.info("Starting the bot...")
    # Start the web server in a background thread
    web_thread = threading.Thread(target=run_web_server)
    web_thread.start()
    
    # Start the Telegram bot in the main thread
    main()