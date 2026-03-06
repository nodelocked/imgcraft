import sys
import os

# Ensure the 'app' directory is in sys.path for bundled execution
basedir = os.path.dirname(__file__)
if basedir not in sys.path:
    sys.path.append(basedir)

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QPlainTextEdit, 
                             QLineEdit, QFileDialog, QFrame, QScrollArea, QMessageBox)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent, QKeyEvent

# Standard absolute imports for PyInstaller compatibility
from logic import Manager

class ImgCraftApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.manager = Manager()
        self.setWindowTitle("ImgCraft Ultimate Pro")
        self.resize(1400, 900)
        self.setAcceptDrops(True)
        
        self.current_filter_tag = None
        self.current_view_mode = "all" 
        
        # Load Styles
        style_path = os.path.join(os.path.dirname(__file__), "styles.css")
        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())

        self.init_ui()
        self.refresh_sidebar()
        self.load_all_photos()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 10)
        sidebar_layout.setSpacing(0)

        sidebar_layout.addWidget(QLabel("COLLECTIONS", objectName="sidebar_title"))
        
        self.all_btn = QPushButton("All Photos")
        self.all_btn.setObjectName("nav_item")
        self.all_btn.clicked.connect(self.load_all_photos)
        sidebar_layout.addWidget(self.all_btn)

        self.untouched_btn = QPushButton("Untouched Photos (No Tags/Notes)")
        self.untouched_btn.setObjectName("nav_item")
        self.untouched_btn.clicked.connect(self.load_untouched_photos)
        sidebar_layout.addWidget(self.untouched_btn)

        sidebar_layout.addWidget(QLabel("FOLDERS", objectName="sidebar_title"))
        self.folder_scroll = QScrollArea()
        self.folder_scroll.setWidgetResizable(True)
        self.folder_scroll.setFrameShape(QFrame.NoFrame)
        self.folder_container = QWidget()
        self.folder_layout = QVBoxLayout(self.folder_container)
        self.folder_layout.setContentsMargins(0, 0, 0, 0)
        self.folder_layout.setAlignment(Qt.AlignTop)
        self.folder_scroll.setWidget(self.folder_container)
        sidebar_layout.addWidget(self.folder_scroll, 1)

        # Bottom Actions
        sidebar_layout.addStretch()
        
        self.export_pdf_btn = QPushButton("Export Inspiration PDF")
        self.export_pdf_btn.setObjectName("nav_item")
        self.export_pdf_btn.clicked.connect(self.export_pdf_workflow)
        sidebar_layout.addWidget(self.export_pdf_btn)

        self.export_bundle_btn = QPushButton("Export Data Bundle (JSON)")
        self.export_bundle_btn.setObjectName("nav_item")
        self.export_bundle_btn.clicked.connect(self.export_bundle_workflow)
        sidebar_layout.addWidget(self.export_bundle_btn)

        self.reset_btn = QPushButton("Reset Database")
        self.reset_btn.setObjectName("nav_item")
        self.reset_btn.clicked.connect(self.confirm_reset)
        sidebar_layout.addWidget(self.reset_btn)

        main_layout.addWidget(self.sidebar)

        # --- Viewer + Advanced Header ---
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 8, 15, 8)
        header_layout.setSpacing(10)

        self.prev_btn = QPushButton("F1 / ←")
        self.prev_btn.setObjectName("main_nav_btn")
        self.prev_btn.clicked.connect(self.show_prev)
        header_layout.addWidget(self.prev_btn)
        
        self.counter_label = QLabel("0 / 0", objectName="counter")
        header_layout.addStretch()
        header_layout.addWidget(self.counter_label)
        header_layout.addStretch()

        self.jump_input = QLineEdit()
        self.jump_input.setPlaceholderText("Go to...")
        self.jump_input.setObjectName("jump_input")
        self.jump_input.returnPressed.connect(self.jump_to_index)
        header_layout.addWidget(self.jump_input)

        self.first_btn = QPushButton("First")
        self.first_btn.setObjectName("nav_item")
        self.first_btn.setFixedWidth(60)
        self.first_btn.clicked.connect(self.show_first)
        header_layout.addWidget(self.first_btn)

        self.last_btn = QPushButton("Last")
        self.last_btn.setObjectName("nav_item")
        self.last_btn.setFixedWidth(60)
        self.last_btn.clicked.connect(self.show_last)
        header_layout.addWidget(self.last_btn)

        self.next_btn = QPushButton("F2 / →")
        self.next_btn.setObjectName("main_nav_btn")
        self.next_btn.clicked.connect(self.show_next)
        header_layout.addWidget(self.next_btn)
        
        content_layout.addWidget(header)

        # Image Viewer
        self.viewer_bg = QFrame()
        self.viewer_bg.setObjectName("viewer_bg")
        viewer_layout = QVBoxLayout(self.viewer_bg)
        self.image_display = QLabel("No Image Loads")
        self.image_display.setObjectName("main_image")
        self.image_display.setAlignment(Qt.AlignCenter)
        viewer_layout.addWidget(self.image_display)
        content_layout.addWidget(self.viewer_bg, 1)

        main_layout.addWidget(content_area, 3)

        # --- Right: Properties ---
        self.right_panel = QFrame()
        self.right_panel.setObjectName("prop_panel")
        prop_layout = QVBoxLayout(self.right_panel)

        prop_layout.addWidget(QLabel("INSPIRATION", objectName="panel_label"))
        self.inspiration_input = QPlainTextEdit()
        self.inspiration_input.setPlaceholderText("Write ideas...")
        self.inspiration_input.textChanged.connect(self.save_inspiration)
        prop_layout.addWidget(self.inspiration_input, 1)

        prop_layout.addSpacing(20)
        prop_layout.addWidget(QLabel("TAGS", objectName="panel_label"))
        self.tag_entry = QLineEdit()
        self.tag_entry.setPlaceholderText("New tag...")
        self.tag_entry.returnPressed.connect(self.add_tag)
        prop_layout.addWidget(self.tag_entry)
        
        self.tags_container = QWidget()
        self.tags_layout = QHBoxLayout(self.tags_container)
        self.tags_layout.setAlignment(Qt.AlignLeft)
        prop_layout.addWidget(self.tags_container)

        prop_layout.addSpacing(20)
        prop_layout.addWidget(QLabel("FILTERS", objectName="panel_label"))
        self.tag_cloud_area = QScrollArea()
        self.tag_cloud_area.setWidgetResizable(True)
        self.tag_cloud_area.setFrameShape(QFrame.NoFrame)
        self.tag_cloud_widget = QWidget()
        self.tag_cloud_layout = QVBoxLayout(self.tag_cloud_widget)
        self.tag_cloud_layout.setAlignment(Qt.AlignTop)
        self.tag_cloud_area.setWidget(self.tag_cloud_widget)
        prop_layout.addWidget(self.tag_cloud_area, 2)

        prop_layout.addSpacing(10)
        self.archive_btn = QPushButton("Archive Filter Output")
        self.archive_btn.setObjectName("archive_btn")
        self.archive_btn.clicked.connect(self.archive_workflow)
        prop_layout.addWidget(self.archive_btn)
        
        prop_layout.addWidget(QLabel("HOTKEYS: F1/← (Prev) | F2/→ (Next) | DEL (Delete File)", objectName="shortcut_hint"))

        main_layout.addWidget(self.right_panel)

    # --- Navigation & Hotkeys ---
    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        
        # F1 and F2 are SAFE to be global always (no text editing conflict)
        if key == Qt.Key_F1:
            self.show_prev()
            event.accept()
            return
        elif key == Qt.Key_F2:
            self.show_next()
            event.accept()
            return
            
        # Arrows and Delete are only global if NOT in text focus
        # This prevents breaking text editing (cursor movement/backspace)
        if not (self.inspiration_input.hasFocus() or self.tag_entry.hasFocus() or self.jump_input.hasFocus()):
            if key == Qt.Key_Left:
                self.show_prev()
                event.accept()
                return
            elif key == Qt.Key_Right:
                self.show_next()
                event.accept()
                return
            elif key == Qt.Key_Delete:
                self.delete_permanently()
                event.accept()
                return
        
        super().keyPressEvent(event)

    def delete_permanently(self):
        # Silent delete as per user request
        if self.manager.delete_current_image():
            self.display_current()

    # --- Actions ---
    def display_current(self):
        data = self.manager.get_current_image()
        total = len(self.manager.current_images)
        current = self.manager.current_index + 1 if total > 0 else 0
        
        self.counter_label.setText(f"{current} / {total}")
        
        if data:
            pixmap = QPixmap(data["path"])
            if not pixmap.isNull():
                scaled = pixmap.scaled(self.image_display.size() - QSize(40, 40), 
                                     Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_display.setPixmap(scaled)
            else:
                self.image_display.setText("Load error")
            
            self.inspiration_input.blockSignals(True)
            self.inspiration_input.setPlainText(data["inspiration"])
            self.inspiration_input.blockSignals(False)
            
            # Tags
            for i in reversed(range(self.tags_layout.count())):
                self.tags_layout.itemAt(i).widget().setParent(None)
            for tag in data["tags"]:
                lbl = QLabel(tag)
                lbl.setObjectName("tag_chip")
                self.tags_layout.addWidget(lbl)
        else:
            self.image_display.setPixmap(QPixmap())
            self.image_display.setText("Drop Folders to Start")

    def show_next(self):
        self.manager.next_image()
        self.manager.update_position()
        self.display_current()

    def show_prev(self):
        self.manager.prev_image()
        self.manager.update_position()
        self.display_current()

    def show_first(self):
        self.manager.jump_to(0)
        self.display_current()

    def show_last(self):
        self.manager.jump_to(len(self.manager.current_images) - 1)
        self.display_current()

    def jump_to_index(self):
        try:
            val = int(self.jump_input.text()) - 1
            if self.manager.jump_to(val):
                self.display_current()
                self.jump_input.clear()
                self.jump_input.clearFocus()
        except ValueError:
            pass

    # --- Data & Settings ---
    def load_all_photos(self):
        self.current_filter_tag = None
        self.manager.get_all_images()
        self.display_current()
        self.update_tag_cloud()
        self.refresh_sidebar()

    def load_untouched_photos(self):
        self.current_filter_tag = "Untouched"
        self.manager.filter_untouched()
        self.display_current()
        self.update_tag_cloud()
        self.refresh_sidebar()

    def load_folder(self, path):
        self.manager.load_folder(path)
        self.current_filter_tag = None
        self.display_current()
        self.update_tag_cloud()

    def refresh_sidebar(self):
        for i in reversed(range(self.folder_layout.count())):
            self.folder_layout.itemAt(i).widget().setParent(None)
        
        for name, path, _ in self.manager.get_folders():
            btn = QPushButton(name)
            btn.setObjectName("nav_item")
            btn.clicked.connect(lambda chk=False, p=path: self.load_folder(p))
            self.folder_layout.addWidget(btn)

    def update_tag_cloud(self):
        for i in reversed(range(self.tag_cloud_layout.count())):
            self.tag_cloud_layout.itemAt(i).widget().setParent(None)
        
        if self.current_filter_tag:
            btn = QPushButton(f"✕ CLEAR FILTER: {self.current_filter_tag}")
            btn.setObjectName("tag_chip_active")
            btn.clicked.connect(self.load_all_photos)
            self.tag_cloud_layout.addWidget(btn)

        for tag in self.manager.get_all_tags():
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)
            
            # Left: APPLY Tag
            apply_btn = QPushButton(f"+ {tag}")
            apply_btn.setObjectName("tag_chip")
            apply_btn.setToolTip(f"Apply '{tag}' to current photo")
            apply_btn.clicked.connect(lambda chk=False, t=tag: self.apply_tag_to_current(t))
            
            # Right: FILTER Tag
            filter_btn = QPushButton("🔍")
            filter_btn.setObjectName("tag_chip")
            filter_btn.setFixedWidth(40)
            filter_btn.setToolTip(f"Filter library by '{tag}'")
            filter_btn.clicked.connect(lambda chk=False, t=tag: self.filter_tag(t))
            
            layout.addWidget(apply_btn, 1)
            layout.addWidget(filter_btn)
            self.tag_cloud_layout.addWidget(container)

    def apply_tag_to_current(self, tag):
        data = self.manager.get_current_image()
        if data:
            self.manager.add_tag(data["id"], tag)
            self.display_current()

    def filter_tag(self, tag):
        self.current_filter_tag = tag
        self.manager.filter_by_tag(tag)
        self.display_current()
        self.update_tag_cloud()

    def confirm_reset(self):
        reply = QMessageBox.question(self, "Reset Database", 
                                   "This will clear ALL folders, tags, and notes. Continue?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.manager.reset_all()
            self.load_all_photos()
            self.refresh_sidebar()

    def export_pdf_workflow(self):
        dest, _ = QFileDialog.getSaveFileName(self, "Save Inspiration PDF", "", "PDF Files (*.pdf)")
        if dest:
            if self.manager.export_to_pdf(dest):
                QMessageBox.information(self, "Export Successful", f"PDF exported to:\n{dest}")
            else:
                QMessageBox.warning(self, "Export Error", "Failed to generate PDF. Make sure you have photos with inspiration notes.")

    def export_bundle_workflow(self):
        dest = QFileDialog.getExistingDirectory(self, "Select Folder for Data Bundle")
        if dest:
            count = self.manager.export_inspiration_bundle(dest)
            if count > 0:
                QMessageBox.information(self, "Export Successful", 
                                       f"Successfully exported {count} images and metadata.json to:\n{dest}")
            else:
                QMessageBox.warning(self, "Export Empty", "No photos with inspirations found to export.")

    def archive_workflow(self):
        if not self.current_filter_tag:
            QMessageBox.warning(self, "Archive Error", "Select a Tag filter first to archive those files.")
            return
            
        target = QFileDialog.getExistingDirectory(self, "Select Archive Directory")
        if target:
            count = self.manager.archive_by_tag(self.current_filter_tag, target)
            QMessageBox.information(self, "Archive Complete", f"Successfully archived {count} images to:\n{target}")

    def save_inspiration(self):
        data = self.manager.get_current_image()
        if data:
            self.manager.save_inspiration(data["id"], self.inspiration_input.toPlainText())

    def add_tag(self):
        tag = self.tag_entry.text().strip()
        data = self.manager.get_current_image()
        if tag and data:
            self.manager.add_tag(data["id"], tag)
            self.tag_entry.clear()
            self.display_current()
            self.update_tag_cloud()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): e.accept()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.isdir(path):
                self.manager.scan_folder(path)
                self.load_folder(path)
                self.refresh_sidebar()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.display_current()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    window = ImgCraftApp()
    window.show()
    sys.exit(app.exec())
