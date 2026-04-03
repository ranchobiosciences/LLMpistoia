"""Run agentic strategy 5 - single question x10.
Usage: python _run_q3_10x.py [question_number] [model_name]
  question_number: 1, 2, or 3 (default: 3)
  model_name: e.g. claude-sonnet-4-6, gpt-5.2 (default: claude-sonnet-4-6)
"""
import os, sys, re, json, time, threading
from datetime import datetime
from py2neo import Graph, ClientError

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from aillc.agents import Agent
from aillc.chat import Chat
from aillc.llm import LLM

# Init LLMs
LLM.init_anthropic(".env/anthropic_pistoia.json")
try:
    LLM.init_openai(".env/openai_pistoia.json")
except Exception:
    pass

# Init graph
with open(".env/neo4j_pistoia.json", "r") as f:
    neo4jconfig = json.load(f)

graph = Graph(
    neo4jconfig["NEO4J_URI"],
    auth=(neo4jconfig["NEO4J_USERNAME"], neo4jconfig["NEO4J_PASSWORD"])
)

# Load agents
name = "graph_test"
folder = os.path.join("projects", name)
agents_folder = os.path.join(folder, "agents_anthropic")
scratch_dir = ".scratch"

ag_coder = Agent(agents_folder, "@coder")
ag_assistant = Agent(agents_folder, "@assistant")
ag_checklist = Agent(agents_folder, "@checklist")

print(f"Agents: coder={ag_coder.parameters['model']}, assistant={ag_assistant.parameters['model']}, checklist={ag_checklist.parameters['model']}")

# Report task
with open(os.path.join(folder, "data", "report.txt"), "r", encoding="utf-8") as f:
    report_task = f.read()

# --- Helpers (from 05-agentic_3Q.py) ---

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
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.error = None
    def run(self):
        try:
            self.result = self.func(*self.args, **self.kwargs)
        except Exception as e:
            self.error = e

def run_with_timeout(func, timeout, *args, **kwargs):
    thread = TimeoutThread(func, *args, **kwargs)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise TimeoutError("Function execution timed out")
    elif thread.error:
        raise thread.error
    return thread.result

def run_cypher_query(query):
    return graph.query(query)

def validate_code_blocks(code_blocks):
    for block in code_blocks:
        if block['language'] not in supported_languages:
            return f"Language {block['language']} is not supported."
    return None

def run_code_blocks(code_blocks):
    res = []
    for code_block in code_blocks:
        try:
            output = run_with_timeout(run_cypher_query, 60, code_block['content'])
            res.append({"success": True, "results": output})
        except (ClientError, TimeoutError) as e:
            res.append({"success": False, "results": str(e)})
    return res

def truncate_output(result, max_length=10000):
    if result and len(result) > max_length:
        return f"{result[:max_length]}...\noutput truncated"
    return result

def process_execution_results(results):
    explanation = f"Executed {len(results)} commands:"
    for it, res in enumerate(results):
        cur = f"query {it}: "
        if res['success']:
            cur += f'success\noutput:\n{truncate_output(str(res["results"]))}\n'
        else:
            cur += f'failure\noutput:\n{truncate_output(str(res["results"]))}\n'
        explanation += cur + "\n"
    return explanation

def json_message(dt):
    return f"```json\n{json.dumps(dt)}\n```"

def handle_zero_code_blocks(solution, name_prefix=None):
    chat = Chat(ag_coder, ag_assistant, solution)
    if name_prefix is None:
        name_prefix = "zero_block_handling"
    chat.name = os.path.join(scratch_dir, generate_chat_name(None, name_prefix, f"{counter['zero']}"))
    counter['zero'] += 1
    output = chat.reply(json=True)
    chat.extend_thread(json_message(output))
    chat.to_html()
    allowed_status = ['finished', 'help', 'other', 'stuck']
    if output['status'] not in allowed_status:
        raise ValueError(f"Incorrect value of status: {output['status']}")
    return output

def generate_report(chat, report_task):
    chat.extend_thread(report_task)
    chat.to_html()
    report = chat.reply()
    chat.extend_thread(report)
    chat.to_html()
    return report

def qc_checklist_passed(agent_coder, agent_checklist, chat, task, task_name_prefix):
    qc_chat = Chat(agent_coder, agent_checklist, entry_question="Please proceed with QC checklist",
                   background_asker=f"# Description of the current project:\n\n{task}")
    qc_chat.name = os.path.join(scratch_dir, generate_chat_name(None, f'{task_name_prefix}_checklist', f"{counter['checklist']}"))
    counter['checklist'] += 1
    while True:
        qc_json = qc_chat.reply(json=True)
        if 'state' not in qc_json:
            return True
        qc_state = qc_json['state']
        qc_message = qc_json['message']
        print(f"    QC: {qc_state}")
        if qc_state != 'pass':
            chat.extend_thread(qc_message, tags=['qc'])
        qc_chat.extend_thread(json_message(qc_json))
        chat.to_html()
        qc_chat.to_html()
        if qc_state == 'failed':
            return False
        elif qc_state == 'pass':
            return True
        elif qc_state == 'unknown':
            pass
        else:
            raise KeyError(f"Format violation - wrong qc checklist state {qc_state}")
        answer = chat.reply()
        qc_chat.extend_thread(answer)
        chat.extend_thread(answer)
        qc_chat.to_html()
        chat.to_html()

