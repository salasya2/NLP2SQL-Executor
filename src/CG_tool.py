from langchain_core.tools import tool
from utils.custom_exception import CustomException
from src.query import QueryExecutor
from utils.logger import get_logger

logger = get_logger(__name__)


@tool
def execute_query(query:str):
    """
    Executes a SQL query on the California Schools database.
    """

    try:
        with QueryExecutor('data/active/database.sqlite') as executor:
            result = executor.query(query)
            return result
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return f"SQL ERROR: {e}"  # Return error as string so LLM can observe and self-correct


CG_tools = [execute_query]
CG_tool_mapping = {tool.name:tool for tool in CG_tools}


