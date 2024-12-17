# %%

import os
from dotenv import load_dotenv
import pandas as pd
from tqdm import tqdm
import json


# %%
# Load environment variables from the .env file

load_dotenv('.env', override=True)

neo4j_uri = os.getenv("NEO4J_URI")
neo4j_username = os.getenv("NEO4J_USERNAME")
neo4j_password = os.getenv("NEO4J_PASSWORD")

# Check if any variable is missing
if not all([neo4j_uri, neo4j_username, neo4j_password]):
    raise EnvironmentError("One or more environment variables are missing: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD")

print(f"Accessing OpenTargets at {neo4j_uri} as user {neo4j_username}")


# %%

INPUT = "db/gene_disease_combinations.xlsx"
OUTPUT_INEXACT = "db/gene_disease_queries_combinations_inexact.xlsx"
OUTPUT_EXACT = "db/gene_disease_queries_combinations_exact.xlsx"

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
    print(query)
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


def run_gene_disease_query(gene, disease, substr=True):
    if substr:
        disease_query = f"LOWER(disease.name) CONTAINS LOWER('{disease}')"
    else:
        disease_query = f"LOWER(disease.name) = LOWER('{disease}')"
    query = f"""
MATCH (gene:HumanGene)-[:IS_PART_OF]-(assoc)-[:IS_PART_OF]-(disease:Disease)
WHERE gene.approvedSymbol = '{gene}'
  AND ({disease_query})
RETURN 
    gene.approvedSymbol as Gene,
    disease.name as Disease,
    head([label IN labels(assoc) WHERE label CONTAINS '.GeneToDiseaseAssociation']) as EvidenceType,
    assoc.score as Score,
    assoc.literature as Literature
ORDER BY assoc.score DESC
"""
    return run_query(query)




# %%
# Checking the whole list of stuff, inexactly

df = pd.read_excel(INPUT)
output = []

CACHE_DIR = ".temp/gene-disease-inexact"
os.makedirs(CACHE_DIR, exist_ok=True)

for _,row in tqdm(df.iterrows(), total = len(df)):
    gene = row['gene']
    disease = row['disease']
    json_filename = os.path.join(f"{CACHE_DIR}/{gene}-{disease}.json")
    if os.path.exists(json_filename):
        with open(json_filename) as f:
            res = json.load(f)
    else:
        res = run_gene_disease_query(row['gene'], row['disease'])
        with open(json_filename, 'w') as f:
            json.dump(res, f, indent=4)
    
    output.append({"count":len(res), "results":res})


# %%
# Saving output

counts = [out['count'] for out in output]
df['counts'] = counts
df.to_excel(OUTPUT_INEXACT, index=False)



# %%
# Checking queries that are exact

df = pd.read_excel(INPUT)
CACHE_DIR = ".temp/gene-disease-exact"
os.makedirs(CACHE_DIR, exist_ok=True)

output = []
for _,row in tqdm(df.iterrows(), total = len(df)):
    gene = row['gene']
    disease = row['disease']
    json_filename = os.path.join(f"{CACHE_DIR}/{gene}-{disease}.json")
    if os.path.exists(json_filename):
        with open(json_filename) as f:
            res = json.load(f)
    else:
        res = run_gene_disease_query(row['gene'], row['disease'], substr=False)
        with open(json_filename, 'w') as f:
            json.dump(res, f, indent=4)
    
    output.append({"count":len(res), "results":res, "gene":gene, "disease":disease})


# %%
# Saving output
    
counts = [out['count'] for out in output]
df['counts'] = counts
df.to_excel(OUTPUT_EXACT, index=False)



# %%