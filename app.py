import streamlit as st
import webbrowser
import matplotlib.pyplot as plt
from ticketing_functions import *
from db_operations import get_cursor

cursor, conn = get_cursor()

# App Layout
st.set_page_config(page_title="ICT Support Ticketing System", page_icon="🎫")

# Button to navigate to the external system
if st.button("Go to Main page"):
    # Open the URL using the default web browser
    webbrowser.open("http://localhost/fuelmanager/main.php")

st.title("ICT Support Ticketing System")

# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

# Display the notification icon with pending tickets count
if st.session_state.logged_in:
    pending_tickets_count = get_pending_tickets_count(st.session_state.role, st.session_state.username)
    
    # Sidebar notification icon
    notification_icon = "🔔"  # Notification bell emoji
    st.sidebar.markdown(f"{notification_icon} **Pending Tickets**: {pending_tickets_count}")

# Login / Sign up
if not st.session_state.logged_in:
    st.subheader("Login or Sign Up")
    
    option = st.radio("Choose an option", ("Login", "Sign Up"))
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if option == "Sign Up":
        role = st.selectbox("Select Role", ("user", "admin"))
        sign_up_button = st.button("Sign Up")
        
        if sign_up_button:
            sign_up(username, password, role)
            st.success("User created successfully. Please log in.")
    
    login_button = st.button("Login")
    
    if login_button:
        role = login(username, password)
        if role:
            st.session_state.logged_in = True
            st.session_state.role = role
            st.session_state.username = username
            st.success(f"Welcome, {username}! Logged in as {role.capitalize()}.")
        else:
            st.error("Invalid username or password.")
else:
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False}))
    
    if st.session_state.role == "user":
        st.subheader("Submit a Support Ticket")

        with st.form("ticket_form"):
            issue = st.text_area("Describe the issue")
            priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            submitted = st.form_submit_button("Submit")

        if submitted:
            add_ticket(issue, priority, st.session_state.username)
            st.success("Ticket submitted successfully!")

        st.subheader("Your Tickets")
        date_filter = st.selectbox("Filter Tickets by", ["All", "Daily", "Weekly", "Monthly"])
        user_tickets = get_tickets("user", st.session_state.username, date_filter)
        st.dataframe(user_tickets, use_container_width=True, height=300)  # Added scrollable height

    elif st.session_state.role == "admin":
        st.subheader(f"Welcome, Admin {st.session_state.username}!")
        
        # Display resolved ticket count for the admin
        cursor.execute('''
            SELECT COUNT(*) FROM tickets WHERE resolved_by = %s
        ''', (st.session_state.username,))
        resolved_count = cursor.fetchone()[0]
        st.write(f"You have resolved {resolved_count} ticket(s).")
        
        st.subheader("All Tickets")
        date_filter = st.selectbox("Filter Tickets by", ["All", "Daily", "Weekly", "Monthly"])
        tickets = get_tickets("admin", st.session_state.username, date_filter)
        
        if not tickets.empty:
            open_tickets = tickets[tickets["Status"] != "Closed"]
            
            st.dataframe(tickets, use_container_width=True, height=300)  # Added scrollable height
            
            # Display detailed information only for open tickets
            for idx, row in open_tickets.iterrows():
                st.markdown(f"**Ticket ID**: {row['ID']} | **Status**: {row['Status']} | **Priority**: {row['Priority']}")
                st.markdown(f"**Issue**: {row['Issue']}")
                st.markdown(f"**Submitted By**: {row['Submitted By']} | **Date Submitted**: {row['Date Submitted']}")
                st.markdown(f"**Resolved By**: {row['Resolved By']}")  # Display the resolved_by field

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Mark as In Progress ({row['ID']})"):
                        update_ticket_status(row['ID'], "In Progress", admin_username=st.session_state.username)
                        st.rerun()
                with col2:
                    if st.button(f"Mark as Closed ({row['ID']})"):
                        update_ticket_status(row['ID'], "Closed", admin_username=st.session_state.username)
                        st.rerun()
                st.markdown("---")
        else:
            st.write("No tickets available.")
        
        # Ticket Analytics
        st.subheader("Ticket Analytics")
        analytics_df = get_ticket_analytics()

        # Create side-by-side bar charts
        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots(figsize=(6, 4))  
            ax.bar(analytics_df["Status"], analytics_df["Count"])
            ax.set_xlabel("Ticket Status")
            ax.set_ylabel("Count")
            ax.set_title("Tickets by Status")
            st.pyplot(fig)

        # Admin-specific ticket analytics
        with col2:
            admin_analytics_df = get_admin_ticket_analytics(st.session_state.username)
            fig2, ax2 = plt.subplots(figsize=(6, 4))  
            ax2.bar(admin_analytics_df["Status"], admin_analytics_df["Count"])
            ax2.set_xlabel("Ticket Status")
            ax2.set_ylabel("Count")
            ax2.set_title(f"Tickets Resolved by {st.session_state.username}")
            st.pyplot(fig2)

        # New table: Display users and their ticket counts
        st.subheader("Ticket Submission by Users")
        user_ticket_counts_df = get_user_ticket_count()
        st.dataframe(user_ticket_counts_df, use_container_width=True, height=300)  # Scrolling data frame
