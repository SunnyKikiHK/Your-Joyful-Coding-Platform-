import sys
import subprocess
from sqlalchemy.orm import Session
from src.crud import question as question_crud

def run_code_submission(db: Session, question_id: int, code: str):
    #fetch the question and its test cases
    question = question_crud.get_question(db, question_id=question_id)
    if not question:
        return None  #return None so the api layer can handle the 404

    #iterate through each test case
    for index, test_case in enumerate(question.test_cases):
        input_data = test_case["input"]
        expected_output = test_case["expected_output"]

        #construct the executable script
        executable_code = f"""
{code}

# Execution block dynamically added by backend
try:
    result = {input_data}
    print(result)
except Exception as e:
    print(f"Error: {{e}}")
"""
        
        #run the code in an isolated subprocess with a strict 2-second timeout
        try:
            process = subprocess.run(
                [sys.executable, "-c", executable_code], 
                capture_output=True,
                text=True,
                timeout=2.0 
            )
            
            #check for runtime errors
            if process.returncode != 0:
                return {
                    "status": "Runtime Error",
                    "failed_case_index": index,
                    "error_message": process.stderr.strip()
                }

            #capture stdout and compare to expected output
            actual_output = process.stdout.strip()
            
            if actual_output != str(expected_output).strip():
                return {
                    "status": "Wrong Answer",
                    "failed_case_index": index,
                    "expected": expected_output,
                    "actual": actual_output
                }

        except subprocess.TimeoutExpired:
            return {"status": "Time Limit Exceeded", "failed_case_index": index}

    #all test cases passed
    return {"status": "Accepted", "message": "All test cases passed!"}