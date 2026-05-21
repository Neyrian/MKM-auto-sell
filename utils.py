# --- CREDENTIALS & BROWSER SETTINGS ---
USERNAME = ""                          # Your Cardmarket account username
PASSWORD = ""                          # Your Cardmarket account password
USE_MOBILE = False                     # Set to True to emulate an iPhone; False for standard Windows desktop mode
DEBUG = True                           # Set to True to print logs and save OpenCV debug images; False to run silently

# --- AUTOMATION TOGGLES ---
SELL_CARD = False                      # Set to True to automatically list successfully scanned cards on Cardmarket
FETCH_PRICES = False                   # Set to True to launch the stealth browser and scrape MKM prices

# --- OPENCV VISION PARAMETERS ---
FILTER = [11, 17, 17]                  # bilateralFilter params: [diameter, sigmaColor, sigmaSpace] for noise reduction
THRESHOLD = [120, 255]                 # threshold params: [thresh, maxval] for background/card edge detection
MIN_CARD_AREA = 15000                  # Minimum pixel area for OpenCV to consider a detected contour as a valid card

# --- SCRYFALL & MATCHING SETTINGS ---
LANGUAGES = ['en', 'fr', 'ja']         # Scryfall language codes to search (e.g., 'en' = English, 'fr' = French, 'ja' = Japanese)
MATCH_THRESHOLD = 50                   # Minimum ORB feature matches required to confirm the physical card matches Scryfall's art

# --- FILE DIRECTORIES & LOGGING ---
FOLDER_PATH = "./mobile"               # The input directory where the raw webcam/phone photos are stored
SUCCESS_FOLDER = "./success"           # The output directory where successfully processed/listed images are moved
FAILED_FOLDER = "./failed"             # The output directory where unreadable or failed images are moved
CSV_FILENAME = "collection_prices.csv" # The file name for the CSV database where pricing stats are saved

# Maps Scryfall language codes to MKM language dropdown values
MKM_LANGUAGES = {
    'en': '1',
    'fr': '2',
    'de': '3',
    'es': '4',
    'it': '5',
    'zhs': '6', # Simplified Chinese
    'ja': '7',
    'pt': '8',
    'ru': '9',
    'ko': '10',
    'zht': '11' # Traditional Chinese
}

def calculate_selling_price(market_data):
    """
    Takes the scraped market data dictionary and returns the final selling price.
    
    Args:
        market_data (dict): The pricing data scraped from Cardmarket.
        
    Returns:
        str: The calculated price formatted for MKM (e.g., "0,23").
    """
    target_price = market_data.get('Price Trend') or market_data.get('From') or "0,02 €"
    clean_price = target_price.replace('€', '').strip()
    
    log("INFO", f"Calculated selling price: {clean_price} €")
    return clean_price

def log(level, message):
    """
    Simple console logger to filter output based on severity and the global DEBUG flag.
    
    Args:
        level (str): The severity level ("INFO", "OK", "ERROR", or "RAW").
        message (str): The actual text string to print to the console.
        
    Returns:
        None
    """
    if not DEBUG:
        return
        
    if level == "INFO":
        print(f"ℹ️  [INFO] {message}")
    elif level == "OK":
        print(f"✅ [OK] {message}")
    elif level == "ERROR":
        print(f"❌ [ERROR] {message}")
    elif level == "RAW":
        print(message)