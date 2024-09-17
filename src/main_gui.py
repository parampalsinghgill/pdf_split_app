import sys
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QHBoxLayout, QVBoxLayout, QLineEdit, QDialog, QDialogButtonBox, QWidget, QProgressBar

from pdf_split.pdf_splitter import split_pdf


class ErrorDialog(QDialog):
    def __init__(self, e, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Error !!!")
        QBtn = QDialogButtonBox.Ok
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        layout = QVBoxLayout()
        message = QLabel(f"{type(e).__name__}: {str(e)}")
        layout.addWidget(message)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)


class InfoDialog(QDialog):
    def __init__(self, info_msg, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Info !")
        QBtn = QDialogButtonBox.Ok
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        layout = QVBoxLayout()
        message = QLabel(info_msg)
        layout.addWidget(message)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)


class PDFSplitWorker(QThread):
    finished = pyqtSignal()
    error_occurred = pyqtSignal(Exception)
    progress = pyqtSignal(int)  # Signal for progress updates

    def __init__(self, file_path, start_page, end_page, output_pdf):
        super().__init__()
        self.file_path = file_path
        self.start_page = start_page
        self.end_page = end_page
        self.output_pdf = output_pdf

    def run(self):
        try:
            split_pdf(self.file_path, self.start_page, self.end_page, self.output_pdf, verbose=False)
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(e)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.start_page_number = None
        self.end_page_number = None
        self.setWindowTitle("PDF Splitter app")
        self.setFixedSize(700, 350)

        main_layout = QVBoxLayout()

        # Filename layout
        layout1 = QHBoxLayout()
        self.label_filename = QLabel("<No file selected>")
        self.label_filename.setStyleSheet("border: 1px solid black;")
        self.label_filename.setFixedSize(600, 30)
        layout1.addWidget(self.label_filename)

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.get_file)
        browse_btn.setFixedSize(50, 30)
        layout1.addWidget(browse_btn, alignment=Qt.AlignRight)

        # Start page layout
        layout2 = QHBoxLayout()
        label_page_start = QLabel("Start page number (this page included in the pdf)")
        layout2.addWidget(label_page_start)

        self.textbox_start = QLineEdit()
        self.textbox_start.setFixedSize(50, 30)
        self.textbox_start.editingFinished.connect(self.save_page_number)
        layout2.addWidget(self.textbox_start)

        # End page layout
        layout3 = QHBoxLayout()
        label_page_end = QLabel("End page number (this page included in the pdf)")
        layout3.addWidget(label_page_end)

        self.textbox_end = QLineEdit()
        self.textbox_end.setFixedSize(50, 30)
        self.textbox_end.editingFinished.connect(self.save_page_number)
        layout3.addWidget(self.textbox_end)

        # Split button layout
        layout4 = QHBoxLayout()
        btn_split = QPushButton("Split")
        btn_split.setFixedSize(100, 50)
        btn_split.clicked.connect(self.split_the_pdf)
        layout4.addWidget(btn_split)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)  # Hidden by default

        # Status update label
        self.label_status = QLabel("Ready")
        self.label_status.setFixedSize(100, 25)
        self.label_status.setStyleSheet("border: 1px solid red;")

        # Add all layouts to the main layout
        main_layout.addLayout(layout1)
        main_layout.addLayout(layout2)
        main_layout.addLayout(layout3)
        main_layout.addLayout(layout4)
        main_layout.addWidget(self.label_status, alignment=Qt.AlignLeft)
        main_layout.addWidget(self.progress_bar)

        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

    def get_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Open file', "", "Pdf files (*.pdf)")
        if filename:
            self.label_filename.setText(filename)

    def save_page_number(self):
        sender = self.sender()
        try:
            if sender == self.textbox_start:
                self.start_page_number = int(self.textbox_start.text())
            elif sender == self.textbox_end:
                self.end_page_number = int(self.textbox_end.text())
        except ValueError as ex:
            ErrorDialog(ex, self).exec()

    def split_the_pdf(self):
        # Check if a file is selected
        file_path = self.label_filename.text()
        if file_path == "<No file selected>":
            ErrorDialog(ValueError("No file selected"), self).exec()
            return

        # Check if page numbers are valid
        if self.start_page_number is None or self.end_page_number is None:
            ErrorDialog(ValueError("Invalid page numbers"), self).exec()
            return

        if self.start_page_number > self.end_page_number:
            ErrorDialog(ValueError("Start page cannot be greater than end page"), self).exec()
            return

        if self.start_page_number <= 0 or self.end_page_number <= 0:
            ErrorDialog(ValueError("Page numbers must be greater than 0"), self).exec()
            return

        # Get the output file
        output_file, _ = QFileDialog.getSaveFileName(self, "Save Split PDF", "", "PDF files (*.pdf)")
        if not output_file:
            self.update_status("Ready")
            return

        # Update status and start the PDF splitting in a background thread
        self.update_status("Splitting...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker = PDFSplitWorker(file_path, self.start_page_number, self.end_page_number, output_file)
        self.worker.finished.connect(self.on_split_finished)
        self.worker.error_occurred.connect(self.on_split_error)
        self.worker.progress.connect(self.update_progress)  # Connect progress signal
        self.worker.start()

    def on_split_finished(self):
        self.update_status("Ready")
        self.progress_bar.setVisible(False)
        InfoDialog("PDF Split Successful!").exec()

    def on_split_error(self, e):
        self.update_status("Ready")
        self.progress_bar.setVisible(False)
        ErrorDialog(e, self).exec()

    def update_status(self, message):
        self.label_status.setText(message)

    def update_progress(self, value):
        self.progress_bar.setValue(value)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
