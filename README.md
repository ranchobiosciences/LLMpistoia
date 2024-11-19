# LLM

Pistoia Alliance LLM project repository

This repository is for a Pistoia Alliance project whose aims are as follows 
We wish to explore the use of Large Language Models for biological research, using target discovery and validation as the initial use case. Target discovery was picked as a use case because it is a common process in all pharmaceutical R&D businesses that requires mining of large volumes of information. We plan to use prompt-tuned LLMs on a highly structured public data resource for the Retrieval-Augmented Generation (RAG) of plain English answers to the typical research questions asked in target discovery. Expected project outputs are a set of guidelines for the most advantageous use of LLMs in research and an open-source target discovery pipeline with prompt-tuned Large Language Models.

## Usage


To run the provided Jupyter notebooks, follow these steps:

1. **Create a Virtual Environment**:
   `python -m venv .venv`

2. **Activate the Virtual Environment**:
   - On Linux/Mac:
     `source venv/bin/activate`
   - On Windows:
     `venv\Scripts\activate`

3. **Install Dependencies**:
   `pip install -r requirements.txt`

4. **Launch Jupyter Notebook**:
   `jupyter notebook`
