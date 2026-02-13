"""
Main GUI Window - Floating overlay widget.
"""
import sys
from multiprocessing import Queue
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QThread
from PyQt6.QtGui import QPainter, QColor, QPen, QFont


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
        
        self._init_ui()
        self._start_response_processor()
        
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
        layout.addStretch()
        
        central.setLayout(layout)
        
        self.setWindowTitle("AI Agent")
    
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
    
    def _handle_response(self, response: dict):
        """Handle responses from AI backend."""
        status = response.get("status", "unknown")
        message = response.get("message", "")
        
        if status == "success":
            self.set_status(f"✓ {message}")
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
    
    def closeEvent(self, event):
        """Handle window close."""
        self.processor.stop()
        self.processor.wait()
        event.accept()


def run_gui(command_queue: Queue, response_queue: Queue):
    """Run the GUI application."""
    app = QApplication(sys.argv)
    
    window = FloatingWidget(command_queue, response_queue)
    window.show()
    
    sys.exit(app.exec())
