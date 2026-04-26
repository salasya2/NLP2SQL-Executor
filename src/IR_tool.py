from langchain_core.tools import tool
from dotenv import load_dotenv
import json
from utils.logger import get_logger

logger = get_logger(__name__)
load_dotenv()

with open('index/index.json', 'r') as f:
    index = json.load(f)


@tool
def search_index(entities: list[str],keywords: list[str]):
    """
    Search the database index for relevant tables based on keywords.
    """
    all_search_terms = keywords + entities
    table_scores = {table_name : 0 for table_name in index.keys()}
    logger.info("Starting Index search")
    for keyword in all_search_terms:
        for table_name, table_data in index.items():
            
            if keyword.lower() in table_name.lower():
                table_scores[table_name] += 1
            
            for columns in table_data['columns']:
                if keyword.lower() in columns[1].lower():
                    table_scores[table_name] += 2
            
            for values in table_data['sample_values'].values():
                if 'sample_values' not in values:
                    continue
                if keyword.lower() in str(values['sample_values']).lower():
                    table_scores[table_name] += 3

    sorted_tables = sorted(table_scores.items(), key = lambda x: x[1], reverse = True)
    top_tables = [table[0] for table in sorted_tables[:3] if table[1] > 0]
    logger.info(f"Top tables found: {top_tables}")

    # relevant_columns = set()
    # for table in top_tables:
    #     column_scores = {column[1] : 0 for column in index[table]['columns']}
    #     for keyword in all_search_terms:
    #         for columns in index[table]['columns']:
    #             if keyword.lower() in columns[1].lower():
    #                 column_scores[columns[1]] += 1
            
    #         for col_name, values in index[table]['sample_values'].items():
    #             if keyword.lower() in str(values).lower():
    #                 if col_name in column_scores:
    #                     column_scores[col_name] += 3
        
    #     sorted_columns = sorted(column_scores.items(), key = lambda x: x[1], reverse = True)
    #     top_columns = [column[0] for column in sorted_columns[:3] if column[1] > 0]
    #     relevant_columns.update(top_columns)
    #     logger.info(f"Top columns found: {top_columns}")

    if not top_tables:
        return "No relevant tables found"
    return top_tables

tools = [search_index]
tools_mapping = {tool.name : tool for tool in tools}



