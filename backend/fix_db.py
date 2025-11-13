import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASS = os.getenv("NEO4J_PASS")

driver = GraphDatabase.driver(URI, auth=(USER, PASS))

def fix_database():
    with driver.session() as session:
        # Assign agent to existing order
        session.run("""
            MATCH (a:Agent {agent_id: 'A001'})
            MATCH (o:Order {order_id: 'ORD001'})
            MERGE (a)-[:ASSIGNED_TO]->(o)
        """)
        
        # Add timestamp property to Order if missing
        session.run("""
            MATCH (o:Order)
            WHERE o.timestamp IS NULL
            SET o.timestamp = o.created_at
        """)
        
        print("✅ Database fixed!")
        print("✅ Added ASSIGNED_TO relationship")
        print("✅ Added timestamp property")
        
        # Verify
        result = session.run("CALL db.relationshipTypes()")
        rels = [record[0] for record in result]
        print("\n🔗 Updated Relationship Types:")
        print(rels)

if __name__ == "__main__":
    fix_database()
    driver.close()