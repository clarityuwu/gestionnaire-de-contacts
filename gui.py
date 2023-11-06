import sys
import sqlite3
from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidget, QPushButton, QVBoxLayout, QWidget, QDialog, QLabel, QLineEdit, QMessageBox

# Create or connect to the database
conn = sqlite3.connect('contacts.db')
cursor = conn.cursor()

# Define the schema with an auto-incrementing primary key for the contact table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS contact (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT,
        prenom TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS tel (
        id INTEGER,
        tel TEXT,
        FOREIGN KEY (id) REFERENCES contact(id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS adresse (
        id INTEGER,
        adresse TEXT,
        FOREIGN KEY (id) REFERENCES contact(id)
    )
''')

class ContactApp(QMainWindow):
    """
    Class principale de l'application 
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Contact App")
        self.setGeometry(100, 100, 400, 300)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.contact_list = QListWidget()
        self.layout.addWidget(self.contact_list)

        self.view_button = QPushButton("View Contact")
        self.add_button = QPushButton("Add Contact")
        self.delete_button = QPushButton("Delete Contact")

        self.layout.addWidget(self.view_button)
        self.layout.addWidget(self.add_button)
        self.layout.addWidget(self.delete_button)

        # Load contacts from the "contact" table
        self.load_contacts()

        # Connect buttons to functions
        self.view_button.clicked.connect(self.view_contact)
        self.add_button.clicked.connect(self.add_contact)
        self.delete_button.clicked.connect(self.delete_contact)

    def load_contacts(self):
        """
        Fonction qui sert a charger les nom prénom d'un contact
        """
        cursor.execute('''SELECT id, nom, prenom FROM contact''')
        contacts = cursor.fetchall()
        for contact in contacts:
            id, nom, prenom = contact
            contact_item = f"{nom} {prenom}"
            self.contact_list.addItem(contact_item)

    def view_contact(self):
        """
        Fonction qui sert a avoir les informations du contact sélectionné 
        """
        selected_contact = self.contact_list.currentItem()
        if selected_contact:
            contact_name = selected_contact.text()
            nom, prenom = contact_name.split(' ')
            cursor.execute('''
                SELECT c.nom, c.prenom, t.tel, a.adresse
                FROM contact c
                LEFT JOIN tel t ON c.id = t.id
                LEFT JOIN adresse a ON c.id = a.id
                WHERE c.nom = ? AND c.prenom = ?
            ''', (nom, prenom))
            contact_data = cursor.fetchone()
            if contact_data:
                nom, prenom, tel, address = contact_data
                details_dialog = ContactDetails(nom, prenom, tel, address)
                details_dialog.exec()

    def add_contact(self):
        """
        Fonction qui quand un contact est ajouté est exécuter pour rafraichir la liste des contacts et la rajoute dans la liste
        """
        dialog = AddContactDialog()
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            # Reload the contact list after adding a contact
            self.contact_list.clear()
            self.load_contacts()

    def delete_contact(self):
        """
        Demande la confirmation de l'utilisateur et si confirmé alors supprime le contact de la bdd
        """
        selected_contact = self.contact_list.currentItem()
        if selected_contact:
            confirmation = QMessageBox.question(
                self, "Confirm Deletion", "Are you sure you want to delete this contact?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirmation == QMessageBox.StandardButton.Yes:
                contact_name = selected_contact.text()
                nom, prenom = contact_name.split(' ')
                cursor.execute('SELECT id FROM contact WHERE nom = ? AND prenom = ?', (nom, prenom))
                id = cursor.fetchone()[0]
                cursor.execute('DELETE FROM contact WHERE id = ?', (id,))
                cursor.execute('DELETE FROM tel WHERE id = ?', (id,))
                cursor.execute('DELETE FROM adresse WHERE id = ?', (id,))
                conn.commit()
                self.contact_list.takeItem(self.contact_list.currentRow())

                self.contact_list.takeItem(self.contact_list.currentRow())

class ContactDetails(QDialog):
    """
    Ouvre une fenetre avec les informations du contact
    """
    def __init__(self, nom, prenom, tel, adresse):
        super().__init__()

        self.setWindowTitle("Contact Details")
        self.setGeometry(200, 200, 300, 150)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.nom_label = QLabel(f"Nom: {nom}")
        self.prenom_label = QLabel(f"Prenom: {prenom}")
        self.tel_label = QLabel(f"Tel: {tel}" if tel else "Tel: N/A")
        self.adresse_label = QLabel(f"Adresse: {adresse}" if adresse else "Adresse: N/A")

        self.layout.addWidget(self.nom_label)
        self.layout.addWidget(self.prenom_label)
        self.layout.addWidget(self.tel_label)
        self.layout.addWidget(self.adresse_label)

class AddContactDialog(QDialog):
    """
    Ouvre une fenetre avec les informations nécessaire pour l'enregistrement d'un contact
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Add Contact")
        self.setGeometry(200, 200, 300, 150) # ouvre une nouvelle fenetre

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.form_layout = QVBoxLayout()

        self.nom_input = QLineEdit()
        self.prenom_input = QLineEdit() # permet de creer un champ de texte
        self.tel_input = QLineEdit()
        self.adresse_input = QLineEdit()

        self.form_layout.addWidget(QLabel("Nom:")) # permet de creer un label
        self.form_layout.addWidget(self.nom_input)
        self.form_layout.addWidget(QLabel("Prenom:")) 
        self.form_layout.addWidget(self.prenom_input)
        self.form_layout.addWidget(QLabel("Tel:"))
        self.form_layout.addWidget(self.tel_input)
        self.form_layout.addWidget(QLabel("Adresse:"))
        self.form_layout.addWidget(self.adresse_input)

        self.add_button = QPushButton("Add Contact") # permet de creer un bouton
        self.add_button.clicked.connect(self.add_contact)

        self.layout.addLayout(self.form_layout) 
        self.layout.addWidget(self.add_button)

    def add_contact(self):
        """
        prend les données que l' utilisateur a donnée et les enregistre dans la base de donnée
        """
        nom = self.nom_input.text()
        prenom = self.prenom_input.text()
        tel = self.tel_input.text()
        adresse = self.adresse_input.text()
        cursor.execute('SELECT MAX(id) FROM contact')
        max_id = cursor.fetchone()[0]
        new_id = max_id + 1 if max_id else 1
        cursor.execute('INSERT INTO contact (id, nom, prenom) VALUES (?, ?, ?)', (new_id, nom, prenom))
        if tel:
            cursor.execute('INSERT INTO tel (tel, id) VALUES (?, ?)', (tel, new_id))
        if adresse:
            cursor.execute('INSERT INTO adresse (adresse, id) VALUES (?, ?)', (adresse, new_id))
        conn.commit()
        self.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ContactApp()
    window.show()
    sys.exit(app.exec())