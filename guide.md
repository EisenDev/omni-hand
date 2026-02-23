## 🛡️ Omni-Hand Deployment Guide

Follow these steps to set up your invisible AI assistant.

### 1. Account Setup (Do this first)
*   Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
*   Create one or more API Keys (it's free).
*   Copy these keys.

### 2. File Setup
*   Find the `.env` file in the same folder as the `.exe`.
*   Open it with Notepad.
*   Paste your keys like this: `GEMINI_KEYS=AIza123,AIza456,AIza789`
*   **NOTE**: The `.exe` and the `.env` file **must** be in the same folder.

### 3. Connection (Critical for Exams) 🤫
*   **WARNING**: Do not use the school/office Wi-Fi. It will block the connection.
*   **The Best Way**: 
    1. Turn on **Mobile Hotspot** on your Phone.
    2. Connect your **Laptop** to your Phone's Wi-Fi.
    3. Run `OmApSvcBroker-v5.exe`.
    4. Type the IP address shown in the terminal into your phone's browser.

### 4. Mobile App Shortcut
*   Once the link is open on your phone, tap the **Share** button (iPhone) or **3-Dots** (Android).
*   Select **"Add to Home Screen"**.
*   It now looks like a regular app!

### 5. Stealth Tips
*   You can rename `OmApSvcBroker-v5.exe` to `WinStoreUpdate.exe` or `SystemDriver.exe`.
*   Run it once to verify the IP, then you can minimize the terminal or use the "No Console" version to keep it hidden in Task Manager.