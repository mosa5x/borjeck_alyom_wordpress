import logging
import asyncio
import json
import os
import base64
import requests
import time
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from datetime import datetime, timedelta
import re
import pytz
import argparse
from dataclasses import dataclass, asdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram API credentials
api_id = os.environ.get('TELEGRAM_API_ID', '23070779')
api_hash = os.environ.get('TELEGRAM_API_HASH', '4c836dc6445dac64290261600f685eb5')
phone_number = os.environ.get('TELEGRAM_PHONE', '+9647735875881')

# WordPress API credentials
wp_base_url = os.environ.get('WP_BASE_URL', 'https://al-unwan.com/wp-json/wp/v2')
username = os.environ.get('WP_USERNAME', 'mosasatar88@gmail.com')
app_password = os.environ.get('WP_APP_PASSWORD', 'HkNZvBkU8mzA5eQbyGQZpIVQ')
category_id = 33

# Prepare the authorization header
auth_string = f"{username}:{app_password}"
auth_bytes = auth_string.encode('ascii')
auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
auth_header = f"Basic {auth_b64}"

# Headers for the API request
wp_headers = {
    'Authorization': auth_header
}

# Scraping parameters
channels = ['A_Nl8']
key_search = ''  # Keyword to search
max_t_index = 1000000  # Maximum number of messages to scrape
time_limit = 6 * 60 * 60  # Timeout in seconds (6 hours)

# Data directory
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Baghdad timezone
baghdad_tz = pytz.timezone('Asia/Baghdad')

# Image mapping for WordPress
image_mapping = {
    "Aquarius": "aquarius.webp",
    "Aries": "aries.png",
    "Cancer": "cancer.png",
    "Capricorn": "capricorn.png",
    "Gemini": "gemeni.png",  # Note the spelling difference (gemeni.png vs Gemini)
    "Leo": "leo.png",
    "Libra": "libra.png",
    "Pisces": "pisces.png",
    "Sagittarius": "sagittarius.png",
    "Scorpio": "scorpio.png",
    "Taurus": "taurus.png",
    "Virgo": "virgo.png"
}

# Arabic month names mapping
arabic_months = {
    1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو",
    7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
}

@dataclass
class Horoscope:
    name_ar: str
    name_en: str
    symbol: str
    date: str
    content: str
    professional_percentage: int
    financial_percentage: int
    emotional_percentage: int
    health_percentage: int = None
    message_id: int = None
    html_content: str = None  # Added field for HTML content

def format_date(date_str):
    """Format date string into Arabic date format"""
    try:
        # Parse the date (assuming format is YYYY-MM-DD)
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        # Get day, month, year
        day = date_obj.day
        month = arabic_months[date_obj.month]
        year = date_obj.year
        # Return formatted date string
        return f"{day} {month} {year}"
    except:
        # If there's any error, return the original date string
        return date_str

def remove_unsupported_characters(text):
    """Remove characters that might cause issues in XML or JSON"""
    valid_xml_chars = (
        "[^\u0009\u000A\u000D\u0020-\uD7FF\uE000-\uFFFD"
        "\U00010000-\U0010FFFF]"
    )
    return re.sub(valid_xml_chars, '', str(text))

def clean_horoscope_content(content):
    """Remove unwanted content from horoscope text"""
    lines = content.split('\n')
    cleaned_lines = [line for line in lines if not (
        line.strip().startswith(':-') or 
        '@' in line or 
        'TELE' in line or
        'http' in line or
        'لطلب التمويل' in line or
        line.strip() == ''  # Remove empty lines
    )]
    return '\n'.join(cleaned_lines).strip()

