# %%
# Import the required libraries

import os
from dotenv import load_dotenv
import pandas as pd
from tqdm import tqdm


# %%

# List of entities to query: genes and diseases
INPUT = "tmp/entities.xlsx"

# %%
# Load environment variables from the .env file

load_dotenv(".env")

neo4j_uri = os.getenv("NEO4J_URI")
neo4j_username = os.getenv("NEO4J_USERNAME")
neo4j_password = os.getenv("NEO4J_PASSWORD")

# Check if any variable is missing
if not all([neo4j_uri, neo4j_username, neo4j_password]):
    raise EnvironmentError("One or more environment variables are missing: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD")

print(f"Accessing OpenTargets at {neo4j_uri} as user {neo4j_username}")



# %%
from py2neo import Graph

# Create a Graph instance
graph = Graph(
    neo4j_uri,
    auth=(neo4j_username, neo4j_password)
)



# %%
# Queries


def run_query(query):
    try:
        return list(graph.query(query))
    except:
        return []



def gene_query(gene):
    query = f"""
MATCH (gene:HumanGene)
WHERE gene.approvedSymbol = '{gene}' 
RETURN 
    gene.approvedSymbol as Gene,
    gene.id as id
"""
    return run_query(query)

def disease_query(disease,  substr=True):
    if substr:
        disease_query = f"LOWER(disease.name) CONTAINS LOWER('{disease}')"
    else:
        disease_query = f"LOWER(disease.name) = LOWER('{disease}')"
    query = f"""
MATCH (disease:Disease)
WHERE {disease_query}
RETURN 
    disease.name as Disease,
    disease.id as id
    """
    return run_query(query)



# %%
# Checking the whole list of stuff:

df = pd.read_excel(INPUT)


# %%
# Actually querying the database

disease_exact = {}
disease_substr = {}
gene = {}

for _,row in tqdm(df.iterrows(), total = len(df)):
    query = row['name']
    if row['type'] == 'disease':
        disease_exact[query] = len(disease_query(query, substr=False))
        disease_substr[query] = len(disease_query(query, substr=True))
    elif row['type'] == 'gene':
        gene[query] = len(gene_query(query))
    else:
        count = None

# %%
# Preparing the results

df_exact = df.copy()
df_substr = df.copy

df_exact['nresults'] = df_exact['name'].map(disease_exact)
df_substr['nresults'] = df_substr['name'].map(disease_substr) 

df_exact.to_excel("entities_queried_exact.xlsx", index=False)
df_substr.to_excel("entities_queried_inexact.xlsx", index=False)

# %%

