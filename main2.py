import sys
import shutil
import tempfile
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, QFileDialog, QListWidget, QWidget, QAbstractItemView, QMessageBox, QRadioButton, QMenu
from PySide6.QtGui import Qt
from PySide6.QtCore import QMimeData
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pathlib import Path

class ListBoxWidget(QListWidget):
    def __init__(self, merge_button, split_button):
        super().__init__()
        self.setAcceptDrops(True)
        self.resize(600, 600)
        self.setDragDropMode(QAbstractItemView.InternalMove)  # type: ignore
        self.merge_button = merge_button
        self.split_button = split_button

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.endswith(".pdf") or file_path.endswith(".PDF"):
                    self.addItem(file_path)
        else:
            super().dropEvent(event)

        if self.count() == 1:
            self.split_button.setEnabled(True)
            self.merge_button.setEnabled(False)
        else:
            self.split_button.setEnabled(False)
            self.merge_button.setEnabled(True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        self.setWindowTitle("Fusion / Split de fichiers PDF")
        self.setMinimumSize(400, 300)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)  # type: ignore

        layout = QVBoxLayout()
        label = QLabel("Glissez-déposez les fichiers PDF ici")
        label.setAlignment(Qt.AlignCenter)  # type: ignore
        layout.addWidget(label)

        self.merge_button = QPushButton("Fusionner les fichiers (plusieurs fichiers requis)")
        self.merge_button.clicked.connect(self.merge_files)

        self.split_button = QPushButton("Splitter le fichier (un seul fichier requis)")
        self.split_button.clicked.connect(self.split_file)

        self.list_widget = ListBoxWidget(self.merge_button, self.split_button)  # passer en paramètres merge_button et split_button
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)  # type: ignore
        layout.addWidget(self.list_widget)

        self.select_button = QPushButton("Sélectionner les fichiers")
        self.select_button.clicked.connect(self.select_files)
        layout.addWidget(self.select_button)

        layout.addWidget(self.merge_button)

        layout.addWidget(self.split_button)

        self.clear_button = QPushButton("Effacer la sélection")
        self.clear_button.clicked.connect(self.clear_list)
        layout.addWidget(self.clear_button)

        self.rb1 = QRadioButton("Nom du fichier")
        self.rb1.toggled.connect(self.updateListDisplay)
        layout.addWidget(self.rb1)

        self.rb2 = QRadioButton("Chemin complet")
        self.rb2.toggled.connect(self.updateListDisplay)
        layout.addWidget(self.rb2)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.file_paths = []

        # Désactiver les boutons split_button et merge_button au démarrage (cad quand la liste est vide)
        self.split_button.setEnabled(False)
        self.merge_button.setEnabled(False)

    def select_files(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)  # type: ignore
        file_dialog.setNameFilter("PDF Files (*.pdf *.PDF)")

        if file_dialog.exec():
            self.file_paths = file_dialog.selectedFiles()
            if len(self.file_paths) == 1:
                self.merge_button.setEnabled(False)
                self.split_button.setEnabled(True)
            else:
                self.merge_button.setEnabled(True)
                self.split_button.setEnabled(False)

            self.list_widget.clear()
            self.list_widget.addItems(self.file_paths)

    def merge_files(self):
        self.file_paths = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        if len(self.file_paths) > 0:
            output_file_name = Path(self.file_paths[0]).stem
            # création d'un dossier temporaire
            temp_dir = tempfile.mkdtemp()
            try:
                # stockage des chemins des copies temporaires des fichiers sources
                temp_files = []
                # copie des fichiers sources dans le répertoire temporaire
                for file_path in self.file_paths:
                    temp_file_path = Path(temp_dir) / Path(file_path).name
                    shutil.copyfile(file_path, temp_file_path)
                    temp_files.append(temp_file_path)
                # création d'une instance de PdfMerger
                merger = PdfMerger()
                for file_path in temp_files:
                    merger.append(str(file_path))
                output_file_path, _ = QFileDialog.getSaveFileName(self, "Enregistrer le fichier fusionné", output_file_name, "PDF Files (*.pdf *.PDF)")
                if output_file_path:
                    with open(output_file_path, "wb") as output_file:
                        merger.write(output_file)
                    self.file_paths = []
                    self.list_widget.clear()
            finally:
                # suppression des copies temporaires des fichiers sources et du dossier temporaire
                for temp_file_path in temp_files: # type: ignore
                    temp_file_path.unlink()
                shutil.rmtree(temp_dir)

        self.merge_button.setEnabled(False)
        self.split_button.setEnabled(False)

    def clear_list(self):
        self.list_widget.clear()
        self.file_paths = []
        self.split_button.setEnabled(False)
        self.merge_button.setEnabled(False)
        self.rb1.setChecked(False)
        self.rb2.setChecked(False)

    def split_file(self):
        file_path = self.list_widget.item(0).text()
        pdf_reader = PdfReader(file_path)
        num_pages = len(pdf_reader.pages)

        if num_pages > 1:
            # Ouvrir une boîte de dialogue pour saisir le nom de fichier racine
            save_file_box = QFileDialog()
            save_file_box.setWindowTitle("Nom du fichier racine")
            save_file_box.setAcceptMode(QFileDialog.AcceptSave)  # type: ignore
            save_file_box.setNameFilter("PDF Files (*.pdf *.PDF)")
            save_file_box.setDefaultSuffix(".pdf")

            if save_file_box.exec():
                root_file_name = save_file_box.selectedFiles()[0]

                for i, page in enumerate(pdf_reader.pages):
                    output_file_path = f"{root_file_name[:-4]}_{str(i + 1).zfill(2)}.pdf"
                    page_writer = PdfWriter()
                    page_writer.add_page(page)

                    with open(output_file_path, "wb") as output_file:
                        page_writer.write(output_file)

                    self.list_widget.addItem(output_file_path)

                self.list_widget.takeItem(0)  # Supprimer l'item d'origine

            self.list_widget.clear()
            self.split_button.setEnabled(False)
            self.merge_button.setEnabled(False)

        else:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Warning)  # type: ignore
            msgBox.setText("Vous ne pouvez pas splitter un fichier ne contenant qu'une seule page!")
            msgBox.setWindowTitle("Erreur")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)  # type: ignore
            msgBox.setWindowFlag(Qt.WindowStaysOnTopHint, True)  # type: ignore
            msgBox.exec()

    def updateListDisplay(self):
        show_full_path = self.rb2.isChecked()
        self.list_widget.clear()
        if show_full_path:
            self.list_widget.addItems(self.file_paths)
        else:
            self.list_widget.addItems([Path(file_path).name for file_path in self.file_paths])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
