import sqlite3
import pathlib
from utils.logger import get_logger
from utils.custom_exception import CustomException

logger = get_logger(__name__)
class QueryExecutor:

    def __init__(self,db_path):
        self.db_path = db_path
        logger.info(f"Initializing QueryExecutor for database: {db_path}")
        
        # Safely convert to an absolute URI (e.g. file:///C:/...)
        db_uri = f"{pathlib.Path(db_path).absolute().as_uri()}?mode=ro"
        
        self.conn = sqlite3.connect(db_uri, uri=True)
        logger.info("Database Connection Established")
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type,exc_val,exc_tb):
        if self.conn:
            self.conn.close()
            logger.info("Database Connection Closed")

    def query(self, query, verification_query = None):        
        cursor = self.conn.cursor()
        try:
            result = cursor.execute(query)

            if verification_query:
                logger.info("Executing Verification Query")
                cursor.execute(verification_query).fetchall()
                
            logger.info("Query Executed Successfully")
            return result.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error executing query: {e}")
            raise CustomException("Error executing query",e)



