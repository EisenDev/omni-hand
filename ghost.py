import mss
import mss.tools
from PIL import Image
import google.generativeai as genai
import config
import socket
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import threading
import os
import time

# --- 1. THE BRAIN (Identical to main.py) ---
class OmniBrain:
    def __init__(self):
        self.api_keys = config.API_KEYS
        self.current_key_index = 0
        self.models_to_try = ["gemini-2.5-flash", "gemini-3-flash-preview"] 
        self.current_model_name = self.models_to_try[0]
        self.setup_genai()

    def setup_genai(self):
        try:
            current_key = self.api_keys[self.current_key_index]
            genai.configure(api_key=current_key)
            self.model = genai.GenerativeModel(self.current_model_name)
            print(f"[Brain] CONNECTED | Model: {self.current_model_name} | Key Index: {self.current_key_index}")
        except Exception as e:
            print(f"[Brain] Config Error: {e}")

    def analyze_screen(self, image_path):
        system_prompt = (
            "You are an expert exam solver. Provide a text-only cheat sheet.\n"
            "SCENARIO 1: DRAG & DROP (SQL/Code)\n"
            "- Output ordered list of the TEXT inside the source blocks.\n"
            "- Format: '1. Text...'\n"
            "SCENARIO 2: YES/NO\n"
            "- Output: '1. Yes', '2. No', etc.\n"
            "SCENARIO 3: MULTIPLE CHOICE\n"
            "- Output the correct answer text.\n"
            "RULES: Keep it extremely short. No explanations."
        )

        last_error = "Unknown Error"
        for attempt in range(len(self.api_keys)):
            try:
                img = Image.open(image_path)
                response = self.model.generate_content([system_prompt, img])
                return response.text.strip()
            except Exception as e:
                last_error = str(e)
                print(f"[Brain] Key {self.current_key_index} Failed: {e}")
                # Switch to Next Key
                self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                self.setup_genai()
                print(f"[Brain] Retrying with Key {self.current_key_index}...")
                continue

        return f"Fail: {last_error[:50]}"

# --- 2. THE SERVER ---
app = Flask(__name__)
CORS(app)
brain = OmniBrain()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0, viewport-fit=cover">
    
    <!-- PWA / Stealth App Meta Tags (Hides URL Bar) -->
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#000000">
    
    <title>System Monitor</title>
    <style>
        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body { 
            background: #000; color: #1a1a1a; 
            font-family: monospace; margin: 0; 
            display: flex; flex-direction: column; 
            height: 100vh; width: 100vw; overflow: hidden;
        }
        .header { 
            padding: 40px 20px 10px; font-size: 10px; color: #0a0a0a; 
            flex-shrink: 0;
        }
        .content { 
            flex: 1; padding: 20px; overflow-y: auto; 
            display: flex; flex-direction: column;
        }
        #answer { 
            width: 100%; font-size: 14px; 
            color: #000; 
            word-wrap: break-word; line-height: 1.6;
            transition: color 0.2s;
            min-height: 100%;
        }
        #answer.visible { color: #444 !important; }
        
        .footer { 
            padding: 20px; background: #000;
            position: sticky; bottom: 0; width: 100%;
            border-top: 1px solid #050505;
            flex-shrink: 0;
        }
        #btn { 
            width: 100%; padding: 18px; border: 1px solid #080808; 
            background: #030303; color: #0a0a0a; font-size: 10px; border-radius: 4px;
            text-transform: uppercase; letter-spacing: 1px;
        }
        #btn:active { background: #080808; color: #111; }
    </style>
</head>
<body onclick="document.getElementById('answer').classList.toggle('visible')">
    <div class="header">STATUS: SYSTEM_STABLE_0x228</div>
    <div class="content">
        <div id="answer">NULL_INIT</div>
    </div>
    <div class="footer">
        <button id="btn" onclick="event.stopPropagation(); triggerScan()">RELOAD_STREAM</button>
    </div>
    <script>
        function triggerScan() {
            // Expanded compatibility for Fullscreen request
            const el = document.documentElement;
            if (el.requestFullscreen) { el.requestFullscreen(); }
            else if (el.webkitRequestFullscreen) { el.webkitRequestFullscreen(); }
            else if (el.msRequestFullscreen) { el.msRequestFullscreen(); }

            const d = document.getElementById('answer');
            d.classList.remove('visible'); 
            d.innerText = "CAPTURING_STREAM...";
            
            fetch('/scan')
                .then(res => res.json())
                .then(data => {
                    d.innerText = data.result;
                    if (window.navigator.vibrate) window.navigator.vibrate(15);
                })
                .catch(err => { d.innerText = "LINK_TIMEOUT"; });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE)

@app.route('/scan')
def scan_endpoint():
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output="ghost_scan.png")
        result = brain.analyze_screen("ghost_scan.png")
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"result": f"Error: {e}"})

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        return s.getsockname()[0]
    except: return '127.0.0.1'
    finally: s.close()

if __name__ == '__main__':
    print(f"\n[Ghost] RUNNING ON: http://{get_ip()}:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
