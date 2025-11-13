from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class Neo4jClient:
    def __init__(self):
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASS")

        if not uri or not user or not password:
            raise ValueError("❌ Neo4j credentials not loaded. Check your .env file.")

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
                "SET o.customer_name=$customer_name, o.address=$address, "
                "o.lat=$lat, o.lon=$lon, o.status='pending'",
                order_id=order_id,
                customer_name=customer_name,
                address=address,
                lat=lat,
                lon=lon
            )

    # ✅ NEW: Create or update a brand
    def create_brand(self, brand_name, **properties):
        """
        Create or update a brand node
        """
        with self.driver.session() as session:
            query = """
            MERGE (b:Brand {name: $brand_name})
            SET b += $properties
            RETURN b
            """
            session.run(query, brand_name=brand_name, properties=properties)

    # ✅ NEW: Log an issue for a brand
    def log_brand_issue(self, brand_name, issue_type, severity="medium", **metadata):
        """
        Log an issue for a specific brand and create/update the HAS_ISSUE relationship
        """
        with self.driver.session() as session:
            query = """
            MERGE (b:Brand {name: $brand_name})
            MERGE (i:Issue {type: $issue_type})
            SET i.severity = $severity,
                i.last_seen = datetime()
            MERGE (b)-[r:HAS_ISSUE]->(i)
            ON CREATE SET 
                r.frequency = 1, 
                r.first_seen = datetime(),
                r.metadata = $metadata
            ON MATCH SET 
                r.frequency = r.frequency + 1, 
                r.last_seen = datetime(),
                r.metadata = $metadata
            RETURN b, r, i
            """
            result = session.run(
                query, 
                brand_name=brand_name, 
                issue_type=issue_type,
                severity=severity,
                metadata=metadata
            )
            return result.single()

    # ✅ NEW: Get all issues for a brand
    def get_brand_issues(self, brand_name):
        """
        Retrieve all issues associated with a brand
        """
        with self.driver.session() as session:
            query = """
            MATCH (b:Brand {name: $brand_name})-[r:HAS_ISSUE]->(i:Issue)
            RETURN b.name as brand, 
                   i.type as issue_type, 
                   i.severity as severity,
                   r.frequency as frequency,
                   r.first_seen as first_seen,
                   r.last_seen as last_seen
            ORDER BY r.frequency DESC
            """
            result = session.run(query, brand_name=brand_name)
            return [dict(record) for record in result]

    # ✅ NEW: Get all brands with issue counts
    def get_all_brands_with_issues(self):
        """
        Get all brands and their issue statistics
        """
        with self.driver.session() as session:
            query = """
            MATCH (b:Brand)-[r:HAS_ISSUE]->(i:Issue)
            RETURN b.name as brand,
                   count(i) as total_issues,
                   sum(r.frequency) as total_occurrences,
                   collect({
                       type: i.type, 
                       frequency: r.frequency,
                       severity: i.severity
                   }) as issues
            ORDER BY total_occurrences DESC
            """
            result = session.run(query)
            return [dict(record) for record in result]

neo4j_client = Neo4jClient()