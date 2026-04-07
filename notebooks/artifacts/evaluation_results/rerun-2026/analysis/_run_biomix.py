"""Run agentic strategy 5 - BioMix 100 questions.
Usage: python _run_biomix.py [model_name]
  model_name: e.g. gpt-5.2, claude-sonnet-4-6 (default: claude-sonnet-4-6)
"""
import os, sys, re, json, time, threading
from datetime import datetime
import pandas as pd
from py2neo import Graph, ClientError

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from aillc.agents import Agent
from aillc.chat import Chat
from aillc.llm import LLM

# --- Init ---
LLM.init_openai(".env/openai_pistoia.json")
LLM.init_anthropic(".env/anthropic_pistoia.json")

with open(".env/neo4j_pistoia.json", "r") as f:
    neo4jconfig = json.load(f)
graph = Graph(neo4jconfig["NEO4J_URI"], auth=(neo4jconfig["NEO4J_USERNAME"], neo4jconfig["NEO4J_PASSWORD"]))

# --- Load agents ---
name = "graph_biomix"
folder = os.path.join("projects", name)
agents_folder = os.path.join(folder, "agents_anthropic")
scratch_dir = ".scratch"

ag_coder = Agent(agents_folder, "@coder")
ag_assistant = Agent(agents_folder, "@assistant")
ag_checklist = Agent(agents_folder, "@checklist")

# Model override
model_override = sys.argv[1] if len(sys.argv) > 1 else None
if model_override:
    ag_coder.parameters['model'] = model_override
    ag_assistant.parameters['model'] = model_override
    ag_checklist.parameters['model'] = model_override

model_label = (model_override or ag_coder.parameters['model']).replace('.', '')

print(f"Model: {ag_coder.parameters['model']}")
print(f"Agents: coder={ag_coder.parameters['model']}, assistant={ag_assistant.parameters['model']}, checklist={ag_checklist.parameters['model']}")

# --- Report task ---
with open(os.path.join(folder, "data", "report.txt"), "r", encoding="utf-8") as f:
    report_task = f.read()

# --- Questions ---
biomix = pd.read_csv(os.path.join(folder, "data", "biomix_true_false_selected_augmented.csv"))
questions = list(biomix['text'])
labels = list(biomix['label'])
print(f"Questions: {len(questions)}")

# --- Helpers ---
MAX_ITERATIONS = 200
counter = {'zero': 1, 'checklist': 1}

def generate_chat_name(name_val, name_prefix, name_suffix):
    if name_val is None:
        datetimestr = datetime.now().strftime("%Y-%m-%d %H.%M.%S")
        return f"{name_prefix}__{datetimestr}__{name_suffix}"
    return name_val

def extract_code_from_md(md_content):
    pattern = re.compile(r"```(.*?)\n(.*?)```", re.DOTALL)
    code_blocks = pattern.findall(md_content)
    extracted = [{'language': (lang.strip() if lang.strip() else "no_language"), 'content': content.strip()} for lang, content in code_blocks]
    return [d for d in extracted if d['language'] != 'no_language']

supported_languages = 'cypher'

class TimeoutThread(threading.Thread):
    def __init__(self, func, *args, **kwargs):
        threading.Thread.__init__(self)
        self.func = func; self.args = args; self.kwargs = kwargs
        self.result = None; self.error = None
    def run(self):
        try: self.result = self.func(*self.args, **self.kwargs)
        except Exception as e: self.error = e

def run_with_timeout(func, timeout, *args, **kwargs):
    thread = TimeoutThread(func, *args, **kwargs)
    thread.start(); thread.join(timeout)
    if thread.is_alive(): raise TimeoutError("Function execution timed out")
    elif thread.error: raise thread.error
    return thread.result

def run_cypher_query(query): return graph.query(query)

def validate_code_blocks(code_blocks):
    for block in code_blocks:
        if block['language'] not in supported_languages:
            return f"Language {block['language']} is not supported."
    return None

def run_code_blocks(code_blocks):
    res = []
    for cb in code_blocks:
        try:
            output = run_with_timeout(run_cypher_query, 60, cb['content'])
            res.append({"success": True, "results": output})
        except (ClientError, TimeoutError) as e:
            res.append({"success": False, "results": str(e)})
    return res

