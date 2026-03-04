import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QDialog, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QTableWidget, 
                             QTableWidgetItem, QDateEdit, QMessageBox, QTextEdit, 
                             QFormLayout, QVBoxLayout, QHBoxLayout, QHeaderView)
from PyQt6 import uic
from PyQt6.QtCore import QDate, Qt
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

# --- ADD / EDIT DEVICE DIALOG ---
class DeviceDialog(QDialog):
    def __init__(self, edit_data=None):
        super().__init__()
        uic.loadUi('add_device.ui', self)
        self.edit_mode_serial = edit_data[0] if edit_data else None
        
        self.serial_input = self.findChild(QLineEdit, 'serial_input')
        self.model_input = self.findChild(QLineEdit, 'model_input')
        self.date_input = self.findChild(QDateEdit, 'date_input')
        self.client_combo = self.findChild(QComboBox, 'client_combo')
        self.save_button = self.findChild(QPushButton, 'save_button')
        self.cancel_button = self.findChild(QPushButton, 'cancel_button')

        self.populate_clients()

        if edit_data:
            self.setWindowTitle("Edit Device")
            self.serial_input.setText(edit_data[0])
            self.model_input.setText(edit_data[1])
            self.date_input.setDate(QDate.fromString(edit_data[2], "yyyy-MM-dd"))
            self.client_combo.setCurrentText(edit_data[3])
        else:
            self.setWindowTitle("Add New Device")
            self.date_input.setDate(QDate.currentDate())
        
        self.save_button.clicked.connect(self.save_device)
        self.cancel_button.clicked.connect(self.reject)
        
    def populate_clients(self):
        clients = db.get_all_clients()
        self.client_combo.clear()
        self.client_combo.addItems(clients)
        
    def save_device(self):
        serial = self.serial_input.text()
        model = self.model_input.text()
        date = self.date_input.date().toString("yyyy-MM-dd")
        client = self.client_combo.currentText()
        
        if not serial or not model or not client:
            QMessageBox.warning(self, "Validation Error", "Please fill in all fields.")
            return

        if self.edit_mode_serial:
            success = db.update_device(self.edit_mode_serial, serial, model, date, client)
        else:
            success = db.add_device(serial, model, date, client)

        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Could not save device details.")

# --- SERVICE HISTORY DIALOG ---
class ServiceHistoryDialog(QDialog):
    def __init__(self, device_serial):
        super().__init__()
        uic.loadUi('service_history.ui', self)
        self.setWindowTitle(f"Service History: {device_serial}")
        
        self.history_table = self.findChild(QTableWidget, 'history_table')
        self.close_btn = self.findChild(QPushButton, 'close_button')
        
        # Configure table behavior
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Start Date", "End Date", "Type", "Description"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.close_btn.clicked.connect(self.accept)
        self.load_history(device_serial)

    def load_history(self, serial):
        if hasattr(db, 'get_service_history'):
            records = db.get_service_history(serial)
            self.history_table.setRowCount(0)
            for row_idx, record in enumerate(records):
                self.history_table.insertRow(row_idx)
                for col_idx, value in enumerate(record):
                    self.history_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
        else:
            QMessageBox.warning(self, "Database Error", "get_service_history function not found.")

# --- SERVICE DIALOG ---
class ServiceDialog(QDialog):
    def __init__(self, device_serial):
        super().__init__()
        self.device_serial = device_serial
        
        # Crucial: Load UI FIRST
        uic.loadUi('service_dialog.ui', self)
        self.setWindowTitle(f"Service: {device_serial}")
        
        # Link widgets using names from your service_dialog.ui
        self.start_date = self.findChild(QDateEdit, 'start_date_input')
        self.end_date = self.findChild(QDateEdit, 'end_date_input')
        self.service_type = self.findChild(QComboBox, 'type_combo')
        self.description = self.findChild(QTextEdit, 'desc_input')
        self.save_btn = self.findChild(QPushButton, 'save_button')
        self.cancel_btn = self.findChild(QPushButton, 'cancel_button')
        self.history_btn = self.findChild(QPushButton, 'history_button')

        # Setup initial values (respecting UI file settings)
        self.start_date.setDate(QDate.currentDate())
        self.end_date.setDate(QDate.currentDate())
        
        if self.service_type.count() == 0:
            self.service_type.addItems(["Requested", "Maintenance", "Unknown", "Yearly service"])

        # Signal connections
        self.save_btn.clicked.connect(self.handle_save)
        self.cancel_btn.clicked.connect(self.reject)
        self.history_btn.clicked.connect(self.show_history)

    def show_history(self):
        history_dialog = ServiceHistoryDialog(self.device_serial)
        history_dialog.exec()

    def handle_save(self):
        data = {
            "serial": self.device_serial,
            "start": self.start_date.date().toString("yyyy-MM-dd"),
            "end": self.end_date.date().toString("yyyy-MM-dd"),
            "type": self.service_type.currentText(),
            "desc": self.description.toPlainText()
        }
        
        if not data["desc"]:
            QMessageBox.warning(self, "Validation", "Please provide a description.")
            return

        if hasattr(db, 'add_service'):
            if db.add_service(data["serial"], data["start"], data["end"], data["type"], data["desc"]):
                QMessageBox.information(self, "Success", "Service recorded successfully.")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to save service.")
        else:
            QMessageBox.critical(self, "Error", "Database function 'add_service' missing.")

