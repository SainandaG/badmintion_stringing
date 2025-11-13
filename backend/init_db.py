import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASS = os.getenv("NEO4J_PASS")

driver = GraphDatabase.driver(URI, auth=(USER, PASS))

def init_database():
    with driver.session() as session:
        # Create constraints (optional but recommended)
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Customer) REQUIRE c.name IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Agent) REQUIRE a.agent_id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (o:Order) REQUIRE o.order_id IS UNIQUE")
        
        # Create sample customer
        session.run("""
            MERGE (c:Customer {name: 'John Doe', phone: '1234567890'})
        """)
        
        # Create sample racket
        session.run("""
            MATCH (c:Customer {name: 'John Doe'})
            MERGE (r:Racket {racket_id: 'R001', brand: 'Yonex', model: 'Astrox 99'})
            MERGE (c)-[:OWNS]->(r)
        """)
        
        # Create sample order
        session.run("""
            MATCH (c:Customer {name: 'John Doe'})
            MATCH (r:Racket {racket_id: 'R001'})
            MERGE (o:Order {
                order_id: 'ORD001',
                status: 'pending',
                issue: 'String replacement',
                created_at: datetime()
            })
            MERGE (c)-[:PLACED]->(o)
            MERGE (o)-[:RELATES_TO]->(r)
        """)
        
        # Create sample location
        session.run("""
            MATCH (o:Order {order_id: 'ORD001'})
            MERGE (l:Location {
                address: 'Hyderabad, India',
                lat: 17.385,
                lon: 78.4867
            })
            MERGE (o)-[:DELIVERED_TO]->(l)
        """)
        
        # Create sample agent
        session.run("""
            MERGE (a:Agent {
                agent_id: 'A001',
                name: 'Ravi Kumar',
                phone: '9876543210',
                status: 'available'
            })
        """)
        
        print("✅ Database initialized with sample data!")

if __name__ == "__main__":
    init_database()
    driver.close()