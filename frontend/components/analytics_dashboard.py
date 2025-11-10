import streamlit as st
import plotly.express as px
import pandas as pd
from backend.services.neo4j_client import neo4j_client

def show_analytics():
    st.title("📊 Analytics Dashboard")
    st.write("Track performance, orders, and agent metrics in real-time.")

    try:
        with neo4j_client.driver.session() as session:
            # Deliveries per agent
            result = session.run(
                "MATCH (a:Agent)-[:ASSIGNED_TO]->(o:Order) "
                "RETURN a.name AS agent, count(o) AS deliveries"
            )
            data = pd.DataFrame(result.data())
            if not data.empty:
                fig = px.bar(data, x="agent", y="deliveries", title="Deliveries per Agent")
                st.plotly_chart(fig)
            else:
                st.info("No delivery data available yet.")

            # Orders table with coordinates
            order_result = session.run(
                """
                MATCH (o:Order)-[:DELIVERED_TO]->(l:Location)
                OPTIONAL MATCH (a:Agent)-[:ASSIGNED_TO]->(o)
                RETURN o.order_id AS order_id, o.status AS status, o.issue AS issue,
                       l.address AS address, l.lat AS lat, l.lon AS lon,
                       a.name AS agent
                ORDER BY o.timestamp DESC
                LIMIT 50
                """
            )
            orders = pd.DataFrame(order_result.data())
            if not orders.empty:
                st.subheader("🟢 Update Delivery Status")
                for idx, row in orders.iterrows():
                    new_status = st.selectbox(
                        f"Order ID: {row['order_id']} | Status: {row['status']} | Issue: {row['issue']} | Address: {row['address']}",
                        ["pending", "in_progress", "completed"],
                        index=["pending","in_progress","completed"].index(row['status'])
                    )
                    if st.button(f"Update {row['order_id']}"):
                        session.run(
                            "MATCH (o:Order {order_id:$order_id}) SET o.status=$status",
                            order_id=row['order_id'], status=new_status
                        )
                        st.success(f"Order {row['order_id']} status updated to {new_status}")

                # Map visualization
                map_df = orders.dropna(subset=['lat','lon'])
                if not map_df.empty:
                    st.subheader("🗺️ Delivery Map")
                    st.map(map_df[['lat','lon']])
            else:
                st.info("No delivery data available yet.")

    except Exception as e:
        st.error(f"Error connecting to Neo4j: {e}")
