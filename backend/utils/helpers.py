# D:\badminton_agent_1\backend\utils\helpers.py

from math import radians, cos, sin, sqrt, atan2
from backend.services.neo4j_client import neo4j_client
from backend.services.geocode_client import geocode_address
from datetime import datetime, timedelta


# --------------------------
# Distance calculation (Haversine)
# --------------------------
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance in kilometers between two coordinates using Haversine formula.
    """
    R = 6371  # Radius of Earth in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    return distance


# --------------------------
# Assign nearest active agent to an order
# --------------------------
def assign_agent_to_order(order_id, order_lat, order_lon):
    """
    Assign nearest active agent to a new order based on coordinates.
    """
    with neo4j_client.driver.session() as session:
        # Get all active agents with location
        result = session.run(
            "MATCH (a:Agent {status:'active'})-[:LOCATED_AT]->(l:Location) "
            "RETURN a.agent_id AS agent_id, a.name AS name, l.lat AS lat, l.lon AS lon"
        )
        agents = result.data()
        if not agents:
            return None, "No active agents available"

        # Find nearest agent
        nearest = None
        min_distance = float('inf')
        for agent in agents:
            dist = calculate_distance(order_lat, order_lon, agent['lat'], agent['lon'])
            if dist < min_distance:
                min_distance = dist
                nearest = agent

        # Assign agent
        if nearest:
            session.run(
                "MATCH (o:Order {order_id:$order_id}), (a:Agent {agent_id:$agent_id}) "
                "MERGE (a)-[:ASSIGNED_TO]->(o)",
                order_id=order_id, agent_id=nearest['agent_id']
            )
            return nearest['name'], min_distance
        return None, None


# --------------------------
# ETA Calculation (simple)
# --------------------------
def estimate_eta(distance_km, speed_kmh=30):
    """
    Estimate ETA in minutes given distance in km and average speed in km/h.
    """
    if distance_km is None:
        return None
    hours = distance_km / speed_kmh
    eta_minutes = int(hours * 60)
    return eta_minutes


# --------------------------
# Create or get Location node
# --------------------------
def get_or_create_location(address):
    """
    Convert address to coordinates (lat/lon) and store as Location node in Neo4j.
    """
    try:
        lat, lon, city = geocode_address(address)
    except Exception as e:
        print(f"Error geocoding address {address}: {e}")
        return None, None

    with neo4j_client.driver.session() as session:
        session.run(
            "MERGE (l:Location {address:$address}) "
            "SET l.lat=$lat, l.lon=$lon",
            address=address, lat=lat, lon=lon
        )
    return lat, lon


# --------------------------
# Update Order Status
# --------------------------
def update_order_status(order_id, status="completed"):
    """
    Update order status and completed timestamp.
    """
    with neo4j_client.driver.session() as session:
        ts = datetime.now().isoformat()
        session.run(
            "MATCH (o:Order {order_id:$order_id}) "
            "SET o.status=$status, o.completed_at=$ts",
            order_id=order_id, status=status, ts=ts
        )


# --------------------------
# Fetch order + agent + location details
# --------------------------
def fetch_orders_with_agents():
    """
    Return list of orders with assigned agent and delivery coordinates.
    """
    with neo4j_client.driver.session() as session:
        result = session.run(
            "MATCH (o:Order)-[:DELIVERED_TO]->(l:Location) "
            "OPTIONAL MATCH (a:Agent)-[:ASSIGNED_TO]->(o) "
            "RETURN o.order_id AS order_id, o.status AS status, "
            "l.address AS address, l.lat AS lat, l.lon AS lon, "
            "a.name AS agent_name"
        )
        return result.data()


# --------------------------
# Route Sorting Helper
# --------------------------
def sort_orders_by_distance(agent_lat, agent_lon, orders):
    """
    Sort orders by distance from given agent coordinates.
    """
    for order in orders:
        order['distance'] = calculate_distance(agent_lat, agent_lon, order['lat'], order['lon'])
    return sorted(orders, key=lambda x: x['distance'])
