import asyncio
import csv
import os
import re
import time
import random
from shutil import copy as scopy
from readingcards import extract_text_from_image, verify_with_scryfall
from authenticate import authenticate_and_scrape, scrape_mkm_prices, sell_card_on_mkm
from utils import *

async def process_folder_with_auth(page):
    """
    Main asynchronous pipeline: iterates through the directory, scans the cards, 
    scrapes prices from Cardmarket, sell it, moves the images to success/failed folders, 
    and logs the pricing data to a CSV file.
    
    Args:
        page (nodriver.Tab): The authenticated active browser tab connected to Cardmarket.
        
    Returns:
        None
    """
    log("INFO", f"Looking for images in folder: '{FOLDER_PATH}'")
    os.makedirs(SUCCESS_FOLDER, exist_ok=True)
    os.makedirs(FAILED_FOLDER, exist_ok=True)
    os.makedirs(NOT_SOLD_FOLDER, exist_ok=True)

    if not os.path.exists(FOLDER_PATH):
        log("ERROR", f"The folder '{FOLDER_PATH}' does not exist. Please create it.")
        return

    valid_extensions = ('.jpg', '.jpeg', '.png')
    all_files = os.listdir(FOLDER_PATH)
    image_files = [f for f in all_files if f.lower().endswith(valid_extensions)]
    
    if not image_files:
        log("INFO", f"No images found in '{FOLDER_PATH}'.")
        return
        
    log("OK", f"Found {len(image_files)} image(s). Starting batch process...\n")
    
    for filename in image_files:
        image_path = os.path.join(FOLDER_PATH, filename)
        final_status = "FAILED"

        log("INFO", "=" * 50)
        log("INFO", f"PROCESSING: {filename}")
        log("INFO", "=" * 50)
        
        # Phase 1: Scan the physical image
        raw_name, flat_card_img = extract_text_from_image(image_path)
        
        # Phase 2: Verify with Scryfall
        if raw_name and flat_card_img is not None:
            official_name, official_set, card_lang, mkm_url = verify_with_scryfall(raw_name, flat_card_img)
            
            if official_name and mkm_url:
                log("OK", f"🎯 SCANNED: {official_name} [{official_set}] in {card_lang}")
                
                # Phase 3: Scrape Cardmarket Prices
                market_data = await scrape_mkm_prices(page, mkm_url)
                
                if market_data and market_data.get("idProduct"):
                    log("OK", f"✅ Data successfully gathered for {filename}!")
                    
                    # Phase 4: Auto-List the Card
                    selling_price = calculate_selling_price(market_data)
                    id_product = market_data.get("idProduct")
                    
                    if selling_price:
                        if SELL_CARD:
                            listing_success = await sell_card_on_mkm(page, id_product, selling_price, card_lang)
                        
                            if listing_success:
                                final_status = "SUCCESS"
                        else:
                            final_status = "SUCCESS"
                    else:
                        final_status = "NOT_SOLD"
                else:
                    log("ERROR", "Could not scrape market data or find idProduct.")
            else:
                log("ERROR", f"Could not confidently identify {filename} via Scryfall or missing MKM URL.")
        else:
            log("ERROR", f"Extraction failed for {filename}. Check the debug images.")
        
        # Keep tract of sucess 
        # Renaming, Sorting, and CSV Logging
        try:
            if final_status in ["SUCCESS", "NOT_SOLD"]:
                clean_name = re.sub(r'[^\w\s]', '', official_name).strip().replace(' ', '_')
                _, ext = os.path.splitext(filename)
                new_filename = f"{clean_name}_{int(time.time())}{ext}"
                if final_status == "SUCCESS":
                    dest_path = os.path.join(SUCCESS_FOLDER, new_filename)
                    csv_estimate = selling_price if SELL_CARD else market_data.get('Price Trend', '')
                else:
                    dest_path = os.path.join(NOT_SOLD_FOLDER, new_filename)
                    csv_estimate = "Not Sold (Held)"
                scopy(image_path, dest_path)
                
                file_exists = os.path.isfile(CSV_FILENAME)
                with open(CSV_FILENAME, mode='a', newline='', encoding='utf-8') as f:
                    headers = [
                        'Card Name', 'Set Code', 'Starting Price',
                        'Price Trend', '1-Day Average', '7-Days Average', '30-Days Average',
                        'Estimated Value (Sold)'
                    ]
                    writer = csv.DictWriter(f, fieldnames=headers)
                    
                    if not file_exists:
                        writer.writeheader() 
                        
                    writer.writerow({
                        'Card Name': official_name,
                        'Set Code': official_set.upper() if official_set else '',
                        'Starting Price': market_data.get('From', ''),
                        'Price Trend': market_data.get('Price Trend', ''),
                        '1-Day Average': market_data.get('1-day average price', ''),
                        '7-Days Average': market_data.get('7-days average price', ''),
                        '30-Days Average': market_data.get('30-days average price', ''),
                        'Estimated Value (Sold)': csv_estimate
                    })
                log("OK", f"Logged {official_name} to CSV and moved to {dest_path}")
            
            else:
                scopy(image_path, os.path.join(FAILED_FOLDER, filename))
                log("INFO", f"Copied {filename} to /failed")
                
        except Exception as e:
            log("ERROR", f"Could not move file {filename} or write CSV: {e}")
            
        os.remove(image_path)

        delay = random.uniform(3.5, 7.5)
        await asyncio.sleep(delay)
        
