# Agentic approach

We utilize Rancho agent framework that is based on conversations (chat) between agents and offers flexibility in the choice of LLMs and flexible tuning of the workflows.

Specific tasks (e.g. answering biological questions) are defined in subfolders of `projects` folder. Each task contain a description of agents in `agents` subfolder. Agents are:

- `@coder.md` for main data science agent
- `@checklist.md` for QC agent
- `@assistant.md` for default LLM assistant

Specific subtask instructions are stored in `data/` folder.

The **05-agentic_3Q.py** and **05-agentic_biomix.py** implement agent-based approach with internal (@coder executing cypher queries and reflecting on results) and external (@checklist agent verifying correctness of the approach) loops. Results are saved as chat logs in html format as well as processed txt files with final reports (for biomix test-set).