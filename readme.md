# MTG Cardmarket Scanner & Auto-Lister 🃏🤖

A fully automated, end-to-end Python pipeline that takes raw photos of physical Magic: The Gathering cards, identifies them using Computer Vision and OCR, fetches real-time market prices, and can automatically list them for sale on your live Cardmarket (MKM) account.

## ✨ Features

* **Computer Vision Extraction:** Uses OpenCV to automatically detect, crop, and flatten MTG cards from a raw webcam or smartphone photo, regardless of background clutter.
* **Smart OCR & Visual Verification:** Uses Tesseract OCR with custom noise-reduction post-processing to read card names, and verifies the exact printing/expansion using Scryfall API and ORB feature artwork matching.
* **Stealth MKM Scraping:** Utilizes `nodriver` to spin up a stealth Chromium browser, bypassing Cloudflare's bot protection to securely log into your Cardmarket account and scrape live market data.
* **Automated Selling (Auto-Lister):** Optionally navigates to the Cardmarket Sell page and automatically injects condition, language, and dynamically calculated under-cut pricing to list the card in your live inventory.
* **Collection Management:** Automatically logs all scanned cards and pricing data (Trend, 30-Day Average, etc.) into a clean CSV database and sorts processed images into `/success` and `/failed` directories.

---

## 🛠️ Prerequisites

### 1. Tesseract OCR Engine
You must install the Tesseract engine and the required language packs (English, French... ) on your system.
**Ubuntu / WSL / Debian:**
```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-eng tesseract-ocr-fra
```
**Windows:** Download the installer from the [UB-Mannheim repository](https://github.com/UB-Mannheim/tesseract/wiki) and ensure the executable is in your system PATH.

### 2. Chromium Browser
`nodriver` requires a Chromium-based browser to operate its stealth CDP hooks.
**Ubuntu / WSL / Debian:**
```bash
sudo apt install chromium-browser
```

---

## 🚀 Installation

1. Clone this repository:
```bash
git clone [https://github.com/Neyrian/mkm-bot.git](https://github.com/Neyrian/mkm-bot.git)
cd mkm-bot
```

2. Install the required Python packages:
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration (`utils.py`)

All core logic, credentials, and toggles are stored in `utils.py`. **Open this file and configure your settings before running the bot.**

```python
USERNAME = "YourMkmUsername"     # Your Cardmarket login
PASSWORD = "YourMkmPassword!"    # Your Cardmarket password
USE_MOBILE = False               # Set to True to emulate iPhone, False for Windows Desktop

SELL_CARD = False                # WARNING: Set to True to actually push listings to your live MKM inventory!
FETCH_PRICES = True              # Set to True to launch the browser and fetch MKM prices
DEBUG = True                     # Set to True to save OpenCV debug images
```

---

## 📸 Usage

1. Create a folder named `test` (or whatever `FOLDER_PATH` is set to in `utils.py`) in the root directory.
2. Drop your raw photos of MTG cards (`.jpg`, `.png`) into the `test` folder.
3. Run the main script:

```bash
python mkmbot.py
```

### The Workflow:
1. The script will spin up a stealth browser and log into Cardmarket.
2. If a Cloudflare "Verify you are human" check appears, the script will pause and beep in the console. Complete the captcha manually in the open browser, and the script will automatically resume.
3. It will process images one by one, moving successful scans to `/success` and failed ones to `/failed`.
4. Pricing data will be saved to `collection_prices.csv`.

---

## 📂 Project Structure

* `mkmbot.py`: The main execution loop and file-sorting logic.
* `readingcards.py`: Handles all OpenCV image flattening, Tesseract OCR reading, and Scryfall API visual matching.
* `authenticate.py`: Handles `nodriver` stealth browser initialization, MKM authentication, price scraping, Cloudflare handling, and auto-listing.
* `utils.py`: Centralized configuration file for credentials, system toggles, and OpenCV parameters.
* `requirements.txt`: Python package dependencies.

---

## ⚠️ Disclaimer & Warning

* **Live Account Interaction:** If `SELL_CARD = True`, this script **will** list items on your real Cardmarket account. Test with cheap bulk commons first to ensure your pricing logic, language mappings, and condition settings behave exactly as you expect.
* **Terms of Service:** Automated scraping and botting may violate Cardmarket's Terms of Service. Use this tool responsibly, add reasonable delays (`asyncio.sleep`) between requests, and do not hammer their servers. The developers of this repository are not responsible for banned accounts or incorrect listings.

---

## ⚙️ To Do

- [ ] 
