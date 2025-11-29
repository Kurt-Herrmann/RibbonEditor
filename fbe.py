import sys

from PyQt6.QtGui import QPainter, QKeySequence, QAction
from PyQt6.QtWidgets import (QApplication, QGraphicsScene, QMainWindow, QGraphicsView,
                             QDialog, QMessageBox, QSizePolicy)

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
        self.window_w = 300
        self.window_h = 800
        self.window_edge = 25

        self.setCentralWidget(self.view)
        self.setWindowTitle("Ribbon Editor")

    def closeEvent(self, e):
        # if not text.document().isModified():
        #     return
        # answer = QMessageBox.question(
        #     window, None,
        #     "You have unsaved changes. Save before closing?",
        #     QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        # )
        # if answer & QMessageBox.Save:
        #     save()
        #     if text.document().isModified():
        #         # This happens when the user closes the Save As... dialog.
        #         # We do not want to close the window in this case because it
        #         # would throw away unsaved changes.
        #         e.ignore()
        # elif answer & QMessageBox.Cancel:
        #     e.ignore()
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
                                                 "The next smaller odd number has been assigned.")A popup
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
        self.setGeometry(2400,-250,self.window_w, 800)

    def open_file():
        global file_path
        path = QFileDialog.getOpenFileName(window, "Open")[0]
        if path:
            text.setPlainText(open(path).read())
            file_path = path

    def save():
        if file_path is None:
            save_as()
        else:
            with open(file_path, "w") as f:
                f.write(text.toPlainText())
            text.document().setModified(False)

    def save_as():
        global file_path
        path = QFileDialog.getSaveFileName(window, "Save As")[0]
        if path:
            file_path = path
            save()

    def show_about_dialog():
        text = "<center>" \
               "<h1>Text Editor</h1>" \
               "&#8291;" \
               "<img src=icon.svg>" \
               "</center>" \
               "<p>Version 31.4.159.265358<br/>" \
               "Copyright &copy; Company Inc.</p>"
        QMessageBox.about(window, "About Text Editor", text)


def show_warning_messagebox(text):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setText(text)
    msg.setWindowTitle("Warning MessageBox")
    msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)


def main():
    file_path = None
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
    about_action = QAction("&About")
    help_menu.addAction(about_action)
    about_action.triggered.connect(window.show_about_dialog)

    window.resize(250, 150)
    window.show()
    # window.setCentralWidget(self.view)
    window.scene.update()
    window.view.show()

    app.exec()


if __name__ == "__main__":
    main()
