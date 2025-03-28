import re

# Read the original file
with open('horoscope_scraper_publisher.py', 'r', encoding='utf-8') as file:
    content = file.read()

# Add more robust session handling
connect_code = '''
        await client.connect()
        logger.info("Connected to Telegram")
        
        if not await client.is_user_authorized():
            logger.info("User not authorized. Attempting to use bot token...")
            # Try to use the session file that should have been created elsewhere
            if os.path.exists('the_alabrage_session.session'):
                logger.info("Session file exists but is not authorized")
            else:
                logger.error("Session file does not exist")
            
            # We can't fully authenticate here without the code, but we'll log the issue
            logger.error("Cannot authenticate in automated environment without pre-authorized session")
            return False
        else:
            logger.info("Already authorized")
'''

# Find and replace the connection code
orig_connect = re.search(r'await client\.connect\(\).*?logger\.info\("Already authorized"\)', content, re.DOTALL)
if orig_connect:
    content = content.replace(orig_connect.group(0), connect_code)

# Write the updated file
with open('horoscope_scraper_publisher.py', 'w', encoding='utf-8') as file:
    file.write(content)

print("Script has been updated with more robust session handling")