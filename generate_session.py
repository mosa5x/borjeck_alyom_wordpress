# Add this to a new script called generate_session.py
from telethon.sync import TelegramClient
import os
import base64

api_id = '23070779'
api_hash = '4c836dc6445dac64290261600f685eb5'
phone_number = '+9647735875881'

with TelegramClient('the_alabrage_session', api_id, api_hash) as client:
    print("Client is running...")
    print("Please check your Telegram app for code...")
    client.sign_in(phone_number)
    
    # Get the session file data
    with open('the_alabrage_session.session', 'rb') as f:
        session_data = f.read()
    
    # Encode it to base64
    b64_session = base64.b64encode(session_data).decode('utf-8')
    print(f"Add this as your TELEGRAM_SESSION secret:\n{b64_session}")