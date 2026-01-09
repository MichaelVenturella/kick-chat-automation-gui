# kick-chat-automation-gui
A Python-based GUI application that demonstrates controlled browser automation for interacting with fast-moving live chat environments.

# Kick Chat Automation GUI

A Python-based GUI application that demonstrates controlled browser automation for interacting with fast-moving live chat environments.

This project uses **PyQt5** and **Selenium (undetected-chromedriver)** to automate message sending in a **single authenticated browser session**, with full user control and visibility.

---

<img width="480" height="480" alt="image" src="https://github.com/user-attachments/assets/2c405bfc-7630-4dd6-820e-52d3a293bba6" />


## 🔨 To Build Executable:
```bash
python -m PyInstaller --onefile --windowed --name "KickChatAutomator" kick_chat_bot.py
```
## 🚀 Features

- GUI-based interface (PyQt5)
- Uses a real Chrome browser session
- Manual login (no credential handling)
- Configurable message interval
- Success / failure telemetry
- Thread-safe execution
- Multiple selector fallbacks for resilience

---

## 🧠 Use Case

In high-velocity live chats, individual messages are often missed due to volume.  
This tool helps users **repeat a message at a controlled interval** to increase visibility while remaining in a single, user-controlled session.

---

## ⚠️ Important Notes

- This tool **does not create accounts**
- This tool **does not bypass authentication**
- This tool **does not scale horizontally**
- The user must manually log in and monitor activity
- Users are responsible for complying with platform terms of service

This project is intended for **educational, automation, and UI demonstration purposes**.

---

## 📦 Requirements

- Python 3.9+
- Google Chrome (installed locally)

Install dependencies:

```bash
pip install -r requirements.txt
