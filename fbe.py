import json
import os
import sys
from datetime import datetime

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QPainter, QKeySequence, QAction
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
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

    def new_file(self, checked=False):

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

    def show_about_dialog(self):
        text = ("Freundschafts-Band-Editor\n"
                "Version 1.0\n"
                "2025.12.16\n"
                "Autor: Kurt Herrmann")
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

    close = QAction("&Close")
    menu.addAction(close)
    close.triggered.connect(window.close)

    help_menu = window.menuBar().addMenu("&Help")
    help_action = QAction("&Help")
    help_menu.addAction(help_action)
    help_action.triggered.connect(window.show_help_dialog)

    about_action = QAction("&About")
    help_menu.addAction(about_action)
    about_action.triggered.connect(window.show_about_dialog)

    window.resize(300,180)
    window.show()
    window.scene.update()
    window.view.show()

    app.exec()


if __name__ == "__main__":
    main()
