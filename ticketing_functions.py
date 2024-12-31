import datetime
import pandas as pd
from hashlib import sha256
from db_operations import get_cursor
import pymysql
import streamlit as st
from datetime import timedelta  # <-- Add this import

cursor, conn = get_cursor()

# Function to add a user (Sign-up)
def sign_up(username, password, role):
    hashed_password = sha256(password.encode()).hexdigest()
    try:
        cursor.execute('INSERT INTO users (username, password, role) VALUES (%s, %s, %s)', 
                       (username, hashed_password, role))
        conn.commit()
        st.success("User signed up successfully!")
    except pymysql.MySQLError as e:
        st.error(f"Error: {e.args[1]}")

# Function to validate login
def login(username, password):
    cursor.execute('SELECT password, role FROM users WHERE username = %s', (username,))
    result = cursor.fetchone()
    if result:
        stored_password, role = result
        if sha256(password.encode()).hexdigest() == stored_password:
            return role
    return None

# Add a new ticket
def add_ticket(issue, priority, submitted_by):
    ticket_id = f"TICKET-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    date_submitted = datetime.date.today().strftime('%Y-%m-%d')
    cursor.execute('''
        INSERT INTO tickets (id, issue, priority, status, date_submitted, submitted_by)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (ticket_id, issue, priority, 'Open', date_submitted, submitted_by))
    conn.commit()
    st.success(f"Ticket {ticket_id} added successfully!")

# Get tickets (for user or admin) with date filter
def get_tickets(role, username, date_filter=None):
    query = 'SELECT id, issue, priority, status, date_submitted, submitted_by, resolved_by FROM tickets'
    
    if date_filter:
        if date_filter == 'Daily':
            start_date = (datetime.date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
            query += f' WHERE date_submitted >= "{start_date}"'
        elif date_filter == 'Weekly':
            start_date = (datetime.date.today() - timedelta(weeks=1)).strftime('%Y-%m-%d')
            query += f' WHERE date_submitted >= "{start_date}"'
        elif date_filter == 'Monthly':
            start_date = (datetime.date.today() - timedelta(weeks=4)).strftime('%Y-%m-%d')
            query += f' WHERE date_submitted >= "{start_date}"'

    if role == 'user':
        if 'WHERE' in query:
            query += f' AND submitted_by = "{username}"'
        else:
            query += f' WHERE submitted_by = "{username}"'
    
    cursor.execute(query)
    tickets = cursor.fetchall()
    return pd.DataFrame(tickets, columns=["ID", "Issue", "Priority", "Status", "Date Submitted", "Submitted By", "Resolved By"])

# Update ticket status and resolved_by field
def update_ticket_status(ticket_id, status, admin_username=None):
    if status in ["Closed", "In Progress"] and admin_username:
        cursor.execute('''
            UPDATE tickets
            SET status = %s, resolved_by = %s
            WHERE id = %s
        ''', (status, admin_username, ticket_id))
    else:
        cursor.execute('UPDATE tickets SET status = %s WHERE id = %s', (status, ticket_id))
    conn.commit()

# Get ticket analytics
def get_ticket_analytics():
    cursor.execute('SELECT status, COUNT(*) FROM tickets GROUP BY status')
    analytics = cursor.fetchall()
    return pd.DataFrame(analytics, columns=["Status", "Count"])

def get_admin_ticket_analytics(admin_username):
    cursor.execute('SELECT status, COUNT(*) FROM tickets WHERE resolved_by = %s GROUP BY status', (admin_username,))
    analytics = cursor.fetchall()
    return pd.DataFrame(analytics, columns=["Status", "Count"])

def get_user_ticket_count():
    cursor.execute('''
        SELECT submitted_by, COUNT(*) 
        FROM tickets 
        GROUP BY submitted_by
    ''')
    result = cursor.fetchall()
    return pd.DataFrame(result, columns=["User", "Total Tickets"])

def get_pending_tickets_count(role, username):
    if role == "admin":
        cursor.execute('SELECT COUNT(*) FROM tickets WHERE status IN ("Open", "In Progress")')
    else:
        cursor.execute('SELECT COUNT(*) FROM tickets WHERE status IN ("Open", "In Progress") AND submitted_by = %s', (username,))
    count = cursor.fetchone()[0]
    return count

# Streamlit UI
def main():
    st.title("Ticket Management System")

    # Choose action: Login or Sign-up
    action = st.sidebar.selectbox("Select Action", ["Login", "Sign Up"])
    
    if action == "Login":
        # Login Form
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            role = login(username, password)
            if role:
                st.success(f"Logged in as {role}")
                # After successful login, show ticket options
                show_ticket_options(role, username)
            else:
                st.error("Invalid credentials")
    
    elif action == "Sign Up":
        # Sign Up Form
        username = st.text_input("New Username")
        password = st.text_input("New Password", type="password")
        role = st.selectbox("Role", ["user", "admin"])
        
        if st.button("Sign Up"):
            sign_up(username, password, role)

def show_ticket_options(role, username):
    st.subheader("Ticket Options")
    action = st.selectbox("Choose Action", ["Add Ticket", "View Tickets", "Update Ticket Status"])
    
    if action == "Add Ticket":
        issue = st.text_area("Describe the issue")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        
        if st.button("Submit Ticket"):
            add_ticket(issue, priority, username)
    
    elif action == "View Tickets":
        date_filter = st.selectbox("Filter by Date", ["All", "Daily", "Weekly", "Monthly"])
        tickets_df = get_tickets(role, username, date_filter)
        st.dataframe(tickets_df)
    
    elif action == "Update Ticket Status":
        ticket_id = st.text_input("Enter Ticket ID")
        status = st.selectbox("Update Status", ["Open", "In Progress", "Closed"])
        
        if role == "admin":
            admin_username = st.text_input("Admin Username")
            if st.button("Update Status"):
                update_ticket_status(ticket_id, status, admin_username)
        else:
            if st.button("Update Status"):
                update_ticket_status(ticket_id, status)

if __name__ == "__main__":
    main()