# --- Main graph loop ---
MAX_ITERATIONS = int(os.environ.get('MAX_ITERATIONS', 20))

def graph_loop(task, task_name_prefix):
    chat = Chat(ag_assistant, ag_coder, task)
    chat.name = os.path.join(scratch_dir, generate_chat_name(None, task_name_prefix, '1'))
    iteration = 0

    while iteration < MAX_ITERATIONS:
        iteration += 1
        solution = chat.reply()
        chat.extend_thread(solution)
        chat.to_html()

        code_blocks = extract_code_from_md(solution)
        invalid_blocks = validate_code_blocks(code_blocks)
        if invalid_blocks:
            print(f"    iter {iteration}: invalid blocks, stopping")
            break

        if len(code_blocks) == 0:
            actions = handle_zero_code_blocks(solution, f"{task_name_prefix}-zerocode")
            current_status = actions['status']
            print(f"    iter {iteration}: no code, status={current_status}")

            if current_status == 'help':
                response = "Unfortunately I don't know"
                chat.extend_thread(response, tags=['human response'])
                chat.to_html()
            elif current_status == 'finished':
                if qc_checklist_passed(ag_coder, ag_checklist, chat, task, task_name_prefix):
                    report = generate_report(chat, report_task)
                    chat.to_html()
                    return {"status": "success", "iterations": iteration, "report": report}
                else:
                    print(f"    QC failed, continuing...")
            else:
                chat.extend_thread(actions.get('request', 'Please continue'), tags=['request'])
                chat.to_html()
        else:
            n_success = sum(1 for r in run_code_blocks(code_blocks) if r['success'])
            results = run_code_blocks(code_blocks)
            explanation = process_execution_results(results)
            s = sum(1 for r in results if r['success'])
            print(f"    iter {iteration}: {len(code_blocks)} queries, {s}/{len(code_blocks)} success")
            chat.extend_thread(explanation, tags=['execution results'])
            chat.to_html()

    return {"status": "max_iterations", "iterations": iteration, "report": None}


# === Run question x 10 ===
questions = {
    1: "What (or how strong, or is there any) is the evidence between TDP-43 and amyotrophic lateral sclerosis (ALS)",
    2: "What is the evidence linking TDP-43 to cancer in animal models?",
    3: "What (or is there) is the clinical evidence linking BRAF to Melanoma?"
}

q_num = int(sys.argv[1]) if len(sys.argv) > 1 else 3
model_override = sys.argv[2] if len(sys.argv) > 2 else None
task = questions[q_num]
num_runs = 10

# Override agent models if specified
if model_override:
    ag_coder.parameters['model'] = model_override
    ag_assistant.parameters['model'] = model_override
    ag_checklist.parameters['model'] = model_override

model_label = (model_override or ag_coder.parameters['model']).replace('.', '')
template_name = f"q{q_num}-{model_label}"

print(f"\nQuestion: {task}")
print(f"Runs: {num_runs}")
print(f"Model: {ag_coder.parameters['model']}")
print(f"{'='*60}\n")

results_summary = []

for i in range(num_runs):
    counter = {'zero': 1, 'checklist': 1}  # reset counters each run
    run_name = f"{template_name}_run{i}"
    output_file = os.path.join(scratch_dir, f"{run_name}.txt")

    print(f"--- Run {i+1}/{num_runs} ---")
    start = time.time()

    try:
        result = graph_loop(task, run_name)
        duration = time.time() - start
        result['duration'] = duration
        result['run'] = i

        if result['report']:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result['report'])

        print(f"  Result: {result['status']}, {result['iterations']} iterations, {duration:.1f}s")
        results_summary.append(result)

    except Exception as e:
        duration = time.time() - start
        print(f"  ERROR after {duration:.1f}s: {e}")
        results_summary.append({"status": "error", "error": str(e), "duration": duration, "run": i})

# === Summary ===
print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")

for r in results_summary:
    status = r['status']
    dur = r.get('duration', 0)
    iters = r.get('iterations', '?')
    err = r.get('error', '')
    print(f"  Run {r['run']}: {status}, {iters} iters, {dur:.1f}s {err}")

successes = sum(1 for r in results_summary if r['status'] == 'success')
print(f"\nSuccess: {successes}/{num_runs}")
if results_summary:
    avg_dur = sum(r.get('duration', 0) for r in results_summary) / len(results_summary)
    print(f"Avg duration: {avg_dur:.1f}s")

# Save summary
with open(os.path.join(scratch_dir, f"{template_name}_summary.json"), "w", encoding="utf-8") as f:
    # Strip full reports for summary json (too large)
    summary_clean = []
    for r in results_summary:
        entry = {k: v for k, v in r.items() if k != 'report'}
        entry['has_report'] = r.get('report') is not None
        summary_clean.append(entry)
    json.dump(summary_clean, f, indent=2)

print("\nDone!")
