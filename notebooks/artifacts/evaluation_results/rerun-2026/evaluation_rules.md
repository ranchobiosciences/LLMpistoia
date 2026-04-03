# Evaluation Rules for Strategy 5 (Agentic)

## Overview

These rules describe how to evaluate individual runs of the agentic pipeline (Strategy 5) against the Neo4j OpenTargets knowledge graph. Each run is an agent conversation where `@coder` writes Cypher queries, executes them, and produces a report answering a biological question.

## Questions

| ID | Question | Key Elements |
|----|----------|--------------|
| Q1 | What is the evidence between TDP-43 and ALS? | Gene: TARDBP, Disease: amyotrophic lateral sclerosis, Evidence: all types |
| Q2 | What is the evidence linking TDP-43 to cancer in animal models? | Gene: TARDBP, Disease: cancer, Evidence: AnimalModel only |
| Q3 | What is the clinical evidence linking BRAF to Melanoma? | Gene: BRAF, Disease: melanoma, Evidence: clinical (GeneticAssociation, KnownDrug, SomaticMutation, Literature) |

## Graph Schema (critical for evaluation)

The OpenTargets graph has this structure:
```
(HumanGene)-[:IS_PART_OF]->(*.GeneToDiseaseAssociation)<-[:IS_PART_OF]-(Disease)
```
Both Gene and Disease point INTO the association node. The association node is an intermediate node with labels like:
- `GeneticAssociation.GeneToDiseaseAssociation`
- `AnimalModel.GeneToDiseaseAssociation`
- `SomaticMutation.GeneToDiseaseAssociation`
- `KnownDrug.GeneToDiseaseAssociation`
- `RnaExpression.GeneToDiseaseAssociation`
- `Literature.GeneToDiseaseAssociation`
- `AffectedPathway.GeneToDiseaseAssociation`

## Outcome Classification

### is_success = 1 (Success)
The run produced a final report that correctly answers the question with data from the graph. Requirements:
1. **Correct gene** was queried (TARDBP for TDP-43, BRAF for BRAF)
2. **Correct disease** was matched (ALS, cancer, melanoma respectively)
3. **Correct evidence type** was used (if the question specifies one)
4. **Non-zero relevant results** were returned from the graph
5. **Report accurately reflects** the query results

### partial_success = "yes"
Marked alongside `is_success=1` when the answer is correct but with minor issues:
- Results slightly broader than asked (e.g., returned all evidence types when only clinical was asked, but correctly noted this)
- Agent found results but acknowledged limitations
- Agent returned correct answer but took an unusual/inefficient path

### is_success = 0 (Failure)
The run failed to correctly answer the question. Classify by `failure_type`:

---

## Failure Types

### 1. `directionality`
**Most common error.** Agent writes Cypher queries with wrong edge direction.

**What happens:** Agent chains edges as `Gene -> Association -> Disease` but in the graph, Disease also points INTO Association (not out). The correct pattern is:
```cypher
-- WRONG (returns 0 results):
MATCH (g:HumanGene)-[:IS_PART_OF]->(a)-[:IS_PART_OF]->(d:Disease)

-- CORRECT:
MATCH (g:HumanGene)-[:IS_PART_OF]->(a)<-[:IS_PART_OF]-(d:Disease)
-- or equivalently, two separate MATCH clauses:
MATCH (g:HumanGene)-[:IS_PART_OF]->(a)
MATCH (d:Disease)-[:IS_PART_OF]->(a)
```

**How to detect:**
- Agent finds the gene successfully
- Agent finds association nodes connected to the gene
- Agent gets 0 results when trying to connect associations to diseases
- Agent concludes "no data found" or provides association metadata without disease names
- Agent does NOT try reversing the direction or using separate MATCH clauses

### 2. `schema`
**Agent doesn't use the intermediate association node.**

**What happens:** Agent tries to directly connect Gene to Disease:
```cypher
-- WRONG:
MATCH (g:HumanGene)-[:ASSOCIATED_WITH]->(d:Disease)
MATCH (g:HumanGene)-[:IS_PART_OF]->(d:Disease)
```

