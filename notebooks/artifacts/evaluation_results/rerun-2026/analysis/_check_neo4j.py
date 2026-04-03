"""Quick Neo4j connectivity check."""
import json
from py2neo import Graph

with open(".env/neo4j_pistoia.json", "r") as f:
    c = json.load(f)

try:
    g = Graph(c["NEO4J_URI"], auth=(c["NEO4J_USERNAME"], c["NEO4J_PASSWORD"]))
    r = g.run("RETURN 1 AS test").data()
    print(f"Neo4j OK: {r}")
except Exception as e:
    print(f"Neo4j DOWN: {e}")
