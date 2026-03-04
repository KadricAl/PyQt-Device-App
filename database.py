import sqlite3
import hashlib

def connect_db():
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect('app_database.db')
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def create_tables():
    """Creates the necessary tables if they don't already exist."""
    conn = connect_db()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Users Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL
                );
            ''')
            
            # Devices Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    serial_number TEXT NOT NULL UNIQUE,
                    model TEXT NOT NULL,
                    init_date TEXT,
                    client_id INTEGER,
                    FOREIGN KEY (client_id) REFERENCES users (id)
                );
            ''')

            # Services Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_serial TEXT NOT NULL,
                    start_date TEXT,
                    end_date TEXT,
                    service_type TEXT,
                    description TEXT,
                    FOREIGN KEY (device_serial) REFERENCES devices (serial_number)
                );
            ''')
            
            conn.commit()
            print("Database tables checked/created successfully.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
        finally:
            conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password, role):
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        password_hash = hash_password(password)
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                       (username, password_hash, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.Error as e:
        print(f"Error adding user: {e}")
        return False
    finally:
        conn.close()

def verify_user(username, password, role):
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        password_hash = hash_password(password)
        cursor.execute("SELECT * FROM users WHERE username = ? AND password_hash = ? AND role = ?",
                       (username, password_hash, role))
        user = cursor.fetchone()
        return user is not None
    except sqlite3.Error as e:
        print(f"Error verifying user: {e}")
        return False
    finally:
        conn.close()

def get_user_id(username):
    """Helper to get user ID from username."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def get_all_clients():
    """Returns a list of usernames for users with role 'Client'."""
    conn = connect_db()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE role = 'Client'")
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()

def get_clients_list():
    """Fetches all clients with ID, username and role."""
    conn = connect_db()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users WHERE role = 'Client'")
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error fetching clients: {e}")
        return []
    finally:
        conn.close()

def update_client(user_id, username, password=None):
    """Updates client username and optionally password."""
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        if password:
            password_hash = hash_password(password)
            cursor.execute("UPDATE users SET username = ?, password_hash = ? WHERE id = ?", 
                           (username, password_hash, user_id))
        else:
            cursor.execute("UPDATE users SET username = ? WHERE id = ?", 
                           (username, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating client: {e}")
        return False
    finally:
        conn.close()

def delete_client(user_id):
    """Deletes a client and their associated devices."""
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting client: {e}")
        return False
    finally:
        conn.close()

def add_device(serial, model, init_date, client_username):
    """Adds a new device linked to a client."""
    conn = connect_db()
    if conn is None: return False
    try:
        client_id = get_user_id(client_username)
        if not client_id:
            print(f"Client {client_username} not found.")
            return False

        cursor = conn.cursor()
        cursor.execute("INSERT INTO devices (serial_number, model, init_date, client_id) VALUES (?, ?, ?, ?)",
                       (serial, model, init_date, client_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error adding device: {e}")
        return False
    finally:
        conn.close()

def update_device(old_serial, new_serial, model, init_date, client_username):
    """Updates an existing device's information."""
    conn = connect_db()
    if conn is None: return False
    try:
        client_id = get_user_id(client_username)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE devices 
            SET serial_number = ?, model = ?, init_date = ?, client_id = ?
            WHERE serial_number = ?
        ''', (new_serial, model, init_date, client_id, old_serial))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating device: {e}")
        return False
    finally:
        conn.close()

def get_devices():
    """Fetches all devices with their associated client username."""
    conn = connect_db()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = '''
            SELECT d.serial_number, d.model, d.init_date, u.username 
            FROM devices d
            LEFT JOIN users u ON d.client_id = u.id
        '''
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error fetching devices: {e}")
        return []
    finally:
        conn.close()

def add_service(serial, start, end, service_type, description):
    """Adds a new service record for a specific device."""
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO services (device_serial, start_date, end_date, service_type, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (serial, start, end, service_type, description))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error adding service: {e}")
        return False
    finally:
        conn.close()

def get_service_history(serial):
    """Fetches service history for a specific device."""
    conn = connect_db()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT start_date, end_date, service_type, description 
            FROM services 
            WHERE device_serial = ?
            ORDER BY start_date DESC
        ''', (serial,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error fetching service history: {e}")
        return []
    finally:
        conn.close()