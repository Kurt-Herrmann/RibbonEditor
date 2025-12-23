import json
import os
import sys
from datetime import datetime

from PyQt6.QtCore import QUrl, Qt, QPoint, QMarginsF, QSizeF
from PyQt6.QtGui import QPainter, QKeySequence, QAction, QTransform, QPdfWriter, QPageSize, QPageLayout, QFont
from PyQt6.QtWidgets import (QApplication, QGraphicsScene, QMainWindow, QGraphicsView,
                             QDialog, QMessageBox, QSizePolicy, QFileDialog, QVBoxLayout)

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView

    WEBENGINE_AVAILABLE = True
except ImportError:
    from PyQt6.QtWidgets import QTextBrowser

    WEBENGINE_AVAILABLE = False

from ribbon import *
from ribbon_dialog import Ui_Dialog


class ZoomableGraphicsView(QGraphicsView):
    """QGraphicsView with mouse wheel zoom functionality."""

    # Zoom constraints
    MIN_ZOOM = 0.25
    MAX_ZOOM = 4.0
    ZOOM_INCREMENT = 1.1  # 10% per wheel click

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.zoom_factor = 1.0
        self.panning = False
        self.pan_start_pos = QPoint()

    def wheelEvent(self, event):
        """Handle mouse wheel for vertical scroll or zoom with Ctrl."""
        delta = event.angleDelta().y()
        if delta == 0:
            return

        # Check if Ctrl is pressed - if so, zoom instead of scrolling
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Get current cursor position in scene coordinates
            cursor_pos = event.position()
            scene_pos = self.mapToScene(cursor_pos.toPoint())

            # Determine zoom factor for this operation
            zoom_in = delta > 0
            new_zoom = self.zoom_factor * (self.ZOOM_INCREMENT if zoom_in else 1.0 / self.ZOOM_INCREMENT)

            # Enforce zoom limits
            new_zoom = max(self.MIN_ZOOM, min(new_zoom, self.MAX_ZOOM))

            # If zoom didn't change (hit limit), don't proceed
            if new_zoom == self.zoom_factor:
                event.accept()
                return

            # Apply transformation with zoom-to-cursor behavior
            scale_factor = new_zoom / self.zoom_factor
            self.zoom_factor = new_zoom

            # Create new transform with scaling
            transform = QTransform()
            transform.scale(self.zoom_factor, self.zoom_factor)
            self.setTransform(transform)

            # Center on the scene position to keep it under cursor
            self.centerOn(scene_pos)

            event.accept()
        else:
            # Scroll vertically when Ctrl is not pressed
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta
            )
            event.accept()

    def reset_zoom(self):
        """Reset zoom to 1:1 and restore default view."""
        self.resetTransform()
        self.zoom_factor = 1.0

    def mousePressEvent(self, event):
        """Handle mouse press for panning with middle button."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.panning = True
            self.pan_start_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for panning."""
        if self.panning:
            # Calculate the delta movement
            delta = event.pos() - self.pan_start_pos
            self.pan_start_pos = event.pos()

            # Update scrollbars to pan the view
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop panning."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene(self)
        self.view = ZoomableGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding,
                                QSizePolicy.Policy.Expanding)
        self.R = None
        self.file_path = None
        # self.window_w = 300
        # self.window_h = 800
        self.window_edge = 25

        self.setCentralWidget(self.view)
        self.setWindowTitle("Ribbon Editor")

        # only for debug *******************************************************
        # width = 5
        # length = 15
        # type = "M"
        # # only for debug
        # # make sure that width is un even for types M and A
        # if width % 2 == 0 and (type == "M" or type == "A"):
        #     width = width - 1
        #     QMessageBox.warning(None, "Warning", "For width in ribbon types \"M\" and \"A\" "
        #                                          "no even numbers are \nallowed ! "
        #                                          "The next smaller odd number has been assigned.")
        # self.R = Ribbon(self.scene, width, length, type)
        #
        # All_Knot_Paramters = self.R.extract_KnPar()
        # All_Ribbon_Parameters = {
        #     "width": width,
        #     "length": length,
        #     "type": type,
        #     "all_knot_parameters": All_Knot_Paramters
        # }
        # self.window_w = int(self.R.cplW + 2 * self.window_edge)
        # self.window_h = int(self.R.cplL + 2 * self.window_edge)
        #
        # self.scene.setSceneRect(0, 0, self.R.cplW, self.R.cplL)
        # self.setGeometry(2400, -250, self.window_w, 800)
        # only for debug ***********************************************************

    def closeEvent(self, e):
        if not self.R.changed:
            return

        answer = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Save before closing?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
        )
        if answer == QMessageBox.StandardButton.Save:
            self.save_as()
            if self.R.changed:
                # This happens when the user closes the Save As... dialog.
                # We do not want to close the window in this case because it
                # would throw away unsaved changes.
                e.ignore()
        elif answer == QMessageBox.StandardButton.Cancel:
            e.ignore()
        return

    def new_file(self):
        # def new_file(self, checked=False):
        if self.R:  # is there already an active ribbon ?
            if self.R.changed:
                answer = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    "You have unsaved changes. Save before closing?",
                    QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
                )
                if answer == QMessageBox.StandardButton.Save:
                    self.save_as()
                    self.R.changed = False
            self.scene.clear()

        dialog = QDialog()
        ui = Ui_Dialog()
        ui.setupUi(dialog)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            type, width, length = ui.get_values()
            # print("TYPE:", type, "WIDTH:", width, "LENGTH:", length)

        # make sure that width is un even for types M and A
        if width % 2 == 0 and (type == "M" or type == "A"):
            width = width - 1
            QMessageBox.warning(None, "Warning", "For width in ribbon types \"M\" and \"A\" "
                                                 "no even numbers are \nallowed ! "
                                                 "The next smaller odd number has been assigned.")
        self.R = Ribbon(self.scene, width, length, type)

        All_Knot_Paramters = self.R.extract_KnPar()
        All_Ribbon_Parameters = {
            "width": width,
            "length": length,
            "type": type,
            "all_knot_parameters": All_Knot_Paramters
        }
        self.window_w = int(self.R.cplW + 2 * self.window_edge)
        self.window_h = int(self.R.cplL + 2 * self.window_edge)

        self.scene.setSceneRect(0, 0, self.R.cplW, self.R.cplL)
        self.setGeometry(2400, -250, self.window_w, 800)

    def open_file(self):
        """Open a ribbon pattern file"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Ribbon Pattern",
            "",
            "Ribbon Files (*.rbn);;All Files (*)"
        )
        if not path:
            return

        try:
            with open(path, "r") as f:
                data = json.load(f)

            # Extract ribbon parameters
            ribbon_data = data.get("ribbon", {})
            width = ribbon_data.get("width", 5)
            length = ribbon_data.get("length", 10)
            ribbon_type = ribbon_data.get("type", "L")
            saved_filename = data.get("filename", os.path.basename(path))

            # Create new ribbon with the saved dimensions
            self.R = Ribbon(self.scene, width, length, ribbon_type)

            # Restore saved state
            self.R.restore_from_dict(data)

            # Update window
            self.window_w = int(self.R.cplW + 2 * self.window_edge)
            self.window_h = int(self.R.cplL + 2 * self.window_edge)
            self.scene.setSceneRect(0, 0, self.R.cplW, self.R.cplL)
            self.setGeometry(2400, -250, self.window_w, 800)

            # Update file path and window title
            self.file_path = path
            self.setWindowTitle(f"Ribbon Editor - {saved_filename}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Opening File",
                f"Could not open file: {str(e)}"
            )

    def save(self):
        """Save the current ribbon pattern"""
        if self.R is None:
            QMessageBox.warning(self, "No Ribbon", "Please create a ribbon first.")
            return

        if self.file_path is None:
            self.save_as()
        else:
            try:
                ribbon_data = self.R.to_dict()
                # Create new dict with filename and datetime first
                data = {
                    "filename": os.path.basename(self.file_path),
                    "datetime": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    **ribbon_data
                }
                with open(self.file_path, "w") as f:
                    json.dump(data, f, indent=2)
                self.R.changed = False
                self.setWindowTitle(f"Ribbon Editor - {os.path.basename(self.file_path)}")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Saving File",
                    f"Could not save file: {str(e)}"
                )

    def save_as(self):
        """Save the ribbon pattern with a new filename"""
        if self.R is None:
            QMessageBox.warning(self, "No Ribbon", "Please create a ribbon first.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Ribbon Pattern As",
            "",
            "Ribbon Files (*.rbn);;All Files (*)"
        )
        if path:
            # Add .rbn extension if not present
            if not path.endswith('.rbn'):
                path += '.rbn'
            self.file_path = path
            self.save()

    def export_to_pdf(self):
        """Export the current ribbon pattern to PDF"""
        if self.R is None:
            QMessageBox.warning(self, "No Ribbon", "Please create a ribbon first.")
            return

        # Default filename based on ribbon properties
        default_name = f"ribbon_{self.R.type}_{self.R.w}x{self.R.l}.pdf"

        # File dialog
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to PDF",
            default_name,
            "PDF Files (*.pdf);;All Files (*)"
        )

        if not path:
            return

        # Add .pdf extension if missing
        if not path.endswith('.pdf'):
            path += '.pdf'

        try:
            # Header configuration
            header_height = 0
            header_text_lines = []

            if self.file_path is not None:
                # File is saved, add header with filename, date, and time
                filename = os.path.basename(self.file_path)
                current_datetime = datetime.now()
                date_str = current_datetime.strftime("%Y-%m-%d")
                time_str = current_datetime.strftime("%H:%M")

                header_text_lines = [
                    f"Filename: {filename}",
                    f"Date: {date_str}  Time: {time_str}"
                ]

                # Calculate header height (2 lines of text + margins)
                # Using Cambria 11pt for all text
                header_height = 70  # pixels (2 lines + margin)

            # Get scene dimensions
            scene_width = self.R.cplW
            scene_height = self.R.cplL

            # Calculate total content height (scene + header if applicable)
            total_content_height = scene_height + header_height

            # Create PDF writer with custom page size
            writer = QPdfWriter(path)

            # Set resolution (300 DPI for quality)
            writer.setResolution(300)

            # Calculate page size in points (assuming 96 DPI for scene coordinates)
            # Convert pixels to points: points = pixels * 72 / 96
            margin_mm = 10
            margin_points = margin_mm * 72 / 25.4  # Convert mm to points

            page_width_points = (scene_width * 72 / 96) + (2 * margin_points)
            page_height_points = (total_content_height * 72 / 96) + (2 * margin_points)

            # Create custom page size
            page_size = QPageSize(QSizeF(page_width_points, page_height_points),
                                 QPageSize.Unit.Point)
            writer.setPageSize(page_size)
            writer.setPageMargins(QMarginsF(margin_mm, margin_mm, margin_mm, margin_mm),
                                 QPageLayout.Unit.Millimeter)

            # Create painter
            painter = QPainter(writer)

            # Get the paint rectangle (area within margins)
            page_rect = writer.pageLayout().paintRectPixels(writer.resolution())

            # Calculate current Y position for rendering
            current_y = page_rect.top()

            # Draw header if file is saved
            if header_text_lines:
                # Set font: Cambria 11pt
                font = QFont("Cambria", 11)
                painter.setFont(font)

                # Draw filename
                text_rect = painter.boundingRect(
                    int(page_rect.left()),
                    int(current_y),
                    int(page_rect.width()),
                    100,
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                    header_text_lines[0]
                )
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                               header_text_lines[0])
                current_y += text_rect.height() + 5

                # Draw date and time
                text_rect = painter.boundingRect(
                    int(page_rect.left()),
                    int(current_y),
                    int(page_rect.width()),
                    100,
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                    header_text_lines[1]
                )
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                               header_text_lines[1])
                current_y += text_rect.height() + 30  # Add margin below header

            # Calculate target rectangle for scene rendering
            scene_target_rect = page_rect.toRectF()
            scene_target_rect.setTop(current_y)
            scene_target_rect.setHeight(page_rect.height() - (current_y - page_rect.top()))

            # Render the scene
            self.scene.render(painter, target=scene_target_rect, source=self.scene.sceneRect())

            painter.end()

            QMessageBox.information(
                self,
                "Export Successful",
                f"Pattern exported to:\n{path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Could not export to PDF:\n{str(e)}"
            )

    def show_about_dialog(self):
        # Get absolute path to the about image
        about_gif = os.path.join(os.path.dirname(__file__), "resources", "gifs", "RBE_About_1.gif")
        about_gif_url = QUrl.fromLocalFile(about_gif).toString()

        text = "<center>" \
               "<h2>Ribbon Editor</h2>" \
               "<br/>" \
               f"<img src='{about_gif_url}'>" \
               "<h4>Date 2025.12.20&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Version 1.0<br/>" \
               "<br/>" \
               "Copyright &copy; kurt.herrmann@gmx.at</h4>" \
               "</center>" \
        # About=QMessageBox.about.setBaseSize(400,300)
        # About.setText(text)
        QMessageBox.about(self, "About Ribbon Editor", text)

    def show_help_dialog(self):
        """Display help file in a dialog"""
        help_file = os.path.join(os.path.dirname(__file__), "resources", "helptexts", "Hilfetext_Ge.htm")

        if not os.path.exists(help_file):
            QMessageBox.warning(
                self,
                "Help File Not Found",
                f"Could not find help file: {help_file}"
            )
            return

        try:
            # Create dialog to display help
            help_dialog = QDialog(self)
            help_dialog.setWindowTitle("Help")
            help_dialog.resize(800, 600)

            # Create layout
            layout = QVBoxLayout()

            # Use QWebEngineView if available for full HTML rendering, otherwise QTextBrowser
            if WEBENGINE_AVAILABLE:
                browser = QWebEngineView()
                file_url = QUrl.fromLocalFile(help_file)
                browser.setUrl(file_url)
            else:
                browser = QTextBrowser()
                browser.setOpenExternalLinks(True)
                file_url = QUrl.fromLocalFile(help_file)
                browser.setSource(file_url)

            layout.addWidget(browser)
            help_dialog.setLayout(layout)
            help_dialog.exec()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Opening Help",
                f"Could not open help file: {str(e)}"
            )


def show_warning_messagebox(text):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setText(text)
    msg.setWindowTitle("Warning MessageBox")
    msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    menu = window.menuBar().addMenu("&File")

    new_action = QAction("&New")
    menu.addAction(new_action)
    new_action.triggered.connect(window.new_file)
    new_action.setShortcut(QKeySequence.StandardKey.New)

    open_action = QAction("&Open")
    menu.addAction(open_action)
    open_action.triggered.connect(window.open_file)
    open_action.setShortcut(QKeySequence.StandardKey.Open)

    save_action = QAction("&Save")
    menu.addAction(save_action)
    save_action.triggered.connect(window.save)
    save_action.setShortcut(QKeySequence.StandardKey.Save)

    save_as_action = QAction("Save &As...")
    menu.addAction(save_as_action)
    save_as_action.triggered.connect(window.save_as)

    export_pdf_action = QAction("Export to &PDF...")
    menu.addAction(export_pdf_action)
    export_pdf_action.triggered.connect(window.export_to_pdf)

    close = QAction("&Close")
    menu.addAction(close)
    close.triggered.connect(window.close)

    # View menu
    view_menu = window.menuBar().addMenu("&View")

    reset_zoom_action = QAction("&Reset Zoom")
    view_menu.addAction(reset_zoom_action)
    reset_zoom_action.triggered.connect(window.view.reset_zoom)
    reset_zoom_action.setShortcut("Ctrl+0")

    help_menu = window.menuBar().addMenu("&Help")
    help_action = QAction("&Help")
    help_menu.addAction(help_action)
    help_action.triggered.connect(window.show_help_dialog)

    about_action = QAction("&About")
    help_menu.addAction(about_action)
    about_action.triggered.connect(window.show_about_dialog)

    window.resize(300, 180)
    window.show()
    window.scene.update()
    window.view.show()

    app.exec()


if __name__ == "__main__":
    main()
