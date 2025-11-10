import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st

# --- Import your modules ---
from components.route_visualizer import visualize_routes
from components.analytics_dashboard import show_analytics
from components.registration import register_agent, register_order, show_tables
from components.customer_module import customer_dashboard

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="🏸 Badminton Agent Pro",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Sidebar ---
logo_path = r"D:\badminton_agent_1\frontend\assets\logo.png"
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_container_width=True)
else:
    st.sidebar.warning("⚠️ Logo not found. Please place 'logo.png' in the assets folder.")

st.sidebar.title("🏸 Badminton Agent Pro")

menu_options = ["Home", "Routes", "Analytics", "Registration", "Customer"]
choice = st.sidebar.radio("Navigation", menu_options)

# --- Home Page ---
if choice == "Home":
    banner_path = r"D:\badminton_agent_1\frontend\assets\banner.png"
    if os.path.exists(banner_path):
        st.image(banner_path, use_container_width=True)

    st.markdown("<h1 style='text-align: center;'>Welcome to Badminton Agent Pro 🏸</h1>", unsafe_allow_html=True)
    st.markdown("""
        <p style='text-align: center; font-size:18px;'>
        Manage rackets, repairs, orders, agents, and visualize optimal routes with ease.<br>
        AI-powered customer support is included for customer queries.
        </p>
    """, unsafe_allow_html=True)

# --- Routes Visualizer ---
elif choice == "Routes":
    st.subheader("🚀 Routes Visualizer")
    st.markdown("Visualize agent delivery routes, optimized for efficiency.")
    visualize_routes()

# --- Analytics Dashboard ---
elif choice == "Analytics":
    st.subheader("📊 Analytics Dashboard")
    st.markdown("Track performance, orders, and agent metrics in real-time.")
    show_analytics()

# --- Registration Module ---
elif choice == "Registration":
    st.subheader("📝 Registration & Tables")
    tab = st.radio("Choose entity", ["Agent", "Order", "Show Tables"])
    
    if tab == "Agent":
        register_agent()
    elif tab == "Order":
        register_order()
    elif tab == "Show Tables":
        show_tables()

# --- Customer Module ---
elif choice == "Customer":
    st.subheader("🙋 Customer Panel")
    st.markdown("Add rackets, request repairs, view orders, or chat with AI support.")
    customer_dashboard()

# --- Footer ---
st.markdown("""
    <hr style='border:1px solid #eee'>
    <p style='text-align:center; color: gray;'>
    Badminton Agent Pro © 2025 | Designed for efficient racket & repair management
    </p>
""", unsafe_allow_html=True)
