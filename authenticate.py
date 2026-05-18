import asyncio
import nodriver as uc
import json
import random
from utils import *

async def handle_cloudflare(page):
    """
    Checks the DOM for Cloudflare Turnstile/challenge elements.
    Pauses execution and automatically polls the page until the challenge is solved by the user.
    """
    # Give the DOM a brief moment to render the challenge if it's there
    await asyncio.sleep(2)
    
    content = await page.get_content()
    
    # Common Cloudflare Turnstile/Challenge markers in the HTML
    cf_markers = ["challenge-stage", "cf-please-wait", "challenges.cloudflare.com"]
    
    if any(marker in content for marker in cf_markers):
        log("RAW", "\n" + "🛑" * 25)
        log("RAW", "CLOUDFLARE CHALLENGE DETECTED!")
        log("RAW", "Please look at the browser window and manually solve the captcha.")
        log("RAW", "The script will automatically resume once the page clears...")
        log("RAW", "🛑" * 25 + "\n")
        
        # Poll the page every 2 seconds until the challenge disappears
        while True:
            await asyncio.sleep(2)
            current_content = await page.get_content()
            
            # If the markers are gone, the challenge is passed!
            if not any(marker in current_content for marker in cf_markers):
                # Wait one more second just to ensure the real page fully loads
                await asyncio.sleep(1.5)
                log("OK", "Cloudflare challenge passed! Resuming automation...")
                break

async def authenticate_and_scrape():
    """
    Launches a stealth nodriver browser, navigates to Cardmarket, and injects login credentials.
    
    Args:
        None
        
    Returns:
        tuple (nodriver.Browser | None, nodriver.Tab | None): Returns the active browser instance 
                                                              and the main tab. Returns (None, None) on failure.
    """
    if USE_MOBILE:
        log("INFO", "Starting up in iPhone emulation mode.")
        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1"
        browser_args = ["--window-size=390,844", "--no-sandbox"]
    else:
        log("INFO", "Starting up in standard Windows Desktop mode.")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        browser_args = ["--start-maximized", "--no-sandbox"]
    
    # Fire up the browser and head straight to the Magic homepage.
    log("INFO", "Launching the stealth browser...")
    browser = await uc.start(
        user_agent=user_agent,
        browser_args=browser_args
    )

    page = await browser.get("https://www.cardmarket.com/fr/Magic")

    log("RAW", "\n" + "="*50)
    log("RAW", "ACTION REQUIRED:")
    log("RAW", "1. Look at the opened browser window.")
    log("RAW", "2. If there is an 'I am not a robot' checkbox, solve it.")
    log("RAW", "3. Once you're safely on the homepage, come back here.")
    log("RAW", "="*50)

    await asyncio.get_event_loop().run_in_executor(None, input, "👉 Press ENTER here in the console to continue...")

    log("INFO", "Attempting to inject credentials...")
    try:
        username_input = await page.select('input[name="username"]')
        if not username_input:
            log("ERROR", "Couldn't find the username field. Did the page layout change?")
            return None, None

        await username_input.send_keys(USERNAME)
        
        password_input = await page.select('input[name="userPassword"]')
        await password_input.send_keys(PASSWORD)
        
        login_btn = await page.select('input[value="Connexion"]')
        
        # Fallback just in case the site loaded in English.
        if not login_btn:
            login_btn = await page.select('input[type="submit"]')

        if login_btn:
            await login_btn.click()
            log("INFO", "Clicked the login button. Giving it a few seconds to load...")
        else:
            log("ERROR", "Found the inputs but couldn't find the submit button.")
            return None, None
        
        # Give the server some time to process the login and redirect.
        await asyncio.sleep(random.uniform(8.5, 12.5))
        
        # Let's verify if it actually worked by checking if our username is on the page.
        content = await page.get_content()
        if USERNAME.lower() in content.lower():
            log("OK", f"Logged in successfully as {USERNAME}!")
            return browser, page
        else:
            log("ERROR", "Login seemed to go through, but we aren't seeing the dashboard. Might be bad credentials.")
            
    except Exception as e:
        log("ERROR", f"Something blew up during login: {e}")

    await asyncio.sleep(random.uniform(7.0, 11.0))

    return None, None

