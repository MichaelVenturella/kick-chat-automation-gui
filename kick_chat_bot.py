import sys
import time
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QSpinBox, QTextEdit, QMessageBox, QFrame, QCheckBox, QSizePolicy)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

class BrowserThread(QThread):
    """Thread to handle browser operations"""
    status_update = pyqtSignal(str, str)  # message, color
    message_sent = pyqtSignal(bool)  # success or failure
    browser_ready = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.driver = None
        self.running = False
        self.sending_enabled = False
        self.streamer_url = ""
        self.message = ""
        self.interval = 5
    
    def setup_browser(self):
        """Initialize undetected Chrome browser"""
        try:
            self.status_update.emit("Setting up browser...", "orange")
            
            # Get Chrome user data directory
            user_data_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data')
            
            options = uc.ChromeOptions()
            # Don't use user data dir directly - let undetected_chromedriver handle it
            # This avoids locking issues
            options.add_argument('--no-first-run')
            options.add_argument('--no-service-autorun')
            options.add_argument('--password-store=basic')
            
            # Create driver with undetected_chromedriver
            self.driver = uc.Chrome(options=options, use_subprocess=True)
            
            self.status_update.emit("Browser opened successfully!", "green")
            return True
            
        except Exception as e:
            self.status_update.emit(f"Failed to open browser: {str(e)[:100]}", "red")
            return False
    
    def navigate_to_stream(self):
        """Navigate to the streamer's page"""
        try:
            self.status_update.emit(f"Navigating to stream...", "orange")
            self.driver.get(self.streamer_url)
            time.sleep(5)  # Wait for page load
            self.status_update.emit("Ready! Please login if needed, then click 'Start Chat'", "green")
            self.browser_ready.emit()
            return True
        except Exception as e:
            self.status_update.emit(f"Navigation failed: {str(e)[:50]}", "red")
            return False
    
    def send_chat_message(self):
        """Send a message in the chat"""
        try:
            # Try multiple possible selectors for Kick's chat input
            chat_selectors = [
                "textarea[placeholder*='Send a message' i]",
                "textarea[data-chat-input]",
                "textarea.chat-input",
                "div[contenteditable='true'][role='textbox']",
                "textarea[placeholder*='chat' i]",
                "input[placeholder*='Send a message' i]",
                "div.chat-entry textarea",
                "textarea[aria-label*='chat' i]"
            ]
            
            chat_input = None
            for selector in chat_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            chat_input = element
                            break
                    if chat_input:
                        break
                except:
                    continue
            
            if not chat_input:
                self.status_update.emit("Chat input not found - are you logged in?", "red")
                self.message_sent.emit(False)
                return False
            
            # Clear and send message
            chat_input.click()
            time.sleep(0.3)
            
            # Try clearing
            try:
                chat_input.clear()
            except:
                # If clear doesn't work, try selecting all and deleting
                chat_input.send_keys(Keys.CONTROL + "a")
                chat_input.send_keys(Keys.BACKSPACE)
            
            time.sleep(0.2)
            
            # Type message
            chat_input.send_keys(self.message)
            time.sleep(0.3)
            
            # Send
            chat_input.send_keys(Keys.RETURN)
            
            self.message_sent.emit(True)
            return True
            
        except Exception as e:
            self.status_update.emit(f"Send error: {str(e)[:50]}", "red")
            self.message_sent.emit(False)
            return False
    
    def run(self):
        """Main thread loop for sending messages"""
        while self.running:
            if self.sending_enabled:
                self.send_chat_message()
                time.sleep(self.interval)
            else:
                time.sleep(0.5)
    
    def stop(self):
        """Stop the browser thread"""
        self.running = False
        self.sending_enabled = False
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        self.wait()

