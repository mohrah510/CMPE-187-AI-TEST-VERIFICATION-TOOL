import sys
import os
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import AIRLINE_CSV, VISA_CSV, MAX_TESTS, SCORE_THRESHOLD, VALIDATION_MODE, RESPONSE_PREVIEW_LENGTH
from bots.chatgpt_client import ask_chatgpt
from bots.deepseek_client import ask_deepseek
from judge.llm_judge import judge_llm_response
from utils.csv_loader import load_testcases
from utils.excel_writer import save_results, save_summary


def run_testset(name, path):
    tests = load_testcases(path)
    results = []

    for idx, test_case in enumerate(tests, start=1):
        if idx > MAX_TESTS:
            break

        print(f"[{idx}/{MAX_TESTS}] {test_case['question'][:50]}...")

        question = test_case.get("question", "")
        input_1 = test_case.get("input_1", "")
        input_2 = test_case.get("input_2", "")
        input_3 = test_case.get("input_3", "")
        context_1 = test_case.get("context_1", "")
        context_2 = test_case.get("context_2", "")
        context_3 = test_case.get("context_3", "")
        expected_valid = test_case.get("expected_valid", "")
        expected_invalid = test_case.get("expected_invalid", "")

        try:
            chatgpt_answer = ask_chatgpt(
                question=question, input_1=input_1, input_2=input_2, input_3=input_3,
                context_1=context_1, context_2=context_2, context_3=context_3,
                test_set_type=name
            )
        except Exception as e:
            chatgpt_answer = f"[ChatGPT Error] {str(e)}"

        try:
            deepseek_answer = ask_deepseek(
                question=question, input_1=input_1, input_2=input_2, input_3=input_3,
                context_1=context_1, context_2=context_2, context_3=context_3,
                test_set_type=name
            )
        except Exception as e:
            deepseek_answer = f"[DeepSeek Error] {str(e)}"

        use_simple = (VALIDATION_MODE == 'simple')
        
        try:
            chatgpt_judge = judge_llm_response(
                question=question, llm_answer=chatgpt_answer,
                expected_valid=expected_valid, expected_invalid=expected_invalid,
                use_simple=use_simple
            )
            chatgpt_score = chatgpt_judge.get("score", 0.0)
            chatgpt_validity = chatgpt_judge.get("validity", "Unknown")
            chatgpt_validity_reason = chatgpt_judge.get("validity_reason", "")
            chatgpt_per_keyword = chatgpt_judge.get("per_keyword_status", [])
            chatgpt_expected_keywords = chatgpt_judge.get("expected_keywords_list", [])
        except Exception as e:
            chatgpt_score = 0.0
            chatgpt_validity = f"[Error] {str(e)}"
            chatgpt_validity_reason = f"[Error] {str(e)}"
            chatgpt_per_keyword = []
            chatgpt_expected_keywords = []

        try:
            deepseek_judge = judge_llm_response(
                question=question, llm_answer=deepseek_answer,
                expected_valid=expected_valid, expected_invalid=expected_invalid,
                use_simple=use_simple
            )
            deepseek_score = deepseek_judge.get("score", 0.0)
            deepseek_validity = deepseek_judge.get("validity", "Unknown")
            deepseek_validity_reason = deepseek_judge.get("validity_reason", "")
            deepseek_per_keyword = deepseek_judge.get("per_keyword_status", [])
            deepseek_expected_keywords = deepseek_judge.get("expected_keywords_list", [])
        except Exception as e:
            deepseek_score = 0.0
            deepseek_validity = f"[Error] {str(e)}"
            deepseek_validity_reason = f"[Error] {str(e)}"
            deepseek_per_keyword = []
            deepseek_expected_keywords = []

        gpt_status = "✓" if chatgpt_validity == "Valid" else "✗"
        ds_status = "✓" if deepseek_validity == "Valid" else "✗"
        print(f"  ChatGPT: {gpt_status} {chatgpt_score:.1f}% | DeepSeek: {ds_status} {deepseek_score:.1f}%")
        
        # Print detailed analysis (like sample group's AnalysisString)
        if chatgpt_expected_keywords and (chatgpt_per_keyword or deepseek_per_keyword):
            print(f"\n  Expected Outputs:")
            for i, keyword in enumerate(chatgpt_expected_keywords):
                gpt_match = "True" if i < len(chatgpt_per_keyword) and chatgpt_per_keyword[i] else "False"
                ds_match = "True" if i < len(deepseek_per_keyword) and deepseek_per_keyword[i] else "False"
                print(f"    [{keyword}: GPT={gpt_match}, DS={ds_match}]")
            
            chatgpt_matched = sum(1 for status in chatgpt_per_keyword if status) if chatgpt_per_keyword else 0
            deepseek_matched = sum(1 for status in deepseek_per_keyword if status) if deepseek_per_keyword else 0
            total = len(chatgpt_expected_keywords)
            print(f"  Total Correct: GPT={chatgpt_matched}/{total} ({chatgpt_score:.1f}%), DS={deepseek_matched}/{total} ({deepseek_score:.1f}%)")
            print(f"  Validity: GPT={chatgpt_validity} ({chatgpt_validity_reason})")
            print(f"            DS={deepseek_validity} ({deepseek_validity_reason})")

        # Truncate responses for preview (like sample group)
        chatgpt_preview = chatgpt_answer[:RESPONSE_PREVIEW_LENGTH] if len(chatgpt_answer) > RESPONSE_PREVIEW_LENGTH else chatgpt_answer
        deepseek_preview = deepseek_answer[:RESPONSE_PREVIEW_LENGTH] if len(deepseek_answer) > RESPONSE_PREVIEW_LENGTH else deepseek_answer
        
        results.append({
            "test_number": idx,
            "question": question,
            "input_1": input_1,
            "input_2": input_2,
            "input_3": input_3,
            "context_1": context_1,
            "context_2": context_2,
            "context_3": context_3,
            "expected_valid": expected_valid,
            "chatgpt_answer": chatgpt_answer,
            "deepseek_answer": deepseek_answer,
            "chatgpt_preview": chatgpt_preview,
            "deepseek_preview": deepseek_preview,
            "chatgpt_score": chatgpt_score,
            "deepseek_score": deepseek_score,
            "chatgpt_validity": chatgpt_validity,
            "deepseek_validity": deepseek_validity,
            "chatgpt_validity_reason": chatgpt_validity_reason,
            "deepseek_validity_reason": deepseek_validity_reason,
            "chatgpt_per_keyword": chatgpt_per_keyword,
            "deepseek_per_keyword": deepseek_per_keyword,
            "expected_keywords": chatgpt_expected_keywords  # Same for both, just use one
        })

    save_results(name, results)
    print(f"\nSaved: output/{name}.xlsx")
    
    return results


def main():
    print(f"\nAI Test Verification Tool (Max: {MAX_TESTS}, Threshold: {SCORE_THRESHOLD}%)\n")

    # Run tests and collect results
    airline_results = run_testset("airline_policy", AIRLINE_CSV)
    visa_results = run_testset("visa_guidance", VISA_CSV)
    
    # Create summary file
    save_summary(airline_results, visa_results)
    print(f"Saved: output/test_summary.xlsx")
    
    print("\nDone\n")


if __name__ == "__main__":
    main()
