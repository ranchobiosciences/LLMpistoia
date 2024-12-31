library(readxl)
library(tidyverse)

dt <- read_xlsx("04c-evaluations_curated.xlsx")
dt %>% names()


full_success <- dt %>% 
  mutate(res = (is_success == 1 & is.na(partial_success))) %>% 
  group_by(model) %>% 
  summarize(full_success = mean(res) * 100)

partial_success <-  dt %>% 
  mutate(res = (is_success == 1)) %>% 
  group_by(model) %>% 
  summarize(partial_success = mean(res) *100)

failures <- dt %>% 
  mutate(failure_type = ifelse(is_success == 0, failure_type, "success")) %>% 
  select(model, failure_type) %>% 
  group_by(model, failure_type) %>% 
  summarize(count = n(), .groups = 'drop') %>% 
  group_by(model) %>% 
  mutate(percentage = count / sum(count) * 100) %>%
  select(-count) %>% 
  pivot_wider(names_from = failure_type, values_from = percentage, values_fill = 0) %>% 
  ungroup() %>% 
  select(-success)

full_success %>% 
  left_join(partial_success, by = 'model') %>% 
  left_join(failures, by= 'model') %>% 
  arrange(model) %>% 
  print() %>% 
  write_tsv("statistics.tsv", na = '')
    
