import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASS = os.getenv("NEO4J_PASS")

driver = GraphDatabase.driver(URI, auth=(USER, PASS))

def check_database():
    with driver.session() as session:
        # Check all node labels
        result = session.run("CALL db.labels()")
        labels = [record[0] for record in result]
        print("📊 Node Labels in Database:")
        print(labels)
        print()
        
        # Check all relationship types
        result = session.run("CALL db.relationshipTypes()")
        rels = [record[0] for record in result]
        print("🔗 Relationship Types in Database:")
        print(rels)
        print()
        
        # Check sample data
        result = session.run("MATCH (n) RETURN labels(n) as label, count(n) as count")
        print("📈 Node Counts:")
        for record in result:
            print(f"  {record['label']}: {record['count']}")
        print()
        
        # Check Orders specifically
        result = session.run("MATCH (o:Order) RETURN o LIMIT 1")
        orders = [dict(record["o"]) for record in result]
        if orders:
            print("🎯 Sample Order Properties:")
            print(orders[0])
        else:
            print("⚠️ No Orders found!")

if __name__ == "__main__":
    check_database()
    driver.close()