def truncate_output(result, max_length=10000):
    if result and len(result) > max_length: return f"{result[:max_length]}...\noutput truncated"
    return result

def process_execution_results(results):
    explanation = f"Executed {len(results)} commands:"
    for it, res in enumerate(results):
        cur = f"query {it}: "
        if res['success']: cur += f'success\noutput:\n{truncate_output(str(res["results"]))}\n'
        else: cur += f'failure\noutput:\n{truncate_output(str(res["results"]))}\n'
        explanation += cur + "\n"
    return explanation

def json_message(dt): return f"```json\n{json.dumps(dt)}\n```"

def handle_zero_code_blocks(solution, name_prefix=None):
    chat = Chat(ag_coder, ag_assistant, solution)
    if name_prefix is None: name_prefix = "zero_block_handling"
    chat.name = os.path.join(scratch_dir, generate_chat_name(None, name_prefix, f"{counter['zero']}"))
    counter['zero'] += 1
    output = chat.reply(json=True)
    chat.extend_thread(json_message(output)); chat.to_html()
    if output['status'] not in ['finished', 'help', 'other', 'stuck']:
        raise ValueError(f"Incorrect status: {output['status']}")
    return output

def generate_report(chat, report_task):
    chat.extend_thread(report_task); chat.to_html()
    report = chat.reply(); chat.extend_thread(report); chat.to_html()
    return report

def qc_checklist_passed(agent_coder, agent_checklist, chat, task, task_name_prefix):
    qc_chat = Chat(agent_coder, agent_checklist, entry_question="Please proceed with QC checklist",
                   background_asker=f"# Description of the current project:\n\n{task}")
    qc_chat.name = os.path.join(scratch_dir, generate_chat_name(None, f'{task_name_prefix}_checklist', f"{counter['checklist']}"))
    counter['checklist'] += 1
    while True:
        qc_json = qc_chat.reply(json=True)
        if 'state' not in qc_json: return True
        qc_state = qc_json['state']; qc_message = qc_json['message']
        if qc_state != 'pass': chat.extend_thread(qc_message, tags=['qc'])
        qc_chat.extend_thread(json_message(qc_json)); chat.to_html(); qc_chat.to_html()
        if qc_state == 'failed': return False
        elif qc_state == 'pass': return True
        elif qc_state == 'unknown': pass
        else: raise KeyError(f"Wrong qc state {qc_state}")
        answer = chat.reply()
        qc_chat.extend_thread(answer); chat.extend_thread(answer); qc_chat.to_html(); chat.to_html()

# --- Main graph loop with iteration cap ---
def graph_loop(task, task_name_prefix):
    chat = Chat(ag_assistant, ag_coder, task)
    chat.name = os.path.join(scratch_dir, generate_chat_name(None, task_name_prefix, '1'))
    iteration = 0

    while iteration < MAX_ITERATIONS:
        iteration += 1
        solution = chat.reply(); chat.extend_thread(solution); chat.to_html()
        code_blocks = extract_code_from_md(solution)
        invalid_blocks = validate_code_blocks(code_blocks)
        if invalid_blocks: break

        # Check if agent signaled FINAL ANSWER (even if code blocks present)
        has_final_answer = 'FINAL ANSWER' in solution

        if has_final_answer:
            # FIX: If agent said FINAL ANSWER, run any remaining code blocks then
            # go straight to report generation — skip assistant classification and QC
            # (prevents zerocode infinite loop and overzealous QC failures)
            if len(code_blocks) > 0:
                results = run_code_blocks(code_blocks)
                explanation = process_execution_results(results)
                chat.extend_thread(explanation, tags=['execution results']); chat.to_html()

            report = generate_report(chat, report_task); chat.to_html()
            return {"status": "success", "iterations": iteration, "report": report}

        elif len(code_blocks) == 0:
            actions = handle_zero_code_blocks(solution, f"{task_name_prefix}-zerocode")
            current_status = actions['status']

            if current_status == 'help':
                chat.extend_thread("Unfortunately I don't know", tags=['human response']); chat.to_html()
            elif current_status == 'finished':
                if qc_checklist_passed(ag_coder, ag_checklist, chat, task, task_name_prefix):
                    report = generate_report(chat, report_task); chat.to_html()
                    return {"status": "success", "iterations": iteration, "report": report}
                else:
                    # FIX: If QC fails but agent already answered, generate report anyway
                    report = generate_report(chat, report_task); chat.to_html()
                    return {"status": "success_qc_failed", "iterations": iteration, "report": report}
            else:
                chat.extend_thread(actions.get('request', 'Please continue'), tags=['request']); chat.to_html()
        else:
            results = run_code_blocks(code_blocks)
            explanation = process_execution_results(results)
            chat.extend_thread(explanation, tags=['execution results']); chat.to_html()

    return {"status": "max_iterations", "iterations": iteration, "report": None}


