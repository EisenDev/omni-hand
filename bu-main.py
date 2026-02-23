import sys
import json
import threading
import time
import mss
import mss.tools
import keyboard
import google.generativeai as genai
from PIL import Image
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QFont, QPen

import config

# --- AI Logic & Key Rotation ---

class OmniBrain:
    def __init__(self):
        self.api_keys = config.GEMINI_API_KEYS
        self.current_key_index = 0
        self.model_name = getattr(config, "MODEL_NAME", "gemini-3-flash-preview")
        self.last_results = None
        self.setup_genai()

    def setup_genai(self):
        """Configure the SDK with the current rotated key."""
        genai.configure(api_key=self.api_keys[self.current_key_index])
        self.model = genai.GenerativeModel(self.model_name)

    def rotate_key(self):
        """Move to the next API key in the list."""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.setup_genai()
        print(f"[Brain] Rotated to API key index {self.current_key_index}")

    def analyze_screen(self, image_path):
        """Sends the screenshot to Gemini and parses the strict JSON output."""
        system_prompt = (
            "Analyze this screenshot. Determine the question type and provide details in strict JSON format. "
            "Coordinates must be normalized [0-1000] where [ymin, xmin, ymax, xmax].\n"
            "JSON Structure: {\"type\": \"A\"|\"B\"|\"C\", \"results\": [{\"box\": [y1, x1, y2, x2], \"text\": \"...\"}]}\n"
            "- Type A (Multiple Choice): Return the box of the correct option.\n"
            "- Type B (Drag & Drop): Return the boxes of the DRAGGABLE ITEMS in the correct sorted order (1st, 2nd, 3rd, 4th) based on the logic of the question.\n"
            "- Type C (Input): Return the box of the input field and the 'text' to be typed."
        )
        
        try:
            img = Image.open(image_path)
            response = self.model.generate_content([system_prompt, img])
            
            # Extract JSON from markdown or raw text
            raw_text = response.text
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            if start != -1 and end != -1:
                data = json.loads(raw_text[start:end])
                self.last_results = data
                return data
            return None
        except Exception as e:
            print(f"[Brain] AI Error: {e}")
            self.rotate_key() # Rotate on failure
            return None

# --- Stealth UI & Graphics ---

class HeartbeatState:
    IDLE = QColor(100, 100, 100)      # Gray
    SCANNING = QColor(0, 150, 255)    # Pulsing Blue
    SUCCESS = QColor(0, 255, 100)     # Green
    ERROR = QColor(255, 50, 50)       # Red

class Overlay(QWidget):
    # Signals for thread-safe UI updates from hotkeys
    sig_arm = pyqtSignal()
    sig_scan = pyqtSignal()
    sig_clear = pyqtSignal()
    sig_recall = pyqtSignal()
    sig_reset = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.brain = OmniBrain()
        self.results = None
        self.dot_color = HeartbeatState.IDLE
        self.is_armed = False
        self.pulse_val = 255
        self.pulse_dir = -15
        
        self.init_ui()
        self.setup_hotkeys()
        
        # Animation timer for the Pulse effect
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(50)

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput  # EXTREMELY CRITICAL: Click-Through
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.showFullScreen()

    def setup_hotkeys(self):
        # Map physical keys to PyQt Signals
        keyboard.add_hotkey('f2', self.sig_arm.emit)
        keyboard.add_hotkey('alt+z', self.sig_scan.emit)
        keyboard.add_hotkey('alt+x', self.sig_clear.emit)
        keyboard.add_hotkey('alt+s', self.sig_recall.emit)
        keyboard.add_hotkey('alt+r', self.sig_reset.emit)
        keyboard.add_hotkey('f4', lambda: QApplication.quit())

        # Connect signals to internal methods
        self.sig_arm.connect(self.action_arm)
        self.sig_scan.connect(self.action_scan)
        self.sig_clear.connect(self.action_clear)
        self.sig_recall.connect(self.action_recall)
        self.sig_reset.connect(self.action_reset)

    def update_animation(self):
        """Handles the blue pulse effect during scanning."""
        if self.dot_color == HeartbeatState.SCANNING:
            self.pulse_val += self.pulse_dir
            if self.pulse_val <= 80 or self.pulse_val >= 255:
                self.pulse_dir *= -1
            self.update()
        elif self.pulse_val != 255:
            self.pulse_val = 255
            self.update()

    def paintEvent(self, event):
        if not self.is_armed:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # 1. Draw Stealth Heartbeat (2x2 dot top-right)
        color = QColor(self.dot_color)
        color.setAlpha(self.pulse_val)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(w - 2, 0, 2, 2)

        if not self.results:
            return

        # 2. Draw Visual Hints
        res_type = self.results.get('type')
        items = self.results.get('results', [])

        for i, item in enumerate(items):
            box = item.get('box') # [ymin, xmin, ymax, xmax]
            if not box or len(box) != 4: continue
            
            # Map normalized [0-1000] to screen pixels
            y1, x1, y2, x2 = box
            ry1, rx1 = int(y1 * h / 1000), int(x1 * w / 1000)
            ry2, rx2 = int(y2 * h / 1000), int(x2 * w / 1000)
            rect = QRect(rx1, ry1, rx2 - rx1, ry2 - ry1)

            if res_type == 'A':
                # Faint Blue Box
                painter.setBrush(QColor(0, 100, 255, 80))
                painter.setPen(QPen(QColor(0, 100, 255, 150), 1))
                painter.drawRect(rect)
                
            elif res_type == 'B':
                # Numbered Sorting Boxes
                painter.setBrush(QColor(0, 255, 100, 40))
                painter.setPen(QPen(QColor(0, 255, 100, 180), 2))
                painter.drawRect(rect)
                painter.setPen(QColor(255, 255, 255))
                painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                painter.drawText(rect.topLeft() + QPoint(-15, 15), str(i + 1))

            elif res_type == 'C':
                # Yellow Input Box + Floating Text
                painter.setBrush(QColor(255, 200, 0, 60))
                painter.setPen(QPen(QColor(255, 200, 0, 200), 2))
                painter.drawRect(rect)
                
                txt = item.get('text', 'Input Here')
                painter.setPen(QColor(255, 255, 255))
                painter.setFont(QFont("Segoe UI", 9))
                painter.drawText(rect.topLeft() + QPoint(0, -5), txt)

    # --- Actions ---

    def action_arm(self):
        self.is_armed = True
        self.dot_color = HeartbeatState.IDLE
        self.update()
        print("[System] Armed - Heartbeat Active")

    def action_scan(self):
        if not self.is_armed: return
        self.dot_color = HeartbeatState.SCANNING
        self.update()
        
        def run_thread():
            try:
                with mss.mss() as sct:
                    # Capture full screen
                    sct.shot(output="capture.png")
                
                data = self.brain.analyze_screen("capture.png")
                
                if data:
                    self.results = data
                    self.dot_color = HeartbeatState.SUCCESS
                else:
                    self.dot_color = HeartbeatState.ERROR
            except Exception as e:
                print(f"[System] Scan Failed: {e}")
                self.dot_color = HeartbeatState.ERROR
            
            self.update()
        
        threading.Thread(target=run_thread, daemon=True).start()

    def action_clear(self):
        self.results = None
        self.update()

    def action_recall(self):
        if self.brain.last_results:
            self.results = self.brain.last_results
            self.update()

    def action_reset(self):
        self.results = None
        self.brain.last_results = None
        self.dot_color = HeartbeatState.IDLE
        self.update()
        print("[System] Memory Wiped")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Overlay()
    sys.exit(app.exec())