def generate_attractive_html(horoscope):
    """Generate attractive HTML for the horoscope data without header and redundant percentages"""
    # Parse content to separate main text and emotional section
    main_content = horoscope.content
    emotional_content = ""
    
    # Extract emotional section if it exists using regex
    emotional_match = re.search(r'عاطفيا\s*[🤕😊😢😍🙂]*\s*(.*?)(?=\n\n|$)', main_content, re.DOTALL)
    if emotional_match:
        emotional_content = emotional_match.group(1).strip()
        # Remove the emotional section from main_content
        main_content = re.sub(r'عاطفيا\s*[🤕😊😢😍🙂]*\s*.*?(?=\n\n|$)', '', main_content, flags=re.DOTALL).strip()
    
    # Create the HTML with inline styles - without the purple header
    html = f"""<div dir="rtl" style="max-width: 100%; margin: 20px auto; font-family: 'Noto Sans Arabic', 'Segoe UI', Tahoma, sans-serif; background: white; border-radius: 10px; box-shadow: 0 2px 20px rgba(0,0,0,0.08); overflow: hidden;">
    <!-- Content -->
    <div style="padding: 25px 20px;">
        <!-- Main Text -->
        <p style="font-size: 17px; line-height: 1.8; margin-bottom: 25px; color: #333; text-align: right;">{main_content}</p>
        
        <!-- Emotional Section -->
        <div style="background-color: #f6f4ff; border-right: 5px solid #6b5ce7; border-radius: 8px; padding: 18px; margin: 25px 0; position: relative;">
            <h3 style="color: #6b5ce7; margin: 0 0 10px 0; font-size: 18px; display: inline-block;">عاطفيا</h3>
            <span style="font-size: 24px; margin-right: 5px; vertical-align: middle;">🤕</span>
            <p style="margin: 10px 0 0 0; color: #444; line-height: 1.7; font-size: 16px;">{emotional_content}</p>
        </div>
        
        <!-- Percentages Section -->
        <div style="margin-top: 30px; background-color: #fafafa; border-radius: 8px; padding: 20px;">
            <h3 style="color: #6b5ce7; text-align: center; margin-top: 0; margin-bottom: 20px; font-size: 20px; font-weight: 700;">النسبة المئوية</h3>
            
            <!-- Professional -->
            <div style="margin-bottom: 18px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-weight: 600; color: #444; font-size: 16px;">مهنيا</span>
                    <span style="font-weight: 700; color: #6b5ce7; font-size: 16px;">{horoscope.professional_percentage}%</span>
                </div>
                <div style="height: 10px; background-color: #e9e5ff; border-radius: 5px; overflow: hidden;">
                    <div style="width: {horoscope.professional_percentage}%; height: 100%; background: linear-gradient(to right, #6b5ce7, #a599f7); border-radius: 5px;"></div>
                </div>
            </div>
            
            <!-- Financial -->
            <div style="margin-bottom: 18px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-weight: 600; color: #444; font-size: 16px;">ماليا</span>
                    <span style="font-weight: 700; color: #4a9fff; font-size: 16px;">{horoscope.financial_percentage}%</span>
                </div>
                <div style="height: 10px; background-color: #e5f0ff; border-radius: 5px; overflow: hidden;">
                    <div style="width: {horoscope.financial_percentage}%; height: 100%; background: linear-gradient(to right, #4a9fff, #73b5ff); border-radius: 5px;"></div>
                </div>
            </div>
            
            <!-- Emotional -->
            <div style="margin-bottom: 18px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-weight: 600; color: #444; font-size: 16px;">عاطفيا</span>
                    <span style="font-weight: 700; color: #ff6b9d; font-size: 16px;">{horoscope.emotional_percentage}%</span>
                </div>
                <div style="height: 10px; background-color: #ffe5ef; border-radius: 5px; overflow: hidden;">
                    <div style="width: {horoscope.emotional_percentage}%; height: 100%; background: linear-gradient(to right, #ff6b9d, #ff97bb); border-radius: 5px;"></div>
                </div>
            </div>"""
    
    # Add health section if available
    if horoscope.health_percentage:
        html += f"""
            <!-- Health -->
            <div style="margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-weight: 600; color: #444; font-size: 16px;">صحيا</span>
                    <span style="font-weight: 700; color: #4cd964; font-size: 16px;">{horoscope.health_percentage}%</span>
                </div>
                <div style="height: 10px; background-color: #e5ffe9; border-radius: 5px; overflow: hidden;">
                    <div style="width: {horoscope.health_percentage}%; height: 100%; background: linear-gradient(to right, #4cd964, #83e895); border-radius: 5px;"></div>
                </div>
            </div>"""
    
    # Close the HTML
    html += """
        </div>
    </div>
</div>"""
    
    return html

