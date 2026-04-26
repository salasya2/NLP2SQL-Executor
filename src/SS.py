from src.IR import IRAgent
from src.SS_tool import select_tables, select_columns

class SSAgent:
    def __init__(self,query):
        self.select_tables = select_tables
        self.select_columns = select_columns
        self.IR = IRAgent()
        self.IR_result = self.IR.extract_keywords(query)

    def prune_schema(self):
        return self.select_tables(self.IR_result['tables'],self.IR_result['keywords'],self.IR_result['entities']), self.select_columns(self.IR_result['tables'],self.IR_result['keywords'],self.IR_result['entities'])


# print(SSAgent("What is the Charter School number in Alameda county for the year 2014-2015?").prune_schema())

    
