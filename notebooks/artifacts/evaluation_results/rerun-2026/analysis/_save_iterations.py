"""Save iteration counts to Excel."""
import sys, os, re, glob
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

base = r"d:\Rancho\projects\2409 - Pistoia\tasks\2603-01 - rerun 5\LLM\notebooks\artifacts\evaluation_results\rerun-2026"

settings = [
    ("claude-sonnet-4-6 (20it)", os.path.join(base, "05-Q3-claude-4.6-sonnet"), "claude-sonnet46"),
    ("claude-sonnet-4-6 (100it)", os.path.join(base, "05-Q3-claude-4.6-sonnet-100it"), "claude-sonnet-4-6"),
    ("gpt-5.2 (20it)", os.path.join(base, "05-Q3-gpt-5.2"), "gpt-52"),
    ("gpt-5.2 (100it)", os.path.join(base, "05-Q3-gpt-5.2-100it"), "gpt-52"),
]

questions = {1: "TDP-43, ALS", 2: "TDP-43, cancer", 3: "BRAF, melanoma"}

def count_iterations(html_path):
    with open(html_path, encoding='utf-8') as f:
        return f.read().count('class="assistant"')

rows = []
for label, folder, model_pat in settings:
    for q in [1, 2, 3]:
        pattern = os.path.join(folder, f"q{q}-{model_pat}_run*__*.html")
        all_htmls = glob.glob(pattern)
        main_htmls = [h for h in all_htmls if '-zerocode' not in h and '_checklist' not in h]
        runs = {}
        for h in main_htmls:
            m = re.search(r'_run(\d+)', os.path.basename(h))
            if m:
                rn = int(m.group(1))
                if rn not in runs or os.path.getmtime(h) > os.path.getmtime(runs[rn]):
                    runs[rn] = h
        for rn in sorted(runs.keys()):
            rows.append({
                "model": label,
                "question": questions[q],
                "run": rn,
                "iterations": count_iterations(runs[rn])
            })

df = pd.DataFrame(rows)
out = os.path.join(base, "05-Q3-iterations.xlsx")
df.to_excel(out, index=False)
print(f"Saved {len(df)} rows to {out}")
print(df.groupby(['model', 'question'])['iterations'].agg(['mean', 'sum', 'count']).to_string())
