# This script checks if BioMix test-set is compatible with data in OpenTargets Neo4j database

library(tidyverse)
library(writexl)
library(readxl)


# True/False questions -----------------------------------------------------------------------------

# Extracting information about entities & what needs to be present in the database
# for true/false questions

df <- read_csv('testset/original/true_false_biomix.csv') %>% 
  mutate(qid = row_number())



# Gene-Disease associations

df1 <- df %>% 
  filter(str_detect(text, "is not associated with Gene")) %>% 
  mutate(rel = "disease_gene", dir = "invert") %>% 
  extract(text, "^(.*)\\s+is not associated with Gene\\s+(.*)$", into = c('s','o'), remove=FALSE) %>% 
  mutate(s_type = "disease", o_type = "gene", p ="associated")

dx <- df %>% anti_join(df1, by = 'qid')

df2 <- dx %>% 
  filter(str_detect(text, "associates Gene")) %>% 
  mutate(rel = "disease_gene", dir = "direct") %>% 
  extract(text, "^(.*)\\s+associates Gene\\s+(.*)$", into = c('s','o'), remove=FALSE)  %>% 
  mutate(s_type = "disease", o_type = "gene", p ="associated")

dx <- dx %>% anti_join(df2, by = 'qid')

  
# Disease ontology identifier

df3 <- dx %>%
  filter(str_detect(text, "Disease ontology identifier")) %>% 
  mutate(rel = "doid_id", dir = "direct") %>% 
  extract(text, "^Disease ontology identifier for\\s+(.*)\\s+is\\s+(DOID.*)", into=c('s','o'), remove = FALSE) %>% 
  mutate(s_type = "disease", o_type = "onto_id", p="has_id")

dx <- dx %>% anti_join(df3, by = 'qid')


# Treat

df4 <- dx %>%
  filter(str_detect(text, " treats ")) %>% 
  mutate(rel = "treats", dir = "direct") %>% 
  extract(text, "^(.*)\\s+treats\\s+(.*)", into=c('s','o'), remove = FALSE) %>% 
  mutate(s_type = "drug", o_type = "disease", p="treats") 

dx <- dx %>% anti_join(df4, by = 'qid')


# Subclass of (inverted)

df5 <- dx %>%
  filter(str_detect(text, " is not a ")) %>% 
  mutate(rel = "subclass", dir = "invert") %>% 
  extract(text, "^(.*)\\s+is not a\\s+(.*)", into=c('s','o'), remove = FALSE) %>% 
  mutate(s_type = "disease", o_type = "disease", p="subclass of") 

dx <- dx %>% anti_join(df5, by = 'qid')

# Subclass of (direct)

df6 <- dx %>%
  filter(str_detect(text, " is a ")) %>% 
  mutate(rel = "subclass", dir = "direct") %>% 
  extract(text, "^(.*)\\s+is a\\s+(.*)", into=c('s','o'), remove = FALSE) %>% 
  mutate(s_type = "disease", o_type = "disease", p="subclass of") 

dx <- dx %>% anti_join(df6, by = 'qid')


# Variant associations

df7 <- dx %>%
  filter(str_detect(text, "^Variant")) %>% 
  mutate(rel = "disease_variant", dir = "direct") %>% 
  extract(text, "^Variant\\s+(.*)\\s+associates\\s+(.*)", into=c('s','o'), remove = FALSE) %>% 
  mutate(s_type = "variant", o_type = "disease", p="associated") 

dx <- dx %>% anti_join(df7, by = 'qid')


# Merging & saving

df_TF <- bind_rows(df1, df2, df3, df4, df5, df6, df7) %>% 
  mutate(q_type = "tf")
df_TF %>% 
  write_xlsx("testset/biomix_true_false_processed.xlsx")


# Multiple QA --------------------------------------------------------------------------------------

df <- read_csv('testset/original/mcq_biomix.csv') %>% 
  mutate(qid = row_number())

df1 <- df %>%
  filter(str_detect(text, "which Gene is associated")) %>% 
  mutate(rel = "disease_gene", dir = "direct") %>% 
  extract(text, "which Gene is associated with\\s+(.*)\\.\\s+Given list", into = c('s'), remove=FALSE) %>% 
  mutate(s_type = "disease", o_type = "gene", p ="associated")

