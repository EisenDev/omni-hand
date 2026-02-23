import sys
import threading
import mss
import mss.tools
import keyboard
import google.generativeai as genai
from PIL import Image
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QFont
import config

# --- 1. The Brain (Unchanged) ---
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
            print(f"[Brain] CONNECTED | Model: {self.current_model_name}")
        except Exception as e:
            print(f"[Brain] Config Error: {e}")

    def analyze_screen(self, image_path):
        # Concise Prompt for Stealth Text
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

        for attempt in range(len(self.api_keys)):
            try:
                img = Image.open(image_path)
                response = self.model.generate_content([system_prompt, img])
                return response.text.strip()
            except Exception as e:
                print(f"[Brain] Key {self.current_key_index} Failed: {e}")
                # Switch to Next Key
                self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                self.setup_genai()
                print(f"[Brain] Retrying with Key {self.current_key_index}...")
                continue

        return "All Keys Failed."

# --- 2. The Stealth UI ---
class HeartbeatState:
    HIDDEN = 0
    IDLE = 1     # Gray (Armed)
    SCANNING = 2 # Blue Blink
    SUCCESS = 3  # Green

class StealthBox(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        # STEALTH STYLING: Looks like the "No API Key" tooltip
        self.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d; 
                color: #cccccc; 
                border: 1px solid #454545;
                border-radius: 4px;
                padding: 8px;
                font-family: "Segoe UI";
                font-size: 11px;
            }
        """)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setFixedWidth(280) # Fixed small width
        self.hide() # Hidden by default

class Overlay(QWidget):
    sig_update = pyqtSignal(str)
    sig_toggle_arm = pyqtSignal()
    sig_toggle_visibility = pyqtSignal()
    sig_clear_result = pyqtSignal()
    sig_trigger_scan = pyqtSignal()
    sig_quit = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.brain = OmniBrain()
        self.state = HeartbeatState.HIDDEN
        
        # UI Components
        self.stealth_box = StealthBox(self)
        self.is_scanning = False
        self.opacity_level = 0.5
        self.fade_dir = 0.05
        
        self.init_ui()
        self.setup_hotkeys()
        
        # Connect Signals to Main Thread UI Methods
        self.sig_update.connect(self.show_result)
        self.sig_toggle_arm.connect(self.toggle_arm)
        self.sig_toggle_visibility.connect(self.toggle_visibility)
        self.sig_clear_result.connect(self.clear_result)
        self.sig_trigger_scan.connect(self._trigger_scan_handler)
        self.sig_quit.connect(QApplication.quit)
        
        # Animation Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(20)

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.showFullScreen()

    def setup_hotkeys(self):
        # Use lambda to JUST emit signals. This keeps the keyboard thread free
        # and moves the actual UI work to the PyQt Main Thread.
        keyboard.add_hotkey('f2', lambda: self.sig_toggle_arm.emit())
        keyboard.add_hotkey('alt+x', lambda: self.sig_toggle_visibility.emit()) 
        keyboard.add_hotkey('alt+c', lambda: self.sig_clear_result.emit())     
        keyboard.add_hotkey('alt+z', lambda: self.sig_trigger_scan.emit())
        keyboard.add_hotkey('f4', lambda: self.sig_quit.emit())

    def toggle_arm(self):
        if self.state == HeartbeatState.HIDDEN:
            self.state = HeartbeatState.IDLE
            print("[System] ARMED (Gray Dot)")
            # If armed, we SHOULD be visible.
            self.showFullScreen()
            self.raise_()
        else:
            self.state = HeartbeatState.HIDDEN
            self.stealth_box.hide()
            print("[System] DISARMED")
        self.update()

    def animate(self):
        if self.state == HeartbeatState.SCANNING:
            self.opacity_level += self.fade_dir
            if self.opacity_level >= 1.0 or self.opacity_level <= 0.3:
                self.fade_dir *= -1
        else:
            self.opacity_level = 0.8
        self.update()

    def _trigger_scan_handler(self):
        """Called on Main Thread via signal to safely initiate scan thread."""
        if self.state == HeartbeatState.HIDDEN or self.is_scanning: 
            return
        
        self.is_scanning = True
        
        # 1. Hide previous result
        self.stealth_box.hide()
        
        # 2. Set State to Scanning (Blue Blink)
        self.state = HeartbeatState.SCANNING
        self.update()
        
        threading.Thread(target=self._scan_logic, daemon=True).start()

    def _scan_logic(self):
        try:
            # Randomize filename slightly to avoid locks if multiple instances run? 
            # Or just use the lock logic we have now.
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                mss.tools.to_png(screenshot.rgb, screenshot.size, output="scan.png")
            
            answer = self.brain.analyze_screen("scan.png")
            self.sig_update.emit(answer)
        except Exception as e:
            print(f"[System] Scan Error: {e}")
            self.sig_update.emit("Error.")
        finally:
            self.is_scanning = False

    def show_result(self, text):
        # 1. Update Text
        self.stealth_box.setText(text)
        self.stealth_box.adjustSize()
        
        # 2. Position Bottom Right (Stealth)
        screen_geo = self.geometry()
        box_w = self.stealth_box.width()
        box_h = self.stealth_box.height()
        
        # 20px padding from bottom-right corner
        self.stealth_box.move(screen_geo.width() - box_w - 20, screen_geo.height() - box_h - 40)
        
        # 3. Show Box
        self.stealth_box.show()
        
        # 4. Set State to Success (Green Dot)
        self.state = HeartbeatState.SUCCESS
        self.update()

    def clear_result(self):
        self.stealth_box.hide()
        if self.state != HeartbeatState.HIDDEN:
            self.state = HeartbeatState.IDLE
        self.update()

    def toggle_visibility(self):
        # Instead of hiding the widget (which can break the paint loop), 
        # we just make it 100% transparent.
        if self.windowOpacity() > 0:
            self.setWindowOpacity(0.0)
            print("[System] UI HIDDEN (Stealth)")
        else:
            self.setWindowOpacity(1.0)
            self.raise_()
            print("[System] UI VISIBLE")
        self.update()

    def paintEvent(self, event):
        # Draw the Heartbeat Dot in Bottom Left
        if self.state == HeartbeatState.HIDDEN: return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        color = QColor(128, 128, 128) # Default Gray
        
        if self.state == HeartbeatState.SCANNING:
            color = QColor(0, 200, 255) # Cyan/Blue
        elif self.state == HeartbeatState.SUCCESS:
            color = QColor(0, 255, 100) # Green
        
        color.setAlphaF(self.opacity_level)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw small dot 15px from bottom-left
        h = self.height()
        painter.drawEllipse(15, h - 25, 8, 8)

if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    window = Overlay()
    sys.exit(app.exec())