# Strategy 5 (Agentic) Rerun — 2026

Rerun of the agentic knowledge graph querying strategy using current-generation LLMs (claude-sonnet-4-6, gpt-5.2) against the OpenTargets Neo4j graph, compared to the 2024 baseline (claude-3.5-sonnet, gpt-4o).

## What was done

### 1. Q3 Evaluation (3 open-ended questions, 10 runs each)
Three questions from the original evaluation:
- **Q1**: TDP-43 / ALS evidence (all evidence types)
- **Q2**: TDP-43 / cancer in animal models (AnimalModel only)
- **Q3**: BRAF / melanoma clinical evidence

Tested with two iteration limits (20 and 100) to measure the effect of iteration budget on success rate.

### 2. BioMix Evaluation (100 True/False gene-disease questions)
Full biomix test set (`biomix_true_false_selected_augmented.csv`), each question run once per model.

### 3. Graph Change Detection
Re-ran all 100 template queries from the 2024 Strategy 2 evaluation to detect changes in the Neo4j graph. Found 4 gene-disease pairs that lost their associations since 2024.

## Key findings

### Q3 Success Rates

| Model | 20 iter | 100 iter |
|-------|:-------:|:--------:|
| claude-sonnet-4-6 | 20/30 (67%) | 30/30 (100%) |
| gpt-5.2 | 26/30 (87%) | 29/30 (97%) |

### BioMix Accuracy (96 valid questions, excluding 4 with stale ground truth)

| Model | Accuracy |
|-------|----------|
| claude-sonnet-4-6 | 96/96 (100%) |
| gpt-5.2 | 85/96 (88.5%) |

### Iteration Efficiency

| Model | Avg iterations/run (100 iter setting) |
|-------|:-------------------------------------:|
| claude-sonnet-4-6 | 21.7 |
| gpt-5.2 | 10.9 |

### Graph Changes Since 2024
4 of 100 gene-disease pairs lost associations (96 unchanged):
- DHCR7 / Smith-Lemli-Opitz: 746 → 0
- ETHE1 / Ethylmalonic encephalopathy: 261 → 0
- HMBS / Acute intermittent porphyria: 307 → 0
- ACADVL / VLCAD deficiency: 1253 → 0

## Results files

### Q3 Evaluations (curated, with is_success/failure_type/comment)
- `05-evaluations_rerun2026_claude-sonnet-4-6.xlsx` — Q3, 20 iter
- `05-evaluations_rerun2026_claude-sonnet-4-6_100it.xlsx` — Q3, 100 iter
- `05-evaluations_rerun2026_gpt-5.2.xlsx` — Q3, 20 iter
- `05-evaluations_rerun2026_gpt-5.2_100it.xlsx` — Q3, 100 iter

### BioMix Evaluations (accuracy per question, with error explanations)
- `05-biomix_claude-sonnet-46_accuracy.xlsx` — 100 questions, answer vs ground truth
- `05-biomix_gpt52_accuracy.xlsx` — 100 questions, answer vs ground truth

### Iteration Analysis
- `05-Q3-iterations.xlsx` — iterations per run across all 4 settings (120 rows)
- `05-Q3-iterations-barplot.png` — visual comparison

### Graph Change Analysis
- `05-biomix_template_2024_vs_2026.xlsx` — all 100 template queries re-run, 2024 count vs 2026 count

### Reference
- `evaluation_rules.md` — evaluation criteria and failure type taxonomy
- `Pistoia-KG-rerun.xlsx` — master tracking spreadsheet

### Raw Run Data (archived)
Zip files contain HTML chat logs and text reports for each run:
- `05-Q3-claude-4.6-sonnet.zip` — Q3, sonnet, 20 iter
- `05-Q3-claude-4.6-sonnet-100it.zip` — Q3, sonnet, 100 iter
- `05-Q3-gpt-5.2.zip` — Q3, gpt-5.2, 20 iter
- `05-Q3-gpt-5.2-100it.zip` — Q3, gpt-5.2, 100 iter
- `05-biomix_gpt-5.2.zip` — BioMix, gpt-5.2
- `05-biomix_sonnet-4-6.zip` — BioMix, sonnet

### 2024 Baseline
Available at `notebooks/artifacts/evaluation_results/`:
- `05-evaluation.zip` — 2024 HTML chat logs (batches 1-12)
- `05-evaluations_curated.xlsx` — 2024 curated evaluation (batches 1-12)
- `biomix02b-evaluations.xlsx` — 2024 template-based biomix results (used for graph change comparison)

## Analysis scripts

Located in `analysis/`. All scripts run from `notebooks/05-agentic/` as working directory.

| Script | Purpose |
|--------|---------|
| `_run_q3_10x.py` | Run Q3 (3 questions x 10 runs). Args: `[question_number] [model_name]`. Env: `MAX_ITERATIONS` (default 20). |
| `_run_biomix.py` | Run BioMix (100 True/False questions). Args: `[model_name]`. Includes FINAL ANSWER detection fix and QC bypass. |
| `_compare_2024_vs_now.py` | Re-runs all 100 template queries from 2024 biomix02b evaluation, compares result counts. |
| `_save_iterations.py` | Generates `05-Q3-iterations.xlsx` from HTML chat logs across all settings. |
| `_count_iterations.py` | Prints iteration count summary to console. |
| `_plot_iterations.py` | Generates `05-Q3-iterations-barplot.png`. |
| `_check_neo4j.py` | Quick Neo4j connectivity check. |

## Code changes

Changes to the agentic framework (`notebooks/05-agentic/aillc/llm.py`):
- Updated claude model names: `claude-3-5-sonnet-20240620` → `claude-sonnet-4-6`, `claude-3-opus-20240229` → `claude-opus-4-6`
- Added `gpt-5.2` and `claude-sonnet-4-6` to model registry
- Implemented JSON extraction from Anthropic API responses (was only supported for OpenAI)

Agent config changes (`notebooks/05-agentic/projects/graph_test/agents_anthropic/`):
- All agents (@coder, @assistant, @checklist) updated to `claude-sonnet-4-6`

Neo4j connection fix (`notebooks/.env`):
- Changed `bolt+s://` to `bolt+ssc://` (SSL cert verification was failing)
