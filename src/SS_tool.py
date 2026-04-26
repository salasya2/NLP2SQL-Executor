from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import json
import os
from utils.logger import get_logger
from utils.custom_exception import CustomException

load_dotenv()

logger = get_logger(__name__)

with open('index/index.json','r') as f:
    index = json.load(f)


def select_columns(tables: list[str], keywords: list[str], entities: list[str]):
    """
    Select relevant columns from a table using a single batched LLM call.
    The LLM sees ALL columns and their descriptions at once for accurate decisions.
    """
    relevant_columns = set()
    prompt = PromptTemplate.from_template("""You are a SQL schema analyst. Given a table schema and a natural language query, return ONLY the column names needed to answer the query.

    Rules:
    - Include columns needed for SELECT, WHERE, JOIN, GROUP BY, or ORDER BY.
    - Exclude columns that are irrelevant to the query.
    - Output ONLY a comma-separated list of column names. No explanation, no extra text.

    Example:
    Table: [frpm,schools]
    Columns:
    - County: Name of the California county
    - CharterNum: Charter School Number
    - Magnet: 1=Magnet school, 0=Not magnet
    - Longitude: Geographic longitude
    - Latitude: Geographic latitude
    Keywords: ["Longitude","Latitude"]
    Entities: ["Alameda county"]
    Answer:
    {{"columns": ["Longitude","Latitude","County"]}}

    Now evaluate:
    Table: {table_name}
    Columns:
    {schema}
    Keywords: {keywords}
    Entities: {entities}

    Answer:
    {{"columns": [<only the relevant column names from the list above>]}}
    """)
    model = ChatGroq(api_key=os.getenv('GROQ_API_KEY'), model_name="llama-3.3-70b-versatile")
    chain = prompt | model
    for table_name in tables:
        columns = index[table_name]['columns']
        

        # Build full schema string: one line per column with its description
        schema_lines = []
        for col in columns:
            col_name = col[1]
            sample_info = index[table_name]['sample_values'].get(col_name, {})
            desc = sample_info.get('value_description', '') if isinstance(sample_info, dict) else ''
            desc = desc or 'No description'
            schema_lines.append(f"  - {col_name}: {desc}")
        schema_str = "\n".join(schema_lines)

        
        response = chain.invoke({
            "table_name": table_name,
            "schema": schema_str,
            "keywords": keywords,
            "entities": entities
        })
        content = response.content.strip()
        logger.info(f"LLM raw response for [{table_name}]: {content}")

        try:
            parsed = json.loads(content)
            cols = parsed.get("columns", [])
            if isinstance(cols, str):
                cols = [c.strip().strip('"') for c in cols.split(",") if c.strip()]
        except (json.JSONDecodeError, AttributeError):
            cols = [c.strip().strip('"') for c in content.split(",") if c.strip()]

        valid_cols = set(index[table_name]['sample_values'].keys())
        for col in cols:
            if col in valid_cols:
                relevant_columns.add((col,index[table_name]['sample_values'][col]['value_description']))
            else:
                logger.warning(f"Skipping unknown column: '{col}'")

    return relevant_columns



def select_tables(tables : list[str] , keywords : list[str], entities : list[str]):
    
    
    prompt = PromptTemplate.from_template("""
        You are given a list of tables and their descriptions. 
        Return the tables that are relevant to the query.

         Example:
            Table: [Country,State,Revenue, Tourists]
            Columns:
            - Country_name: Name of the country
            - State_name: Name of the state
            - Revenue_year: Revenue year
            - Revenue: Revenue of the state
            - numTourists: Number of tourists per year

            Keywords: ["no of Tourists"]
            Entities: ["California"]
            Answer:
            {{"tables": ["State","Tourists"]}}



        Now Evaluate:
        Tables:{tables}
        table summary : {table_summary}
        keywords : {keywords}
        Entities : {entities}

        Output only the json. No reasoning. No explanation. Return only the table names that are relevant to the query.
        {{"tables": [<only the relevant table names from the list above>]}}
        
    
    """)
    model = ChatGroq(api_key=os.getenv('GROQ_API_KEY'), model_name="llama-3.3-70b-versatile")
    table_summary = ""
    for table in tables:
        col_descriptions = []
        for col_name, values in index[table]['sample_values'].items():
            col_descriptions.append(f"{col_name}: {values.get('value_description')}")
        table_summary  +=  f"\n{table} - {','.join(col_descriptions[:5])}"

    chain = prompt | model
    response = chain.invoke({
        "tables": tables,
        "table_summary": table_summary,
        "keywords": keywords,
        "entities": entities
    })

    content = response.content.strip()
    logger.info(f"LLM raw response for [{tables}]: {content}")
    

    try:

        parsed = json.loads(content)
        relevant_tables = parsed['tables']

    except(json.JSONDecodeError, AttributeError):
        relevant_tables = [t.strip().strip('"') for t in content.split(",") if t.strip()]
    

    valid_tables = set(index.keys())
    
    for t in relevant_tables:
        if t not in valid_tables:
            logger.warning(f"Skipping unknown table: '{t}'")
            relevant_tables.remove(t)
    
    return relevant_tables

