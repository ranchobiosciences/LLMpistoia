Updating biomix test-set to work with OT data

The script `biomix_check_compatibility.R` checks compatibility of biomix test-set (https://huggingface.co/datasets/kg-rag/BiomixQA) with data in KG.

Sripts `count_entities.py` and `count_gene_disease.py` are used to generate statistics on number of entities and relationships in the KG. 

Script `biomix_extended.R` creates an extended version of BioMix test-set that is used in LLM evaluation:

There are 134 True/False questions that can be answered with KG. Script randomly samples 50 questions:
- 25 questions in the form "disease is associated with gene" where answer is True
- 25 questions in the form "disease is not associated with gene" where answer is False

The the script augments these questions by generating gene/disease combinations (same genes & diseases, but no relationship according to OT Knowledge Graph
- 25 questions in the form "disease is associated with gene" where answer is False
- 25 questions in the form "disease is not associated with gene" where answer is True

Resulting test-set contains 100 questions. Two non-intersecting versions are generated:

- `testset/biomix_true_false_selected_augmented.csv` - is used to for testing
- `testset/biomix_true_false_selected_augmented_2.csv` - is used for training of DSPy models

Corresponding xlsx files contain entity labels and additional information that could be used to construct cypher queries


