"""
Main GUI Window - Floating overlay widget.
"""
import sys
import logging
from multiprocessing import Queue
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QThread
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

logger = logging.getLogger("GUI")


class CommandProcessor(QThread):
    """Thread to process responses from AI backend."""
    response_received = pyqtSignal(dict)
    
    def __init__(self, response_queue: Queue):
        super().__init__()
        self.response_queue = response_queue
        self.running = True
    
    def run(self):
        """Check for responses from AI backend."""
        while self.running:
            if not self.response_queue.empty():
                response = self.response_queue.get()
                self.response_received.emit(response)
            
            self.msleep(100)  # Check every 100ms
    
    def stop(self):
        """Stop the thread."""
        self.running = False


class FloatingWidget(QMainWindow):
    """Main floating overlay window."""
    
    def __init__(self, command_queue: Queue, response_queue: Queue):
        super().__init__()
        self.command_queue = command_queue
        self.response_queue = response_queue
        
        self.state = "idle"  # idle, listening, thinking, speaking
        self.status_text = "Ready"
        self.is_recording = False
        
        self._init_ui()
        self._start_response_processor()
        self._setup_hotkey()
        
        # Test the connection
        self._test_backend()
    
    def _init_ui(self):
        """Initialize the UI."""
        # Window flags for floating overlay
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        
        # Make background semi-transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set window size and position
        self.setFixedSize(300, 200)
        self._position_window()
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title label
        self.title_label = QLabel("AI Agent")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #00ff88;
                font-size: 24px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
            }
        """)
        
        # Status label
        self.status_label = QLabel(self.status_text)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-family: 'Segoe UI', Arial;
            }
        """)
        
        # State indicator
        self.state_label = QLabel("●")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setStyleSheet("""
            QLabel {
                color: #00ff88;
                font-size: 48px;
            }
        """)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.state_label)
        layout.addWidget(self.status_label)
        
        # Voice control button
        self.voice_button = QPushButton("🎤 Click or Press Ctrl+Space")
        self.voice_button.setStyleSheet("""
            QPushButton {
                background-color: #1a1a2e;
                color: #00ff88;
                border: 2px solid #00ff88;
                border-radius: 10px;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00ff88;
                color: #1a1a2e;
            }
            QPushButton:pressed {
                background-color: #00cc66;
            }
        """)
        self.voice_button.clicked.connect(self._toggle_recording)
        layout.addWidget(self.voice_button)
        
        layout.addStretch()
        
        central.setLayout(layout)
        
        self.setWindowTitle("AI Agent")
        
        # Enable drag and drop
        self.setAcceptDrops(True)
    
    def _position_window(self):
        """Position window in top-right corner."""
        from PyQt6.QtGui import QScreen
        screen = QApplication.primaryScreen().geometry()
        
        x = screen.width() - self.width() - 50
        y = 50
        
        self.move(x, y)
    
    def paintEvent(self, event):
        """Custom paint for rounded background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.setBrush(QColor(20, 20, 30, 240))
        painter.setPen(QPen(QColor(0, 255, 136), 2))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 20, 20)
    
    def _start_response_processor(self):
        """Start thread to process AI backend responses."""
        self.processor = CommandProcessor(self.response_queue)
        self.processor.response_received.connect(self._handle_response)
        self.processor.start()
    
    def _test_backend(self):
        """Test connection to AI backend."""
        self.command_queue.put({
            "type": "test"
        })
        self.set_status("Testing backend connection...")
    
    def _setup_hotkey(self):
        """Setup global hotkey for voice activation."""
        try:
            from src.audio.hotkey import HotkeyHandler
            
            self.hotkey_handler = HotkeyHandler(
                hotkey="<ctrl>+<space>",
                callback=self._toggle_recording
            )
            self.hotkey_handler.start()
            logger.info("Hotkey activated: Ctrl+Space")
            
        except Exception as e:
            logger.error(f"Failed to setup hotkey: {e}")
            self.hotkey_handler = None
    
    def _toggle_recording(self):
        """Toggle voice recording."""
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()
    
    def _start_recording(self):
        """Start voice recording."""
        logger.info("Starting voice recording...")
        self.is_recording = True
        self.set_state("listening")
        self.set_status("Listening... (Click again to stop)")
        self.voice_button.setText("⏹ Stop Recording")
        
        # Send command to backend to start recording
        self.command_queue.put({
            "type": "start_recording"
        })
    
    def _stop_recording(self):
        """Stop voice recording."""
        logger.info("Stopping voice recording...")
        self.is_recording = False
        self.set_state("thinking")
        self.set_status("Processing...")
        self.voice_button.setText("🎤 Click or Press Ctrl+Space")
        
        # Send command to backend to stop and process
        self.command_queue.put({
            "type": "stop_recording"
        })
    
    def _handle_response(self, response: dict):
        """Handle responses from AI backend."""
        response_type = response.get("type", "response")

        if response_type == "event" and response.get("event") == "wake_word_detected":
            self.set_status("Wake word detected")
            if not self.is_recording:
                self._start_recording()
            return

        status = response.get("status", "unknown")
        message = response.get("message", "")
        
        if status == "success":
            self.set_status(f"✓ {message}")
            
            # Check if there's a plan to execute
            if "plan" in response:
                plan = response["plan"]
                needs_confirm = response.get("needs_confirmation", False)
                
                if needs_confirm:
                    remaining = response.get("remaining_confirmations", 3)
                    self.set_status(f"⚠ Dangerous action blocked. Say confirm ({remaining} remaining)")
                    return
                
                # Execute the plan
                self.command_queue.put({
                    "type": "execute_plan",
                    "plan": plan
                })

            if response.get("awaiting_confirmation"):
                remaining = response.get("remaining_confirmations", 3)
                self.set_status(f"⚠ Awaiting confirmation: {remaining} remaining")
                
        else:
            self.set_status(f"✗ {message}")
    
    def set_state(self, state: str):
        """Set the current state."""
        self.state = state
        
        colors = {
            "idle": "#00ff88",
            "listening": "#ffaa00",
            "thinking": "#00aaff",
            "speaking": "#ff00aa"
        }
        
        color = colors.get(state, "#00ff88")
        self.state_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 48px;
            }}
        """)
    
    def set_status(self, text: str):
        """Update status text."""
        self.status_text = text
        self.status_label.setText(text)
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
    
    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.set_status("Drop files here...")
            self.set_state("thinking")
    
    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        self.set_status(self.status_text)
        self.set_state("idle")
    
    def dropEvent(self, event):
        """Handle file drop event."""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path:
                files.append(file_path)
        
        if files:
            logger.info(f"Files dropped: {files}")
            
            # Create a command describing the dropped files
            file_list = "\n".join(files)
            drop_message = f"Files dropped:\n{file_list}"
            
            self.set_status(f"Received {len(files)} file(s)")
            
            # Send to AI backend for processing
            self.command_queue.put({
                "type": "file_drop",
                "files": files,
                "message": drop_message
            })
            
            event.acceptProposedAction()
        
        self.set_state("idle")
    
    def closeEvent(self, event):
        """Handle window close."""
        if hasattr(self, 'hotkey_handler') and self.hotkey_handler:
            self.hotkey_handler.stop()
        
        self.processor.stop()
        self.processor.wait()
        event.accept()


def run_gui(command_queue: Queue, response_queue: Queue):
    """Run the GUI application."""
    app = QApplication(sys.argv)
    
    window = FloatingWidget(command_queue, response_queue)
    window.show()
    
    sys.exit(app.exec())
