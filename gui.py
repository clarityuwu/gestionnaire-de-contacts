import sys
import sqlite3
from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidget, QPushButton, QVBoxLayout, QWidget, QDialog, QLabel, QLineEdit, QMessageBox

# Create or connect to the database
conn = sqlite3.connect('contacts.db')
cursor = conn.cursor()

class ContactApp(QMainWindow):
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
        cursor.execute('''
            SELECT c.id, c.nom, c.prenom
            FROM contact c
        ''')
        contacts = cursor.fetchall()
        for contact in contacts:
            id, nom, prenom = contact
            contact_item = f"{nom} {prenom}"
            self.contact_list.addItem(contact_item)

    def view_contact(self):
        selected_contact = self.contact_list.currentItem()
        if selected_contact:
            contact_name = selected_contact.text()
        
            cursor.execute('''
                SELECT c.nom, c.prenom, t.tel, a.adresse
                FROM contact c
                LEFT JOIN link_contact_tel t ON c.nom = t.nom AND c.prenom = t.prenom
                LEFT JOIN link_contact_adresse a ON c.nom = a.nom AND c.prenom = a.prenom
                WHERE c.nom || ' ' || c.prenom = ?
            ''', (contact_name,))
        
            contact_data = cursor.fetchone()

            if contact_data:
                nom, prenom, tel, address = contact_data
                details_dialog = ContactDetails(nom, prenom, tel, address)
                details_dialog.exec()


    def add_contact(self):
        dialog = AddContactDialog()
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            # Reload the contact list after adding a contact
            self.contact_list.clear()
            self.load_contacts()

    def delete_contact(self):
        selected_contact = self.contact_list.currentItem()
        if selected_contact:
            confirmation = QMessageBox.question(
                self, "Confirm Deletion", "Are you sure you want to delete this contact?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if confirmation == QMessageBox.StandardButton.Yes:
                contact_name = selected_contact.text()
                contact_nom = contact_name.split(" ")[0]
                contact_prenom = contact_name.split(" ")[1]

                cursor.execute('''
                    DELETE FROM link_contact_tel WHERE nom = ? AND prenom = ?
                ''', (contact_nom, contact_prenom))
                
                cursor.execute('''
                    DELETE FROM link_contact_adresse WHERE nom = ? AND prenom = ?
                ''', (contact_nom, contact_prenom))

                cursor.execute('''
                    DELETE FROM tel WHERE id IN (
                        SELECT t.id FROM contact c
                        LEFT JOIN link_contact_tel t ON c.nom = t.nom AND c.prenom = t.prenom
                        WHERE c.nom = ? AND c.prenom = ?
                    )
                ''', (contact_nom, contact_prenom))
                
                cursor.execute('''
                    DELETE FROM adresse WHERE id IN (
                        SELECT a.id FROM contact c
                        LEFT JOIN link_contact_adresse a ON c.nom = a.nom AND c.prenom = a.prenom
                        WHERE c.nom = ? AND c.prenom = ?
                    )
                ''', (contact_nom, contact_prenom))

                cursor.execute('''
                    DELETE FROM contact WHERE nom = ? AND prenom = ?
                ''', (contact_nom, contact_prenom))

                conn.commit()
                self.contact_list.takeItem(self.contact_list.currentRow())


class ContactDetails(QDialog):
    def __init__(self, nom, prenom, tel, adresse):
        super().__init__()

        self.setWindowTitle("Contact Details")
        self.setGeometry(200, 200, 300, 150)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.nom_label = QLabel(f"Nom: {nom}")
        self.prenom_label = QLabel(f"Prenom: {prenom}")
        self.tel_label = QLabel(f"Tel: {tel}" if tel else "Tel: N/A")
        self.adresse_label = QLabel(f"adresse: {adresse}" if adresse else "adresse: N/A")

        self.layout.addWidget(self.nom_label)
        self.layout.addWidget(self.prenom_label)
        self.layout.addWidget(self.tel_label)
        self.layout.addWidget(self.adresse_label)

class AddContactDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Add Contact")
        self.setGeometry(200, 200, 300, 150)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.form_layout = QVBoxLayout()

        self.nom_input = QLineEdit()
        self.prenom_input = QLineEdit()
        self.tel_input = QLineEdit()
        self.adresse_input = QLineEdit()

        self.form_layout.addWidget(QLabel("Nom:"))
        self.form_layout.addWidget(self.nom_input)
        self.form_layout.addWidget(QLabel("Prenom:"))
        self.form_layout.addWidget(self.prenom_input)
        self.form_layout.addWidget(QLabel("Tel:"))
        self.form_layout.addWidget(self.tel_input)
        self.form_layout.addWidget(QLabel("adresse:"))
        self.form_layout.addWidget(self.adresse_input)

        self.add_button = QPushButton("Add Contact")
        self.add_button.clicked.connect(self.add_contact)

        self.layout.addLayout(self.form_layout)
        self.layout.addWidget(self.add_button)

    def add_contact(self):
        nom = self.nom_input.text()
        prenom = self.prenom_input.text()
        tel = self.tel_input.text()
        adresse = self.adresse_input.text()

        cursor.execute('''
            INSERT INTO contact (nom, prenom) VALUES (?, ?)
        ''', (nom, prenom))

        cursor.execute('SELECT last_insert_rowid()')  # Get the last inserted contact ID
        contact_id = cursor.fetchone()[0]

        if tel:
            cursor.execute('INSERT INTO link_contact_tel (id, nom, prenom, tel) VALUES (?, ?, ?, ?)', (contact_id, nom, prenom, tel))
            cursor.execute('INSERT INTO tel (tel, id) VALUES (?, ?)', (tel, contact_id))

        if adresse:
            cursor.execute('INSERT INTO link_contact_adresse (id, nom, prenom, adresse) VALUES (?, ?, ?, ?)', (contact_id, nom, prenom, adresse))
            cursor.execute('INSERT INTO adresse (adresse, id) VALUES (?, ?)', (adresse, contact_id))

        conn.commit()
        self.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ContactApp()
    window.show()
    sys.exit(app.exec())
