# Knowledge graph querying strategies


## 1. Naïve generation of Cypher queries from natural language questions. 

It is expected that the resulting Cypher queries will be wrong in many cases. This use case is necessary as a baseline for other techniques. 
a.	Include prompt tuning for optimization of performance. 
b.	Document the proportion of correct and erroneous queries, determine whether there is pattern in generation of correct and erroneous queries. 

Results include:
01a - Query without any information about database schema
01b - Prompt with general description of the knowledge graph
01c - Additional prompt with instructions to ignore directionality
01d - Investigation of the effect of temperature on the prompt


## 2. Template-based. 

Hand-code query templates and only allow the LLM to (a) select the right template from a finite collection of templates using the natural language prompt and (b) populate the plug-in parameters in these query templates, also using information supplied in the prompt.

Just a single query is required to retrieve answers to all questions. Two extra queries (wthat would not produce any results) were included into the process.