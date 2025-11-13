import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASS = os.getenv("NEO4J_PASS")

print(f"Connecting to: {URI}")
print(f"User: {USER}")

try:
    driver = GraphDatabase.driver(URI, auth=(USER, PASS))
    with driver.session() as session:
        result = session.run("RETURN 1 as test")
        print(f"✅ Neo4j connected successfully!")
        print(f"Test query result: {result.single()['test']}")
        
        # Try to create a test Issue node
        session.run("""
            MERGE (i:Issue {type: 'test_issue'})
            SET i.frequency = 1, i.last_seen = datetime()
        """)
        print("✅ Test Issue node created!")
        
        # Verify it exists
        result = session.run("MATCH (i:Issue {type: 'test_issue'}) RETURN i")
        node = result.single()
        if node:
            print(f"✅ Test Issue node found: {dict(node['i'])}")
        
    driver.close()
except Exception as e:
    print(f"❌ Error: {e}")