async def scrape_mkm_prices(page, mkm_url):
    """
    Navigates an authenticated page to a specific Cardmarket URL and extracts the pricing data 
    from the DOM using an injected JavaScript IIFE.
    
    Args:
        page (nodriver.Tab): The active, authenticated browser tab.
        mkm_url (str): The direct URL to the specific Magic card on Cardmarket.
        
    Returns:
        dict | None: A dictionary containing 'Available items', 'From', 'Price Trend', 
                     '1-day average price', '7-days average price', and '30-days average price'. 
                     Returns None if the scrape fails.
    """
    log("INFO", f"Navigating to Cardmarket: {mkm_url}")

    await page.get(mkm_url)
    
    await asyncio.sleep(random.uniform(4.5, 8.2)) # Give the page a variable amount of time to render the DOM
    
    await handle_cloudflare(page)

    # Inside scrape_mkm_prices, update the Javascript IIFE to this:
    js_scraper = r"""
        (() => {
            let data = {};
            let labels = document.querySelectorAll('dt');
            let values = document.querySelectorAll('dd');
            let idInput = document.querySelector('input[name="idProduct"]');
            if (idInput) {
                data['idProduct'] = idInput.value;
            }
            
            if (labels.length === 0) return null;
            
            for(let i = 0; i < labels.length; i++) {
                let key = labels[i].textContent.trim();
                let val = values[i].textContent.replace(/\s+/g, ' ').trim();
                if (key) { data[key] = val; }
            }
            return JSON.stringify(data); 
        })();
    """
    
    try:
        raw_data = await page.evaluate(js_scraper)
        
        if not raw_data:
            log("ERROR", "Failed to find the pricing table on MKM.")
            return None
        
        json_string = None
        if isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, str) and item.startswith("{"):
                    json_string = item
                    break
        elif isinstance(raw_data, str):
            json_string = raw_data
            
        if not json_string:
            log("ERROR", f"Could not extract JSON string from nodriver output: {raw_data}")
            return None

        # 3. Parse and Map
        scraped_data = json.loads(json_string)
            
        prices = {
            "idProduct": scraped_data.get("idProduct"),
            "Available items": scraped_data.get("Available items"),
            "From": scraped_data.get("From"),
            "Price Trend": scraped_data.get("Price Trend"),
            "30-days average price": scraped_data.get("30-days average price"),
            "7-days average price": scraped_data.get("7-days average price"),
            "1-day average price": scraped_data.get("1-day average price")
        }
        
        log("OK", "Successfully extracted Cardmarket pricing!")
        for key, val in prices.items():
            if val:
                log("INFO", f"   -> {key}: {val}")
                
        return prices
        
    except Exception as e:
        log("ERROR", f"An error occurred while scraping MKM: {e}")
        return None

async def sell_card_on_mkm(page, id_product, price, lang_code):
    """
    Navigates to the MKM Sell page, fills the form (NM, Non-Foil, Language, Price), 
    and submits the listing to the live inventory.

    Args:
        page (nodriver.Tab): The active, authenticated browser tab.
        id_product (str): The id of card within cardmarket.
        price (str): the desire selling price
        lang_code (str): the code (e.g. fr, en...) of the card 
        
    Returns:
        bool: whether the bot successfully listed the card on mkm
    """
    sell_url = f"https://www.cardmarket.com/en/Magic/MainPage/showSellArticle?idProduct={id_product}"
    log("INFO", f"Navigating to Sell Page: {sell_url}")
    
    await page.get(sell_url)
    await asyncio.sleep(random.uniform(3.5, 5.5))
    await handle_cloudflare(page)

    mkm_lang_id = MKM_LANGUAGES.get(lang_code, '1')

    js_seller = f"""
        (() => {{
            try {{
                // 1. Set Quantity to 1
                let amount = document.querySelector('input[name="amount"]');
                if(amount) amount.value = '1';

                // 2. Set Price (injecting our calculated price)
                let priceInput = document.querySelector('input[name="price"]');
                if(priceInput) priceInput.value = '{price}';

                // 3. Set Condition to Near Mint (Value '2' in MKM's dropdown)
                let condition = document.querySelector('select[name="idCondition"]');
                if(condition) condition.value = '2';

                // 4. Set Language
                let lang = document.querySelector('select[name="idLanguage"]');
                if(lang) lang.value = '{mkm_lang_id}';

                // 5. Ensure Foil is unchecked
                let foil = document.querySelector('input[name="isFoil"]');
                if(foil) foil.checked = false;

                // 6. Find and click the Submit button
                // MKM usually uses a primary submit button on this form
                let submitBtn = document.querySelector('button[type="submit"]') || document.querySelector('input[type="submit"]');
                if(submitBtn) {{
                    submitBtn.click();
                    return true;
                }}
                return false;
            }} catch(err) {{
                return false;
            }}
        }})();
    """
    
    try:
        success = await page.evaluate(js_seller)
        if success:
            log("OK", f"✅ Card successfully listed on Cardmarket for {price} €!")
            await asyncio.sleep(random.uniform(4.0, 7.5)) 
            return True
        else:
            log("ERROR", "Failed to interact with the Sell form. The DOM might have changed.")
            return False
    except Exception as e:
        log("ERROR", f"Error during auto-listing: {e}")
        return False