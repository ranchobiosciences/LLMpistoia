# %% [markdown]
# # Interacting with knowledge graphs
#
# This demonstrates a tool for interacting with knowledge graphs
# Agents will solve problems on how to make cypher queries that actually work and how to
# ask human specific questions before engaging with answers

# %%
# Imports

import os
from aillc.agents import Agent
from aillc.chat import Chat
from aillc.llm import LLM
from datetime import datetime
import json
from py2neo import Graph, ClientError


# %%
# Playsound

try:
    from pygame import mixer
    def notification(filename = "notification.mp3"):
        mixer.init()
        mixer.music.load(os.path.join('.assets', filename))
        mixer.music.play()

except Exception as e:
    def notification():
        pass


# %%
# Load the company and agents

name = "graph_test"
folder = os.path.join("projects", name)
agents_folder = os.path.join(folder, "agents_anthropic")
#agents_folder = os.path.join(folder, "agents")
scratch_dir = ".scratch"

start_counter = {
    'zero' :   1,
    'checklist': 1
}
counter = start_counter

# %%
# read tasks

def read_task(task_name): 
    with open(os.path.join(folder, "data", f"{task_name}.txt"), "r", encoding='utf-8') as file:
        task = file.read()
    return task

# %%
# Initializing LLMs

LLM.init_openai(".env/openai_pistoia.json")
LLM.init_anthropic(".env/anthropic_pistoia.json")

# %%
# Initializing graph


with open(".env/neo4j_pistoia.json", "r") as f:
    neo4jconfig = json.load(f)

# Retrieve the variables from the environment
neo4j_uri = neo4jconfig["NEO4J_URI"]
neo4j_username = neo4jconfig["NEO4J_USERNAME"]
neo4j_password = neo4jconfig["NEO4J_PASSWORD"]

graph = Graph(
    neo4j_uri,
    auth=(neo4j_username, neo4j_password)
)


# %%
# Loading agents

ag_coder = Agent(agents_folder, "@coder")
ag_assistant = Agent(agents_folder, "@assistant")
ag_checklist = Agent(agents_folder, "@checklist")

# %%
# Setting up intermediate tasks

report_task = read_task('report')


# %%
# Chat name generation

def generate_chat_name(name, name_prefix, name_suffix):
    if name is None:
        datetimestr = datetime.now().strftime("%Y-%m-%d %H.%M.%S")
        return f"{name_prefix}__{datetimestr}__{name_suffix}"
    else:
        return name



# %%
# Extracting cypher code from markdown

def extract_code_from_md(md_content):
    import re
    pattern = re.compile(r"```(.*?)\n(.*?)```", re.DOTALL)
    code_blocks = pattern.findall(md_content)
    extracted = [{'language': (lang.strip() if lang.strip() else "no_language"), 'content': content.strip()} for lang, content in code_blocks]
    extracted = [d for d in extracted if d['language'] != 'no_language']
    return extracted

def extract_json_from_md(md_content):
    code_blocks = extract_code_from_md(md_content)
    for code in code_blocks:
        if code['language'] == 'json':
            return json.loads(code['content'])
    return {}

supported_languages = 'cypher'



# %%
# Timeout handlers

import threading

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




# %%
# Running the code

def run_cypher_query(query):
    return graph.query(query)

def validate_code_blocks(code_blocks):
    for block in code_blocks:
        if block['language'] not in supported_languages:
            return f"Language {block['language']} is not supported. Please modify your response to include supported languages only"
    return None

def run_code_blocks(code_blocks):
    res = []
    for code_block in code_blocks:
        try:
            output = run_with_timeout(run_cypher_query, 60, code_block['content']) 
            res.append({"success":True, "results":output})
        except (ClientError, TimeoutError) as e:
            res.append({"success":False, "results":str(e)})
        
    return res

def run_code(md_description):
    code_blocks = extract_code_from_md(md_description)
    return run_code_blocks(code_blocks)


def truncate_output(result, max_length = 10000):
    if result and len(result) > max_length:
        return f"{result[:max_length]}...\noutput truncated"
    else:
        return result

def process_execution_results(results):
    explanation = f"Executed {len(results)} commands:"
    it = 0
    for res in results:
        cur = f"query {it}: "
        if res['success']:
            cur += 'success\n'
            cur += f'output:\n{truncate_output(str(res["results"]))}\n'
        else:
            cur += f'failure\n'
            cur += f'output:\n{truncate_output(str(res["results"]))}\n'
        cur += "\n"
        explanation += cur
        it += 1
    return explanation