# --- CLIENTS MANAGER ---
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
            if db.update_client(self.client_id, username, password if password else None):
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to update client.")
        else:
            if not password:
                QMessageBox.warning(self, "Validation", "Password is required for new clients.")
                return
            if db.add_user(username, password, "Client"):
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to add client.")

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
        clients = db.get_clients_list()
        self.clients_table.setRowCount(0)
        for row_idx, client_data in enumerate(clients):
            self.clients_table.insertRow(row_idx)
            for col_idx, data in enumerate(client_data):
                self.clients_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

    def add_client(self):
        if ClientForm().exec(): self.load_clients()

    def edit_client(self):
        row = self.clients_table.currentRow()
        if row < 0: return
        c_id = self.clients_table.item(row, 0).text()
        c_name = self.clients_table.item(row, 1).text()
        if ClientForm(client_id=c_id, username=c_name).exec(): self.load_clients()

    def delete_client(self):
        row = self.clients_table.currentRow()
        if row < 0: return
        c_id = self.clients_table.item(row, 0).text()
        if db.delete_client(c_id): self.load_clients()

# --- MAIN WINDOW ---
class MainWindow(QMainWindow):
    def __init__(self, username, role):
        super().__init__()
        uic.loadUi('main_window.ui', self)
        self.current_user = username
        self.current_role = role
        
        self.device_table = self.findChild(QTableWidget, 'device_table')
        self.add_device_btn = self.findChild(QPushButton, 'add_device_btn')
        self.manage_clients_btn = self.findChild(QPushButton, 'manage_clients_btn')
        self.refresh_btn = self.findChild(QPushButton, 'refresh_btn')
        self.edit_device_btn = self.findChild(QPushButton, 'edit_device_btn')
        self.add_service_btn = self.findChild(QPushButton, 'add_service_btn')
        
        if self.current_role != 'Technician':
            self.manage_clients_btn.hide()

        self.add_device_btn.clicked.connect(self.open_add_device_dialog)
        self.manage_clients_btn.clicked.connect(self.open_clients_manager)
        self.refresh_btn.clicked.connect(self.load_devices)
        self.edit_device_btn.clicked.connect(self.edit_selected_device)
        self.add_service_btn.clicked.connect(self.add_service_to_device)
        
        self.load_devices()

    def load_devices(self):
        devices = db.get_devices()
        self.device_table.setRowCount(0)
        for row_idx, device_data in enumerate(devices):
            self.device_table.insertRow(row_idx)
            for col_idx, data in enumerate(device_data):
                self.device_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

    def open_add_device_dialog(self):
        if DeviceDialog().exec():
            self.load_devices()

    def edit_selected_device(self):
        row = self.device_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Info", "Please select a device to edit.")
            return
        
        serial = self.device_table.item(row, 0).text()
        model = self.device_table.item(row, 1).text()
        date = self.device_table.item(row, 2).text()
        client = self.device_table.item(row, 3).text()
        
        dialog = DeviceDialog(edit_data=(serial, model, date, client))
        if dialog.exec():
            self.load_devices()

    def open_clients_manager(self):
        ClientsManager().exec()
        self.load_devices()

    def add_service_to_device(self):
        row = self.device_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Info", "Please select a device to add a service record.")
            return
            
        serial = self.device_table.item(row, 0).text()
        dialog = ServiceDialog(serial)
        dialog.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    db.create_tables()
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())