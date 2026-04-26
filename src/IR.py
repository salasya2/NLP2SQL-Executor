from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
import os
from src.IR_tool import tools_mapping,tools
from templates.IR_prompt import IR_PROMPT
from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

class IRAgent:
    def __init__(self,model_name="llama-3.3-70b-versatile"):
        self.model = ChatGroq(api_key=os.getenv('GROQ_API_KEY'), model_name=model_name)
        self.model_with_tools = self.model.bind_tools(tools)
        self.prompt = PromptTemplate.from_template(IR_PROMPT)
        self.chain = self.prompt | self.model_with_tools

    def extract_keywords(self,question):
        response = self.chain.invoke({"question": question})
        IR_result = response.tool_calls[0]['args']
        response = tools_mapping['search_index'].invoke(IR_result)
        logger.info(f"Tables found: {response}")
        return {"tables": response, "keywords": IR_result['keywords'], "entities": IR_result['entities']}




