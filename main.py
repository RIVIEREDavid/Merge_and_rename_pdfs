import sys
import shutil
import tempfile
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, QFileDialog, QListWidget, QWidget, QAbstractItemView
from PySide6.QtGui import Qt, QDragEnterEvent, QDropEvent, QDragMoveEvent, QMouseEvent, QCursor, QDrag
from PySide6.QtCore import QMimeData
from PyPDF2 import PdfMerger
from pathlib import Path

# Classe perso héritant de QListWidget
class ListBoxWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.resize(600, 600)
        self.setDragDropMode(QAbstractItemView.InternalMove) #type: ignore

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.endswith(".pdf"):
                    self.addItem(file_path)
        else:
            super().dropEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Fusion de fichiers PDF")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout()
        label = QLabel("Glissez-déposez vos fichiers PDF ici")
        label.setAlignment(Qt.AlignCenter) #type: ignore
        layout.addWidget(label)

        self.list_widget = ListBoxWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove) #type: ignore
        layout.addWidget(self.list_widget)

        self.button = QPushButton("Sélectionner les fichiers")
        self.button.clicked.connect(self.select_files)
        layout.addWidget(self.button)

        self.merge_button = QPushButton("Fusionner les fichiers")
        self.merge_button.clicked.connect(self.merge_files)
        layout.addWidget(self.merge_button)

        self.clear_button = QPushButton("Effacer la sélection")
        self.clear_button.clicked.connect(self.clear_list)
        layout.addWidget(self.clear_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.file_paths = []

    def select_files(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles) #type: ignore
        file_dialog.setNameFilter("PDF Files (*.pdf)")

        if file_dialog.exec():
            self.file_paths = file_dialog.selectedFiles()
            self.merge_button.setEnabled(True)
            self.list_widget.clear()
            self.list_widget.addItems(self.file_paths)

    def merge_files(self):
        self.file_paths = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        if len(self.file_paths) > 0:
            output_file_name = Path(self.file_paths[0]).stem
            #création d'un dossier temporaire
            temp_dir = tempfile.mkdtemp() 
            try:
                #stockage des chemins des copies temporaires des fichiers sources
                temp_files = []  
                #copie des fichiers sources dans le répertoire temporaire
                for file_path in self.file_paths:
                    temp_file_path = Path(temp_dir) / Path(file_path).name
                    shutil.copyfile(file_path, temp_file_path)
                    temp_files.append(temp_file_path)
                #création d'une instance de PdfMerger
                merger = PdfMerger()
                for file_path in temp_files:
                    merger.append(str(file_path))
                output_file_path, _ = QFileDialog.getSaveFileName(self, "Enregistrer le fichier fusionné", output_file_name, "PDF Files (*.pdf)")
                if output_file_path:
                    with open(output_file_path, "wb") as output_file:
                        merger.write(output_file)
                    self.file_paths = []
                    self.list_widget.clear()
            finally:
                #suppression des copies temporaires des fichiers sources et du dossier temporaire
                for temp_file_path in temp_files:
                    temp_file_path.unlink()
                shutil.rmtree(temp_dir)

    def clear_list(self):
        self.list_widget.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())