class KickChatAutomator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kick Chat Automator (Undetected Chrome)")
        self.setGeometry(100, 100, 700, 600)
        
        self.is_running = False
        self.browser_ready = False
        self.success_count = 0
        self.fail_count = 0
        self.dark_mode = False
        
        if SELENIUM_AVAILABLE:
            self.browser_thread = BrowserThread()
            self.browser_thread.status_update.connect(self.update_status)
            self.browser_thread.message_sent.connect(self.on_message_sent)
            self.browser_thread.browser_ready.connect(self.on_browser_ready)
        
        self.init_ui()
        # Apply initial theme (light by default)
        self.apply_theme()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Kick Chat Automator")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("padding: 10px;")
        layout.addWidget(title)
        # Theme toggle (top-right)
        theme_layout = QHBoxLayout()
        theme_layout.addStretch()
        self.theme_toggle = QCheckBox("Dark Mode")
        self.theme_toggle.setToolTip("Toggle dark mode")
        self.theme_toggle.stateChanged.connect(lambda _: self.toggle_dark_mode(self.theme_toggle.isChecked()))
        theme_layout.addWidget(self.theme_toggle)
        layout.addLayout(theme_layout)
        
        if not SELENIUM_AVAILABLE:
            # Show installation instructions
            error_box = QTextEdit()
            error_box.setReadOnly(True)
            error_box.setHtml("""
            <div style='background-color: #ffebee; padding: 20px; border: 2px solid #f44336;'>
            <h2 style='color: #f44336;'>⚠️ Missing Required Packages</h2>
            <p><b>You need to install the required packages first!</b></p>
            <p>Open Command Prompt (cmd) and run these commands:</p>
            <pre style='background-color: #333; color: #0f0; padding: 10px; font-family: monospace;'>
pip install undetected-chromedriver
pip install selenium</pre>
            <p>After installation, restart this application.</p>
            </div>
            """)
            layout.addWidget(error_box)
            return
        
        # Info box
        info_box = QTextEdit()
        info_box.setReadOnly(True)
        info_box.setMaximumHeight(130)
        # Use neutral HTML so the QTextEdit background/color can adapt to theme
        info_box.setHtml("""
        <div style='padding: 10px; border-left: 4px solid #4CAF50;'>
        <b>✅ Undetected Chrome Mode - No Login Issues!</b><br/>
        <br/>
        <b>How it works:</b><br/>
        1. Click "Open Browser" - A real Chrome window will open<br/>
        2. <b>Login to Kick normally</b> (Google login works perfectly!)<br/>
        3. Once logged in and you can see chat, click "Start Chat"<br/>
        4. Messages will be sent automatically at the interval you set<br/>
        <br/>
        <b>Note:</b> Keep the browser window open while sending is active.
        </div>
        """)
        layout.addWidget(info_box)
        
        # Counter display
        counter_layout = QHBoxLayout()
        counter_font = QFont()
        counter_font.setPointSize(12)
        counter_font.setBold(True)
        
        self.success_label = QLabel("✓ Successful: 0")
        self.success_label.setFont(counter_font)
        self.success_label.setStyleSheet("color: green;")
        
        self.fail_label = QLabel("✗ Failed: 0")
        self.fail_label.setFont(counter_font)
        self.fail_label.setStyleSheet("color: red;")
        
        counter_layout.addWidget(self.success_label)
        counter_layout.addStretch()
        counter_layout.addWidget(self.fail_label)
        layout.addLayout(counter_layout)
        
        # Separator (modern)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #cccccc;")
        layout.addWidget(sep)
        
        # Streamer URL input
        url_label = QLabel("Streamer URL:")
        url_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://kick.com/streamer-name")
        self.url_input.setStyleSheet("padding: 8px; font-size: 10pt; border-radius:6px;")
        layout.addWidget(self.url_input)
        
        # Message input
        message_label = QLabel("Message to Send:")
        message_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(message_label)
        
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Enter your message here (e.g., 'W')")
        self.message_input.setMaximumHeight(80)
        self.message_input.setStyleSheet("padding: 8px; font-size: 10pt; border-radius:6px;")
        layout.addWidget(self.message_input)
        
        # Interval input
        interval_layout = QHBoxLayout()
        interval_label = QLabel("Send Interval (seconds):")
        interval_label.setFont(QFont("Arial", 10, QFont.Bold))
        interval_layout.addWidget(interval_label)
        
        self.interval_input = QSpinBox()
        self.interval_input.setMinimum(1)
        self.interval_input.setMaximum(3600)
        self.interval_input.setValue(5)
        self.interval_input.setStyleSheet("padding: 5px; font-size: 10pt; border-radius:6px;")
        interval_layout.addWidget(self.interval_input)
        interval_layout.addStretch()
        
        layout.addLayout(interval_layout)
        
        # Status display
        self.status_label = QLabel("Status: Ready - Click 'Open Browser' to begin")
        self.status_label.setStyleSheet("color: #555; font-size: 10pt; padding: 10px; background-color: #f5f5f5; border-radius: 8px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Open Browser button
        self.open_browser_button = QPushButton("🌐 Open Browser")
        self.open_browser_button.setCursor(Qt.PointingHandCursor)
        self.open_browser_button.setStyleSheet("""
            QPushButton {
                background-color: #2979FF;
                color: white;
                padding: 12px;
                font-size: 11pt;
                font-weight: 600;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #1565c0; }
            QPushButton:pressed { background-color: #0d47a1; }
        """)
        self.open_browser_button.clicked.connect(self.open_browser)
        button_layout.addWidget(self.open_browser_button)
        
        # Start/Stop button
        self.launch_button = QPushButton("🚀 Start Chat")
        self.launch_button.setEnabled(False)
        self.launch_button.setCursor(Qt.PointingHandCursor)
        self.launch_button.setStyleSheet("""
            QPushButton { background-color: #9e9e9e; color: white; padding: 12px; font-size: 11pt; font-weight: 600; border-radius: 8px; }
        """)
        self.launch_button.clicked.connect(self.toggle_automation)
        button_layout.addWidget(self.launch_button)
        
        layout.addLayout(button_layout)
        
        layout.addStretch()
    
    def open_browser(self):
        """Open the undetected Chrome browser"""
        if not SELENIUM_AVAILABLE:
            return
        
        url = self.url_input.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a streamer URL first!")
            return
        
        if not url.startswith("http"):
            url = f"https://kick.com/{url}"
        
        self.open_browser_button.setEnabled(False)
        QApplication.processEvents()
        
        self.browser_thread.streamer_url = url
        
        # Start thread for browser operations
        self.browser_thread.running = True
        
        if self.browser_thread.setup_browser():
            self.browser_thread.navigate_to_stream()
        else:
            self.open_browser_button.setEnabled(True)
    
    def on_browser_ready(self):
        """Called when browser is ready"""
        self.browser_ready = True
        self.launch_button.setEnabled(True)
        self.launch_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 15px;
                font-size: 12pt;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        QMessageBox.information(self, "Browser Ready!", 
                              "Chrome browser opened!\n\n"
                              "✅ LOGIN to Kick if you haven't already\n"
                              "✅ Make sure you can see the chat\n"
                              "✅ Click 'Start Chat' when ready!\n\n"
                              "Keep this browser window open.")
    
    def toggle_automation(self):
        if not self.is_running:
            if not self.browser_ready:
                QMessageBox.warning(self, "Not Ready", "Please open the browser first!")
                return
            
            message = self.message_input.toPlainText().strip()
            
            if not message:
                QMessageBox.warning(self, "Input Error", "Please enter a message to send!")
                return
            
            # Start automation
            self.is_running = True
            self.browser_thread.message = message
            self.browser_thread.interval = self.interval_input.value()
            self.browser_thread.sending_enabled = True
            
            if not self.browser_thread.isRunning():
                self.browser_thread.start()
            
            self.launch_button.setText("⏹ Stop Chat")
            self.launch_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    padding: 15px;
                    font-size: 12pt;
                    font-weight: bold;
                    border: none;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
                QPushButton:pressed {
                    background-color: #c41000;
                }
            """)
            
            self.status_label.setText(f"Status: Chat running - sending every {self.interval_input.value()}s")
            self.status_label.setStyleSheet("color: green; font-size: 10pt; padding: 10px; background-color: #e8f5e9; border-radius: 5px; font-weight: bold;")
        else:
            # Stop automation
            self.stop_automation()
    
    def stop_automation(self):
        self.is_running = False
        self.browser_thread.sending_enabled = False
        
        self.launch_button.setText("🚀 Start Chat")
        self.launch_button.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; padding: 12px; font-size: 11pt; font-weight: 600; border-radius: 8px; }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.status_label.setText("Status: Chat stopped")
        self.status_label.setStyleSheet("color: #555; font-size: 10pt; padding: 10px; background-color: #f5f5f5; border-radius: 5px;")

    def toggle_dark_mode(self, enabled: bool):
        """Toggle dark mode on/off"""
        self.dark_mode = bool(enabled)
        self.apply_theme()

    def apply_theme(self):
        """Apply light or dark palette and tweak widget styles."""
        app = QApplication.instance()
        if not app:
            return

        if self.dark_mode:
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(45,45,45))
            palette.setColor(QPalette.WindowText, QColor(230,230,230))
            palette.setColor(QPalette.Base, QColor(30,30,30))
            palette.setColor(QPalette.AlternateBase, QColor(45,45,45))
            palette.setColor(QPalette.ToolTipBase, QColor(255,255,220))
            palette.setColor(QPalette.ToolTipText, QColor(0,0,0))
            palette.setColor(QPalette.Text, QColor(220,220,220))
            palette.setColor(QPalette.Button, QColor(60,60,60))
            palette.setColor(QPalette.ButtonText, QColor(230,230,230))
            palette.setColor(QPalette.Highlight, QColor(100,100,255))
            palette.setColor(QPalette.HighlightedText, QColor(0,0,0))
            app.setPalette(palette)
            # subtle window-level stylesheet for dark
            app.setStyleSheet("QToolTip{color:#000;background:#fff;border:1px solid black;} QLabel{color:#e6e6e6;} QLineEdit, QTextEdit{background:#252525;color:#e6e6e6;}")
            self.theme_toggle.setChecked(True)
        else:
            app.setPalette(app.style().standardPalette())
            app.setStyleSheet("")
            self.theme_toggle.setChecked(False)
    
    def update_status(self, message, color):
        """Update status label from browser thread"""
        color_map = {
            'green': ('#4CAF50', '#e8f5e9'),
            'red': ('#f44336', '#ffebee'),
            'orange': ('#FF9800', '#fff3cd')
        }
        text_color, bg_color = color_map.get(color, ('#555', '#f5f5f5'))
        
        self.status_label.setText(f"Status: {message}")
        self.status_label.setStyleSheet(f"color: {text_color}; font-size: 10pt; padding: 10px; background-color: {bg_color}; border-radius: 5px;")
    
    def on_message_sent(self, success):
        """Handle message sent signal"""
        if success:
            self.success_count += 1
            self.success_label.setText(f"✓ Successful: {self.success_count}")
            msg = self.message_input.toPlainText().strip()
            msg_preview = msg[:30] + "..." if len(msg) > 30 else msg
            self.status_label.setText(f"Status: Sent - '{msg_preview}'")
            self.status_label.setStyleSheet("color: green; font-size: 10pt; padding: 10px; background-color: #e8f5e9; border-radius: 5px;")
        else:
            self.fail_count += 1
            self.fail_label.setText(f"✗ Failed: {self.fail_count}")
    
    def closeEvent(self, event):
        """Handle window close"""
        if SELENIUM_AVAILABLE and self.browser_thread.driver:
            reply = QMessageBox.question(self, 'Close Application',
                                        'This will close the browser. Continue?',
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.browser_thread.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = KickChatAutomator()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()