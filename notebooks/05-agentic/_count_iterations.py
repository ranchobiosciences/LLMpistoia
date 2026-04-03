"""Count iterations per run across all Q3 settings by counting assistant messages in HTML."""
import sys, os, re, glob
sys.stdout.reconfigure(encoding='utf-8')

base = r"d:\Rancho\projects\2409 - Pistoia\tasks\2603-01 - rerun 5\LLM\notebooks\artifacts\evaluation_results\rerun-2026"

settings = [
    ("claude-sonnet-4-6 (20it)", os.path.join(base, "05-Q3-claude-4.6-sonnet"), "claude-sonnet46"),
    ("claude-sonnet-4-6 (100it)", os.path.join(base, "05-Q3-claude-4.6-sonnet-100it"), "claude-sonnet-4-6"),
    ("gpt-5.2 (20it)", os.path.join(base, "05-Q3-gpt-5.2"), "gpt-52"),
    ("gpt-5.2 (100it)", os.path.join(base, "05-Q3-gpt-5.2-100it"), "gpt-52"),
]

def count_iterations(html_path):
    """Count assistant messages = iterations in main chat HTML."""
    with open(html_path, encoding='utf-8') as f:
        content = f.read()
    return content.count('class="assistant"')

for label, folder, model_pat in settings:
    print(f"\n{'='*70}")
    print(f"{label}")
    print(f"{'='*70}")

    if not os.path.exists(folder):
        print(f"  FOLDER NOT FOUND: {folder}")
        continue

    for q in [1, 2, 3]:
        # Find main HTML files (not zerocode, not checklist)
        if "gpt" in model_pat:
            pattern = os.path.join(folder, f"q{q}-{model_pat}_run*__*.html")
        else:
            pattern = os.path.join(folder, f"q{q}-{model_pat}_run*__*.html")

        all_htmls = glob.glob(pattern)
        # Filter out zerocode and checklist
        main_htmls = [h for h in all_htmls if '-zerocode' not in h and '_checklist' not in h]

        # Group by run number
        runs = {}
        for h in main_htmls:
            bn = os.path.basename(h)
            m = re.search(r'_run(\d+)', bn)
            if m:
                run_num = int(m.group(1))
                if run_num not in runs or os.path.getmtime(h) > os.path.getmtime(runs[run_num]):
                    runs[run_num] = h  # keep latest if multiple

        iters = []
        for run_num in sorted(runs.keys()):
            n = count_iterations(runs[run_num])
            iters.append(n)

        if iters:
            avg = sum(iters) / len(iters)
            print(f"  Q{q}: runs={len(iters)}, iterations={iters}, avg={avg:.1f}, total={sum(iters)}")
        else:
            print(f"  Q{q}: no runs found")

    # Grand totals
    all_iters = []
    for q in [1, 2, 3]:
        if "gpt" in model_pat:
            pattern = os.path.join(folder, f"q{q}-{model_pat}_run*__*.html")
        else:
            pattern = os.path.join(folder, f"q{q}-{model_pat}_run*__*.html")
        all_htmls = glob.glob(pattern)
        main_htmls = [h for h in all_htmls if '-zerocode' not in h and '_checklist' not in h]
        runs = {}
        for h in main_htmls:
            bn = os.path.basename(h)
            m = re.search(r'_run(\d+)', bn)
            if m:
                run_num = int(m.group(1))
                if run_num not in runs or os.path.getmtime(h) > os.path.getmtime(runs[run_num]):
                    runs[run_num] = h
        for run_num in sorted(runs.keys()):
            all_iters.append(count_iterations(runs[run_num]))

    if all_iters:
        print(f"\n  TOTAL: {len(all_iters)} runs, avg={sum(all_iters)/len(all_iters):.1f} iters/run, grand total={sum(all_iters)} iterations")