**How to detect:**
- Queries don't reference any association/intermediate node
- Agent may try various relationship types but never discovers the `Gene -> Assoc <- Disease` pattern
- Often happens in early iterations before the agent explores the schema

### 3. `evidence_type`
**Agent returns results from wrong evidence type.**

**What happens:** Question asks for a specific evidence type (e.g., "animal models" or "clinical") but agent returns results from a different type (e.g., RNA expression instead of AnimalModel).

**How to detect:**
- Results are returned (non-zero) — query technically worked
- But `labels(a)` or `a.source` don't match what the question asked
- For Q2: should be `AnimalModel.GeneToDiseaseAssociation` (source: `impc`), not expression/genetic
- For Q3: should be clinical evidence types (GeneticAssociation, KnownDrug, SomaticMutation, Literature), not AnimalModel

### 4. `forgot_the_question`
**Agent got a working query but forgot to incorporate part of the question.**

**What happens:** Agent successfully queries the graph but omits a key constraint:
- For Q1: queries TARDBP but doesn't filter for ALS
- For Q2: queries TARDBP but doesn't filter for cancer or animal models
- For Q3: queries BRAF but doesn't filter for melanoma

**How to detect:**
- Query runs successfully with results
- But WHERE clause is missing disease name filter or evidence type filter
- Report discusses results that don't address the specific question

### 5. `gene_name`
**Agent can't find the correct gene.**

**What happens:**
- TDP-43 is a protein name; the gene symbol is TARDBP. Agent may search for "TDP-43" directly and fail.
- Agent may try various names but not find TARDBP
- Agent may ask for human help (which auto-responds "I don't know")

**How to detect:**
- Early iterations show failed gene lookups
- Agent searches for TDP-43, TDP43, TARDBP43, etc.
- Agent may give up after exhausting name variants

### 6. `disease`
**Agent uses too narrow or wrong disease term.**

**What happens:**
- Agent filters for a very specific disease variant instead of broader term
- e.g., searching for "amyotrophic lateral sclerosis type 10" instead of just "amyotrophic lateral sclerosis"
- Or agent confuses disease names

**How to detect:**
- Query has overly specific disease name in WHERE clause
- CONTAINS clause uses a variant name that's too narrow
- Few or zero results because the exact string doesn't match

### 7. `number_of_iterations`
**Agent hit the max iteration limit without producing a report.**

**How to detect:**
- No report generated
- HTML log shows the agent went through all 20 iterations
- Agent was still iterating/querying when it was cut off

### 8. `crash`
**System error or unexpected exception.**

**How to detect:**
- Python traceback in output
- Process terminated abnormally
- No clean completion

---

## Evaluation Procedure for HTML Chat Logs

For each run's HTML file:

1. **Check outcome:** Did the run produce a final report? If not → likely `number_of_iterations` or `crash`

2. **Check gene identification:** Did the agent find the correct gene? (TARDBP for Q1/Q2, BRAF for Q3)
   - If not → `gene_name`

3. **Check query pattern:** Look at the Cypher queries. Did the agent use the intermediate association node?
   - If not → `schema`

4. **Check directionality:** Did the agent use correct edge directions? (`Gene -> Assoc <- Disease`)
   - If agent used `Gene -> Assoc -> Disease` and got 0 results → `directionality`

5. **Check disease filter:** Did the query filter for the correct disease?
   - Missing or wrong disease → `forgot_the_question` or `disease`

6. **Check evidence type:** Did the results come from the correct evidence type?
   - Wrong evidence type → `evidence_type`

7. **Check final results:** Are the results non-zero and relevant?
   - If everything above is correct and results are relevant → `is_success = 1`

## Notes

- A run can have multiple issues but should be classified by the **primary** failure reason
- `partial_success` is only used with `is_success = 1` — it means the answer is acceptable but imperfect
- The `directionality` error is the most subtle: the agent often concludes "no data" when the data exists but the query path is wrong
- For Q2 specifically, animal model associations may exist but may not connect to cancer diseases — if the agent correctly identifies this limitation, it can still be a success
