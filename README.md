# 

# Telegram Reddit Media Downloader Bot

**Telegram Reddit Media Downloader Bot** is a Telegram bot that downloads and sends media (images, videos, and gifs) from Reddit posts directly to your Telegram chat. Built with Python, this bot utilizes the [`bulk-downloader-for-reddit
`](https://github.com/Serene-Arc/bulk-downloader-for-reddit) tool for media downloading and ensures seamless media handling with retry mechanisms and efficient logging.

#### Features:
- **Media Download**: Automatically downloads images, videos, and gifs from Reddit posts.
- **Retry Mechanism**: Handles Telegram's flood control with retry mechanisms.
- **Cleanup**: Cleans up downloaded files after sending them to ensure optimal storage usage.
- **URL Handling**: Processes both short and full Reddit URLs and resolves them to their final destinations.

#### Requirements:
- Python 3.x
- [`bdfr`](https://github.com/Serene-Arc/bulk-downloader-for-reddit) tool
- Telegram Bot API token

#### Installation:
1. Clone the repository:
   ```bash
   git clone https://github.com/ni3x/Telegram-Reddit-Media-Downloader-Bot.git
   cd Telegram-Reddit-Media-Downloader-Bot
   ```
2. Set up a virtual environment::
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
- For On Windows:
    ```bash
    .\venv\Scripts\activate
    ```
- On macOS/Linux:
    ```bash
    source venv/bin/activate
    ```
4. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
5. Configure the bot:
- Create a config.json file in the root directory with your Telegram Bot API token:
   ```json
   {
      "bot_token": "YOUR_TELEGRAM_BOT_API_TOKEN"
   } 
   ```
6. Run the bot::
   ```bash
   python main.py
   ```

### Usage
- Start the bot by sending the /start command in Telegram.
- Send any Reddit post link to the bot, and it will download and send the media to your chat.

### Contributing
- Feel free to submit issues or pull requests to improve the bot.
