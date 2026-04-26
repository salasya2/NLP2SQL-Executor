
import sys


class CustomException(Exception):

    def __init__(self,message:str,error_detail:Exception = None):

        self.error_message = self.get_detailed_error_message(message,error_detail)
        super().__init__(self.error_message)

    @staticmethod
    def get_detailed_error_message(message:str, error_detail : Exception):

        _,_,exc_tb = sys.exc_info()
        linenumber = exc_tb.tb_lineno
        filename = exc_tb.tb_frame.f_code.co_filename

        error_message = f"Error occured in file {filename} at line number {linenumber} with error {error_detail}"

        return error_message

    def __str__(self):
        return self.error_message