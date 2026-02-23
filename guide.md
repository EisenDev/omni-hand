## 🛡️ Omni-Hand Deployment Guide

Follow these steps to set up your invisible AI assistant.

### 1. Account Setup (Do this first)
*   Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
*   Create one or more API Keys (it's free). 
*   **Pro Tip**: Use 10-15 keys for zero-fail rotation.

### 2. Fast File Setup
*   Find the **`OmApSvcBroker.exe`** and the **`config.dat`** file.
*   **Safety First**: For maximum security and proctor bypass, do not run from a USB. Copy these two files directly into a folder on your **`C://`** drive (e.g., `C:\ProgramData\Intel\DriverPackage\`).
*   Open `config.dat` with Notepad.
*   Paste your keys like this: `GEMINI_KEYS=key1,key2,key3`
*   **NOTE**: The `.exe` and the `config.dat` file **must** be in the same folder.

### 3. Connection (Critical for Exams) 🤫
*   **WARNING**: Do not use the school/office Wi-Fi. It will block the connection between your phone and PC.
*   **The Best Way**: 
    1. Turn on **Mobile Hotspot** on your Phone.
    2. Connect your **Laptop/PC** to your Phone's Wi-Fi.
    3. Run `OmApSvcBroker.exe`.
    4. Tape the IP address shown in the terminal into your phone's browser.

### 4. Stealth Mobile UI
*   Once the link is open on your phone, tap the **"RELOAD_STREAM"** button.
*   **Standalone Mode**: On iPhone (Safari) or Android (Chrome), select **"Add to Home Screen"** to hide the browser bar.
*   **Tap to Reveal**: The answer will be **BLACK on BLACK** (Hidden). Tap the center of the phone screen to reveal the text in a very dim, stealthy gray.

### 5. Final Stealth Tips
*   `OmApSvcBroker.exe` looks like a standard MSI/Hardware service in Task Manager.
*   The `config.dat` name ensures it looks like a boring system file to anyone looking in your folder.