# %%
# Processing various conditions


def json_message(dt: dict):
    return f"```json\n{json.dumps(dt)}\n```"

# Interpret zero code blocks with assistant agent
def handle_zero_code_blocks(solution:str, name_prefix = None):

    chat = Chat(ag_coder, ag_assistant, solution)
    if name_prefix is None:
        name_prefix = "zero_block_handling"
    
    chat.name = generate_chat_name(None, name_prefix, f"{counter['zero']}")
    counter['zero'] = counter['zero']+1

    output = chat.reply(json=True)
    chat.extend_thread(json_message(output))
    chat.to_html()

    allowed_status = ['finished', 'help', 'other', 'stuck']
    if output['status'] not in allowed_status:
        raise ValueError(f"Incorrect value of status: {output['status']}")
    
    return output

# Just generate a report according to standards from report_task
def generate_report(chat:Chat, report_task:str) -> str:
    chat.extend_thread(report_task)
    chat.to_html()
    report = chat.reply()
    chat.extend_thread(report)
    chat.to_html()
    return report




# %%
# External QC loop

def json_message(dt: dict):
    return f"```json\n{json.dumps(dt)}\n```"

def qc_checklist_passed(agent_coder: Agent, agent_checklist: Agent, chat: Chat, task:str, task_name_prefix:str):

    qc_chat = Chat(agent_coder, agent_checklist, entry_question="Please proceed with QC checklist", background_asker=f"# Description of the current project:\n\n{task}")
    qc_chat.name = generate_chat_name(None, f'{task_name_prefix}_checklist', f"{counter['checklist']}")
    counter['checklist'] = counter['checklist'] + 1
    
    while True:

        # QC agent asks question
        qc_json = qc_chat.reply(json=True)

        if not 'state' in qc_json:
            print(qc_message)
            return True
        
        try:
            qc_state = qc_json['state']
            qc_message = qc_json['message']
        except KeyError as e:
            print(e)
            print(qc_json)
            raise e

        if qc_state != 'pass':
            chat.extend_thread(qc_message, tags = ['qc'])
        
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



# %%

questions = [
    "What (or how strong, or is there any) is the evidence between TDP-43 and amyotrophic lateral sclerosis (ALS)",
    "What is the evidence linking TDP-43 to cancer in animal models?",
    "What (or is there) is the clinical evidence linking BRAF to Melanoma?"
]
task = "What (or how strong, or is there any) is the evidence between TDP-43 and amyotrophic lateral sclerosis (ALS)"
task = questions[2]
print(task)



# %%
# Testing LLM

if False:
    chat = Chat(ag_assistant, ag_coder, task)
    chat.name = generate_chat_name(None, "test", '1')
    solution = chat.reply()


# %%
# Main graph loop


def graph_loop(task, task_name_prefix):
    
    chat = Chat(ag_assistant, ag_coder, task)
    chat.name = generate_chat_name(None, task_name_prefix, '1')

    while True:

        solution = chat.reply()
        chat.extend_thread(solution)
        chat.to_html()

        code_blocks = extract_code_from_md(solution)
        invalid_blocks = validate_code_blocks(code_blocks)
        if invalid_blocks:
            break

        if len(code_blocks) == 0:
            actions = handle_zero_code_blocks(solution, f"{task_name_prefix}-zerocode")

            current_status = actions['status']
            
            if current_status == 'help':
                notification()
                print(actions['request'])
                response = input("Your answer:")
                chat.extend_thread(response, tags = ['human response'])
                chat.to_html()

            elif current_status == 'finished':
                
                # Version without QC:
                #report = generate_report(chat, report_task)
                #chat.to_html()
                #return report

                # Version with QC:
                if qc_checklist_passed(ag_coder, ag_checklist, chat, task, task_name_prefix):
                    report = generate_report(chat, report_task)
                    chat.to_html()
                    return report
                    

            else:
                chat.extend_thread(actions['request'], tags = ['request'])
                chat.to_html()
            
        
        else:
            results = run_code_blocks(code_blocks)
            explanation = process_execution_results(results)
            chat.extend_thread(explanation, tags = ['execution results'])
            chat.to_html()


# %%
# Run the task

template_name = 'q3-claude-QC2'
num_runs  = 1

for i in range(0,num_runs):

    print(f"\n\n-------------------------------------------\nRun {i} of {num_runs}")
    try:
        graph_loop(task, f'{template_name}_run{i}')
    except KeyError as e:
        pass
        

# %%
        
print("All done!")
notification()

# %%

