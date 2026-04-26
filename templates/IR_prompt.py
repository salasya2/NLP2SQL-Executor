from langchain_core.prompts import PromptTemplate

IR_PROMPT = """
 You are an expert in the CHESS SQL database schema.
 Your goal is to analyze the user's question and extract:
 1. Keywords: Important terms that will help you search the database index.
 2. Entities: Specific values (names, codes, dates,years, numbers) that should be used for filtering.

 Use the search_index tool to perform the extractions.

Return the output in the following JSON format:
{{
    "keywords": ["keyword1", "keyword2", ...],
    "entities": ["entity1", "entity2", ...]
}}

Question: {question}
"""
"""
# You are an expert in the CHESS SQL database schema.
# Your goal is to analyze the user's question and extract:
# 1. Keywords: Important terms that will help you search the database index.
# 2. Entities: Specific values (names, codes, dates, numbers) that should be used for filtering.

# Use the search_index tool to perform the extractions.

# eg:- 
# Question: Which school in Alameda county has the highest enrollment?
# Keywords: ["school", "highest", "enrollment"]
# Entities: ["Alameda"]

# Question: What is the total enrollment in Los Angeles county for the year 2023-2024?
# Keywords: ["total", "enrollment", "year"]
# Entities: ["Los Angeles", "2023-2024"]

# Return the output in the following JSON format:
# {{
#     "keywords": ["keyword1", "keyword2", ...],
#     "entities": ["entity1", "entity2", ...]
# }}


# """