def process_folder():
    """
    Main pipeline: iterates through the directory, scans the cards, 
    moves the images to success/failed folders, and logs the pricing data to a CSV file.
    
    Args:
        None
        
    Returns:
        None
    """
    log("INFO", f"Looking for images in folder: '{FOLDER_PATH}'")
    os.makedirs(SUCCESS_FOLDER, exist_ok=True)
    os.makedirs(FAILED_FOLDER, exist_ok=True)

    # 1. Check if the folder exists
    if not os.path.exists(FOLDER_PATH):
        log("ERROR", f"The folder '{FOLDER_PATH}' does not exist. Please create it.")
        exit

    # 2. Define acceptable image extensions
    valid_extensions = ('.jpg', '.jpeg', '.png')
    
    # 3. Get all files and filter for images
    all_files = os.listdir(FOLDER_PATH)
    image_files = [f for f in all_files if f.lower().endswith(valid_extensions)]
    
    if not image_files:
        log("INFO", f"No images found in '{FOLDER_PATH}'.")
        exit
        
    log("OK", f"Found {len(image_files)} image(s). Starting batch process...\n")
    
    for filename in image_files:
        image_path = os.path.join(FOLDER_PATH, filename)
        is_success = False
        
        log("INFO", "=" * 50)
        log("INFO", f"PROCESSING: {filename}")
        log("INFO", "=" * 50)
        
        # Phase 1: Scan the physical image
        raw_name, flat_card_img = extract_text_from_image(image_path)
        
        # Phase 2: Verify with Scryfall
        if raw_name and flat_card_img is not None:
            official_name, official_set, card_lang, mkm_url = verify_with_scryfall(raw_name, flat_card_img)
            
            if official_name and mkm_url:
                log("OK", f"🎯 SCANNED: {official_name} [{official_set}] in {card_lang}")
                is_success = True
            else:
                log("ERROR", f"Could not confidently identify {filename} via Scryfall or missing MKM URL.")
        else:
            log("ERROR", f"Extraction failed for {filename}. Check the debug images.")
        
        #  Sort the image file 
        try:
            if is_success:
                scopy(image_path, os.path.join(SUCCESS_FOLDER, filename))
                log("INFO", f"Moved {filename} to /success")
            else:
                scopy(image_path, os.path.join(FAILED_FOLDER, filename))
                log("INFO", f"Moved {filename} to /failed")
        except Exception as e:
            log("ERROR", f"Could not move file {filename}: {e}")

async def main():
    """
    The main execution block that initializes the stealth browser, authenticates the user,
    runs the batch processing pipeline, and gracefully shuts down the browser.
    
    Args:
        None
        
    Returns:
        None
    """
    browser, page = await authenticate_and_scrape()
    
    if browser and page:
        log("OK", "--- AUTHENTICATION COMPLETE ---")
        log("INFO", "The browser session is live and ready for card processing.")
        
        log("INFO", "Bot is now in WATCH MODE. Waiting for photos from mobile app...")
        try:
            while True:
                # Check the folder. If it's empty, it will just return and wait.
                await process_folder_with_auth(page)
                
                # Wait 3 seconds before checking the folder again
                await asyncio.sleep(3)
                
        except KeyboardInterrupt:
            log("INFO", "Manual interrupt received. Shutting down...")
        finally:
            log("INFO", "All cards processed. Closing the browser...")
            browser.stop()
    else:
        log("ERROR", "Session failed to start properly. Restart the script and try again.")

if __name__ == "__main__":
    # Start the async event loop
    if FETCH_PRICES:
        asyncio.run(main())
    else:
        process_folder()