dx <- df %>% anti_join(df1, by = 'qid')

df2 <- df %>% 
  filter(str_detect(text, "which Variant is associated")) %>% 
  mutate(rel = "disease_variant", dir = "direct") %>% 
  extract(text, "which Variant is associated with\\s+(.*)\\.\\s+Given list", into = c('s'), remove=FALSE) %>% 
  mutate(s_type = "disease", o_type = "variant", p ="associated")

dx <- dx %>% anti_join(df2, by = 'qid')

df_MA <- bind_rows(df1, df2) %>% 
  mutate(q_type = 'mcq')

# disease is actually a combination of 2 diseases

dis <- df_MA %>% 
  distinct(s)

dis2 <- dis %>% 
  filter(str_detect(s, " and .* and ")) %>% 
  extract(s, "^(.*[^d]) and (.*)", into=c('s1', 's2'), remove = FALSE)

dis1 <- dis %>% 
  filter(!str_detect(s, " and .* and ")) %>%  
  extract(s, "^(.*) and (.*)", into=c('s1', 's2'), remove = FALSE)

df_MA <- df_MA %>% 
  left_join(
    bind_rows(dis1, dis2), by = 's'
  ) 
df_MA %>% 
  write_xlsx("testset/biomix_mcq_processed.xlsx")


# Making a list of entities to look up -------------------------------------------------------------

entities <- bind_rows(
  df_TF %>% select(name = s, type = s_type), 
  df_TF %>% select(name = o, type = o_type),
  df_MA %>% select(name = s1, type = s_type), 
  df_MA %>% select(name = s1, type = s_type),
  df_MA %>% select(name = option_A, type = o_type), 
  df_MA %>% select(name = option_B, type = o_type),
  df_MA %>% select(name = option_C, type = o_type), 
  df_MA %>% select(name = option_D, type = o_type), 
  df_MA %>% select(name = option_E, type = o_type)
) %>% 
  distinct()

entities %>% 
  write_xlsx("db/entities.xlsx")

# Run neo4j on the list of entities (count_entities.py). It will save results to 
# db/entities_queried_inexact.xlsx and db/entities_queried_exact.xlsx


# Checking against existing entities ----------------------------------------------------------------

q_entities <- bind_rows(
  df_TF %>% select(name = s, type = s_type, qid, q_type), 
  df_TF %>% select(name = o, type = o_type, qid, q_type),
  df_MA %>% select(name = s1, type = s_type, qid, q_type), 
  df_MA %>% select(name = s1, type = s_type, qid, q_type),
  df_MA %>% select(name = option_A, type = o_type, qid, q_type), 
  df_MA %>% select(name = option_B, type = o_type, qid, q_type),
  df_MA %>% select(name = option_C, type = o_type, qid, q_type),
  df_MA %>% select(name = option_D, type = o_type, qid, q_type),
  df_MA %>% select(name = option_E, type = o_type, qid, q_type)
) %>% 
  distinct()

res_inx <- read_xlsx('db/entities_queried_inexact.xlsx') %>% rename(nres_inexact = nresults)
res_exa <- read_xlsx('db/entities_queried_exact.xlsx') %>% rename(nres_exact = nresults)

res <- res_inx %>% 
  left_join(res_exa, by = c('name', 'type'))

q_entities <- q_entities %>%
  left_join(res, by = c('name', 'type')) 

# We will only include cases where there is an exact match with disease term

problem_entities <- q_entities %>% 
  filter(is.na(nres_inexact) | nres_exact == 0) %>% 
  distinct(q_type, qid)

df_MA_selected <- df_MA %>% 
  anti_join(problem_entities, by = c('qid', 'q_type')) 

df_MA_selected %>% 
  write_xlsx(".temp/biomix_mcq_selected_entities.xlsx")

df_TF_selected <- df_TF %>% 
  anti_join(problem_entities, by = c('qid', 'q_type'))  %>% 
  filter(rel == 'disease_gene')

df_TF_selected %>% 
  write_xlsx(".temp/biomix_tf_selected_entities.xlsx")


# Making a list of queries to ask ------------------------------------------------------------------

