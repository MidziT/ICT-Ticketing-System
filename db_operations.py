import pymysql
import datetime
from hashlib import sha256

# MySQL database connection details (adjust these based on your local XAMPP setup)
DB_HOST = "localhost"
DB_USER = "root"        # Default MySQL username in XAMPP
DB_PASSWORD = ""        # Default is empty unless you set a password for MySQL
DB_NAME = "ticketing_system"

# Connect to the MySQL database
conn = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
)
cursor = conn.cursor()

# Create tables if they don't exist (including the 'resolved_by' column)
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(255) PRIMARY KEY,
    password VARCHAR(255),
    role VARCHAR(50)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS tickets (
    id VARCHAR(50) PRIMARY KEY,
    issue TEXT,
    priority VARCHAR(20),
    status VARCHAR(20),
    date_submitted DATE,
    submitted_by VARCHAR(255),
    resolved_by VARCHAR(255),  -- New column to track the admin who resolved the ticket
    FOREIGN KEY (submitted_by) REFERENCES users(username)
)
''')

def get_cursor():
    return cursor, conn
