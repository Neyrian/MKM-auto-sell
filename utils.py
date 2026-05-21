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
FOLDER_PATH = "./test"               # The input directory where the raw webcam/phone photos are stored
SUCCESS_FOLDER = "./success"           # The output directory where successfully processed/listed images are moved
FAILED_FOLDER = "./failed"             # The output directory where unreadable or failed images are moved
NOT_SOLD_FOLDER = "./not_sold"
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

def parse_price(price_str):
    """
    Helper function to convert MKM price strings (e.g., '1.234,56 €') into Python floats.
    """
    if not price_str:
        return None
    try:
        # Remove euro symbol and spaces, remove thousands separators, convert comma to dot
        clean_str = price_str.replace('€', '').replace('.', '').replace(',', '.').strip()
        return float(clean_str)
    except ValueError:
        return None
    
def calculate_selling_price(market_data):
    """
    Calculates the selling price based on dynamic market tiers.
    Includes a safeguard to halt sales if a massive price spike is detected.
    If the card is worth 10€ or more, or spiking, it returns None to signal 'Do Not Sell'.
    
    Args:
        market_data (dict): The pricing data scraped from Cardmarket.
        
    Returns:
        str: The calculated price formatted for MKM (e.g., "0,23").
    """
    pt = parse_price(market_data.get('Price Trend'))
    sp = parse_price(market_data.get('From'))
    a1 = parse_price(market_data.get('1-day average price'))
    a7 = parse_price(market_data.get('7-days average price'))
    a30 = parse_price(market_data.get('30-days average price'))
    
    if pt is None:
        log("ERROR", "Could not determine Price Trend. Skipping sale.")
        return None

    # Market Spike Safeguard
    if a1 is not None and a30 is not None:
        if a1 > (a30 * 1.5):
            log("INFO", f"Market spike detected! 1-Day Avg ({a1}€) is > 150% of 30-Day Avg ({a30}€). HOLDING. Do not sell.")
            return None
            
    # Safe fallbacks if a specific average is missing for some reason
    sp_safe = sp if sp is not None else 0.02
    a1_safe = a1 if a1 is not None else pt
    a7_safe = a7 if a7 is not None else pt
    a30_safe = a30 if a30 is not None else pt

    target_price = None

    # 2. Execute the Pricing Logic
    if pt < 0.10:
        # Tier 1: Bulk
        target_price = sp if sp is not None else 0.02
        log("INFO", f"Pricing Tier: Bulk (< 0.10). Set to {target_price}")
        
    elif pt < 1.0:
        # Tier 2: Low Value
        target_price = (sp_safe + min(a1_safe, a7_safe, a30_safe)) / 2
        log("INFO", f"Pricing Tier: Low Value (< 1.00). Set to {target_price}")
        
    elif pt < 10.0:
        # Tier 3: Mid Value
        avg_days = (a1_safe + a7_safe + a30_safe) / 3
        candidate_price = ((pt + avg_days) / 2) * 0.8
        
        if candidate_price > sp_safe:
            target_price = candidate_price
        else:
            if a1_safe > pt:
                target_price = a1_safe
            else:
                target_price = pt
        log("INFO", f"Pricing Tier: Mid Value (< 10.00). Set to {target_price}")
        
    else:
        # Tier 4: High Value (Hold)
        log("INFO", f"Pricing Tier: High Value (>= 10.00). Price is {pt}€. HOLDING. Do not sell.")
        return None

    final_price = max(0.02, target_price)
    mkm_formatted_price = f"{final_price:.2f}".replace('.', ',')
    
    return mkm_formatted_price

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