gene_disease_selected <- bind_rows(
  df_TF_selected %>% 
    select(disease = s, gene = o), 
  
  bind_rows(
    df_MA_selected %>% select(disease = s1, starts_with("option")), 
    df_MA_selected %>% select(disease = s2, starts_with("option"))) %>% 
    pivot_longer(cols = -c(disease)) %>% 
    select(disease, -name, gene=value)
  ) %>% 
  distinct()


# we will check if database has relationships:

gene_disease_selected %>% 
  write_xlsx("db/gene_disease_queries.xlsx")


# Loading and evaluating answers -------------------------------------------------------------------

# Selecting answers that do not exist

ans_exact <- read_excel("db/gene_disease_queries_exact.xlsx") %>% rename(counts_exact = counts)
ans_inex  <- read_excel("db/gene_disease_queries_inexact.xlsx") %>% rename(counts_inexact = counts)

# there are some cases where number of exact and inexact relationships do not match. 
# we'll drop those

join_gd <- c("gene", "disease")

answers <- ans_exact %>% 
  left_join(ans_inex, by = join_gd) %>% 
  mutate(has_exact = counts_exact > 0) %>% 
  mutate(has_inexact = counts_inexact > 0) 

bad_questions <- answers %>% 
  filter(has_exact != has_inexact) %>% 
  distinct(disease, gene)

answers <- answers %>% 
  anti_join(bad_questions, by = join_gd) %>% 
  select(gene, disease, answer = has_exact)

# checking TF results

df_TF_selected_answers <- df_TF_selected %>%
  mutate(has_relations = ifelse(dir == 'invert', !label, label)) %>% 
  select(qid, q_type, gene=o, disease = s, has_relations) %>% 
  semi_join(answers, by = join_gd)

df_TF_selected_answers %>% 
  left_join(answers, by = join_gd) %>% 
  filter(has_relations == answer) 

df_TF %>% 
  semi_join(df_TF_selected_answers, by = c('qid')) %>% 
  write_xlsx("testset/biomix_true_false_selected.xlsx")

df_TF_selected_answers %>% 
  write_xlsx(".temp/biomix_tf_selected_answers.xlsx")

# Okay, a data point: all TF questions that could be answered 
# Also: all gene and diseases relationship actually exist! 

df_MA_selected_answers <- df_MA_selected %>% 
  select(s, s1, s2, qid, q_type, starts_with('option'), correct_answer) %>% 
  pivot_longer(cols = -c(s, s1, s2, qid, q_type, correct_answer)) %>% 
  select(-name) %>% 
  mutate(gene = value) %>% 
  mutate(has_relations = (gene == correct_answer)) %>% 
  select(-correct_answer, -value) %>% 
  mutate(disease1 = s1, disease2 = s2, all_diseases = s)

# Filtering out cases where there are some invalid gene/disease pairs from the bad list:

ambiguous_MA_questions_1 <- bind_rows(
  df_MA_selected_answers %>% semi_join(bad_questions, by = c('gene', 'disease1'= 'disease')),
  df_MA_selected_answers %>% semi_join(bad_questions, by = c('gene', 'disease2'= 'disease'))) %>% 
  distinct(qid, q_type)

# for the remaining questions we have two diseases
# We will only keep questions where same gene is associated with both of the disases.
# because question says "disease1 and disease2"

# essentially this means that has_relationship should be equal to answer1 and answer2
df_MA_trick_questions <- df_MA_selected_answers %>% 
  anti_join(ambiguous_MA_questions_1, by = c("qid", "q_type")) %>% 
  left_join(answers %>% rename(answer1=answer), by = c('gene', 'disease1' = 'disease')) %>% 
  left_join(answers %>% rename(answer2=answer), by = c('gene', 'disease2' = 'disease')) %>%
  filter(has_relations != answer1 | has_relations != answer2) %>% 
  distinct(qid, q_type)

df_MA_good_questions <- df_MA_selected_answers %>% 
  anti_join(ambiguous_MA_questions_1, by = c("qid", "q_type")) %>%
  anti_join(df_MA_trick_questions, by = c("qid", "q_type")) 

# there are 10 multi-choice questions