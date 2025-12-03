import sys
sys.dont_write_bytecode = True
import csv
import os

def load_testcases(path):
    testcases = []
    
    if not os.path.isabs(path):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(project_root, path)

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="|")

        for row in reader:
            testcase = {
                "question": row.get("question", "").strip(),
                "input_1": row.get("input_1", "").strip(),
                "input_2": row.get("input_2", "").strip(),
                "input_3": row.get("input_3", "").strip(),
                "context_1": row.get("context_1", "").strip(),
                "context_2": row.get("context_2", "").strip(),
                "context_3": row.get("context_3", "").strip(),
                "expected_valid": row.get("expected_valid", "").strip(),
                "expected_invalid": row.get("expected_invalid", "").strip()
            }
            
            if testcase["question"]:
                testcases.append(testcase)

    return testcases
