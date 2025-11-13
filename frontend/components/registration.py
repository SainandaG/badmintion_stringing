import streamlit as st
from backend.services.neo4j_client import neo4j_client
from datetime import datetime
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
HEADERS = {"User-Agent": "badminton_agent_app"}


# ----------------- HELPER FUNCTIONS -----------------
def get_coordinates(address):
    """Get lat/lon from address using free OSM Nominatim API."""
    try:
        params = {"q": address, "format": "json", "limit": 1}
        resp = requests.get(NOMINATIM_URL, params=params, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        if data:
            lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
            return lat, lon
        return None, None
    except:
        return None, None


def get_city(lat, lon):
    """Get city from coordinates using free OSM Nominatim API."""
    try:
        params = {"lat": lat, "lon": lon, "format": "json"}
        resp = requests.get(REVERSE_URL, params=params, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        address = data.get("address", {})
        return address.get("city") or address.get("town") or address.get("village") or "Unknown"
    except:
        return "Unknown"


# ----------------- REGISTRATION FUNCTIONS -----------------
def register_agent():
    st.subheader("Register Agent")
    agent_id = st.text_input("Agent ID")
    name = st.text_input("Agent Name")
    status = st.selectbox("Status", ["active", "inactive"])
    address = st.text_input("Address (optional)")

    if st.button("Add Agent"):
        lat, lon = get_coordinates(address) if address else (None, None)
        city = get_city(lat, lon) if lat and lon else None
        timestamp = datetime.now().isoformat()
        neo4j_client.create_agent(agent_id, name, status, lat, lon)
        st.success(f"Agent {name} added! City: {city or 'Unknown'}, Timestamp: {timestamp}")


def register_customer():
    st.subheader("Register Customer")
    customer_id = st.text_input("Customer ID")
    name = st.text_input("Customer Name")
    address = st.text_input("Address")
    if st.button("Add Customer"):
        lat, lon = get_coordinates(address)
        city = get_city(lat, lon) if lat and lon else None
        timestamp = datetime.now().isoformat()
        # Create a Customer node
        with neo4j_client.driver.session() as session:
            session.run(
                "MERGE (c:Customer {customer_id:$id}) "
                "SET c.name=$name, c.address=$address, c.lat=$lat, c.lon=$lon, c.city=$city, c.created_at=$ts",
                id=customer_id, name=name, address=address, lat=lat, lon=lon, city=city, ts=timestamp
            )
        st.success(f"Customer {name} added! City: {city or 'Unknown'}, Timestamp: {timestamp}")


def register_order():
    st.subheader("Register Order")
    order_id = st.text_input("Order ID")
    customer_id = st.text_input("Customer ID")
    agent_id = st.text_input("Agent ID (optional)")
    address = st.text_input("Delivery Address")
    if st.button("Add Order"):
        lat, lon = get_coordinates(address)
        city = get_city(lat, lon) if lat and lon else None
        timestamp = datetime.now().isoformat()
        neo4j_client.create_order(order_id, "Customer-"+customer_id, address, lat, lon)
        if agent_id:
            neo4j_client.assign_agent_to_order(order_id, agent_id)
        st.success(f"Order {order_id} added! City: {city or 'Unknown'}, Timestamp: {timestamp}")


def register_location():
    st.subheader("Register Court / Location")
    name = st.text_input("Location Name")
    address = st.text_input("Address")
    if st.button("Add Location"):
        lat, lon = get_coordinates(address)
        city = get_city(lat, lon) if lat and lon else None
        timestamp = datetime.now().isoformat()
        neo4j_client.create_location(name, lat, lon)
        st.success(f"Location {name} added! City: {city or 'Unknown'}, Timestamp: {timestamp}")


# ----------------- DISPLAY TABLES -----------------
def show_tables():
    with neo4j_client.driver.session() as session:
        st.subheader("Agents")
        agents = session.run("MATCH (a:Agent) RETURN a.agent_id AS ID, a.name AS Name, a.status AS Status, a.lat AS Lat, a.lon AS Lon").data()
        st.dataframe(agents)

        st.subheader("Customers")
        customers = session.run("MATCH (c:Customer) RETURN c.customer_id AS ID, c.name AS Name, c.address AS Address, c.city AS City, c.lat AS Lat, c.lon AS Lon, c.created_at AS Timestamp").data()
        st.dataframe(customers)

        st.subheader("Orders")
        orders = session.run("MATCH (o:Order) RETURN o.order_id AS ID, o.customer_name AS Customer, o.address AS Address, o.lat AS Lat, o.lon AS Lon, o.status AS Status").data()
        st.dataframe(orders)

        st.subheader("Locations")
        locations = session.run("MATCH (l:Location) RETURN l.name AS Name, l.lat AS Lat, l.lon AS Lon").data()
        st.dataframe(locations)