def extract_horoscope_data(content, message_id=None, date_str=None):
    """Extract horoscope data from message content and skip redundant percentage text"""
    zodiac_map = {
        'الحمل': ('Aries', '♈'),
        'الثور': ('Taurus', '♉'),
        'الجوزاء': ('Gemini', '♊'),
        'السرطان': ('Cancer', '♋'),
        'الأسد': ('Leo', '♌'),
        'العذراء': ('Virgo', '♍'),
        'الميزان': ('Libra', '♎'),
        'العقرب': ('Scorpio', '♏'),
        'القوس': ('Sagittarius', '♐'),
        'الجدي': ('Capricorn', '♑'),
        'الدلو': ('Aquarius', '♒'),
        'الحوت': ('Pisces', '♓'),
    }
    
    horoscopes = []
    for arabic_name, (english_name, symbol) in zodiac_map.items():
        pattern = rf"#{arabic_name}\s*{symbol}(.*?)(#|$)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            logger.warning(f"Could not find horoscope for {english_name}")
            continue
            
        horoscope_text = match.group(1).strip()
        cleaned_horoscope_text = clean_horoscope_content(horoscope_text)
        
        # Extract and remove percentage section from content
        percentage_pattern = r'■النسبة المئوية.*?(?=\n\n|$)'
        cleaned_horoscope_text = re.sub(percentage_pattern, '', cleaned_horoscope_text, flags=re.DOTALL).strip()
        
        logger.debug(f"Found horoscope for {english_name}: {cleaned_horoscope_text[:100]}...")
        
        # Try both patterns for percentages
        percentages_match = re.search(
            r'[●◾]مهنيا.*?(\d+).*?[●◾]ماليا.*?(\d+).*?[●◾]عاطفيا.*?(\d+)(?:.*?[●◾]صحيا.*?(\d+))?|'
            r'مهنيا%(\d+).*?ماليا%(\d+).*?عاطفيا%(\d+)(?:.*?صحيا%(\d+))?',
            horoscope_text,  # Use the original text to extract percentages
            re.DOTALL
        )
        
        if not percentages_match:
            logger.warning(f"Could not extract percentages for {english_name}. Horoscope text: {cleaned_horoscope_text}")
            continue
            
        # Get all groups and use the first non-None set
        groups = percentages_match.groups()
        if groups[0] is not None:
            percentages = groups[:4]
        else:
            percentages = groups[4:]
        
        logger.debug(f"Extracted percentages for {english_name}: {percentages}")
        
        # Handle case where health percentage is not present
        health_percentage = int(percentages[3]) if percentages[3] is not None else None
        
        date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').date() if date_str else datetime.now().date()
        
        horoscope = Horoscope(
            name_ar=arabic_name,
            name_en=english_name,
            symbol=symbol,
            date=date.isoformat(),
            content=cleaned_horoscope_text,
            professional_percentage=int(percentages[0]),
            financial_percentage=int(percentages[1]),
            emotional_percentage=int(percentages[2]),
            health_percentage=health_percentage,
            message_id=message_id
        )
        
        # Generate HTML content for the horoscope
        horoscope.html_content = generate_attractive_html(horoscope)
        
        horoscopes.append(horoscope)
        logger.info(f"Processed horoscope for {english_name} on {date}")
        
    return horoscopes

def upload_image(horoscope):
    """Upload the horoscope image and return the media ID"""
    # Get the English name to find the correct image
    name_en = horoscope.name_en
    
    # Find the corresponding image filename
    if name_en in image_mapping:
        image_filename = image_mapping[name_en]
        image_path = os.path.join(DATA_DIR, 'images', image_filename)
        
        # Check if the image file exists
        if not os.path.exists(image_path):
            logger.warning(f"Image file {image_path} not found for {name_en}.")
            return None
        
        # Prepare headers (without Content-Type for file upload)
        upload_headers = {
            'Authorization': auth_header
        }
        
        # Prepare the image file
        with open(image_path, 'rb') as image_file:
            files = {
                'file': (image_filename, image_file, 
                        'image/webp' if image_filename.endswith('.webp') else 'image/png')
            }
            
            # Prepare the title
            formatted_date = format_date(horoscope.date)
            title = f"برج {horoscope.name_ar} {horoscope.symbol} - {formatted_date}"
            
            # Additional metadata
            data = {
                'title': title,
                'alt_text': title,
                'caption': title
            }
            
            # Upload the image
            logger.info(f"Uploading image for {horoscope.name_ar}...")
            upload_url = f"{wp_base_url}/media"
            response = requests.post(upload_url, headers=upload_headers, files=files, data=data)
            
            # Check if upload was successful
            if response.status_code >= 200 and response.status_code < 300:
                media_id = response.json().get('id')
                logger.info(f"Image uploaded successfully! Media ID: {media_id}")
                return media_id
            else:
                logger.error(f"Image upload failed! Status code: {response.status_code}")
                logger.error(f"Error: {response.text}")
                return None
    else:
        logger.warning(f"No image mapping found for {name_en}.")
        return None

