import sys
import os
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
from config import MAX_TESTS, SCORE_THRESHOLD, VALIDATION_MODE, AIRLINE_CSV, VISA_CSV
from bots.chatgpt_client import ask_chatgpt
from bots.deepseek_client import ask_deepseek
from judge.llm_judge import judge_llm_response
from utils.csv_loader import load_testcases
from utils.excel_writer import save_results, save_summary


class TestVerificationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Test Verification Tool")
        self.root.geometry("800x600")
        
        self.selected_path = ""
        self.is_running = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Top frame for file selection
        top_frame = tk.Frame(self.root, padx=10, pady=10)
        top_frame.pack(fill=tk.X)
        
        # File selection
        tk.Label(top_frame, text="CSV File:").pack(side=tk.LEFT, padx=5)
        
        self.path_var = tk.StringVar(value="No file selected")
        path_label = tk.Label(top_frame, textvariable=self.path_var, 
                             relief=tk.SUNKEN, anchor=tk.W, width=50)
        path_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        btn_load = tk.Button(top_frame, text="Load CSV", command=self.load_file)
        btn_load.pack(side=tk.LEFT, padx=5)
        
        # Quick load buttons for default files
        quick_frame = tk.Frame(top_frame)
        quick_frame.pack(side=tk.LEFT, padx=5)
        tk.Label(quick_frame, text="Quick:").pack(side=tk.LEFT, padx=2)
        btn_airline = tk.Button(quick_frame, text="Airline", command=lambda: self.load_default(AIRLINE_CSV), 
                               width=8)
        btn_airline.pack(side=tk.LEFT, padx=2)
        btn_visa = tk.Button(quick_frame, text="Visa", command=lambda: self.load_default(VISA_CSV), 
                            width=8)
        btn_visa.pack(side=tk.LEFT, padx=2)
        
        # Start button
        btn_start = tk.Button(top_frame, text="Start Testing", 
                             command=self.start_testing, 
                             bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        btn_start.pack(side=tk.LEFT, padx=5)
        
        # Output area (like RichTextBox in C#)
        output_frame = tk.Frame(self.root, padx=10, pady=10)
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(output_frame, text="Output:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            wrap=tk.WORD, 
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white"
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                             relief=tk.SUNKEN, anchor=tk.W, bg="#f0f0f0")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def load_file(self):
        """Open file dialog to select CSV file (like btnLoad_Click)"""
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            self.selected_path = filename
            self.path_var.set(os.path.basename(filename))
            self.append_output(f"Loaded: {filename}\n")
            self.status_var.set(f"File loaded: {os.path.basename(filename)}")
    
    def load_default(self, default_path):
        """Load default CSV file from config"""
        if not os.path.isabs(default_path):
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            default_path = os.path.join(project_root, default_path)
        
        if os.path.exists(default_path):
            self.selected_path = default_path
            self.path_var.set(os.path.basename(default_path))
            self.append_output(f"Loaded default: {default_path}\n")
            self.status_var.set(f"File loaded: {os.path.basename(default_path)}")
        else:
            messagebox.showerror("File Not Found", f"Default file not found:\n{default_path}")
    
    def append_output(self, text):
        """Append text to output area"""
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_testing(self):
        """Start the testing process (like btnStart_Click)"""
        if not self.selected_path:
            messagebox.showwarning("No File", "Please select a CSV file first.")
            return
        
        if self.is_running:
            messagebox.showinfo("Already Running", "Testing is already in progress.")
            return
        
        # Clear output
        self.output_text.delete(1.0, tk.END)
        
        # Start in separate thread to keep GUI responsive
        thread = threading.Thread(target=self.run_tests, daemon=True)
        thread.start()
    
    def run_tests(self):
        """Run the test suite (like StartAskingQuestions)"""
        self.is_running = True
        self.status_var.set("Running tests...")
        
        try:
            # Load questions (like LoadQuestions)
            self.append_output(f"Loading test cases from: {self.selected_path}\n")
            self.append_output(f"Max Tests: {MAX_TESTS}, Threshold: {SCORE_THRESHOLD}%, Mode: {VALIDATION_MODE}\n\n")
            
            tests = load_testcases(self.selected_path)
            if not tests:
                self.append_output("No test cases found in file.\n")
                return
            
            results = []
            use_simple = (VALIDATION_MODE == 'simple')
            
            # Process each test case (like AskingQuestions)
            for idx, test_case in enumerate(tests, start=1):
                if idx > MAX_TESTS:
                    break
                
                question = test_case.get("question", "")
                self.append_output(f"Asking question: {question}\n")
                self.status_var.set(f"Processing test {idx}/{min(len(tests), MAX_TESTS)}...")
                
                # Get inputs
                input_1 = test_case.get("input_1", "")
                input_2 = test_case.get("input_2", "")
                input_3 = test_case.get("input_3", "")
                context_1 = test_case.get("context_1", "")
                context_2 = test_case.get("context_2", "")
                context_3 = test_case.get("context_3", "")
                expected_valid = test_case.get("expected_valid", "")
                
                # Ask ChatGPT
                try:
                    chatgpt_answer = ask_chatgpt(
                        question=question, input_1=input_1, input_2=input_2, input_3=input_3,
                        context_1=context_1, context_2=context_2, context_3=context_3,
                        test_set_type=""
                    )
                except Exception as e:
                    chatgpt_answer = f"[ChatGPT Error] {str(e)}"
                
                # Ask DeepSeek
                try:
                    deepseek_answer = ask_deepseek(
                        question=question, input_1=input_1, input_2=input_2, input_3=input_3,
                        context_1=context_1, context_2=context_2, context_3=context_3,
                        test_set_type=""
                    )
                except Exception as e:
                    deepseek_answer = f"[DeepSeek Error] {str(e)}"
                
                # Calculate accuracy (like CalculateAccuracy)
                try:
                    chatgpt_judge = judge_llm_response(
                        question=question, llm_answer=chatgpt_answer,
                        expected_valid=expected_valid, expected_invalid=None,
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
                        expected_valid=expected_valid, expected_invalid=None,
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
                
                # Display analysis (like AnalysisString)
                from config import RESPONSE_PREVIEW_LENGTH
                chatgpt_preview = chatgpt_answer[:RESPONSE_PREVIEW_LENGTH] + ("..." if len(chatgpt_answer) > RESPONSE_PREVIEW_LENGTH else "")
                deepseek_preview = deepseek_answer[:RESPONSE_PREVIEW_LENGTH] + ("..." if len(deepseek_answer) > RESPONSE_PREVIEW_LENGTH else "")
                
                self.append_output(f"\nChatGPT Response: {chatgpt_preview}\n")
                if chatgpt_expected_keywords:
                    self.append_output("ChatGPT Expected outputs:\n")
                    for i, keyword in enumerate(chatgpt_expected_keywords):
                        status = "True" if i < len(chatgpt_per_keyword) and chatgpt_per_keyword[i] else "False"
                        self.append_output(f"\t[{keyword} : {status}]\n")
                    chatgpt_matched = sum(1 for s in chatgpt_per_keyword if s) if chatgpt_per_keyword else 0
                    total = len(chatgpt_expected_keywords)
                    self.append_output(f"Total Correct: {chatgpt_matched} - {chatgpt_score:.1f}%.\n")
                self.append_output(f"Validity of response: {chatgpt_validity}\n")
                self.append_output(f"Reason: {chatgpt_validity_reason}.\n")
                
                self.append_output(f"\nDeepSeek Response: {deepseek_preview}\n")
                if deepseek_expected_keywords:
                    self.append_output("DeepSeek Expected outputs:\n")
                    for i, keyword in enumerate(deepseek_expected_keywords):
                        status = "True" if i < len(deepseek_per_keyword) and deepseek_per_keyword[i] else "False"
                        self.append_output(f"\t[{keyword} : {status}]\n")
                    deepseek_matched = sum(1 for s in deepseek_per_keyword if s) if deepseek_per_keyword else 0
                    total = len(deepseek_expected_keywords)
                    self.append_output(f"Total Correct: {deepseek_matched} - {deepseek_score:.1f}%.\n")
                self.append_output(f"Validity of response: {deepseek_validity}\n")
                self.append_output(f"Reason: {deepseek_validity_reason}.\n")
                self.append_output("\n\n")
                
                # Store results
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
                    "expected_keywords": chatgpt_expected_keywords
                })
            
            # Save results (like PrintAndPackage)
            self.append_output("\nSaving results to Excel...\n")
            base_name = os.path.splitext(os.path.basename(self.selected_path))[0]
            save_results(base_name, results)
            
            # Save console dump (like the C# code does)
            console_dump_path = self.selected_path.replace(".csv", " console dump.txt")
            with open(console_dump_path, "w", encoding="utf-8") as f:
                f.write(self.output_text.get(1.0, tk.END))
            
            self.append_output(f"Results saved to: output/{base_name}.xlsx\n")
            self.append_output(f"Console dump saved to: {console_dump_path}\n")
            self.append_output("\n✓ Testing completed!\n")
            
            self.status_var.set("Testing completed successfully!")
            messagebox.showinfo("Complete", f"Testing completed!\n\nResults saved to:\noutput/{base_name}.xlsx\n\nConsole dump:\n{console_dump_path}")
            
        except Exception as e:
            error_msg = f"Error during testing: {str(e)}"
            self.append_output(f"\n{error_msg}\n")
            self.status_var.set("Error occurred")
            messagebox.showerror("Error", error_msg)
        finally:
            self.is_running = False


def main():
    root = tk.Tk()
    app = TestVerificationGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

