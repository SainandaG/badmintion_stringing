import streamlit as st
from datetime import datetime
from backend.services.neo4j_client import neo4j_client
from backend.services.geocode_client import geocode_address
from components.llm_agent import llm_client  # ✅ Groq client
import os

# =====================================================
# CUSTOMER DASHBOARD (Rackets, Repairs, Orders, AI Chat)
# =====================================================

def customer_dashboard():
    st.title("🏸 Customer Dashboard")
    customer_name = st.text_input("Enter your name")

    if not customer_name:
        st.info("Please enter your name to continue.")
        return

    tabs = st.tabs(["Add Racket", "Request Repair", "View Orders", "AI Chat"])
    with tabs[0]:
        add_racket(customer_name)
    with tabs[1]:
        request_repair(customer_name)
    with tabs[2]:
        view_orders(customer_name)
    with tabs[3]:
        ai_chat(customer_name)


# -----------------------------------------------------
#  ADD RACKET SECTION
# -----------------------------------------------------
def add_racket(customer_name):
    st.subheader("Register Racket")
    brand = st.text_input("Brand", key="brand")
    rtype = st.text_input("Type (e.g., badminton, tennis)", key="type")
    tension = st.text_input("String tension", key="tension")

    if st.button("Add Racket", key="add_racket_btn"):
        if not brand or not rtype or not tension:
            st.warning("Please fill all fields.")
            return

        racket_id = int(datetime.now().timestamp())

        with neo4j_client.driver.session() as session:
            session.run(
                """
                MERGE (c:Customer {name:$customer})
                MERGE (r:Racket {racket_id:$racket_id})
                SET r.brand=$brand, r.type=$rtype, r.tension=$tension
                MERGE (c)-[:HAS_RACKET]->(r)
                """,
                customer=customer_name,
                racket_id=racket_id,
                brand=brand,
                rtype=rtype,
                tension=tension,
            )

        st.success(f"✅ Racket '{brand}' added for {customer_name}")


# -----------------------------------------------------
#  REQUEST REPAIR SECTION
# -----------------------------------------------------
def request_repair(customer_name):
    st.subheader("Request Repair / Stringing")
    racket_id_input = st.text_input("Racket ID", key="repair_racket_id")
    issue = st.text_area("Describe the issue (stringing, frame, grip)", key="repair_issue")
    address = st.text_input("Delivery / Pickup Address", key="repair_address")

    if st.button("Submit Repair", key="submit_repair_btn"):
        if not racket_id_input.isdigit():
            st.warning("Racket ID must be numeric!")
            return
        if not issue or not address:
            st.warning("Please fill all fields.")
            return

        racket_id = int(racket_id_input)

        try:
            lat, lon, city = geocode_address(address)
        except Exception:
            st.warning("Could not geocode address. Please check format.")
            return

        order_id = int(datetime.now().timestamp())

        with neo4j_client.driver.session() as session:
            # Create Order and assign to Location
            session.run(
                """
                MERGE (c:Customer {name:$customer})
                MERGE (o:Order {order_id:$order_id})
                SET o.issue=$issue, o.status='pending', o.timestamp=$ts
                MERGE (c)-[:PLACED]->(o)
                MERGE (l:Location {address:$address})
                SET l.lat=$lat, l.lon=$lon
                MERGE (o)-[:DELIVERED_TO]->(l)
                WITH o
                MATCH (r:Racket {racket_id:$racket_id})
                MERGE (o)-[:RELATES_TO]->(r)
                """,
                customer=customer_name,
                order_id=order_id,
                issue=issue,
                address=address,
                lat=lat,
                lon=lon,
                ts=datetime.now().isoformat(),
                racket_id=racket_id,
            )

            # Auto-assign an active agent
            session.run(
                """
                MATCH (a:Agent {status:'active'})
                WITH a ORDER BY rand() LIMIT 1
                MATCH (o:Order {order_id:$order_id})
                MERGE (a)-[:ASSIGNED_TO]->(o)
                """,
                order_id=order_id,
            )

        st.success(f"🛠️ Repair order {order_id} submitted and assigned to an active agent.")


# -----------------------------------------------------
#  VIEW ORDERS SECTION
# -----------------------------------------------------
def view_orders(customer_name):
    st.subheader("Your Orders")
    with neo4j_client.driver.session() as session:
        result = session.run(
            """
            MATCH (c:Customer {name:$customer})-[:PLACED]->(o:Order)
            OPTIONAL MATCH (o)-[:RELATES_TO]->(r:Racket)
            OPTIONAL MATCH (o)-[:DELIVERED_TO]->(l:Location)
            OPTIONAL MATCH (a:Agent)-[:ASSIGNED_TO]->(o)
            RETURN o.order_id AS order_id, o.status AS status, o.issue AS issue,
                   r.brand AS brand, l.address AS address, l.lat AS lat, l.lon AS lon,
                   a.name AS agent
            """,
            customer=customer_name,
        )
        data = result.data()

        if data:
            for order in data:
                status_color = {
                    "pending": "🟠 Pending",
                    "completed": "🟢 Completed",
                    "in_progress": "🔵 In Progress",
                }.get(order["status"], order["status"])

                st.markdown(
                    f"""
                    <div style="border:1px solid #ccc; padding:10px; border-radius:8px; margin-bottom:8px;">
                        <b>Order ID:</b> {order['order_id']} <br>
                        <b>Status:</b> {status_color} <br>
                        <b>Racket Brand:</b> {order.get('brand', 'N/A')} <br>
                        <b>Issue:</b> {order['issue']} <br>
                        <b>Delivery Address:</b> {order.get('address','N/A')} <br>
                        <b>Coordinates:</b> {order.get('lat','')} , {order.get('lon','')} <br>
                        <b>Assigned Agent:</b> {order.get('agent','N/A')}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No orders found.")


# -----------------------------------------------------
#  AI CHAT SECTION (GROQ + RAG)
# -----------------------------------------------------
def ai_chat(customer_name):
    st.subheader("🤖 AI Support (Groq + Smart Memory)")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_area("Type your message here:", key="ai_input")

    col1, col2 = st.columns([4, 1])
    with col1:
        use_rag = st.checkbox("Use Smart Memory (RAG)", value=True)
    with col2:
        send_clicked = st.button("Send", key="ai_send_btn")

    if send_clicked and user_input.strip():
        # Save user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # Query Groq API
        with st.spinner("Thinking..."):
            try:
                answer = llm_client.chat(user_input, use_rag=use_rag)
            except Exception as e:
                answer = f"[Groq Error] {e}"

        # Save AI response
        st.session_state.chat_history.append({"role": "ai", "content": answer})

    # Display chat
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"**🧍 You:** {msg['content']}")
        else:
            st.markdown(f"**🤖 AI:** {msg['content']}")