def post_horoscope_to_wordpress(horoscope):
    """Post a horoscope to WordPress using the REST API with HTML content"""
    # Format the date for display
    formatted_date = format_date(horoscope.date)
    
    # Prepare the title
    title = f"توقعات برج {horoscope.name_ar} {horoscope.symbol} ليوم {formatted_date}"
    
    # Step 1: Upload the image if available
    media_id = upload_image(horoscope)
    
    # Step 2: Prepare the post data
    post_data = {
        'title': title,
        'content': horoscope.html_content,  # Use the HTML formatted content
        'status': 'publish',
        'categories': [category_id]  # Add to specific category
    }
    
    # Add featured image if media_id is provided
    if media_id:
        post_data['featured_media'] = media_id
    
    # Convert the data to JSON
    headers_with_content_type = wp_headers.copy()
    headers_with_content_type['Content-Type'] = 'application/json'
    
    # Step 3: Make the POST request
    logger.info(f"Posting horoscope for {horoscope.name_ar} to WordPress...")
    post_url = f"{wp_base_url}/posts"
    response = requests.post(post_url, headers=headers_with_content_type, json=post_data)
    
    # Check if post was successful
    if response.status_code >= 200 and response.status_code < 300:
        post_id = response.json().get('id')
        post_link = response.json().get('link', 'unknown')
        logger.info(f"✓ Success! Post ID: {post_id}")
        logger.info(f"  Post URL: {post_link}")
        return True
    else:
        logger.error(f"✗ Failed! Status code: {response.status_code}")
        logger.error(f"Error: {response.text}")
        return False

def extract_horoscope_data(content, message_id=None, date_str=None):
    """Extract horoscope data from message content and completely remove percentage text section"""
    zodiac_map = {
        'الحمل': ('Aries', '♈'),
        'الثور': ('Taurus', '♉'),
        'الجوزاء': ('Gemini', '♊'),
        'السرطان': ('Cancer', '♋'),
        'الأسد': ('Leo', '♌'),
        'العذراء': ('Virgo', '♍'),
        'الميزان': ('Libra', '♎'),
        'العقرب': ('Scorpio', '♏'),
        'القوس': ('Sagittarius', '♐'),
        'الجدي': ('Capricorn', '♑'),
        'الدلو': ('Aquarius', '♒'),
        'الحوت': ('Pisces', '♓'),
    }
    
    horoscopes = []
    for arabic_name, (english_name, symbol) in zodiac_map.items():
        pattern = rf"#{arabic_name}\s*{symbol}(.*?)(#|$)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            logger.warning(f"Could not find horoscope for {english_name}")
            continue
            
        horoscope_text = match.group(1).strip()
        
        # Extract percentages before cleaning the content
        # Try both patterns for percentages
        percentages_match = re.search(
            r'[●◾]مهنيا.*?(\d+).*?[●◾]ماليا.*?(\d+).*?[●◾]عاطفيا.*?(\d+)(?:.*?[●◾]صحيا.*?(\d+))?|'
            r'مهنيا%(\d+).*?ماليا%(\d+).*?عاطفيا%(\d+)(?:.*?صحيا%(\d+))?',
            horoscope_text,
            re.DOTALL
        )
        
        if not percentages_match:
            logger.warning(f"Could not extract percentages for {english_name}. Horoscope text: {horoscope_text[:100]}...")
            continue
            
        # Get all groups and use the first non-None set
        groups = percentages_match.groups()
        if groups[0] is not None:
            percentages = groups[:4]
        else:
            percentages = groups[4:]
        
        logger.debug(f"Extracted percentages for {english_name}: {percentages}")
        
        # Handle case where health percentage is not present
        health_percentage = int(percentages[3]) if percentages[3] is not None else None
        
        # Now clean the content and remove the percentages section
        cleaned_horoscope_text = clean_horoscope_content(horoscope_text)
        
        # Remove the percentage section that appears at the end
        # Pattern to match: ■النسبة المئوية followed by percentage lines
        cleaned_horoscope_text = re.sub(
            r'■النسبة المئوية.*?(?=\n\n|$)', 
            '', 
            cleaned_horoscope_text, 
            flags=re.DOTALL
        ).strip()
        
        # Also try to remove any other percentage formats that might appear
        cleaned_horoscope_text = re.sub(
            r'●مهنيا%\d+.*?●ماليا%\d+.*?●عاطفيا%\d+(?:.*?●صحيا%\d+)?', 
            '', 
            cleaned_horoscope_text, 
            flags=re.DOTALL
        ).strip()
        
        date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').date() if date_str else datetime.now().date()
        
        horoscope = Horoscope(
            name_ar=arabic_name,
            name_en=english_name,
            symbol=symbol,
            date=date.isoformat(),
            content=cleaned_horoscope_text,
            professional_percentage=int(percentages[0]),
            financial_percentage=int(percentages[1]),
            emotional_percentage=int(percentages[2]),
            health_percentage=health_percentage,
            message_id=message_id
        )
        
        # Generate HTML content for the horoscope
        horoscope.html_content = generate_attractive_html(horoscope)
        
        horoscopes.append(horoscope)
        logger.info(f"Processed horoscope for {english_name} on {date}")
        
    return horoscopes

