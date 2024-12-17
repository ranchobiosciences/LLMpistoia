# This script generates a BioMix test-set augmented by negative relationships
# Augmented test-set will contain 50 gene/disease relationships from original BioMix
# and 50 gene/disease relationships that are not present in the database

library(tidyverse)
library(readxl)
library(writexl)

# Selected 50 gene/disease relationships from BioMix:

biomix_orig <- read_xlsx("testset/biomix_true_false_selected.xlsx")

set.seed(42)

# shuffle the rows:
biomix_tf <- biomix_orig[sample(nrow(biomix_orig)),]

biomix_positive <- biomix_tf %>% 
  group_by(label) %>% 
  filter(row_number() <= 25) %>%    # this is version 1 (test set)
  #filter(row_number() > 25 & row_number() <= 50) %>%  # this is version 2 (training set)
  ungroup()


# To reduce the effect of knowledge of specific genes/disease, we will include 
# only genes & diseases that are present in positive test-set. 
# This is hard because only few genes are present. 
# Instead, we will generate all gene / disease combinations and check in the database.

# Generating gene/disease combinations:

genes <- biomix_positive %>% 
  select(gene=o) %>% 
  distinct() %>% 
  mutate(dummy = 1)

diseases <- biomix_positive %>%
  select(disease=s) %>% 
  distinct() %>% 
  mutate(dummy = 1)

gene_disease_combinations <- genes %>%
  left_join(diseases, by = "dummy", relationship = "many-to-many") %>% 
  select(gene, disease) %>% 
  distinct()

gene_disease_combinations %>% 
  write_xlsx("db/gene_disease_combinations.xlsx")


# To construct negative test-set we need queried relationships

rel_exact <- read_xlsx("db/gene_disease_queries_combinations_exact.xlsx") 
rel_inexact <- read_xlsx("db/gene_disease_queries_combinations_inexact.xlsx")

empty_rels <- rel_exact %>% 
  left_join(rel_inexact, by = c("gene" = "gene", "disease" = "disease")) %>% 
  filter(counts.x == 0, counts.y == 0) %>% 
  distinct(gene, disease) 

# For every gene, sample 1 disease at random:
biomix_negative <- empty_rels %>% 
  group_by(gene) %>% 
  sample_n(1) %>% 
  ungroup()

# Randomly split into 2 halves. For the 1st half, label is "TRUE", for the second - FALSE

biomix_negative <- biomix_negative[sample(nrow(biomix_negative)),] %>% 
  mutate(label = ifelse(row_number() <= nrow(biomix_negative)/2, TRUE, FALSE))

biomix_negative_upd <- biomix_negative %>% 
  mutate(s = disease, o = gene, rel = "disease_gene", s_type = 'disease', o_type = 'gene') %>%
  mutate(p = 'associated', q_type = 'tf') %>% 
  mutate(dir = ifelse(label, 'invert', 'direct')) %>% 
  mutate(text = str_c(disease, " is ",ifelse(label, "not ",""),"associated with Gene ", gene)) %>% 
  select(-gene, -disease)

full <- bind_rows(biomix_positive, biomix_negative_upd) 

full %>%
  write_xlsx("testset/biomix_true_false_selected_augmented.xlsx")

full %>% 
  select(text, label) %>% 
  mutate(label = ifelse(label, "True", "False")) %>% 
  write_csv("testset/biomix_true_false_selected_augmented.csv")  
