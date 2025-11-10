from neo4j import GraphDatabase
import os

class Neo4jClient:
    def __init__(self):
        # Use environment variables for Aura connection
        uri = os.getenv("NEO4J_URI", "neo4j+s://1d83f2f7.databases.neo4j.io")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASS", "dOR8KmZJLPfXoupu4s3TzbphGmyNiJUJ0cJEtSV0s74")

        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_location(self, name, lat, lon):
        with self.driver.session() as session:
            session.run(
                "MERGE (l:Location {name:$name}) "
                "SET l.lat=$lat, l.lon=$lon",
                name=name, lat=lat, lon=lon
            )

    def create_agent(self, agent_id, name, status, lat, lon):
        with self.driver.session() as session:
            session.run(
                "MERGE (a:Agent {agent_id:$agent_id}) "
                "SET a.name=$name, a.status=$status, a.lat=$lat, a.lon=$lon",
                agent_id=agent_id, name=name, status=status, lat=lat, lon=lon
            )

    def assign_agent_to_order(self, order_id, agent_id):
        with self.driver.session() as session:
            session.run(
                "MATCH (a:Agent {agent_id:$agent_id}), (o:Order {order_id:$order_id}) "
                "MERGE (a)-[:ASSIGNED_TO]->(o)",
                agent_id=agent_id, order_id=order_id
            )

    def create_order(self, order_id, customer_name, address, lat, lon):
        with self.driver.session() as session:
            session.run(
                "MERGE (o:Order {order_id:$order_id}) "
                "SET o.customer_name=$customer_name, o.address=$address, o.lat=$lat, o.lon=$lon, o.status='pending'",
                order_id=order_id, customer_name=customer_name, address=address, lat=lat, lon=lon
            )

neo4j_client = Neo4jClient()
