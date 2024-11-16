import requests
import pandas as pd
from telegram import Bot
import asyncio
import io
import time
import os
import dotenv

# Telegram bot token and chat ID
dotenv.load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Google Spreadsheet CSV URL
SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1iqtAIifjaSurddhSkg_hlf-VydL7L-I8ccUETgEu5Tw/export?format=csv'

# Path to the local file storing titles
TITLE_FILE_PATH = 'titles.txt'

def fetch_spreadsheet_data():
    # Fetch data from the Google Spreadsheet
    response = requests.get(SPREADSHEET_URL)
    response.raise_for_status()
    data = pd.read_csv(io.StringIO(response.text), header=2)
    return data.dropna()

def get_new_titles(data):
    # Read previously stored titles
    try:
        with open(TITLE_FILE_PATH, 'r') as file:
            stored_titles = set(file.read().splitlines())
    except FileNotFoundError:
        stored_titles = set()

    # Extract current titles from the spreadsheet
    current_titles = set(data['Title'].tolist())

    # Find new titles that aren't in the stored titles
    new_titles = current_titles - stored_titles

    # Update the stored titles file
    with open(TITLE_FILE_PATH, 'w') as file:
        for title in current_titles:
            file.write(f"{title}\n")

    return new_titles

def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def generate_text(row):
    # Escape each field for HTML special characters
    title = escape_html(row["Title"].strip().upper())
    content_area = escape_html(row["Content Area"].strip())
    technology = escape_html(row["Technology"].strip())
    description = escape_html(row["Description"].strip())

    return f"\n✍️ <b>{title}</b> \n📚 {content_area} \n🚀 {technology}\n\n{description}"

async def send_new_title_notification(new_titles, data):
    data_new = data[data['Title'].isin(new_titles)].copy()
    texts = data_new.apply(generate_text, axis=1)
    message = "<b>Check out the new opportunities for DataCamp Instructors!</b>\n\n" + "\n\n".join(texts)

    bot = Bot(token=BOT_TOKEN)
    if new_titles:
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
    else:
        await bot.send_message(chat_id=CHAT_ID, text="No new titles found", parse_mode='HTML')

async def main():
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    data = fetch_spreadsheet_data()
    print("Data fetched successfully.")
    new_titles = get_new_titles(data)
    print("New titles scanned")
    await send_new_title_notification(new_titles, data)
    print("Message sent")

if __name__ == "__main__":
    asyncio.run(main())