# === Main loop ===
print(f"\n{'='*70}")
print(f"Running BioMix evaluation: {len(questions)} questions with {ag_coder.parameters['model']}")
print(f"{'='*70}\n")

results_summary = []
total_start = time.time()

for i, question in enumerate(questions):
    counter = {'zero': 1, 'checklist': 1}
    template_name = f"biomix-q{i}-{model_label}"
    output_file = os.path.join(scratch_dir, f"{template_name}.txt")

    # Skip if already done
    if os.path.exists(output_file):
        print(f"[{i+1:3d}/100] SKIP (exists): {question[:60]}...")
        results_summary.append({"question_idx": i, "question": question, "label": labels[i],
                                "status": "skipped", "iterations": 0, "duration": 0})
        continue

    print(f"[{i+1:3d}/100] {question[:70]}...")
    start = time.time()

    try:
        result = graph_loop(question, template_name)
        duration = time.time() - start
        result['duration'] = duration
        result['question_idx'] = i
        result['question'] = question
        result['label'] = labels[i]

        if result.get('report'):
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result['report'])

        status_icon = "OK" if result['status'] == 'success' else "FAIL"
        print(f"         {status_icon} | {result['status']} | {result['iterations']} iters | {duration:.0f}s")
        results_summary.append(result)

    except Exception as e:
        duration = time.time() - start
        print(f"         ERROR | {duration:.0f}s | {e}")
        results_summary.append({"question_idx": i, "question": question, "label": labels[i],
                                "status": "error", "error": str(e), "duration": duration, "iterations": 0})

    # Progress report every 10 questions
    if (i + 1) % 10 == 0:
        elapsed = time.time() - total_start
        done = sum(1 for r in results_summary if r['status'] != 'skipped')
        successes = sum(1 for r in results_summary if r['status'] == 'success')
        print(f"\n  --- Progress: {i+1}/100 | {successes}/{done} success | {elapsed:.0f}s elapsed ---\n")

# === Final summary ===
total_duration = time.time() - total_start
done_results = [r for r in results_summary if r['status'] != 'skipped']
successes = sum(1 for r in done_results if r['status'] == 'success')
max_iters = sum(1 for r in done_results if r['status'] == 'max_iterations')
errors = sum(1 for r in done_results if r['status'] == 'error')

print(f"\n{'='*70}")
print(f"FINAL SUMMARY")
print(f"{'='*70}")
print(f"Total questions: {len(questions)}")
print(f"Completed: {len(done_results)}")
print(f"Success: {successes}")
print(f"Max iterations: {max_iters}")
print(f"Errors: {errors}")
print(f"Total time: {total_duration:.0f}s ({total_duration/60:.1f}min)")
if done_results:
    avg_dur = sum(r.get('duration', 0) for r in done_results) / len(done_results)
    print(f"Avg duration per question: {avg_dur:.1f}s")

# Save summary JSON
summary_path = os.path.join(scratch_dir, f"biomix-{model_label}_summary.json")
summary_clean = []
for r in results_summary:
    entry = {k: v for k, v in r.items() if k != 'report'}
    entry['has_report'] = r.get('report') is not None
    summary_clean.append(entry)
with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(summary_clean, f, indent=2)
print(f"\nSummary saved to {summary_path}")

print("\nDone!")