async def scrape_and_publish_horoscopes(client, channel, start_date, end_date):
    """Scrape messages from a Telegram channel, extract horoscopes, and publish directly to WordPress"""
    logger.info(f"Scraping channel: {channel}")
    
    try:
        entity = await client.get_entity(channel)
        logger.info(f"Successfully got entity for channel: {channel}")
    except ValueError as e:
        logger.error(f"Could not find entity for {channel}: {str(e)}")
        return []
        
    logger.info(f"Scraping messages from {start_date} to {end_date}")
    
    t_index = 0
    start_time = time.time()
    all_horoscopes = []
    published_count = 0
    
    async for message in client.iter_messages(entity, search=key_search):
        # Convert message date to Baghdad timezone
        message_date = message.date.astimezone(baghdad_tz)
        
        if t_index >= max_t_index or time.time() - start_time > time_limit:
            logger.info(f"Reached limit for channel {channel}. Stopping.")
            break
            
        if start_date < message_date <= end_date:
            # Only process messages with text
            if message.text:
                cleaned_content = remove_unsupported_characters(message.text)
                date_time = message_date.strftime('%Y-%m-%d %H:%M:%S')
                
                # Extract horoscopes directly from the message
                horoscopes = extract_horoscope_data(cleaned_content, message.id, date_time)
                
                if horoscopes:
                    logger.info(f"Found {len(horoscopes)} horoscopes in message {message.id}")
                    
                    # Immediately publish each horoscope to WordPress
                    for horoscope in horoscopes:
                        success = post_horoscope_to_wordpress(horoscope)
                        if success:
                            published_count += 1
                        
                        # Add a short delay between posts to prevent overwhelming the server
                        time.sleep(3)
                    
                    # Keep track of horoscopes for backup purposes
                    all_horoscopes.extend(horoscopes)
                
                t_index += 1
                if t_index % 10 == 0:
                    logger.info(f"Processed {t_index} messages from {channel}")
                    
        elif message_date < start_date:
            logger.info(f"Reached messages before start date. Stopping.")
            break
            
    logger.info(f"Finished scraping {channel}. Found {len(all_horoscopes)} horoscopes and published {published_count} of them.")
    
    # Optionally save a backup of the horoscopes
    if all_horoscopes:
        save_to_json([asdict(h) for h in all_horoscopes], f'horoscopes_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    
    return all_horoscopes

def save_to_json(data, filename):
    """Save data to a JSON file"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logger.info(f"Data saved to {filepath}")
    return filepath

def load_from_json(filename):
    """Load data from a JSON file"""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return []
        
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

async def main_scrape_and_publish(start_date, end_date):
    """Main function to run the scraping and publishing process"""
    client = TelegramClient('the_alabrage_session', api_id, api_hash)
    
    try:
        await client.connect()
        logger.info("Connected to Telegram")
        
        if not await client.is_user_authorized():
            logger.info("User not authorized. Sending code request...")
            await client.send_code_request(phone_number)
            try:
                code = input('Enter the code: ')
                await client.sign_in(phone_number, code)
                logger.info("Successfully signed in")
            except SessionPasswordNeededError:
                password = input('Two-factor authentication enabled. Enter password: ')
                await client.sign_in(password=password)
                logger.info("Successfully signed in with 2FA")
        else:
            logger.info("Already authorized")
        
        all_horoscopes = []
        for channel in channels:
            # Scrape and publish horoscopes directly
            channel_horoscopes = await scrape_and_publish_horoscopes(client, channel, start_date, end_date)
            all_horoscopes.extend(channel_horoscopes)
        
        if all_horoscopes:
            logger.info(f"Total horoscopes processed: {len(all_horoscopes)}")
            return True
        else:
            logger.warning("No horoscopes found in the scraped data")
            return False
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return False
    finally:
        await client.disconnect()
        logger.info("Disconnected from Telegram")

async def run_scrape_with_retry(num_retries=3, hours_between=3):
    """Run the scraping and publishing task with multiple retries"""
    success = False
    retry_count = 0
    
    while not success and retry_count < num_retries:
        retry_count += 1
        logger.info(f"Starting scrape and publish attempt {retry_count} of {num_retries}")
        
        # Get current time in Baghdad timezone
        now = datetime.now(baghdad_tz)
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        # Run the scraping and publishing process
        success = await main_scrape_and_publish(start_date, end_date)
        
        if success:
            logger.info(f"Scrape and publish attempt {retry_count} was successful")
            break
        elif retry_count < num_retries:
            wait_time = hours_between * 60 * 60  # convert to seconds
            logger.info(f"Waiting {hours_between} hours before next attempt")
            await asyncio.sleep(wait_time)
    
    if not success:
        logger.warning(f"All {num_retries} scraping attempts failed")
    
    return success

def run_scheduled_scrape():
    """Run the scheduled scrape with retries"""
    return asyncio.run(run_scrape_with_retry())

def run_manual_scrape(date_str=None):
    """Run a manual scrape for a specific date or today"""
    if date_str:
        try:
            # Parse the date string (format: YYYY-MM-DD)
            date = datetime.strptime(date_str, '%Y-%m-%d')
            start_date = datetime.combine(date, datetime.min.time(), tzinfo=baghdad_tz)
            end_date = start_date + timedelta(days=1)
        except ValueError:
            logger.error(f"Invalid date format: {date_str}. Use YYYY-MM-DD format.")
            return False
    else:
        # Use today's date
        now = datetime.now(baghdad_tz)
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    
    return asyncio.run(main_scrape_and_publish(start_date, end_date))

def publish_from_json():
    """Publish horoscopes from an existing JSON file"""
    horoscopes = load_from_json('horoscopes.json')
    if not horoscopes:
        logger.warning("No horoscope data found in horoscopes.json file.")
        return False
    
    # Group by sign and get the latest for each
    latest_by_sign = {}
    for h in horoscopes:
        sign = h['name_en']
        date = h['date']
        if sign not in latest_by_sign or date > latest_by_sign[sign]['date']:
            latest_by_sign[sign] = h
    
    logger.info(f"Found {len(latest_by_sign)} latest horoscopes to publish.")
    
    published_count = 0
    for sign, data in latest_by_sign.items():
        # Convert dict to Horoscope object
        horoscope = Horoscope(
            name_ar=data['name_ar'],
            name_en=data['name_en'],
            symbol=data['symbol'],
            date=data['date'],
            content=data['content'],
            professional_percentage=data['professional_percentage'],
            financial_percentage=data['financial_percentage'],
            emotional_percentage=data['emotional_percentage'],
            health_percentage=data['health_percentage'] if 'health_percentage' in data else None,
            message_id=data['message_id'] if 'message_id' in data else None
        )
        
        # Generate HTML if not present
        if not hasattr(horoscope, 'html_content') or not horoscope.html_content:
            horoscope.html_content = generate_attractive_html(horoscope)
        
        # Publish to WordPress
        success = post_horoscope_to_wordpress(horoscope)
        if success:
            published_count += 1
        
        # Add a short delay between posts
        time.sleep(3)
    
    logger.info(f"Published {published_count} out of {len(latest_by_sign)} horoscopes.")
    return published_count > 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Horoscope Scraper and Publisher")
    parser.add_argument('--scrape', action='store_true', help='Scrape and publish horoscopes')
    parser.add_argument('--date', type=str, help='Specific date to scrape (YYYY-MM-DD format)')
    parser.add_argument('--retries', type=int, default=3, help='Number of retry attempts')
    parser.add_argument('--publish-json', action='store_true', help='Publish horoscopes from existing JSON file')
    
    args = parser.parse_args()
    
    if args.scrape:
        if args.retries > 1:
            asyncio.run(run_scrape_with_retry(num_retries=args.retries))
        else:
            run_manual_scrape(args.date)
    elif args.publish_json:
        publish_from_json()
    else:
        parser.print_help()