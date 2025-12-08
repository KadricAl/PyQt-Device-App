import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QDialog, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QTableWidget, 
                             QTableWidgetItem, QDateEdit, QMessageBox)
from PyQt6 import uic
from PyQt6.QtCore import QDate
import database as db

# --- REGISTER WINDOW ---
class RegisterWindow(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('register.ui', self)
        self.username_input = self.findChild(QLineEdit, 'username_input')
        self.password_input = self.findChild(QLineEdit, 'password_input')
        self.confirm_password_input = self.findChild(QLineEdit, 'confirm_password_input')
        self.role_combobox = self.findChild(QComboBox, 'role_combobox')
        self.register_button = self.findChild(QPushButton, 'register_button')
        self.message_label = self.findChild(QLabel, 'message_label')
        self.register_button.clicked.connect(self.handle_registration)

    def handle_registration(self):
        username = self.username_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        role = self.role_combobox.currentText()
        
        if not username or not password or not confirm_password:
            self.message_label.setText("All fields are required.")
            self.message_label.setStyleSheet("color: #e74c3c;")
            return
        if password != confirm_password:
            self.message_label.setText("Passwords do not match.")
            self.message_label.setStyleSheet("color: #e74c3c;")
            return

        if db.add_user(username, password, role):
            self.message_label.setText("Registration successful! Close to login.")
            self.message_label.setStyleSheet("color: #2ecc71;")
            self.register_button.setEnabled(False) 
        else:
            self.message_label.setText("Username already exists.")
            self.message_label.setStyleSheet("color: #e74c3c;")

# --- LOGIN WINDOW ---
class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('login.ui', self)
        self.username_input = self.findChild(QLineEdit, 'username_input')
        self.password_input = self.findChild(QLineEdit, 'password_input')
        self.role_combobox = self.findChild(QComboBox, 'role_combobox')
        self.login_button = self.findChild(QPushButton, 'login_button')
        self.register_button = self.findChild(QPushButton, 'register_button')
        self.error_label = self.findChild(QLabel, 'error_label')
        
        self.register_win = None
        self.main_win = None

        self.login_button.clicked.connect(self.handle_login)
        self.register_button.clicked.connect(self.show_register_window)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        role = self.role_combobox.currentText()

        if db.verify_user(username, password, role):
            self.error_label.setText("")
            self.open_main_application(username, role)
        else:
            self.error_label.setText("Invalid credentials.")

    def show_register_window(self):
        if self.register_win is None:
            self.register_win = RegisterWindow()
        self.register_win.show()

    def open_main_application(self, username, role):
        self.main_win = MainWindow(username, role)
        self.main_win.show()
        self.close()

# --- ADD DEVICE DIALOG ---
class AddDeviceDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('add_device.ui', self)
        
        # Find Widgets
        self.serial_input = self.findChild(QLineEdit, 'serial_input')
        self.model_input = self.findChild(QLineEdit, 'model_input')
        self.date_input = self.findChild(QDateEdit, 'date_input')
        self.client_combo = self.findChild(QComboBox, 'client_combo')
        self.save_button = self.findChild(QPushButton, 'save_button')
        self.cancel_button = self.findChild(QPushButton, 'cancel_button')

        # Set Date to current date
        self.date_input.setDate(QDate.currentDate())
        
        # Populate Client ComboBox
        self.populate_clients()
        
        self.save_button.clicked.connect(self.save_device)
        self.cancel_button.clicked.connect(self.reject) # Closes dialog
        
    def populate_clients(self):
        clients = db.get_all_clients()
        self.client_combo.addItems(clients)
        
    def save_device(self):
        serial = self.serial_input.text()
        model = self.model_input.text()
        date = self.date_input.text() # returns string "yyyy-MM-dd" due to ui format
        client = self.client_combo.currentText()
        
        if not serial or not model or not client:
            QMessageBox.warning(self, "Validation Error", "Please fill in all fields.")
            return

        if db.add_device(serial, model, date, client):
            self.accept() # Closes dialog with Success result
        else:
            QMessageBox.critical(self, "Error", "Could not save device.")

# --- CLIENT FORM DIALOG ---
class ClientForm(QDialog):
    def __init__(self, client_id=None, username=None):
        super().__init__()
        uic.loadUi('client_form.ui', self)
        self.client_id = client_id
        
        self.username_input = self.findChild(QLineEdit, 'username_input')
        self.password_input = self.findChild(QLineEdit, 'password_input')
        self.save_button = self.findChild(QPushButton, 'save_button')
        self.cancel_button = self.findChild(QPushButton, 'cancel_button')
        
        if username:
            self.username_input.setText(username)
            self.setWindowTitle("Edit Client")
        else:
            self.setWindowTitle("Add Client")

        self.save_button.clicked.connect(self.save_client)
        self.cancel_button.clicked.connect(self.reject)

    def save_client(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username:
            QMessageBox.warning(self, "Validation", "Username is required.")
            return

        if self.client_id:
            # Update existing
            if db.update_client(self.client_id, username, password if password else None):
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to update client. Username might be taken.")
        else:
            # Add new
            if not password:
                QMessageBox.warning(self, "Validation", "Password is required for new clients.")
                return
            if db.add_user(username, password, "Client"):
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to add client. Username likely taken.")

# --- CLIENTS MANAGER WINDOW ---
class ClientsManager(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('clients.ui', self)
        self.clients_table = self.findChild(QTableWidget, 'clients_table')
        self.add_btn = self.findChild(QPushButton, 'add_client_btn')
        self.edit_btn = self.findChild(QPushButton, 'edit_client_btn')
        self.delete_btn = self.findChild(QPushButton, 'delete_client_btn')
        
        self.add_btn.clicked.connect(self.add_client)
        self.edit_btn.clicked.connect(self.edit_client)
        self.delete_btn.clicked.connect(self.delete_client)
        
        self.load_clients()

    def load_clients(self):
        clients = db.get_clients_list() # returns [(id, username, role), ...]
        self.clients_table.setRowCount(0)
        for row_idx, client_data in enumerate(clients):
            self.clients_table.insertRow(row_idx)
            for col_idx, data in enumerate(client_data):
                self.clients_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

    def add_client(self):
        dialog = ClientForm()
        if dialog.exec():
            self.load_clients()

    def edit_client(self):
        selected = self.clients_table.selectedItems()
        if not selected:
            QMessageBox.information(self, "Info", "Select a client to edit.")
            return
        
        row = self.clients_table.currentRow()
        c_id = self.clients_table.item(row, 0).text()
        c_name = self.clients_table.item(row, 1).text()
        
        dialog = ClientForm(client_id=c_id, username=c_name)
        if dialog.exec():
            self.load_clients()

    def delete_client(self):
        selected = self.clients_table.selectedItems()
        if not selected:
            QMessageBox.information(self, "Info", "Select a client to delete.")
            return
            
        row = self.clients_table.currentRow()
        c_id = self.clients_table.item(row, 0).text()
        c_name = self.clients_table.item(row, 1).text()
        
        confirm = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete client '{c_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            if db.delete_client(c_id):
                self.load_clients()
            else:
                QMessageBox.critical(self, "Error", "Could not delete client.")

# --- MAIN WINDOW ---
class MainWindow(QMainWindow):
    def __init__(self, username, role):
        super().__init__()
        uic.loadUi('main_window.ui', self)
        self.current_user = username
        self.current_role = role
        
        # Find Widgets
        self.device_table = self.findChild(QTableWidget, 'device_table')
        self.add_device_btn = self.findChild(QPushButton, 'add_device_btn')
        self.manage_clients_btn = self.findChild(QPushButton, 'manage_clients_btn') # New Button
        self.refresh_btn = self.findChild(QPushButton, 'refresh_btn')
        self.edit_device_btn = self.findChild(QPushButton, 'edit_device_btn')
        self.add_service_btn = self.findChild(QPushButton, 'add_service_btn')
        
        # Hide "Manage Clients" if user is not a Technician
        if self.current_role != 'Technician':
            self.manage_clients_btn.hide()

        # Connect Signals
        self.add_device_btn.clicked.connect(self.open_add_device_dialog)
        self.manage_clients_btn.clicked.connect(self.open_clients_manager) # New Connection
        self.refresh_btn.clicked.connect(self.load_devices)
        self.edit_device_btn.clicked.connect(self.edit_selected_device)
        self.add_service_btn.clicked.connect(self.add_service_to_device)
        
        # Initial Load
        self.load_devices()

    def open_clients_manager(self):
        manager = ClientsManager()
        manager.exec()
        # Refresh device list in case clients were changed/removed impacting the view
        self.load_devices()

    def load_devices(self):
        """Fetches devices from DB and populates the table."""
        devices = db.get_devices() # Returns list of tuples (serial, model, date, client)
        
        self.device_table.setRowCount(0) # Clear table
        
        for row_idx, device_data in enumerate(devices):
            self.device_table.insertRow(row_idx)
            for col_idx, data in enumerate(device_data):
                item = QTableWidgetItem(str(data))
                self.device_table.setItem(row_idx, col_idx, item)

    def open_add_device_dialog(self):
        dialog = AddDeviceDialog()
        if dialog.exec(): # Returns True if self.accept() was called in dialog
            self.load_devices() # Refresh table after adding
            
    def edit_selected_device(self):
        selected_items = self.device_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Info", "Please select a device to edit.")
            return
        
        # Logic for editing would go here (e.g., open a dialog pre-filled with row data)
        # For now, we just get the Serial Number (column 0)
        row = self.device_table.currentRow()
        serial = self.device_table.item(row, 0).text()
        print(f"Edit requested for Serial: {serial}")
        
    def add_service_to_device(self):
        selected_items = self.device_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Info", "Please select a device to add service to.")
            return
            
        row = self.device_table.currentRow()
        serial = self.device_table.item(row, 0).text()
        print(f"Add Service requested for Serial: {serial}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    db.create_tables()
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())