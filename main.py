__version__ = "1.2.0"

# Eidtara Application (PyQt6 version)
import os
import sys
import json
import threading
import platform
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox, QRadioButton,
    QFileDialog, QSlider, QProgressBar, QScrollArea, QFrame, QMenu, 
    QMessageBox, QGroupBox, QSpinBox, QTabWidget, QSplashScreen, QDialog,
    QGridLayout
)
from PyQt6.QtGui import QPixmap, QImage, QIcon, QColor, QPalette, QAction, QPainter, QPen, QBrush
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QPoint, QTimer
from PIL import Image
import cv2
from PIL import Image
import numpy as np
import requests
from packaging import version
from urllib.parse import urlparse



# Add moviepy for video conversion
try:
    from moviepy import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False


# List of supported formats
SUPPORTED_FORMATS = ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp', 'heic']
SUPPORTED_VIDEO_FORMATS = ['mp4', 'avi', 'mov', 'mkv', 'webm']

# Theme color schemes
LIGHT_THEME = {
    "bg": "#f5f5f5",
    "fg": "#333333",
    "accent": "#4CAF50",
    "accent_hover": "#3e8e41",
    "card_bg": "#ffffff",
    "entry_bg": "#ffffff",
    "border": "#dddddd",
    "hover": "#e6e6e6"
}

DARK_THEME = {
    "bg": "#2e2e2e",
    "fg": "#f0f0f0",
    "accent": "#4CAF50",
    "accent_hover": "#5dbd61",
    "card_bg": "#3e3e3e",
    "entry_bg": "#454545",
    "border": "#555555",
    "hover": "#505050"
}

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# Worker thread for background processing
class Worker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(tuple)
    error = pyqtSignal(str)
    
    def __init__(self, function, args):
        super().__init__()
        self.function = function
        self.args = args
        
    def run(self):
        try:
            result = self.function(*self.args)
            self.finished.emit((result,))  # Wrap in a tuple!
        except Exception as e:
            self.error.emit(str(e))

class UpdateCheckWorker(QThread):
    finished = pyqtSignal(object, object)  # (result, error)

    def run(self):
        try:
            # Check internet connection
            try:
                requests.get("https://www.google.com", timeout=5)
            except requests.RequestException:
                self.finished.emit(None, "No Internet")
                return

            # Check GitHub server
            try:
                requests.get("https://www.github.com", timeout=5)
            except requests.RequestException:
                self.finished.emit(None, "Server Down")
                return

            repo = "basharulalammazu/editara-windows"
            api_url = f"https://api.github.com/repos/{repo}/releases"
            response = requests.get(api_url, timeout=5)
            if response.status_code == 403 and "rate limit" in response.text.lower():
                self.finished.emit(None, "Rate Limit Exceeded")
                return

            if response.status_code != 200:
                self.finished.emit(None, f"Update Error: {response.status_code}")
                return


            releases = response.json()
            if not releases:
                self.finished.emit({"status": "no_update"}, None)
                return

            latest = sorted(
                releases,
                key=lambda r: version.parse(r["tag_name"].lstrip("v")),
                reverse=True
            )[0]
            latest_version = latest["tag_name"].lstrip("v")
            self.finished.emit({
                "status": "ok",
                "latest_version": latest_version,
                "latest": latest
            }, None)
        except Exception as e:
            self.finished.emit(None, str(e))


# Background removal worker
class RemoveBgWorker(QThread):
    finished = pyqtSignal(Image.Image)
    error = pyqtSignal(str)
    
    def __init__(self, image):
        super().__init__()
        self.image = image
        
    def run(self):
        try:
            img_no_bg = self.remove_bg_with_opencv(self.image)
            self.finished.emit(img_no_bg)
        except Exception as e:
            self.error.emit(str(e))

