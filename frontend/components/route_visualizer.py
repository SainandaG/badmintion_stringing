import streamlit as st
import pandas as pd
from backend.services.neo4j_client import neo4j_client
import pydeck as pdk

def visualize_routes():
    st.title("🚀 Routes Visualizer")
    st.write("Visualize agent delivery routes, optimized for efficiency.")

    try:
        with neo4j_client.driver.session() as session:
            # Fetch orders with location and agent info
            query = """
            MATCH (o:Order)-[:DELIVERED_TO]->(l:Location)
            OPTIONAL MATCH (a:Agent)-[:ASSIGNED_TO]->(o)
            OPTIONAL MATCH (c:Customer)-[:PLACED]->(o)
            RETURN o.order_id AS order_id, o.status AS status,
                   o.issue AS issue, l.address AS address, l.lat AS lat, l.lon AS lon,
                   a.name AS agent, c.name AS customer
            """
            result = session.run(query)
            df = pd.DataFrame(result.data())

        if df.empty:
            st.info("No delivery data available yet.")
            return

        # Drop rows without coordinates
        df_map = df.dropna(subset=["lat", "lon"])

        # Assign different colors to agents
        agents = df_map['agent'].dropna().unique()
        color_map = {agent: [int(i*50)%256, int(i*80)%256, int(i*110)%256] for i, agent in enumerate(agents)}
        df_map['color'] = df_map['agent'].apply(lambda x: color_map.get(x, [100,100,100]))

        # Pydeck map
        st.subheader("📍 Delivery Routes Map")
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_map,
            get_position='[lon, lat]',
            get_color='color',
            get_radius=50,
            pickable=True
        )

        # Tooltip
        tooltip = {
            "html": "<b>Order ID:</b> {order_id} <br/>"
                    "<b>Customer:</b> {customer} <br/>"
                    "<b>Agent:</b> {agent} <br/>"
                    "<b>Issue:</b> {issue} <br/>"
                    "<b>Address:</b> {address}",
            "style": {"backgroundColor": "white", "color": "black"}
        }

        view_state = pdk.ViewState(
            latitude=df_map['lat'].mean(),
            longitude=df_map['lon'].mean(),
            zoom=12,
            pitch=0
        )

        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip=tooltip
        )

        st.pydeck_chart(r)

        # Optional: Show order table below map
        st.subheader("📋 Orders Table")
        st.dataframe(df[['order_id','status','agent','customer','issue','address']])

    except Exception as e:
        st.error(f"Error fetching route data: {e}")
