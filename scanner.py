from flask import Flask, request
import os
import time
import socket
from werkzeug.utils import secure_filename
from utils import FOLDER_PATH

app = Flask(__name__)
os.makedirs(FOLDER_PATH, exist_ok=True)

def get_local_ip():
    """
    Creates a dummy socket to reliably determine the machine's local Wi-Fi/LAN IP address.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # It doesn't actually connect to the internet, just routes the packet 
        # to figure out which network interface to use.
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file uploaded."
            
        file = request.files['file']
        if file.filename == '':
            return "No selected file."
            
        if file:
            _, ext = os.path.splitext(file.filename)
            if not ext: ext = ".jpg"
            filename = f"mobile_scan_{int(time.time())}{ext}"
            
            save_path = os.path.join(FOLDER_PATH, filename)
            file.save(save_path)
            
            return HTML_TEMPLATE.replace("WAITING...", f"✅ Sent to PC: {filename}")

    return HTML_TEMPLATE.replace("WAITING...", "Awaiting scan...")

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>MKM Auto-Scanner</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
    <style>
        body { font-family: -apple-system, sans-serif; text-align: center; background-color: #121212; color: #fff; margin: 0; padding: 20px;}
        .camera-btn { 
            display: inline-block; width: 80%; padding: 40px 20px; margin-top: 50px;
            font-size: 28px; font-weight: bold; background-color: #007bff; color: white; 
            border: none; border-radius: 20px; box-shadow: 0 8px 16px rgba(0,0,0,0.5); cursor: pointer;
        }
        .camera-btn:active { background-color: #0056b3; transform: translateY(4px); box-shadow: 0 4px 8px rgba(0,0,0,0.5); }
        .status { margin-top: 30px; font-size: 18px; color: #aaa; }
    </style>
</head>
<body>
    <h2>Cardmarket Bot 🤖</h2>
    <form method="post" enctype="multipart/form-data" id="uploadForm">
        <label class="camera-btn">
            📸 OPEN CAMERA
            <input type="file" name="file" accept="image/*" capture="environment" style="display:none;" onchange="document.getElementById('uploadForm').submit(); document.getElementById('status').innerText = 'Sending to PC...';">
        </label>
    </form>
    <div class="status" id="status">WAITING...</div>
</body>
</html>
"""

if __name__ == '__main__':
    local_ip = get_local_ip()
    print("\n" + "="*50)
    print("📱 MOBILE SCANNER SERVER IS LIVE!")
    print("="*50)
    print(f"👉 Grab your phone and go to: http://{local_ip}:8080")
    print("="*50 + "\n")
    
    # Disable the default, noisy Flask startup text
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    app.run(host='0.0.0.0', port=8080)