# Custom styled button class
class StyledButton(QPushButton):
    def __init__(self, text, accent_color="#4CAF50"):
        super().__init__(text)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent_color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {accent_color}DD;
            }}
            QPushButton:pressed {{
                background-color: {accent_color}AA;
            }}
        """)

# Custom card/panel frame
class CardFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)



# Add this class right after the CardFrame class
class LoadingSpinner(QWidget):
    def __init__(self, parent=None, size=80, line_width=10, color=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.line_width = line_width
        self.color = color or QColor(75, 175, 80)  # Default to accent green
        self.angle = 0
        self.opacity = 255
        
        # Semi-transparent background
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(40)  # ~25 fps
        
        # Label for message underneath spinner
        self.label = QLabel("Processing...", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("background: transparent; color: white; font-weight: bold;")
        label_size = self.label.sizeHint()
        self.label.setGeometry(
            (size - label_size.width()) // 2, 
            size + 5, 
            label_size.width(), 
            label_size.height()
        )
    
    def rotate(self):
        self.angle = (self.angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Determine center and radius
        center = QPoint(self.width() // 2, self.height() // 2)
        outer_radius = (min(self.width(), self.height()) - self.line_width) // 2
        
        # Draw semi-transparent background circle
        painter.setBrush(QColor(30, 30, 30, 120))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, outer_radius + self.line_width, outer_radius + self.line_width)
        
        # Draw spinner arcs with gradient opacity
        pen = QPen()
        pen.setWidth(self.line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        
        for i in range(8):
            rotation_angle = self.angle - i * 45
            opacity = 255 - (i * 32)
            if opacity < 0:
                opacity = 0
                
            color = QColor(self.color)
            color.setAlpha(opacity)
            pen.setColor(color)
            painter.setPen(pen)
            
            painter.save()
            painter.translate(center)
            painter.rotate(rotation_angle)
            painter.drawLine(0, 0, 0, -outer_radius)
            painter.restore()

# Add this class after the CardFrame class and before Editara:

class ImageCropDialog(QDialog):
    def __init__(self, image, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crop Image")
        self.image = image
        self.cropped_image = None
        self.zoom_factor = 1.0  # Track zoom level
        
        # Get original image dimensions
        self.orig_width, self.orig_height = image.size
        
        # Convert PIL image to QImage and QPixmap
        img_array = np.array(image)
        self.height, self.width = img_array.shape[:2]
        
        if image.mode == "RGB":
            qimg = QImage(img_array.data, self.width, self.height, 
                        self.width * 3, QImage.Format.Format_RGB888)
        else:  # RGBA
            qimg = QImage(img_array.data, self.width, self.height, 
                        self.width * 4, QImage.Format.Format_RGBA8888)
        
        self.pixmap = QPixmap.fromImage(qimg)
        self.display_pixmap = self.pixmap  # Pixmap that will be displayed (possibly scaled)
        
        # Setup UI
        layout = QVBoxLayout(self)
        
        # Add image size information at top
        size_info = QLabel(f"Original image size: {self.orig_width}x{self.orig_height} pixels")
        size_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(size_info)
        
        # Instructions
        instruction = QLabel("Select crop area by dragging on the image")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instruction)
        
        # Add zoom controls
        zoom_layout = QHBoxLayout()
        zoom_out_btn = QPushButton("🔍-")
        zoom_out_btn.clicked.connect(lambda: self.adjust_zoom(0.8))
        zoom_layout.addWidget(zoom_out_btn)
        
        self.zoom_label = QLabel("Zoom: 100%")
        zoom_layout.addWidget(self.zoom_label)
        
        zoom_in_btn = QPushButton("🔍+")
        zoom_in_btn.clicked.connect(lambda: self.adjust_zoom(1.25))
        zoom_layout.addWidget(zoom_in_btn)
        
        fit_btn = QPushButton("Fit to View")
        fit_btn.clicked.connect(self.fit_to_view)
        zoom_layout.addWidget(fit_btn)
        
        layout.addLayout(zoom_layout)
        
        # Image display area
        self.image_label = QLabel()
        self.image_label.setPixmap(self.display_pixmap)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Make it scrollable if the image is large
        self.scroll = QScrollArea()
        self.scroll.setWidget(self.image_label)
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll)
        
        
        # Crop dimension inputs
        crop_controls = QHBoxLayout()
        
        crop_controls.addWidget(QLabel("X:"))
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, self.width - 10)
        crop_controls.addWidget(self.x_spin)
        
        crop_controls.addWidget(QLabel("Y:"))
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, self.height - 10)
        crop_controls.addWidget(self.y_spin)
        
        crop_controls.addWidget(QLabel("Width:"))
        self.w_spin = QSpinBox()
        self.w_spin.setRange(10, self.width)
        self.w_spin.setValue(self.width)
        crop_controls.addWidget(self.w_spin)
        
        crop_controls.addWidget(QLabel("Height:"))
        self.h_spin = QSpinBox()
        self.h_spin.setRange(10, self.height)
        self.h_spin.setValue(self.height)
        crop_controls.addWidget(self.h_spin)
        
        layout.addLayout(crop_controls)
        
        # Connect spin box changes to update rectangle
        self.x_spin.valueChanged.connect(self.update_crop_rect)
        self.y_spin.valueChanged.connect(self.update_crop_rect)
        self.w_spin.valueChanged.connect(self.update_crop_rect)
        self.h_spin.valueChanged.connect(self.update_crop_rect)
        
        # Buttons for actions
        button_layout = QHBoxLayout()
        
        preview_btn = QPushButton("Preview")
        preview_btn.clicked.connect(self.preview_crop)
        button_layout.addWidget(preview_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        crop_btn = QPushButton("Crop")
        crop_btn.clicked.connect(self.accept)
        button_layout.addWidget(crop_btn)
        
        layout.addLayout(button_layout)
        
        # Setup drawing variables
        self.drawing = False
        self.start_point = None
        self.current_rectangle = None
        
        # Enable mouse tracking on label
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self.mouse_press
        self.image_label.mouseMoveEvent = self.mouse_move
        self.image_label.mouseReleaseEvent = self.mouse_release
        
        # Make dialog larger
        self.resize(800, 600)
         
    def adjust_zoom(self, factor):
        """Adjust zoom level by the given factor"""
        self.zoom_factor *= factor
        self.zoom_factor = max(0.1, min(5.0, self.zoom_factor))  # Limit zoom range
        self.zoom_label.setText(f"Zoom: {int(self.zoom_factor * 100)}%")
        self.update_display()


    def fit_to_view(self):
        """Resize image to fit in the viewport"""
        viewport_size = self.scroll.viewport().size()
        scale_w = viewport_size.width() / self.pixmap.width()
        scale_h = viewport_size.height() / self.pixmap.height()
        self.zoom_factor = min(scale_w, scale_h) * 0.95  # 95% of available space
        self.zoom_label.setText(f"Zoom: {int(self.zoom_factor * 100)}%")
        self.update_display()


        
    def update_display(self):
        """Update displayed image with current zoom"""
        if hasattr(self, 'modified_pixmap'):
            # If we've already drawn a crop rectangle, update that version
            source_pixmap = self.modified_pixmap
        else:
            # Otherwise use the original pixmap
            source_pixmap = self.pixmap
        
        # Calculate new size based on zoom
        new_width = int(self.width * self.zoom_factor)
        new_height = int(self.height * self.zoom_factor)
        
        if new_width > 0 and new_height > 0:
            self.display_pixmap = source_pixmap.scaled(
                new_width, new_height, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(self.display_pixmap)
            self.image_label.setFixedSize(new_width, new_height)

    

    def mouse_press(self, event):
        self.drawing = True
        self.start_point = event.pos()
        
        # Adjust for scroll position and image position
        scroll_area = self.image_label.parent().parent()
        self.scroll_x = scroll_area.horizontalScrollBar().value()
        self.scroll_y = scroll_area.verticalScrollBar().value()
        
        # Calculate offset if image is centered
        self.offset_x = max(0, (self.image_label.width() - self.pixmap.width()) // 2)
        self.offset_y = max(0, (self.image_label.height() - self.pixmap.height()) // 2)
        
        x = max(0, min(event.pos().x() - self.offset_x + self.scroll_x, self.width))
        y = max(0, min(event.pos().y() - self.offset_y + self.scroll_y, self.height))
        
        self.x_spin.setValue(x)
        self.y_spin.setValue(y)
    
    def mouse_move(self, event):
        if not self.drawing:
            return
            
        # Calculate current position with scroll adjustments
        x = max(0, min(event.pos().x() - self.offset_x + self.scroll_x, self.width))
        y = max(0, min(event.pos().y() - self.offset_y + self.scroll_y, self.height))
        
        # Update width/height spins
        width = max(1, x - self.x_spin.value())
        height = max(1, y - self.y_spin.value())
        
        self.w_spin.setValue(width)
        self.h_spin.setValue(height)
    
    def mouse_release(self, event):
        self.drawing = False
        self.update_crop_rect()
    
    def update_crop_rect(self):
        # Create a copy of the original image to draw on
        if hasattr(self, 'modified_pixmap'):
            del self.modified_pixmap
        self.modified_pixmap = self.pixmap.copy()
        
        # Draw rectangle on the image
        painter = QPainter(self.modified_pixmap)
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawRect(
            self.x_spin.value(), 
            self.y_spin.value(),
            self.w_spin.value(),
            self.h_spin.value()
        )
        painter.end()
        
        # Update displayed image
        self.image_label.setPixmap(self.modified_pixmap)
    
    def preview_crop(self):
        # Show a preview of the cropped image
        x = self.x_spin.value()
        y = self.y_spin.value()
        width = self.w_spin.value()
        height = self.h_spin.value()
        
        # Ensure valid crop area
        if width <= 0 or height <= 0:
            return
            
        # Crop the PIL Image
        cropped = self.image.crop((x, y, x + width, y + height))
        
        # Convert to QImage/QPixmap for display
        img_array = np.array(cropped)
        if cropped.mode == "RGB":
            qimg = QImage(img_array.data, width, height, width * 3, QImage.Format.Format_RGB888)
        else:  # RGBA
            qimg = QImage(img_array.data, width, height, width * 4, QImage.Format.Format_RGBA8888)
            
        preview_pixmap = QPixmap.fromImage(qimg)
        
        # Show preview dialog
        preview = QDialog(self)
        preview.setWindowTitle("Crop Preview")
        preview_layout = QVBoxLayout(preview)
        
        preview_label = QLabel()
        preview_label.setPixmap(preview_pixmap)
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_label)
        
        close_btn = QPushButton("Close Preview")
        close_btn.clicked.connect(preview.close)
        preview_layout.addWidget(close_btn)
        
        preview.exec()
    
    def get_cropped_image(self):
        # Return the cropped PIL Image
        x = self.x_spin.value()
        y = self.y_spin.value()
        width = self.w_spin.value()
        height = self.h_spin.value()
        
        # Ensure valid crop area
        if width <= 0 or height <= 0:
            return None
            
        # Crop the PIL Image
        return self.image.crop((x, y, x + width, y + height))
    



# Main application window
class Editara(QMainWindow):
    @staticmethod
    def save_theme(theme_name):
        with open("theme.json", "w") as f:
            json.dump({"theme": theme_name}, f)
    
    @staticmethod
    def load_theme():
        try:
            with open("theme.json", "r") as f:
                data = json.load(f)
                return data.get("theme", "dark")
        except Exception:
            return "dark"
        
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Eidtara")
        self.setMinimumSize(700, 00)
        
        # Remove maximize button but keep minimize and close buttons
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint
        )
        
        # Load app icon
        try:
            app_icon = QIcon(resource_path("appicon.ico"))
            self.setWindowIcon(app_icon)
        except:
            pass
        
        # Variables for conversion
        self.selected_files = []
        self.file_types = []  # image or video
        self.file_count = 0
        self.is_converting = False
        self.output_folder = ""
        self.mode = "Image"  # Image or Video
        
        # Variables for image edit
        self.edit_image = None
        self.edit_image_path = None
        
        # Load theme
        theme_name = self.load_theme()
        self.theme = DARK_THEME if theme_name == "dark" else LIGHT_THEME
        
        # Create menu bar
        self.setup_menu()
        
        # Create main UI
        self.create_ui()
        
        # Apply theme
        self.apply_theme()
    

    def show_info(self, title, message):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIconPixmap(self.get_accent_icon("info").pixmap(48, 48))
        msg.exec()

    def show_warning(self, title, message):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIconPixmap(self.get_accent_icon("warning").pixmap(48, 48))
        msg.exec()

    def show_error(self, title, message):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIconPixmap(self.get_accent_icon("error").pixmap(48, 48))
        msg.exec()

    def get_accent_icon(self, icon_type="info"):
        # Create a pixmap with your accent color
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        brush = QBrush(QColor(self.theme["accent"]))
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(8, 8, 48, 48)
        painter.setPen(QColor("white"))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(32)
        painter.setFont(font)
        if icon_type == "info":
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "i")
        elif icon_type == "question":
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "?")
        elif icon_type == "warning":
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "!")
        elif icon_type == "error":
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "×")
        painter.end()
        return QIcon(pixmap)

     # Add these methods here
    def show_loading(self, message="Processing..."):
        # Create a semi-transparent overlay for the entire app
        self.overlay = QWidget(self)
        self.overlay.setGeometry(self.rect())
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        
        # Create and position the spinner
        self.spinner = LoadingSpinner(self.overlay, color=QColor(self.theme["accent"]))
        self.spinner.label.setText(message)
        
        # Center the spinner in the overlay
        spinner_x = (self.overlay.width() - self.spinner.width()) // 2
        spinner_y = (self.overlay.height() - self.spinner.height()) // 2
        self.spinner.move(spinner_x, spinner_y)
        
        # Show the overlay with spinner
        self.overlay.show()
        self.overlay.raise_()

    def hide_loading(self):
        if hasattr(self, 'overlay') and self.overlay is not None:
            self.overlay.hide()
            self.overlay.deleteLater
   
        
    def setup_menu(self):
        menubar = self.menuBar()
        
        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        
        privacy_action = QAction("Privacy", self)
        privacy_action.triggered.connect(self.show_privacy)
        settings_menu.addAction(privacy_action)
        
        docs_action = QAction("Documentation", self)
        docs_action.triggered.connect(self.show_documentation)
        settings_menu.addAction(docs_action)
        
        policy_action = QAction("Policy", self)
        policy_action.triggered.connect(self.show_policy)
        settings_menu.addAction(policy_action)
        
         # --- Add Update action here ---
        update_action = QAction("Check for Update", self)
        update_action.triggered.connect(self.check_for_update)
        settings_menu.addAction(update_action)

        settings_menu.addSeparator()
        
        help_action = QAction("Help", self)
        help_action.triggered.connect(self.show_help)
        settings_menu.addAction(help_action)
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        settings_menu.addAction(about_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        converter_action = QAction("Converter", self)
        converter_action.triggered.connect(self.show_converter)
        tools_menu.addAction(converter_action)
        
        image_edit_action = QAction("Image Edit", self)
        image_edit_action.triggered.connect(self.show_image_edit)
        tools_menu.addAction(image_edit_action)
        
        # Theme menu
        theme_menu = menubar.addMenu("Theme")
        
        toggle_theme_action = QAction("Toggle Theme", self)
        toggle_theme_action.triggered.connect(self.toggle_theme)
        theme_menu.addAction(toggle_theme_action)
    
    def create_ui(self):
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Tab widget to switch between Converter and Image Edit
        self.tab_widget = QTabWidget()
        
        # Create converter tab
        self.converter_tab = QWidget()
        self.converter_layout = QVBoxLayout(self.converter_tab)
        self.setup_converter_ui()
        self.tab_widget.addTab(self.converter_tab, "Converter")
        
        # Create image edit tab
        self.image_edit_tab = QWidget()
        self.image_edit_layout = QVBoxLayout(self.image_edit_tab)
        self.setup_image_edit_ui()
        self.tab_widget.addTab(self.image_edit_tab, "Image Edit")
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        self.main_layout.addWidget(self.tab_widget)
        
        # Status bar at the bottom
        self.statusBar().showMessage("Ready")

    def setup_converter_ui(self):
        # Header
        header_layout = QHBoxLayout()
        self.header_label = QLabel("Eidtara")
        self.header_label.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {self.theme['fg']};"
        )
        header_layout.addWidget(self.header_label)
        header_layout.addStretch()
                
        # Theme toggle button in the header
        self.theme_button = QPushButton("🌙" if self.theme == DARK_THEME else "☀️")
        self.theme_button.clicked.connect(self.toggle_theme)
        self.theme_button.setFixedWidth(40)
        header_layout.addWidget(self.theme_button)
        
        self.converter_layout.addLayout(header_layout)
        
        # Source files card
        source_card = CardFrame()
        source_layout = QVBoxLayout(source_card)
        
        self.source_header = QLabel("Source Files")
        self.source_header.setStyleSheet(
            f"font-weight: bold; color: {self.theme['fg']};"
        )
        source_layout.addWidget(self.source_header)
        
        # File path input and browse button
        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Drag and drop files here or click Browse")
        self.file_path_input.setAcceptDrops(True)
        self.file_path_input.dragEnterEvent = self.dragEnterEvent
        self.file_path_input.dropEvent = self.dropEvent
        file_layout.addWidget(self.file_path_input)
        
        browse_button = StyledButton("Browse")
        browse_button.clicked.connect(self.browse_files)
        file_layout.addWidget(browse_button)
        
        preview_button = StyledButton("Preview")
        preview_button.clicked.connect(self.preview_files)
        file_layout.addWidget(preview_button)
        
        source_layout.addLayout(file_layout)
        
        # Drop hint and file count label
        self.drop_label = QLabel("✨ Drag and drop a folder or image/video files here")
        source_layout.addWidget(self.drop_label)
        
        self.files_label = QLabel("No files selected")
        source_layout.addWidget(self.files_label)
        
        self.converter_layout.addWidget(source_card)
        
        # Settings card
        settings_card = CardFrame()
        settings_layout = QVBoxLayout(settings_card)
        
        # Mode switch buttons
        mode_layout = QHBoxLayout()
        self.file_type_label = QLabel("Select your file type:")
        self.file_type_label.setStyleSheet(f"font-weight: bold; color: {self.theme['fg']};")
        mode_layout.addWidget(self.file_type_label)
        mode_layout.addStretch(1)

        self.image_button = QPushButton("Image")
        self.image_button.setCheckable(True)
        self.image_button.setChecked(True)
        self.image_button.clicked.connect(lambda: self.set_mode("Image"))

        self.video_button = QPushButton("Video")
        self.video_button.setCheckable(True)
        self.video_button.clicked.connect(lambda: self.set_mode("Video"))

        mode_layout.addWidget(self.image_button)
        mode_layout.addWidget(self.video_button)

        settings_layout.addLayout(mode_layout)


        # Settings header
        settings_header = QLabel("Conversion Settings")
        settings_header.setStyleSheet("font-weight: bold;")
        settings_layout.addWidget(settings_header)
        
        # Format selection
        format_layout = QHBoxLayout()
        format_label = QLabel("Output Format:")
        format_label.setFixedWidth(120)
        format_layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(SUPPORTED_FORMATS)
        self.format_combo.setCurrentText("webp")
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        
        settings_layout.addLayout(format_layout)
        
        # Quality slider (for images)
        self.quality_container = QWidget()  # Create a container widget
        self.quality_layout = QHBoxLayout(self.quality_container)

        quality_label = QLabel("Image Quality:")
        quality_label.setFixedWidth(120)
        self.quality_layout.addWidget(quality_label)

        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setMinimum(10)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(90)
        self.quality_layout.addWidget(self.quality_slider)

        self.quality_value = QLabel("90%")
        self.quality_layout.addWidget(self.quality_value)

        # Connect quality slider change
        self.quality_slider.valueChanged.connect(self.update_quality_label)

        settings_layout.addWidget(self.quality_container)  # Add the container to the layout
        
        # Resize options
        resize_group = QGroupBox("Resize")
        resize_group.setCheckable(True)
        resize_group.setChecked(False)
        resize_layout = QVBoxLayout(resize_group)
        
        # Resize mode
        self.resize_width_radio = QRadioButton("Specify Width")
        self.resize_height_radio = QRadioButton("Specify Height")
        self.resize_both_radio = QRadioButton("Specify Both")
        self.resize_both_radio.setChecked(True)
        
        resize_layout.addWidget(self.resize_width_radio)
        resize_layout.addWidget(self.resize_height_radio)
        resize_layout.addWidget(self.resize_both_radio)
        
        # Dimensions
        dim_layout = QHBoxLayout()
        dim_layout.addWidget(QLabel("Width:"))
        self.width_input = QSpinBox()
        self.width_input.setRange(1, 10000)
        self.width_input.setValue(800)
        dim_layout.addWidget(self.width_input)
        
        dim_layout.addWidget(QLabel("Height:"))
        self.height_input = QSpinBox()
        self.height_input.setRange(1, 10000)
        self.height_input.setValue(600)
        dim_layout.addWidget(self.height_input)
        
        resize_layout.addLayout(dim_layout)
        settings_layout.addWidget(resize_group)
        self.resize_group = resize_group  # Store for later access
        
        # Video time crop (initially hidden)
        self.time_crop_group = QGroupBox("Video Time Range")
        time_layout = QHBoxLayout(self.time_crop_group)
        
        time_layout.addWidget(QLabel("Start Time (s):"))
        self.start_time = QSpinBox()
        self.start_time.setRange(0, 999999)
        time_layout.addWidget(self.start_time)
        
        time_layout.addWidget(QLabel("End Time (s):"))
        self.end_time = QSpinBox()
        self.end_time.setRange(0, 999999)
        self.end_time.setSpecialValueText("End")
        time_layout.addWidget(self.end_time)
        
        settings_layout.addWidget(self.time_crop_group)
        self.time_crop_group.setVisible(False)
        
        self.converter_layout.addWidget(settings_card)
        
        # Progress and convert button
        action_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        action_layout.addWidget(self.progress_bar)
        
        self.convert_button = StyledButton("🚀 Convert", self.theme["accent"])
        self.convert_button.clicked.connect(self.start_conversion)
        self.convert_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme["accent"]};
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.theme["accent_hover"]};
            }}
        """)
        action_layout.addWidget(self.convert_button)
        
        self.converter_layout.addLayout(action_layout)
        self.converter_layout.addStretch()
    
    def setup_image_edit_ui(self):
        # Image edit tools
        self.tools_label = QLabel("Image Edit Tools")
        self.tools_label.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {self.theme['fg']};"
        )
        self.image_edit_layout.addWidget(self.tools_label)
        
        # Buttons for edit tools
        buttons_layout = QHBoxLayout()
        
        upload_btn = StyledButton("Upload Image", self.theme["accent"])
        upload_btn.clicked.connect(self.upload_edit_image)
        buttons_layout.addWidget(upload_btn)
        
        passport_btn = StyledButton("Passport Size", self.theme["accent"])
        passport_btn.clicked.connect(self.passport_size_image)
        buttons_layout.addWidget(passport_btn)
        
        # Background removal button
        bg_btn = StyledButton("Remove Background", self.theme["accent"])
        bg_btn.clicked.connect(self.remove_background)
        buttons_layout.addWidget(bg_btn)
        
        crop_btn = StyledButton("Crop Image", self.theme["accent"])
        crop_btn.clicked.connect(self.crop_image)
        buttons_layout.addWidget(crop_btn)

        # Quality improvement button
        quality_btn = StyledButton("Improve Quality", self.theme["accent"])
        quality_btn.clicked.connect(self.improve_quality)
        buttons_layout.addWidget(quality_btn)
        
        self.image_edit_layout.addLayout(buttons_layout)


        # Image preview area
        self.edit_image_label = QLabel("No image uploaded")
        self.edit_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit_image_label.setMinimumHeight(300)
        self.edit_image_label.setStyleSheet(f"background-color: {self.theme['card_bg']}; border-radius: 8px;")
        
        self.image_edit_layout.addWidget(self.edit_image_label)
        self.image_edit_layout.addStretch(1)

    
    def on_tab_changed(self, index):
        if index == 0:  # Converter tab
            self.statusBar().showMessage("Converter mode active")
        else:  # Image Edit tab
            self.statusBar().showMessage("Image Edit mode active")


    def check_for_update(self):
        self.show_loading("Checking for updates...")  # Show spinner

        self.update_worker = UpdateCheckWorker()
        self.update_worker.finished.connect(self.handle_update_result)
        self.update_worker.start()

    def handle_update_result(self, result, error):
        self.hide_loading()
        if error:
            if error == "No Internet":
                msg = QMessageBox(self)
                msg.setWindowTitle("No Internet")
                msg.setText("Please check your internet connection and try again.")
                msg.setIconPixmap(self.get_accent_icon("error").pixmap(48, 48))
                msg.exec()
            elif error == "Server Down":
                msg = QMessageBox(self)
                msg.setWindowTitle("Server Down")
                msg.setText("Oops! It looks like the update server is currently down.\nPlease try again later.")
                msg.setIconPixmap(self.get_accent_icon("error").pixmap(48, 48))
                msg.exec()
            elif error == "Update Error":
                msg = QMessageBox(self)
                msg.setWindowTitle("Update Error")
                msg.setText("Could not connect to the update server.")
                msg.setIconPixmap(self.get_accent_icon("error").pixmap(48, 48))
                msg.exec()
            elif error == "Rate Limit Exceeded":
                msg = QMessageBox(self)
                msg.setWindowTitle("Rate Limit Exceeded")
                msg.setText("GitHub update server rate limit has been reached.\nTry again in a few minutes or use a GitHub token.")
                msg.setIconPixmap(self.get_accent_icon("error").pixmap(48, 48))
                msg.exec()
            else:
                msg = QMessageBox(self)
                msg.setWindowTitle("Update Error")
                msg.setText(f"An error occurred while checking for updates:\n{error}")
                msg.setIconPixmap(self.get_accent_icon("error").pixmap(48, 48))
                msg.exec()
            return

        if result["status"] == "no_update":
            msg = QMessageBox(self)
            msg.setWindowTitle("No Update")
            msg.setText("No releases found.")
            msg.setIconPixmap(self.get_accent_icon("info").pixmap(48, 48))
            msg.exec()
            return

        latest_version = result["latest_version"]
        latest = result["latest"]
        if version.parse(latest_version) > version.parse(__version__):
            msg = QMessageBox(self)
            msg.setWindowTitle("Update Available")
            msg.setText("A newer version is available...")
            msg.setIconPixmap(self.get_accent_icon("question").pixmap(48, 48))
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            reply = msg.exec()

            if reply == QMessageBox.StandardButton.Yes:
                exe_asset = next(
                    (asset for asset in latest["assets"] if asset["name"].endswith(".exe")),
                    None
                )
                if not exe_asset:
                    msg = QMessageBox(self)
                    msg.setWindowTitle("Download Error")
                    msg.setText("No .exe file found in the latest release.")
                    msg.setIconPixmap(self.get_accent_icon("error").pixmap(48, 48))
                    msg.exec()
                    return

                download_url = exe_asset["browser_download_url"]
                filename = os.path.basename(urlparse(download_url).path)
                save_path = os.path.join(os.path.expanduser("~"), "Downloads", filename)

                # Download in a thread to keep spinner visible
                self.show_loading("Downloading update...")
                thread = QThread()
                def download():
                    try:
                        with requests.get(download_url, stream=True) as r:
                            r.raise_for_status()
                            with open(save_path, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    f.write(chunk)
                        QTimer.singleShot(0, lambda: (
                            self.hide_loading(),
                            QMessageBox(self).setWindowTitle("Download Complete"),
                            QMessageBox(self).setText(f"The latest version has been downloaded to:\n{save_path}\n\nPlease run it to complete the update."),
                            QMessageBox(self).setIconPixmap(self.get_accent_icon("info").pixmap(48, 48)),
                            QMessageBox(self).exec(),
                            os.startfile(save_path)
                        ))
                    except Exception as e:
                        # ...for download failed...
                        QTimer.singleShot(0, lambda: (
                            self.hide_loading(),
                            QMessageBox(self).setWindowTitle("Download Failed"),
                            QMessageBox(self).setText(f"Failed to download update:\n{e}"),
                            QMessageBox(self).setIconPixmap(self.get_accent_icon("error").pixmap(48, 48)),
                            QMessageBox(self).exec()
                        ))
                thread.run = download
                thread.start()
        else:
            # ...for up to date...
            msg = QMessageBox(self)
            msg.setWindowTitle("Up To Date")
            msg.setText(f"You are using the latest version ({__version__}).")
            msg.setIconPixmap(self.get_accent_icon("info").pixmap(48, 48))
            msg.exec()
  
    def show_converter(self):
        self.tab_widget.setCurrentIndex(0)
    
    def show_image_edit(self):
        self.tab_widget.setCurrentIndex(1)

    def upload_edit_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Image files (*.jpg *.jpeg *.png *.bmp *.tiff *.webp *.heic);;All files (*.*)"
        )
        if file_path:
            try:
                self.edit_image_path = file_path
                self.edit_image = Image.open(file_path)
                
                # Create preview
                img = self.edit_image.copy()
                img.thumbnail((300, 300))
                qimage = self.pil_to_qimage(img)
                pixmap = QPixmap.fromImage(qimage)
                
                self.edit_image_label.setPixmap(pixmap)
                self.statusBar().showMessage(f"Loaded image: {os.path.basename(file_path)}")
            except Exception as e:
                msg = QMessageBox(self)
                msg.setWindowTitle("Error")
                msg.setText(f"Failed to load image:\n{str(e)}")
                msg.setIconPixmap(self.get_accent_icon("error").pixmap(48, 48))
                msg.exec()
        else:
            self.edit_image_path = None
            self.edit_image = None
            self.edit_image_label.setText("No image uploaded")
            self.edit_image_label.setPixmap(QPixmap())

    def passport_size_image(self):
        if not self.edit_image:
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText("Please upload an image first.")
            msg.setIconPixmap(self.get_accent_icon("warning").pixmap(48, 48))
            msg.exec()
            return
        
        # Show loading spinner
        self.show_loading("Creating Passport Photo...")
    
        # Resize to passport size (413x531 pixels, 300 DPI)
        try:
            passport_img = self.edit_image.copy()
            passport_img = passport_img.resize((413, 531), Image.LANCZOS)
            
            self.hide_loading()  # Hide spinner after processing
            # Save dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Passport Size Image",
                os.path.join(self.get_downloads_folder(), "passport_size_image.jpg"),
                "JPEG (*.jpg);;PNG (*.png);;All files (*.*)"
            )
            
            # ...after saving...
            if file_path:
                msg = QMessageBox(self)
                msg.setWindowTitle("Success")
                msg.setText(f"Passport size image saved:\n{file_path}")
                msg.setIconPixmap(self.get_accent_icon("info").pixmap(48, 48))
                msg.exec()

        except Exception as e:
            self.hide_loading()
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to create passport image:\n{str(e)}")
            msg.setIconPixmap(self.get_accent_icon("error").pixmap(48, 48))
            msg.exec()



    def remove_background(self):
        if not self.edit_image:
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText("Please upload an image first.")
            msg.setIconPixmap(self.get_accent_icon("warning").pixmap(48, 48))
            msg.exec()
            return
        
        try:
            # Show loading spinner
            self.show_loading("Removing Background...")
            self.statusBar().showMessage("Removing background, please wait...")

            # Run background removal in a worker thread
            self.bg_worker = Worker(self.remove_bg_with_opencv, (self.edit_image,))
            self.bg_worker.finished.connect(self.bg_removal_done)
            self.bg_worker.error.connect(self.bg_removal_error)
            self.bg_worker.start()

        # ...on error...
        except Exception as e:
            self.hide_loading()
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to remove background:\n{str(e)}")
            msg.setIconPixmap(self.get_accent_icon("error").pixmap(48, 48))
            msg.exec()

    def remove_bg_with_opencv(self, image):
        import cv2
        import numpy as np
        from PIL import Image

        # Convert PIL to OpenCV image
        img = np.array(image)

        if len(img.shape) == 2:  # Grayscale fallback
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        has_alpha = img.shape[2] == 4 if len(img.shape) == 3 else False

        # Convert to proper format for OpenCV
        if has_alpha:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        else:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        # Prepare mask and models for GrabCut
        mask = np.zeros(img_rgb.shape[:2], np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        height, width = img_rgb.shape[:2]
        rect_margin = min(width, height) // 6
        rect = (rect_margin, rect_margin, width - 2*rect_margin, height - 2*rect_margin)

        # Run GrabCut
        cv2.grabCut(img_rgb, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

        # Mask: 1 (fg) and 3 (probable fg) are foreground
        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype("uint8")

        # Apply the mask
        result = img.copy()
        if has_alpha:
            result[:, :, 3] = mask2 * 255
        else:
            result_rgba = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2RGBA)
            result_rgba[:, :, 3] = mask2 * 255
            result = result_rgba

        return Image.fromarray(result)



    def bg_removal_done(self, result_tuple):
        self.hide_loading()  # Hide spinner after processing
        
        # Unpack the image from the tuple
        img_no_bg = result_tuple[0]
        
        # Continue with existing code
        display_img = img_no_bg.copy()
        display_img.thumbnail((300, 300))
        qimage = self.pil_to_qimage(display_img)
        pixmap = QPixmap.fromImage(qimage)
        
        self.edit_image_label.setPixmap(pixmap)
        self.statusBar().showMessage("Background removed successfully")
        
        # Ask to save
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Background-Removed Image",
            "",
            "PNG (*.png);;All files (*.*)"
        )
        
        if file_path:
            msg = QMessageBox(self)
            msg.setWindowTitle("Success")
            msg.setText(f"Background-removed image saved:\n{file_path}")
            msg.setIconPixmap(self.get_accent_icon("info").pixmap(48, 48))
            msg.exec()


    def bg_removal_error(self, error):
        self.hide_loading()  # Hide spinner on error
        self.statusBar().showMessage("Error removing background")
        msg = QMessageBox(self)
        msg.setWindowTitle("Error")
        msg.setText(f"Failed to remove background:\n{error}")
        msg.setIconPixmap(self.get_accent_icon("error").pixmap(48, 48))
        msg.exec()

    
    def crop_image(self):
        if not self.edit_image:
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText("Please upload an image first.")
            msg.setIconPixmap(self.get_accent_icon("warning").pixmap(48, 48))
            msg.exec()
            return
        
        try:
            # Create and show the crop dialog
            crop_dialog = ImageCropDialog(self.edit_image, self)
            result = crop_dialog.exec()
            
            # If user clicked Crop (accept), process the cropped image
            if result == QDialog.DialogCode.Accepted:
                cropped_img = crop_dialog.get_cropped_image()
                if cropped_img:
                    # Update display
                    preview = cropped_img.copy()
                    preview.thumbnail((300, 300))
                    qimage = self.pil_to_qimage(preview)
                    pixmap = QPixmap.fromImage(qimage)
                    self.edit_image_label.setPixmap(pixmap)
                    
                    # Update stored image
                    self.edit_image = cropped_img
                    
                    # Ask to save
                    file_path, _ = QFileDialog.getSaveFileName(
                        self,
                        "Save Cropped Image",
                        "",
                        "PNG (*.png);;JPEG (*.jpg);;All files (*.*)"
                    )
                    
                    # ...after saving...
                    if file_path:
                        msg = QMessageBox(self)
                        msg.setWindowTitle("Success")
                        msg.setText(f"Cropped image saved:\n{file_path}")
                        msg.setIconPixmap(self.get_accent_icon("info").pixmap(48, 48))
                        msg.exec()
        # ...on error...
        except Exception as e:
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to crop image:\n{str(e)}")
            msg.setIconPixmap(self.get_accent_icon("error").pixmap(48, 48))
            msg.exec()

    def improve_quality(self):
        if not self.edit_image:
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText("Please upload an image first.")
            msg.setIconPixmap(self.get_accent_icon("warning").pixmap(48, 48))
            msg.exec()
            return

        try:
            # Show loading spinner
            self.show_loading("Enhancing image quality...")
            self.statusBar().showMessage("Enhancing image quality, please wait...")
            # Convert PIL image to OpenCV (numpy) format
            img = np.array(self.edit_image.convert("RGB"))
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            # Load LapSRN model
            sr = cv2.dnn_superres.DnnSuperResImpl_create()
            model_path = "LapSRN_x2.pb"
            sr.readModel(model_path)
            sr.setModel("lapsrn", 2)  # scale = 2

            # Apply super resolution
            result = sr.upsample(img)
            self.hide_loading()  # Hide spinner after processing
            # Update stored image
            self.edit_image = Image.fromarray(result_rgb)
            # Convert back to PIL for GUI usage
            result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            result_pil = Image.fromarray(result_rgb)

            # Show preview
            preview = result_pil.copy()
            preview.thumbnail((300, 300))
            qimage = self.pil_to_qimage(preview)
            pixmap = QPixmap.fromImage(qimage)
            self.edit_image_label.setPixmap(pixmap)

            # Save file dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Enhanced Image",
                "",
                "PNG (*.png);;JPEG (*.jpg);;All files (*.*)"
            )

            self.hide_loading()  # Hide spinner after processing
            # ...after saving...
            if file_path:
                msg = QMessageBox(self)
                msg.setWindowTitle("Success")
                msg.setText(f"Enhanced image saved:\n{file_path}")
                msg.setIconPixmap(self.get_accent_icon("info").pixmap(48, 48))
                msg.exec()

        # ...on error...
        except Exception as e:
            self.hide_loading()
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to enhance image:\n{str(e)}")
            msg.setIconPixmap(self.get_accent_icon("error").pixmap(48, 48))
            msg.exec()
            

    def get_downloads_folder(self):
        if platform.system() == "Windows":
            return os.path.join(os.environ["USERPROFILE"], "Downloads")
        elif platform.system() == "Darwin":  # macOS
            return os.path.join(os.path.expanduser("~"), "Downloads")
        else:  # Linux and others
            return os.path.join(os.path.expanduser("~"), "Downloads")

    # Helper to convert PIL Image to QImage
    def pil_to_qimage(self, pil_image):
        if pil_image.mode == "RGB":
            r, g, b = pil_image.split()
            pil_image = Image.merge("RGB", (b, g, r))
        elif pil_image.mode == "RGBA":
            r, g, b, a = pil_image.split()
            pil_image = Image.merge("RGBA", (b, g, r, a))
        
        im_data = pil_image.convert("RGBA").tobytes("raw", "RGBA")
        qimage = QImage(
            im_data, pil_image.size[0], pil_image.size[1], 
            QImage.Format.Format_RGBA8888
        )
        return qimage

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        file_paths = []
        
        for url in urls:
            file_path = url.toLocalFile()
            file_paths.append(file_path)
        
        if file_paths:
            self.process_dropped_files(file_paths)
    
    def process_dropped_files(self, file_paths):
        # Check if files match current mode
        valid_files = []
        file_types = []
        
        if self.mode == "Image":
            valid_extensions = SUPPORTED_FORMATS
        else:
            valid_extensions = SUPPORTED_VIDEO_FORMATS
            
        for path in file_paths:
            if os.path.isdir(path):
                # Process directory contents
                for root, dirs, files in os.walk(path):
                    for file in files:
                        full_path = os.path.join(root, file)
                        ext = os.path.splitext(file)[1].lower().lstrip('.')
                        if ext in valid_extensions:
                            valid_files.append(full_path)
                            file_types.append(self.mode.lower())
            else:
                # Process single file
                ext = os.path.splitext(path)[1].lower().lstrip('.')
                if ext in valid_extensions:
                    valid_files.append(path)
                    file_types.append(self.mode.lower())
        
        if valid_files:
            self.selected_files = valid_files
            self.file_types = file_types
            self.file_count = len(valid_files)
            self.file_path_input.setText(";".join(valid_files))
            self.files_label.setText(f"Found {self.file_count} convertible {self.mode.lower()}{'s' if self.file_count != 1 else ''}")
            self.statusBar().showMessage(f"Ready to convert {self.file_count} {self.mode.lower()}{'s' if self.file_count != 1 else ''}")
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("Invalid Files")
            msg.setText(f"No valid {self.mode.lower()} files found.")
            msg.setIconPixmap(self.get_accent_icon("warning").pixmap(48, 48))
            msg.exec()
                    
    def browse_files(self):
        if self.mode == "Image":
            filter_str = "Image files (*.jpg *.jpeg *.png *.bmp *.tiff *.webp *.heic);;All files (*.*)"
        else:
            filter_str = "Video files (*.mp4 *.avi *.mov *.mkv *.webm);;All files (*.*)"
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, 
            f"Select {self.mode} Files",
            "",
            filter_str
        )
        
        if file_paths:
            self.process_dropped_files(file_paths)

    def preview_files(self):
        if not self.selected_files:
            msg = QMessageBox(self)
            msg.setWindowTitle("Preview")
            msg.setText("No files selected for preview.")
            msg.setIconPixmap(self.get_accent_icon("info").pixmap(48, 48))
            msg.exec()
            return
        
        # Simple preview dialog showing the first few files
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("File Preview")
        preview_dialog.setMinimumSize(400, 500)
        
        layout = QVBoxLayout(preview_dialog)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Keep track of files being removed
        removed_indices = []
        
        # Function to remove a file
        def remove_file(index):
            removed_indices.append(index)
            file_frames[index].setVisible(False)
            update_count_label()
        
        # Update the count label based on remaining files
        def update_count_label():
            remaining = len(self.selected_files) - len(removed_indices)
            count_label.setText(f"Selected files: {remaining}")
        
        # Add file count
        count_label = QLabel(f"Selected files: {len(self.selected_files)}")
        count_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(count_label)
        
        file_frames = []
        
        # Add all file previews (not just 5)
        for i, file_path in enumerate(self.selected_files):
            file_frame = QFrame()
            file_frames.append(file_frame)
            file_frame.setFrameShape(QFrame.Shape.StyledPanel)
            file_layout = QHBoxLayout(file_frame)
            
            # File info
            file_name = os.path.basename(file_path)
            file_label = QLabel(file_name)
            file_label.setWordWrap(True)
            
            # Try to add a thumbnail for images
            if self.file_types[i] == "image":
                try:
                    img = Image.open(file_path)
                    img.thumbnail((80, 80))
                    qimage = self.pil_to_qimage(img)
                    pixmap = QPixmap.fromImage(qimage)
                    thumb = QLabel()
                    thumb.setPixmap(pixmap)
                    thumb.setFixedSize(80, 80)
                    file_layout.addWidget(thumb)
                except:
                    pass
            
            file_layout.addWidget(file_label, 1)
            
            # Add remove button
            remove_btn = QPushButton("❌")
            remove_btn.setToolTip("Remove from selection")
            remove_btn.setFixedWidth(30)
            remove_btn.clicked.connect(lambda checked, idx=i: remove_file(idx))
            file_layout.addWidget(remove_btn)
            
            scroll_layout.addWidget(file_frame)
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        # Buttons at bottom
        button_layout = QHBoxLayout()
        
        apply_button = StyledButton("Apply Changes", self.theme["accent"])
        apply_button.clicked.connect(lambda: apply_changes())
        button_layout.addWidget(apply_button)
        
        cancel_button = StyledButton("Cancel", self.theme["accent"])
        cancel_button.clicked.connect(preview_dialog.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        def apply_changes():
            # Remove files in reverse order to avoid index shifting
            for index in sorted(removed_indices, reverse=True):
                if 0 <= index < len(self.selected_files):
                    del self.selected_files[index]
                    del self.file_types[index]
            
            # Update file count
            self.file_count = len(self.selected_files)
            
            # Update file display
            if self.file_count > 0:
                self.file_path_input.setText(";".join(self.selected_files))
                self.files_label.setText(f"Found {self.file_count} convertible {self.mode.lower()}{'s' if self.file_count != 1 else ''}")
                self.statusBar().showMessage(f"Ready to convert {self.file_count} {self.mode.lower()}{'s' if self.file_count != 1 else ''}")
            else:
                self.file_path_input.clear()
                self.files_label.setText("No files selected")
                self.statusBar().showMessage("Ready")
            
            preview_dialog.accept()
        
        # Show the dialog
        preview_dialog.exec()
    
    def update_quality_label(self, value):
        self.quality_value.setText(f"{value}%")

    def set_mode(self, mode):
        self.mode = mode
        
        if mode == "Image":
            self.image_button.setChecked(True)
            self.video_button.setChecked(False)
            self.format_combo.clear()
            self.format_combo.addItems(SUPPORTED_FORMATS)
            self.format_combo.setCurrentText("webp")
            self.quality_container.setVisible(True)  # Show the container instead of the layout
            self.time_crop_group.setVisible(False)
        else:  # Video
            self.image_button.setChecked(False)
            self.video_button.setChecked(True)
            self.format_combo.clear()
            self.format_combo.addItems(SUPPORTED_VIDEO_FORMATS)
            self.format_combo.setCurrentText("mp4")
            self.quality_container.setVisible(False)  # Hide the container instead of the layout
            self.time_crop_group.setVisible(True)

        # Clear selected files when mode changes
        self.selected_files = []
        self.file_types = []
        self.file_count = 0
        self.file_path_input.clear()
        self.files_label.setText("No files selected")

    def toggle_theme(self):
        if self.theme == DARK_THEME:
            self.theme = LIGHT_THEME
            self.save_theme("light")
            self.theme_button.setText("☀️")
        else:
            self.theme = DARK_THEME
            self.save_theme("dark")
            self.theme_button.setText("🌙")
        
        self.apply_theme()

    def apply_theme(self):
        th = self.theme
        
        # App-wide palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(th["bg"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(th["fg"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(th["card_bg"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(th["fg"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(th["bg"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(th["fg"]))
        self.setPalette(palette)


         # Update label colors for theme
        if hasattr(self, "header_label"):
            self.header_label.setStyleSheet(
                f"font-size: 16px; font-weight: bold; color: {th['fg']};"
            )
        if hasattr(self, "source_header"):
            self.source_header.setStyleSheet(
                f"font-weight: bold; color: {th['fg']};"
            )
        
        if hasattr(self, "file_type_label"):
            self.file_type_label.setStyleSheet(
                f"font-weight: bold; color: {th['fg']};"
            )

        if hasattr(self, "tools_label"):
            self.tools_label.setStyleSheet(
                f"font-size: 16px; font-weight: bold; color: {th['fg']};"
            )

        
        # Buttons with accent color
        accent_style = f"""
            QPushButton {{
                background-color: {th["accent"]};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {th["accent_hover"]};
            }}
            QPushButton:checked {{
                background-color: {th["accent"]};
                color: white;
            }}
            QPushButton:!checked {{
                background-color: {th["card_bg"]};
                color: {th["fg"]};
            }}
        """
        
        # Update styled components
        self.convert_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {th["accent"]};
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {th["accent_hover"]};
            }}
        """)
        
        # Mode buttons
        self.image_button.setStyleSheet(accent_style)
        self.video_button.setStyleSheet(accent_style)
        
        # Input fields
        input_style = f"""
            QLineEdit, QComboBox, QSpinBox {{
                background-color: {th["entry_bg"]};
                color: {th["fg"]};
                border: 1px solid {th["border"]};
                padding: 6px;
                border-radius: 4px;
            }}
        """
        self.file_path_input.setStyleSheet(input_style)
        self.format_combo.setStyleSheet(input_style)
        self.width_input.setStyleSheet(input_style)
        self.height_input.setStyleSheet(input_style)
        
        # Card frames
        frame_style = f"""
            QFrame {{
                background-color: {th["card_bg"]};
                border: 1px solid {th["border"]};
                border-radius: 8px;
            }}
        """
        
        # Slider
        self.quality_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {th["border"]};
                height: 8px;
                background: {th["entry_bg"]};
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {th["accent"]};
                border: 1px solid {th["accent"]};
                width: 18px;
                height: 18px;
                margin: -8px 0;
                border-radius: 9px;
            }}
        """)
        
        # Progress bar
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {th["border"]};
                border-radius: 5px;
                text-align: center;
                background-color: {th["entry_bg"]};
            }}
            QProgressBar::chunk {{
                background-color: {th["accent"]};
                border-radius: 5px;
            }}
        """)
        
        # Image edit preview area
        self.edit_image_label.setStyleSheet(f"""
            QLabel {{
                background-color: {th["card_bg"]};
                border-radius: 8px;
                padding: 10px;
                color: {th["fg"]};
            }}
        """)
    
    def show_privacy(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Privacy Policy")  
        msg.setText("Privacy Policy\n\n"
            "• This application does NOT collect, store, or transmit any personal data.\n"
            "• All image and video processing is performed locally on your device.\n"
            "• No files are uploaded to any server or shared with third parties.\n"
            "• The app does not use cookies, analytics, or tracking technologies.\n"
            "• Your usage and converted files remain private and secure.\n\n"
            "If you have any privacy concerns or questions, please contact:\n"
            "basharulalam6@gmail.com")
        msg.setIconPixmap(self.get_accent_icon("info").pixmap(48, 48))
        msg.exec()
    
    def show_documentation(self):
        # Create a custom dialog
        doc_dialog = QDialog(self)
        doc_dialog.setWindowTitle("Documentation")
        doc_dialog.setMinimumSize(500, 400)  # Set a reasonable size
        
        # Main layout for the dialog
        layout = QVBoxLayout(doc_dialog)
        
        # Title label
        title_label = QLabel("🖼️ Editara Documentation")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme['fg']}; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Scroll area for documentation text
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Documentation text
        doc_text = QLabel(
                    "Features:\n"
                    "• Image Conversion: Convert between JPG, PNG, BMP, TIFF, WEBP, HEIC formats.\n"
                    "• Video Conversion: Convert between MP4, AVI, MOV, MKV, WEBM formats.\n"
                    "• Batch Processing: Convert multiple files at once.\n"
                    "• Resize Options: Resize images or videos by width, height, or both.\n"
                    "• Image Quality Adjustment: Set quality for image conversions.\n"
                    "• Video Time Cropping: Specify start and end times for video conversions.\n"
                    "• Image Editing Tools:\n"
                    "  - Create passport size images (413x531 pixels).\n"
                    "  - Remove background from images using GrabCut.\n"
                    "  - Crop images with interactive selection.\n"
                    "  - Improve image quality using super-resolution (requires LapSRN_x2.pb model).\n"
                    "• Theme Toggle: Switch between dark and light themes.\n"
                    "• Drag & Drop: Easily add files or folders.\n"
                    "• File Preview: Preview selected files before conversion.\n"
                    "• Update Checker: Check for the latest version via Settings menu.\n\n"
                    "How to Use:\n\n"
                    "1. Conversion:\n"
                    "   a. Select the file type (Image or Video) using the mode buttons.\n"
                    "   b. Add files using the Browse button or by dragging and dropping them into the app.\n"
                    "   c. Choose the output format from the dropdown menu.\n"
                    "   d. Adjust settings:\n"
                    "      - For images: Set quality (10-100%) using the slider.\n"
                    "      - For videos: Set start/end times in the Video Time Range section.\n"
                    "      - Enable resizing and specify width/height if desired.\n"
                    "   e. Click 'Convert' to start the process.\n"
                    "   f. Monitor progress via the progress bar.\n\n"
                    "2. Image Editing:\n"
                    "   a. Switch to the 'Image Edit' tab.\n"
                    "   b. Click 'Upload Image' to select an image.\n"
                    "   c. Use the tools:\n"
                    "      - 'Passport Size': Resize to standard passport dimensions.\n"
                    "      - 'Remove Background': Automatically remove the image background.\n"
                    "      - 'Crop Image': Select and crop a region interactively.\n"
                    "      - 'Improve Quality': Enhance resolution (model file required).\n"
                    "   d. Save the edited image when prompted.\n\n"
                    "Other Information:\n"
                    "• Converted files are saved in a 'Converted_to_[format]' folder next to your originals.\n"
                    "• All processing is local; no data is collected or shared.\n"
                    "• Check the current version in the About section.\n"
                    "• For support, contact the developer via the About section.\n\n"
                    "Requirements:\n"
                    "• Video conversion is built-in to the EXE version (no extra install needed).\n"
                    "• Quality improvement requires the 'LapSRN_x2.pb' model file in the app directory."
                )





        doc_text.setStyleSheet(f"color: {self.theme['fg']}; padding: 10px;")
        doc_text.setWordWrap(True)
        scroll_layout.addWidget(doc_text)
        scroll_area.setWidget(scroll_content)
        
        # Style the scroll area
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.theme['card_bg']};
                border: 1px solid {self.theme['border']};
                border-radius: 8px;
            }}
            QScrollBar:vertical {{
                border: none;
                background: {self.theme['entry_bg']};
                width: 10px;
                margin: 0px 0px 0px 0px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.theme['accent']};
                border-radius: 5px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
        """)
        
        layout.addWidget(scroll_area)
        
        # Close button
        close_button = StyledButton("Close", self.theme["accent"])
        close_button.clicked.connect(doc_dialog.accept)
        layout.addWidget(close_button)
        
        # Add icon to the dialog
        doc_dialog.setWindowIcon(self.get_accent_icon("info"))
        
        # Show the dialog
        doc_dialog.exec()


    
    def show_policy(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Privacy Policy")  # or "Documentation", etc.
        msg.setText("Usage Policy:\n\n"
            "• This application is provided for personal and internal use only.\n"
            "• Redistribution, modification, or commercial use is strictly prohibited without written permission from the developer.\n"
            "• All conversions are performed locally; no files are uploaded or shared.\n"
            "• By using this app, you agree to the terms described in the LICENSE file.\n"
            "\n"
            "For permissions or questions, contact: basharulalammazu6@gmail.com")
        msg.setIconPixmap(self.get_accent_icon("info").pixmap(48, 48))
        msg.exec()
    
    
    def show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Help")
        msg.setText(
            "How to use Editara:\n\n"
            "1. Converter Tab:\n"
            "   - Select 'Image' or 'Video' mode.\n"
            "   - Add files via Browse or drag-and-drop.\n"
            "   - Set output format and settings (quality, resize, etc.).\n"
            "   - Click 'Convert' to process.\n"
            "2. Image Edit Tab:\n"
            "   - Upload an image and use tools like passport size, background removal, crop, or quality enhancement.\n"
            "   - Save your edits.\n\n"
            "For detailed instructions, see the Documentation section."
        )
        msg.setIconPixmap(self.get_accent_icon("info").pixmap(48, 48))
        msg.exec()


    def show_about(self):
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("About Developer")
        about_dialog.setFixedSize(400, 250)
        
        layout = QVBoxLayout(about_dialog)
        
        title_label = QLabel("🧑‍💻 Developer Information")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        layout.addWidget(title_label)
        
        info_layout = QGridLayout()
        
        info_layout.addWidget(QLabel("Name:"), 0, 0)
        info_layout.addWidget(QLabel("Basharul - Alam - Mazu"), 0, 1)
        
        info_layout.addWidget(QLabel("GitHub:"), 1, 0)
        github_link = QLabel("<a href='https://github.com/basharulalammazu'>basharulalammazu</a>")
        github_link.setOpenExternalLinks(True)
        info_layout.addWidget(github_link, 1, 1)
        
        info_layout.addWidget(QLabel("Website:"), 2, 0)
        website_link = QLabel("<a href='https://basharulalammazu.github.io'>basharulalammazu.github.io</a>")
        website_link.setOpenExternalLinks(True)
        info_layout.addWidget(website_link, 2, 1)
        
        info_layout.addWidget(QLabel("Email:"), 3, 0)
        email_link = QLabel("<a href='mailto:basharulalammazu6@gmail.com'>basharulalammazu6@gmail.com</a>")
        email_link.setOpenExternalLinks(True)
        info_layout.addWidget(email_link, 3, 1)
        
        layout.addLayout(info_layout)
        layout.addStretch(1)
        
        close_button = StyledButton("Close", self.theme["accent"])
        close_button.clicked.connect(about_dialog.accept)
        layout.addWidget(close_button)
        
        about_dialog.exec()

    def start_conversion(self):
        if self.is_converting:
            return
        
        # Check if files are selected
        if not self.selected_files:
            msg = QMessageBox(self)
            msg.setWindowTitle("No Files")
            msg.setText(f"No {self.mode.lower()}s selected for conversion.")
            msg.setIconPixmap(self.get_accent_icon("warning").pixmap(48, 48))
            msg.exec()
            return
        
        # Get output format
        output_format = self.format_combo.currentText()
        
        # Get quality setting for images
        quality = self.quality_slider.value() if self.mode == "Image" else None
        
        # Check resize settings
        resize_enabled = self.resize_group.isChecked()
        
        # Start conversion
        self.is_converting = True
        self.progress_bar.setValue(0)
        self.convert_button.setEnabled(False)
        self.statusBar().showMessage(f"Converting {self.mode.lower()}s...")
        
        # Start conversion in a worker thread
        if self.mode == "Image":
            self.conversion_worker = Worker(
                self.convert_images,
                (self.selected_files, output_format, quality, resize_enabled)
            )
        else:
            self.conversion_worker = Worker(
                self.convert_videos,
                (self.selected_files, output_format, resize_enabled)
            )
        
        self.conversion_worker.progress.connect(self.update_progress)
        self.conversion_worker.finished.connect(self.conversion_complete)
        self.conversion_worker.error.connect(self.conversion_error)
        self.conversion_worker.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def conversion_complete(self, result_tuple):
        # Unpack the result tuple correctly
        result = result_tuple[0]  # Extract first (and only) element from outer tuple
        
        # Now unpack the inner tuple containing converted and skipped counts
        converted, skipped = result
        
        self.is_converting = False
        self.convert_button.setEnabled(True)
        self.progress_bar.setValue(100)
        self.statusBar().showMessage(f"Completed: {converted} converted, {skipped} skipped")
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Conversion Complete")
        msg.setText(
            f"✅ Converted: {converted}\n"
            f"⏭️ Skipped: {skipped}\n\n"
            f"Saved to: {self.output_folder}"
        )
        msg.setIconPixmap(self.get_accent_icon("info").pixmap(48, 48))
        msg.exec()
    
    def conversion_error(self, error_msg):
        self.is_converting = False
        self.convert_button.setEnabled(True)
        self.statusBar().showMessage("Error during conversion")
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Conversion Error")
        msg.setText(f"An error occurred during conversion:\n{error_msg}")
        msg.setIconPixmap(self.get_accent_icon("error").pixmap(48, 48))
        msg.exec()

    def convert_images(self, files, target_format, quality, resize_enabled):
        target_ext = f".{target_format.lower()}"
        
        # Create output folder
        if os.path.isdir(files[0]):
            output_folder = os.path.join(files[0], f"Converted_to_{target_format}")
        else:
            output_folder = os.path.join(os.path.dirname(files[0]), f"Converted_to_{target_format}")
        
        os.makedirs(output_folder, exist_ok=True)
        self.output_folder = output_folder
        
        converted = 0
        skipped = 0
        total_files = len(files)
        
        for idx, file_path in enumerate(files):
            try:
                # Update progress
                progress = int(((idx + 0.5) / total_files) * 100)
                self.conversion_worker.progress.emit(progress)
                
                # Skip if same format
                filename = os.path.basename(file_path)
                base_name, ext = os.path.splitext(filename)
                if ext.lower() == target_ext:
                    skipped += 1
                    continue
                
                # Open and convert image
                with Image.open(file_path) as img:
                    # Apply resize if enabled
                    if resize_enabled:
                        original_w, original_h = img.size
                        
                        # Get new dimensions based on selected resize mode
                        if self.resize_width_radio.isChecked():
                            new_width = self.width_input.value()
                            new_height = int(original_h * (new_width / original_w))
                        elif self.resize_height_radio.isChecked():
                            new_height = self.height_input.value()
                            new_width = int(original_w * (new_height / original_h))
                        else:  # Both width and height
                            new_width = self.width_input.value()
                            new_height = self.height_input.value()
                        
                        img = img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # Handle mode conversion if needed
                    if img.mode in ("RGBA", "P") and target_format.lower() in ['jpg', 'jpeg']:
                        img = img.convert("RGB")
                    
                    # Save with appropriate quality settings
                    target_path = os.path.join(output_folder, f"{base_name}{target_ext}")
                    save_args = {}
                    
                    if target_format.lower() in ['jpg', 'jpeg', 'webp']:
                        save_args['quality'] = quality
                    elif target_format.lower() == 'png':
                        # PNG uses compression level (0-9) instead of quality
                        # Convert quality (10-100) to compression (9-0)
                        compression = min(9, max(0, int(9 - (quality / 10))))
                        save_args['compress_level'] = compression
                    
                    img.save(target_path, **save_args)
                    converted += 1
                    
            except Exception as e:
                print(f"Error converting {file_path}: {e}")
                skipped += 1
            
            # Update progress
            progress = int(((idx + 1) / total_files) * 100)
            self.conversion_worker.progress.emit(progress)
        
        return converted, skipped

    def convert_videos(self, files, target_format, resize_enabled):
        if not MOVIEPY_AVAILABLE:
            raise Exception("moviepy is not installed. Please run: pip install moviepy")
        
        target_ext = f".{target_format.lower()}"
        
        # Create output folder
        if os.path.isdir(files[0]):
            output_folder = os.path.join(files[0], f"Converted_to_{target_format}")
        else:
            output_folder = os.path.join(os.path.dirname(files[0]), f"Converted_to_{target_format}")
        
        os.makedirs(output_folder, exist_ok=True)
        self.output_folder = output_folder
        
        converted = 0
        skipped = 0
        total_files = len(files)
        
        # Get time crop settings
        start_time = self.start_time.value() if self.start_time.value() > 0 else None
        end_time = self.end_time.value() if self.end_time.value() > 0 else None
        
        for idx, file_path in enumerate(files):
            try:
                # Update progress
                progress = int(((idx + 0.5) / total_files) * 100)
                self.conversion_worker.progress.emit(progress)
                
                # Skip if same format
                filename = os.path.basename(file_path)
                base_name, ext = os.path.splitext(filename)
                if ext.lower() == target_ext:
                    skipped += 1
                    continue
                
                # Process video
                clip = VideoFileClip(file_path)
                
                # Apply time crop if enabled
                if start_time is not None or end_time is not None:
                    clip = clip.subclip(
                        start_time if start_time is not None else 0, 
                        end_time if end_time is not None else clip.duration
                    )
                
                # Apply resize if enabled
                if resize_enabled:
                    from moviepy.video.fx import resize as mp_resize
                    if self.resize_width_radio.isChecked():
                        new_width = self.width_input.value()
                        clip = mp_resize(clip, width=new_width)
                    elif self.resize_height_radio.isChecked():
                        new_height = self.height_input.value()
                        clip = mp_resize(clip, height=new_height)
                    else:  # Both width and height
                        new_width = self.width_input.value()
                        new_height = self.height_input.value()
                        clip = mp_resize(clip, newsize=(new_width, new_height))
                
                # Set output path
                output_path = os.path.join(output_folder, f"{base_name}{target_ext}")
                
                # Set codec based on format
                if target_format.lower() in ['mp4', 'mkv']:
                    codec = 'libx264'
                    audio_codec = 'aac'
                elif target_format.lower() == 'webm':
                    codec = 'libvpx'
                    audio_codec = 'libvorbis'
                else:
                    codec = None
                    audio_codec = None
                
                # Write video file
                clip.write_videofile(output_path, codec=codec, audio_codec=audio_codec)
                clip.close()
                
                converted += 1
                
            except Exception as e:
                print(f"Error converting {file_path}: {e}")
                skipped += 1
            
            # Update progress
            progress = int(((idx + 1) / total_files) * 100)
            self.conversion_worker.progress.emit(progress)
        
        return converted, skipped

# Main application entry point
def main():
    # Create the QApplication instance
    app = QApplication(sys.argv)

    # --- Splash Screen with logo.png ---
    logo_path = resource_path("logo.png")
    if os.path.exists(logo_path):
        splash_pix = QPixmap(logo_path)
        if not splash_pix.isNull():
            splash = QSplashScreen(
                splash_pix.scaled(256, 256, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
            splash.show()
            app.processEvents()
        else:
            splash = None
    else:
        splash = None

    # Delay for 2 seconds, then show main window
    def show_main():
        window = Editara()
        window.show()
        if splash:
            splash.finish(window)

    QTimer.singleShot(2000, show_main)  # 2000 ms = 2 seconds

    sys.exit(app.exec())

if __name__ == "__main__":
    main()