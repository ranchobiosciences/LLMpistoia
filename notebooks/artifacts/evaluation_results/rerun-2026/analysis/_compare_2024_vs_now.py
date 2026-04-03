"""Re-run every template query from 2024 biomix02b evaluation and compare counts."""
import sys, json, time
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
from py2neo import Graph

with open(".env/neo4j_pistoia.json", "r") as f:
    c = json.load(f)
graph = Graph(c["NEO4J_URI"], auth=(c["NEO4J_USERNAME"], c["NEO4J_PASSWORD"]))
print("Neo4j connected\n")

# Load 2024 results (use gpt-4o since it had 100% accuracy)
path = r"d:\Rancho\projects\2409 - Pistoia\tasks\2603-01 - rerun 5\LLM\notebooks\artifacts\evaluation_results\biomix02b-evaluations.xlsx"
df = pd.read_excel(path)
gpt4o = df[df['model'] == 'gpt-4o'].copy().reset_index(drop=True)

print(f"Total questions: {len(gpt4o)}")
print(f"Questions with query: {gpt4o['query'].notna().sum()}")
print()

results = []
for i, row in gpt4o.iterrows():
    question = row['question']
    query_2024 = row['query']
    count_2024 = row['count']
    success_2024 = row['success']
    label = row['label']

    if pd.isna(query_2024) or not success_2024:
        # No query or query failed in 2024
        results.append({
            'idx': i, 'question': question[:70], 'label': label,
            'count_2024': count_2024, 'count_2026': None,
            'match': None, 'status': 'no_query_2024'
        })
        continue

    # Run the exact same query now
    try:
        # The query from 2024 returns full rows; wrap in count
        # Actually just run it and count
        res = list(graph.run(query_2024))
        count_2026 = len(res)
    except Exception as e:
        count_2026 = None
        results.append({
            'idx': i, 'question': question[:70], 'label': label,
            'count_2024': count_2024, 'count_2026': None,
            'match': None, 'status': f'error: {str(e)[:80]}'
        })
        continue

    match = (count_2024 == count_2026)
    results.append({
        'idx': i, 'question': question[:70], 'label': label,
        'count_2024': int(count_2024) if pd.notna(count_2024) else None,
        'count_2026': count_2026,
        'match': match,
        'status': 'ok'
    })

    # Progress
    if (i + 1) % 10 == 0:
        print(f"  [{i+1}/100]")

results_df = pd.DataFrame(results)

# Summary
ok = results_df[results_df['status'] == 'ok']
matched = ok[ok['match'] == True]
changed = ok[ok['match'] == False]

print(f"\n{'='*70}")
print(f"RESULTS")
print(f"{'='*70}")
print(f"Total: {len(results_df)}")
print(f"Queried: {len(ok)}")
print(f"Matched (same count): {len(matched)}")
print(f"Changed (different count): {len(changed)}")
print(f"Errors: {len(results_df[results_df['status'].str.startswith('error', na=False)])}")
print(f"No query in 2024: {len(results_df[results_df['status'] == 'no_query_2024'])}")

if len(changed) > 0:
    print(f"\n--- Changed questions ---")
    for _, r in changed.iterrows():
        direction = "↑" if r['count_2026'] > r['count_2024'] else "↓"
        print(f"  Q{r['idx']}: {r['count_2024']} → {r['count_2026']} ({direction})  label={r['label']}")
        print(f"    {r['question']}")

# Save
out = r"d:\Rancho\projects\2409 - Pistoia\tasks\2603-01 - rerun 5\LLM\notebooks\artifacts\evaluation_results\rerun-2026\05-biomix_template_2024_vs_2026.xlsx"
results_df.to_excel(out, index=False)
print(f"\nSaved to {out}")
