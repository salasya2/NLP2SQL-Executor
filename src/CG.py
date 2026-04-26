from dotenv import load_dotenv
from langchain_groq import ChatGroq
# from langchain_core.prompts import PromptTemplate
from utils.logger import get_logger
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from templates.CG_prompt import SYS_PROMPT,USER_PROMPT
from src.SS import SSAgent
import os
import json
from src.CG_tool import CG_tool_mapping, CG_tools

load_dotenv(override=True)
logger = get_logger(__name__)


class CGAgent:

    def __init__(self, query, model_name = "llama-3.3-70b-versatile"):
        self.model = ChatGroq(api_key=os.getenv('GROQ_API_KEY'), model_name=model_name)
        self.model_with_tools = self.model.bind_tools(CG_tools)
        self.query = query
        self.SSAgent = SSAgent(self.query)
        self.SS_result = self.SSAgent.prune_schema()
        logger.info(f"Schema pruned: {self.SS_result}")

    def generate_sql(self):

        with open('index/index.json','r') as f:
            index = json.load(f)

        schema = ""
        foreign_keys = ""
        for table in self.SS_result[0]:
            table_cols = [(col,desc) for col,desc in self.SS_result[1] if col in index[table]['sample_values'].keys()]
            ddl_lines = [f" {col} TEXT, -- {desc}" for col,desc in table_cols]
            schema += f"\nCREATE TABLE {table} (\n" + "\n".join(ddl_lines) + "\n);\n"
            foreign_keys += f"\n{index[table]['foreign_keys']}"

        logger.info(f"Schema: {schema}\n")


        

        sys_message = SystemMessage(content=SYS_PROMPT)
        user_message = HumanMessage(content=USER_PROMPT.format(schema=schema,foreign_keys=foreign_keys,question=self.query))
        messages = [sys_message,user_message]
        MAX_ITER = 3

        for step in range(MAX_ITER):
            try:
                response = self.model_with_tools.invoke(messages)
            except Exception as e:
                logger.error(f"Error invoking model: {e}")
                response = AIMessage(content=f"ERROR: {e}")
            messages.append(response)
            logger.info(f"Response: {response}")
            if response.tool_calls:
                tool_call = response.tool_calls[0]
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                tool_result = CG_tool_mapping[tool_name].invoke(tool_args)
                messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call['id']))
            if not response.tool_calls:
                break

        
        return messages[-1].content



