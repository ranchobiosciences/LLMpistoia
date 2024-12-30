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

## 4. Biochatter

**04-biochatter.ipynb**

Thus BioChatter's approach to generating Cypher queries involves a structured, multi-step process, it breaks down query generation into stages. Each stage isolates specific elements—entities, properties, relationships—before building the final query prompt.

- Step 1: Entity selection
- Step 2: Relationship selection
- Step 3: Property selection
- Step 4: Final query generation

## 5. Agentic-based approach

The code for agentic-based approach is located in **05-agentic** subfolder

## 7. Deployment of specialized LLMs to use with Cypher (5 LLMs in total)

**07-text2cypher.ipynb**

5 links were selected by Pistoia:

- [7a. Cypher Generation: The Good, The Bad, and The Messy](https://towardsdatascience.com/cypher-generation-the-good-the-bad-and-the-messy-4ec119dd72ea). This is not really a specialized LLM, but instructions on how to prepare a dataset for fine-tuning.
- [7b. Llama3 Text2Cypher Demo](https://huggingface.co/collections/tomasonjo/llama3-text2cypher-demo-6647a9eae51e5310c9cfddcf) There are 5 models derived from the Llama3 model (with different sizes).
- [7c. Text2Cypher GitHub Repository](https://github.com/neo4j-labs/text2cypher) -  A description of the approach in general.
- [7d. Text2Cypher Demo 16-bit](https://huggingface.co/tomasonjo/text2cypher-demo-16bit) - A specific 16-bit model.
- [7e. Text2Cypher Demo 6-bit GGUF](https://huggingface.co/tomasonjo/text2cypher-demo-6bit-gguf)     - A specific 6-bit model.

Ignoring option 7a, we will evaluate 5 different fine-tuned llama3 variants:
- https://huggingface.co/tomasonjo/text2cypher-demo-16bit
- https://huggingface.co/tomasonjo/text2cypher-demo-16bit-gguf
- https://huggingface.co/tomasonjo/text2cypher-demo-4bit-gguf
- https://huggingface.co/tomasonjo/text2cypher-demo-8bit-gguf
- https://huggingface.co/tomasonjo/text2cypher-demo-6bit-gguf

These variants were deployed locally with ollama. 3Q test-set was used to evaluate the output.


## 8. Adapters with Predibase

**08-adapters_predibase.ipynb**

The notebook evaluates the effectiveness of model adapters in improving Cypher query generation capabilities of large language models. Adapters (such as lora) add task-specific layers to tune model to work on specific tasks while keeping base model untouched. 

In the implementation we use [Predibase](https://predibase.com/), a platform that simplifies adapter management and model fine-tuning workflows. 

We evaluate adapter (https://huggingface.co/sarangsonar/mistral_instruct_cypher) which is based on mistralai/Mistral-7B-Instruct-v0.1, a fine-tuned mistralai/Mistral-7B-v0.1 and compare its performance with performance of the base model.


## 9. DSPy framework

**09.1-dspy-gpt4o.ipynb**
**09.2-dspy-claude.ipynb**
**09.3-dspy-cypher.ipynb**


DSPy (https://dspy.ai/) is a framework to "program" language models:

> DSPy is the framework for programming—rather than prompting—language models. It allows you to iterate fast on building modular AI systems and offers algorithms for optimizing their prompts and weights, whether you're building simple classifiers, sophisticated RAG pipelines, or Agent loops.
> 
> DSPy stands for Declarative Self-improving Python. Instead of brittle prompts, you write compositional Python code and use DSPy to teach your LM to deliver high-quality outputs
>

We test different components of this framework on a BioMix test-set:
- Naive QA (Predict) and Chain of Thoughts (CoT) strategies to evaluate background knowledge of LLMs
- Naive CoT optimized with MIPROv2 optimizer
- Two-step strategy with query generation, retrieval & answering (non-optimized and MIPROv2 optimized)
- ReAct strategy (non-optimized and MIPROv2 optimized)

All strategies are tested with gpt-4o (09.1) and claude LLM (09.2). 

Training DSPy on true/false biomix questions can lead to overfitting due to the high level of background knowledge (~100%). To distinguish between its biological knowledge and knowledge graph utilization, we will train it to generate correct Cypher statements instead.

To achieve this, we need an extended biomix test set that includes genes, diseases, and the number of relationships between genes and diseases in the knowledge graph. We will then ask the LLM to generate queries that output the correct number of results. This was separately investigated in **09.3-dspy-cypher.ipynb**