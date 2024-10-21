# Knowledge graph querying strategies


## 1. Naïve generation of Cypher queries from natural language questions. 

It is expected that the resulting Cypher queries will be wrong in many cases. This use case is necessary as a baseline for other techniques. 
a.	Include prompt tuning for optimization of performance. 
b.	Document the proportion of correct and erroneous queries, determine whether there is pattern in generation of correct and erroneous queries. 


## 2. Template-based. 

Hand-code query templates and only allow the LLM to (a) select the right template from a finite collection of templates using the natural language prompt and (b) populate the plug-in parameters in these query templates, also using information supplied in the prompt.