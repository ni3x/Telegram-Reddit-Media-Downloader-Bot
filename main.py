import os
import re
import time
import shutil
import subprocess
import json
import requests
from urllib.parse import urlparse, urlunparse
from telegram import Update, Bot, InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.error import RetryAfter, TelegramError
from typing import List, Dict, Tuple, Union, Generator

def load_config(filename: str) -> Dict[str, str]:
    """Load the configuration from a JSON file."""
    with open(filename, 'r') as f:
        return json.load(f)

def load_allowed_users(filename: str) -> set:
    """Load the allowed user IDs from a JSON file."""
    with open(filename, 'r') as f:
        data = json.load(f)
    return set(data.get('allowed_users', []))

def download_reddit_media(reddit_url: str, download_dir: str) -> None:
    """Download media from a Reddit URL using bdfr."""
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    command = f'bdfr download -l {reddit_url} {download_dir} --no-dupes'
    print(f"Executing command: {command}")

    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        print("Command output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Command error: {e.stderr}")
        raise

async def start(update: Update, context: CallbackContext) -> None:
    """Send a start message to the user."""
    await update.message.reply_text("Send me a Reddit post link, and I'll download the media for you!")

def chunk_list(lst: List, chunk_size: int) -> Generator[List, None, None]:
    """Yield successive chunk_size chunks from lst."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

async def send_media(context: CallbackContext, chat_id: int, media_group: List[Union[InputMediaPhoto, InputMediaVideo, InputMediaDocument]]) -> None:
    """Send a media group with retry mechanism."""
    while True:
        try:
            await context.bot.send_media_group(chat_id=chat_id, media=media_group)
            break
        except RetryAfter as e:
            print(f"Flood control exceeded. Retrying in {e.retry_after} seconds...")
            time.sleep(e.retry_after)
        except TelegramError as e:
            print(f"Telegram error: {e.message}")
            break

async def send_animation(context: CallbackContext, chat_id: int, animation: InputFile) -> None:
    """Send an animation with retry mechanism."""
    while True:
        try:
            await context.bot.send_animation(chat_id=chat_id, animation=animation)
            break
        except RetryAfter as e:
            print(f"Flood control exceeded. Retrying in {e.retry_after} seconds...")
            time.sleep(e.retry_after)
        except TelegramError as e:
            print(f"Telegram error: {e.message}")
            break

def remove_query_parameters(url: str) -> str:
    """Remove query parameters from the URL."""
    parsed_url = urlparse(url)
    cleaned_url = urlunparse(
        (parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, '', '')
    )
    return cleaned_url

def get_final_url(url: str) -> str:
    """Resolve URL to its final destination and remove unnecessary parameters."""
    try:
        response = requests.head(url, allow_redirects=True)
        final_url = response.url
        return remove_query_parameters(final_url)
    except requests.RequestException as e:
        print(f"Error resolving URL: {e}")
        return url

async def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming messages, download and send media from Reddit links."""

    user_id = update.message.from_user.id
    
    users_path = 'users.json'
    allowed_users = load_allowed_users(users_path)

    if user_id not in allowed_users:
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    message_text = update.message.text
    chat_id = update.message.chat_id
    user_url_message = update.message.message_id

    print(f"Received message from chat_id {chat_id}: {message_text}")

    reddit_url_pattern = re.compile(r'https?://(www\.)?reddit\.com/r/\S+')
    match = reddit_url_pattern.search(message_text)

    if match:
        reddit_url = match.group(0)
        final_url = get_final_url(reddit_url)
        download_message = await update.message.reply_text("Downloading media...")

        download_dir = 'downloads'
        try:
            download_reddit_media(final_url, download_dir)
        except Exception as e:
            await context.bot.delete_message(chat_id=chat_id, message_id=download_message.message_id)
            await update.message.reply_text("Error downloading media.")
            print(f"Error: {e}")
            return

        await context.bot.delete_message(chat_id=chat_id, message_id=download_message.message_id)
        upload_message = await update.message.reply_text("Uploading media...")

        image_group, video_group, document_group, animation_files = categorize_files(download_dir)

        await send_media_groups(context, chat_id, image_group, video_group, document_group)
        await send_animations(context, chat_id, animation_files)

        shutil.rmtree(download_dir)

        await context.bot.delete_message(chat_id=chat_id, message_id=upload_message.message_id)
        await context.bot.delete_message(chat_id=chat_id, message_id=user_url_message)
        await update.message.reply_text("Media sent!")
        print(f"Completed processing for chat_id {chat_id}")
    else:
        await context.bot.delete_message(chat_id=chat_id, message_id=user_url_message)
        await update.message.reply_text("Please send a valid Reddit post link.")

def categorize_files(download_dir: str) -> Tuple[List[InputMediaPhoto], List[InputMediaVideo], List[InputMediaDocument], List[str]]:
    """Categorize files into images, videos, documents, and animations."""
    image_group, video_group, document_group, animation_files = [], [], [], []

    for root, _, files in os.walk(download_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)

            if file.lower().endswith(('.jpeg', '.jpg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.heif', '.heic', '.raw', '.cr2', '.nef', '.arw', '.orf', '.sr2', '.dng', '.eps', '.ai', '.pdf', '.svg', '.ico', '.emf', '.wmf', '.indd', '.psd', '.xpm', '.wbmp', '.j2k', '.jpf', '.jp2', '.j2c', '.pcx', '.pict', '.exif')):
                if file_size <= 50 * 1024 * 1024:  # Check file size limit
                    with open(file_path, 'rb') as f:
                        image_group.append(InputMediaPhoto(f))
            elif file.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.mpeg', '.mpg', '.m4v', '.3gp', '.rm', '.rmvb', '.ts', '.ogv', '.vob', '.m2ts', '.f4v', '.mts', '.asf', '.svi', '.yuv', '.dv', '.prx', '.mxf')):
                if file_size <= 50 * 1024 * 1024:  # Check file size limit
                    with open(file_path, 'rb') as f:
                        video_group.append(InputMediaVideo(f))
            elif file.lower().endswith('.gif'):
                if file_size <= 50 * 1024 * 1024:  # Check file size limit
                    animation_files.append(file_path)
            elif file_size <= 50 * 1024 * 1024:  # Check file size limit for documents
                with open(file_path, 'rb') as f:
                    document_group.append(InputMediaDocument(f))

    return image_group, video_group, document_group, animation_files

async def send_media_groups(context: CallbackContext, chat_id: int, image_group: List[InputMediaPhoto], video_group: List[InputMediaVideo], document_group: List[InputMediaDocument]) -> None:
    """Send media groups in chunks."""
    for media_group in chunk_list(image_group, 10):
        await send_media(context, chat_id, media_group)
    for media_group in chunk_list(video_group, 10):
        await send_media(context, chat_id, media_group)
    for media_group in chunk_list(document_group, 10):
        await send_media(context, chat_id, media_group)

async def send_animations(context: CallbackContext, chat_id: int, animation_files: List[str]) -> None:
    """Send animation files."""
    for animation_file in animation_files:
        with open(animation_file, 'rb') as f:
            animation = InputFile(f)
            await send_animation(context, chat_id, animation)

def main() -> None:
    """Main function to run the bot."""
    config = load_config('config.json')
    bot_token = config['bot_token']
   
    application = Application.builder().token(bot_token).build()
    print("Bot has started...")

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()