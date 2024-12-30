# Knowledge graph querying strategies

## 0. Basic queries


**00-basic_queries.ipynb**

This notebook demonstrates the integration of a Neo4j knowledge graph populated with biological data from OpenTargets using the Biocypher package. It includes examples of how to connect to the Neo4j database, execute Cypher queries, and analyze the graph's structure and content. The notebook also highlights the use of the LangChain framework to interact with various large language models (LLMs) such as OpenAI, Anthropic, and Mistral, showcasing their ability to generate Cypher queries and enhance graph exploration.

## 1. Naïve generation of Cypher queries from natural language questions. 

**01-naive_generation.ipynb**

It is expected that the resulting Cypher queries will be wrong in many cases. This use case is necessary as a baseline for other techniques. 
a.	Include prompt tuning for optimization of performance. 
b.	Document the proportion of correct and erroneous queries, determine whether there is pattern in generation of correct and erroneous queries. 

Results include:
- 01a - Query without any information about database schema
- 01b - Prompt with general description of the knowledge graph
- 01c - Additional prompt with instructions to ignore directionality
- 01d - Investigation of the effect of temperature on the prompt


## 2. Template-based. 

**02-template_based.ipynb**

Hand-code query templates and only allow the LLM to (a) select the right template from a finite collection of templates using the natural language prompt and (b) populate the plug-in parameters in these query templates, also using information supplied in the prompt.

Just a single query is required to retrieve answers to all questions. Two extra queries (wthat would not produce any results) were included into the process.

Three sub-strategies are evaluated:
- 2a - with a single option (to understand if LLM picks parameters correctly), 
- 2b - with decoy queries and examples of correct query
- 2c - with decoy queries and without examples

## 3. Template-based query (2)

**03-template_based_2.ipynb**

Template-based. Create a Query Template that has several different Cypher queries embedded as training cases for the LLM (along with the schema) and then use that as the basis for the query a user adds.

Three options are evaluated:
- 3a - only examples of correct queries are provided
- 3b - examples of correct queries and "normal" graph schema is provided
- 3c - examples of correct queries and "enhanced" graph schema is provided