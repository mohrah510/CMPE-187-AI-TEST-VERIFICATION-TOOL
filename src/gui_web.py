import sys
import os
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template_string, request, jsonify, send_from_directory, make_response
import threading
import webbrowser
import socket
import time
from config import MAX_TESTS, SCORE_THRESHOLD, VALIDATION_MODE, AIRLINE_CSV, VISA_CSV
from bots.chatgpt_client import ask_chatgpt
from bots.deepseek_client import ask_deepseek
from judge.llm_judge import judge_llm_response
from utils.csv_loader import load_testcases
from utils.excel_writer import save_results
import json

app = Flask(__name__)

# Disable Flask's strict slashes to avoid 403 errors
app.url_map.strict_slashes = False

# Add CORS headers to allow local access (simplified for localhost)
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Global state
test_state = {
    "status": "ready",
    "output": [],
    "progress": {"current": 0, "total": 0, "file_index": 0, "total_files": 0},
    "selected_files": [],  # Changed to support multiple files
    "is_running": False
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Test Verification Tool</title>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        .file-input-wrapper {
            flex: 1;
            min-width: 200px;
        }
        input[type="file"] {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            width: 100%;
        }
        .file-list {
            margin-top: 10px;
            padding: 10px;
            background: #f9f9f9;
            border-radius: 4px;
            max-height: 150px;
            overflow-y: auto;
        }
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 5px;
            margin: 3px 0;
            background: white;
            border-radius: 3px;
        }
        .file-item button {
            padding: 4px 8px;
            font-size: 11px;
            background: #f44336;
        }
        .file-item button:hover {
            background: #d32f2f;
        }
        .btn-run-all {
            background: #FF9800;
            color: white;
            font-weight: bold;
        }
        .btn-run-all:hover { background: #F57C00; }
        .quick-buttons {
            display: flex;
            gap: 5px;
        }
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        .btn-primary {
            background: #4CAF50;
            color: white;
            font-weight: bold;
        }
        .btn-primary:hover { background: #45a049; }
        .btn-secondary {
            background: #2196F3;
            color: white;
        }
        .btn-secondary:hover { background: #0b7dda; }
        .btn-small {
            padding: 8px 15px;
            font-size: 12px;
        }
        .status-bar {
            background: #f0f0f0;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .output-area {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            line-height: 1.6;
            max-height: 500px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .output-area::-webkit-scrollbar {
            width: 10px;
        }
        .output-area::-webkit-scrollbar-track {
            background: #2d2d2d;
        }
        .output-area::-webkit-scrollbar-thumb {
            background: #555;
            border-radius: 5px;
        }
        .output-area::-webkit-scrollbar-thumb:hover {
            background: #777;
        }
        .file-info {
            color: #666;
            font-size: 12px;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>AI Test Verification Tool</h1>
        
        <div class="controls">
            <div class="file-input-wrapper">
                <input type="file" id="fileInput" accept=".csv" multiple />
                <div class="file-info" id="fileInfo">No files selected (you can select multiple)</div>
            </div>
            <div class="quick-buttons">
                <button class="btn-secondary btn-small" onclick="loadDefault('airline')">Airline</button>
                <button class="btn-secondary btn-small" onclick="loadDefault('visa')">Visa</button>
            </div>
            <button class="btn-primary" onclick="startTesting()">Start Testing (Current)</button>
            <button class="btn-run-all" onclick="startAllTests()">Run All Tests</button>
        </div>
        
        <div class="file-list" id="fileList" style="display: none;">
            <strong>Selected Files:</strong>
            <div id="fileItems"></div>
        </div>
        
        <div class="status-bar" id="statusBar">Ready</div>
        
        <div class="output-area" id="outputArea">Waiting for file selection...</div>
    </div>

    <script>
        let selectedFile = null;
        let isRunning = false;

        let selectedFiles = [];
        
        document.getElementById('fileInput').addEventListener('change', function(e) {
            const files = Array.from(e.target.files);
            if (files.length > 0) {
                selectedFiles = files;
                updateFileList();
                uploadFiles(files);
            }
        });
        
        function updateFileList() {
            const fileList = document.getElementById('fileList');
            const fileItems = document.getElementById('fileItems');
            
            if (selectedFiles.length === 0) {
                fileList.style.display = 'none';
                document.getElementById('fileInfo').textContent = 'No files selected (you can select multiple)';
                return;
            }
            
            fileList.style.display = 'block';
            fileItems.innerHTML = '';
            
            selectedFiles.forEach((file, index) => {
                const item = document.createElement('div');
                item.className = 'file-item';
                item.innerHTML = `
                    <span>${file.name}</span>
                    <button onclick="removeFile(${index})">Remove</button>
                `;
                fileItems.appendChild(item);
            });
            
            document.getElementById('fileInfo').textContent = `${selectedFiles.length} file(s) selected`;
        }
        
        function removeFile(index) {
            selectedFiles.splice(index, 1);
            updateFileList();
            // Update the file input
            const dataTransfer = new DataTransfer();
            selectedFiles.forEach(file => dataTransfer.items.add(file));
            document.getElementById('fileInput').files = dataTransfer.files;
            uploadFiles(selectedFiles);
        }
        
        function uploadFiles(files) {
            const formData = new FormData();
            Array.from(files).forEach((file, index) => {
                formData.append(`file${index}`, file);
            });
            formData.append('count', files.length);
            
            fetch('/upload_multiple', {
                method: 'POST',
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    updateStatus(`${files.length} file(s) loaded`);
                } else {
                    alert('Error uploading files: ' + data.error);
                }
            });
        }

        function loadDefault(type) {
            fetch('/load_default', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({type: type})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    // Add to selected files
                    const file = {name: data.filename};
                    if (!selectedFiles.find(f => f.name === file.name)) {
                        selectedFiles.push(file);
                    }
                    updateFileList();
                    updateStatus('File loaded: ' + data.filename);
                } else {
                    alert('Error: ' + data.error);
                }
            });
        }

        function uploadFile(file) {
            const formData = new FormData();
            formData.append('file', file);
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    updateStatus('File loaded: ' + file.name);
                } else {
                    alert('Error uploading file: ' + data.error);
                }
            });
        }

        function startTesting() {
            if (isRunning) {
                alert('Testing is already in progress.');
                return;
            }
            
            fetch('/start', {method: 'POST'})
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    isRunning = true;
                    document.getElementById('outputArea').textContent = '';
                    updateStatus('Running tests...');
                    pollOutput();
                } else {
                    alert('Error: ' + data.error);
                }
            });
        }
        
        function startAllTests() {
            if (isRunning) {
                alert('Testing is already in progress.');
                return;
            }
            
            if (selectedFiles.length === 0) {
                alert('Please select at least one file first.');
                return;
            }
            
            fetch('/start_all', {method: 'POST'})
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    isRunning = true;
                    document.getElementById('outputArea').textContent = '';
                    updateStatus(`Running tests on ${data.file_count} file(s)...`);
                    pollOutput();
                } else {
                    alert('Error: ' + data.error);
                }
            });
        }

        function pollOutput() {
            const interval = setInterval(() => {
                fetch('/status')
                    .then(r => r.json())
                    .then(data => {
                        if (data.output) {
                            document.getElementById('outputArea').textContent = data.output;
                            document.getElementById('outputArea').scrollTop = document.getElementById('outputArea').scrollHeight;
                        }
                        
                        if (data.status) {
                            updateStatus(data.status);
                        }
                        
                        if (data.status && data.status.includes('completed')) {
                            clearInterval(interval);
                            isRunning = false;
                            if (data.results_file) {
                                alert('Testing completed!\\n\\nResults saved to: ' + data.results_file);
                            }
                        }
                    });
            }, 500);
        }

        function updateStatus(text) {
            document.getElementById('statusBar').textContent = text;
        }

        // Auto-refresh status on load
        setInterval(() => {
            fetch('/status')
                .then(r => r.json())
                .then(data => {
                    if (data.status && !isRunning) {
                        updateStatus(data.status);
                    }
                });
        }, 2000);
    </script>
</body>
</html>
"""

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Server is running"}), 200

@app.route('/')
@app.route('/index')
def index():
    """Main page route"""
    try:
        return render_template_string(HTML_TEMPLATE)
    except Exception as e:
        error_msg = f"Error loading page: {str(e)}"
        print(f"Error in index route: {error_msg}")
        return error_msg, 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file provided"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"})
    
    # Save uploaded file temporarily
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    try:
        os.makedirs(upload_dir, exist_ok=True, mode=0o755)
    except PermissionError as e:
        return jsonify({"success": False, "error": f"Permission denied creating uploads directory: {str(e)}"})
    
    filepath = os.path.join(upload_dir, file.filename)
    try:
        file.save(filepath)
        os.chmod(filepath, 0o644)  # Make file readable
    except PermissionError as e:
        return jsonify({"success": False, "error": f"Permission denied saving file: {str(e)}"})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error saving file: {str(e)}"})
    
    # Keep single file for backward compatibility
    test_state["selected_files"] = [filepath]
    test_state["status"] = f"File loaded: {file.filename}"
    test_state["output"] = [f"Loaded: {filepath}\n"]
    
    return jsonify({"success": True, "filename": file.filename})

@app.route('/upload_multiple', methods=['POST'])
def upload_multiple_files():
    """Handle multiple file uploads"""
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    try:
        os.makedirs(upload_dir, exist_ok=True, mode=0o755)
    except PermissionError as e:
        return jsonify({"success": False, "error": f"Permission denied creating uploads directory: {str(e)}"})
    
    uploaded_files = []
    file_count = int(request.form.get('count', 0))
    
    for i in range(file_count):
        file_key = f'file{i}'
        if file_key in request.files:
            file = request.files[file_key]
            if file.filename:
                filepath = os.path.join(upload_dir, file.filename)
                try:
                    file.save(filepath)
                    os.chmod(filepath, 0o644)  # Make file readable
                    uploaded_files.append(filepath)
                except PermissionError as e:
                    return jsonify({"success": False, "error": f"Permission denied saving file {file.filename}: {str(e)}"})
                except Exception as e:
                    return jsonify({"success": False, "error": f"Error saving file {file.filename}: {str(e)}"})
    
    if not uploaded_files:
        return jsonify({"success": False, "error": "No files provided"})
    
    test_state["selected_files"] = uploaded_files
    test_state["status"] = f"{len(uploaded_files)} file(s) loaded"
    test_state["output"] = [f"Loaded {len(uploaded_files)} file(s)\n"]
    
    return jsonify({"success": True, "count": len(uploaded_files), "files": [os.path.basename(f) for f in uploaded_files]})

@app.route('/load_default', methods=['POST'])
def load_default():
    data = request.json
    file_type = data.get('type', '')
    
    if file_type == 'airline':
        default_path = AIRLINE_CSV
    elif file_type == 'visa':
        default_path = VISA_CSV
    else:
        return jsonify({"success": False, "error": "Invalid file type"})
    
    if not os.path.isabs(default_path):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        default_path = os.path.join(project_root, default_path)
    
    if os.path.exists(default_path):
        test_state["selected_files"] = [default_path]
        test_state["status"] = f"File loaded: {os.path.basename(default_path)}"
        test_state["output"] = [f"Loaded default: {default_path}\n"]
        return jsonify({"success": True, "filename": os.path.basename(default_path)})
    else:
        return jsonify({"success": False, "error": f"File not found: {default_path}"})

@app.route('/start', methods=['POST'])
def start_testing():
    if test_state["is_running"]:
        return jsonify({"success": False, "error": "Testing already in progress"})
    
    if not test_state["selected_files"]:
        return jsonify({"success": False, "error": "No file selected"})
    
    # Use first file for single test (backward compatibility)
    test_state["selected_file"] = test_state["selected_files"][0] if test_state["selected_files"] else ""
    
    # Start testing in background thread
    thread = threading.Thread(target=run_tests, daemon=True)
    thread.start()
    
    return jsonify({"success": True})

@app.route('/start_all', methods=['POST'])
def start_all_tests():
    """Start testing on all selected files"""
    if test_state["is_running"]:
        return jsonify({"success": False, "error": "Testing already in progress"})
    
    if not test_state["selected_files"]:
        return jsonify({"success": False, "error": "No files selected"})
    
    # Start testing all files in background thread
    thread = threading.Thread(target=run_all_tests, daemon=True)
    thread.start()
    
    return jsonify({"success": True, "file_count": len(test_state["selected_files"])})

@app.route('/status')
def get_status():
    output_text = "\n".join(test_state["output"])
    progress = test_state["progress"]
    
    # Build detailed status if multiple files
    status = test_state["status"]
    if progress.get("total_files", 0) > 1:
        file_idx = progress.get("file_index", 0)
        total_files = progress.get("total_files", 0)
        current = progress.get("current", 0)
        total = progress.get("total", 0)
        if file_idx > 0 and total > 0:
            status = f"File {file_idx}/{total_files}: Test {current}/{total} - {status}"
    
    return jsonify({
        "status": status,
        "output": output_text,
        "progress": progress,
        "results_file": test_state.get("results_file", "")
    })

def append_output(text):
    test_state["output"].append(text)
    # Keep only last 1000 lines to prevent memory issues
    if len(test_state["output"]) > 1000:
        test_state["output"] = test_state["output"][-1000:]

def run_tests():
    test_state["is_running"] = True
    test_state["output"] = []
    test_state["status"] = "Running tests..."
    
    try:
        # Use first file from selected_files or fallback to selected_file for backward compatibility
        if test_state["selected_files"]:
            filepath = test_state["selected_files"][0]
        else:
            filepath = test_state.get("selected_file", "")
        append_output(f"Loading test cases from: {filepath}\n")
        append_output(f"Max Tests: {MAX_TESTS}, Threshold: {SCORE_THRESHOLD}%, Mode: {VALIDATION_MODE}\n\n")
        
        tests = load_testcases(filepath)
        if not tests:
            append_output("No test cases found in file.\n")
            test_state["status"] = "Error: No test cases found"
            test_state["is_running"] = False
            return
        
        results = []
        use_simple = (VALIDATION_MODE == 'simple')
        total_tests = min(len(tests), MAX_TESTS)
        
        for idx, test_case in enumerate(tests, start=1):
            if idx > MAX_TESTS:
                break
            
            test_state["progress"] = {"current": idx, "total": total_tests}
            test_state["status"] = f"Processing test {idx}/{total_tests}..."
            
            question = test_case.get("question", "")
            append_output(f"Asking question: {question}\n")
            
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
            
            # Calculate accuracy
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
            
            # Display analysis
            from config import RESPONSE_PREVIEW_LENGTH
            chatgpt_preview = chatgpt_answer[:RESPONSE_PREVIEW_LENGTH] + ("..." if len(chatgpt_answer) > RESPONSE_PREVIEW_LENGTH else "")
            deepseek_preview = deepseek_answer[:RESPONSE_PREVIEW_LENGTH] + ("..." if len(deepseek_answer) > RESPONSE_PREVIEW_LENGTH else "")
            
            append_output(f"\nChatGPT Response: {chatgpt_preview}\n")
            if chatgpt_expected_keywords:
                append_output("ChatGPT Expected outputs:\n")
                for i, keyword in enumerate(chatgpt_expected_keywords):
                    status = "True" if i < len(chatgpt_per_keyword) and chatgpt_per_keyword[i] else "False"
                    append_output(f"\t[{keyword} : {status}]\n")
                chatgpt_matched = sum(1 for s in chatgpt_per_keyword if s) if chatgpt_per_keyword else 0
                total = len(chatgpt_expected_keywords)
                append_output(f"Total Correct: {chatgpt_matched} - {chatgpt_score:.1f}%.\n")
            append_output(f"Validity of response: {chatgpt_validity}\n")
            append_output(f"Reason: {chatgpt_validity_reason}.\n")
            
            append_output(f"\nDeepSeek Response: {deepseek_preview}\n")
            if deepseek_expected_keywords:
                append_output("DeepSeek Expected outputs:\n")
                for i, keyword in enumerate(deepseek_expected_keywords):
                    status = "True" if i < len(deepseek_per_keyword) and deepseek_per_keyword[i] else "False"
                    append_output(f"\t[{keyword} : {status}]\n")
                deepseek_matched = sum(1 for s in deepseek_per_keyword if s) if deepseek_per_keyword else 0
                total = len(deepseek_expected_keywords)
                append_output(f"Total Correct: {deepseek_matched} - {deepseek_score:.1f}%.\n")
            append_output(f"Validity of response: {deepseek_validity}\n")
            append_output(f"Reason: {deepseek_validity_reason}.\n")
            append_output("\n\n")
            
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
        
        # Save results
        append_output("\nSaving results to Excel...\n")
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        try:
            save_results(base_name, results)
        except PermissionError as e:
            append_output(f"✗ Permission denied saving Excel file: {str(e)}\n")
            raise
        except Exception as e:
            append_output(f"✗ Error saving Excel file: {str(e)}\n")
            raise
        
        # Save console dump
        console_dump_path = filepath.replace(".csv", " console dump.txt")
        try:
            with open(console_dump_path, "w", encoding="utf-8") as f:
                f.write("\n".join(test_state["output"]))
        except PermissionError as e:
            append_output(f"⚠ Permission denied saving console dump: {str(e)}\n")
        except Exception as e:
            append_output(f"⚠ Error saving console dump: {str(e)}\n")
        
        append_output(f"Results saved to: output/{base_name}.xlsx\n")
        append_output(f"Console dump saved to: {console_dump_path}\n")
        append_output("\n✓ Testing completed!\n")
        
        test_state["status"] = "Testing completed successfully!"
        test_state["results_file"] = f"output/{base_name}.xlsx"
        
    except Exception as e:
        error_msg = f"Error during testing: {str(e)}"
        append_output(f"\n{error_msg}\n")
        test_state["status"] = "Error occurred"
    finally:
        test_state["is_running"] = False

def run_all_tests():
    """Run tests on all selected files sequentially"""
    test_state["is_running"] = True
    test_state["output"] = []
    test_state["status"] = "Running tests on all files..."
    
    try:
        files = test_state["selected_files"]
        if not files:
            append_output("No files selected.\n")
            test_state["status"] = "Error: No files selected"
            test_state["is_running"] = False
            return
        
        total_files = len(files)
        test_state["progress"] = {"current": 0, "total": 0, "file_index": 0, "total_files": total_files}
        
        append_output(f"Starting batch testing on {total_files} file(s)...\n")
        append_output(f"Max Tests per file: {MAX_TESTS}, Threshold: {SCORE_THRESHOLD}%, Mode: {VALIDATION_MODE}\n")
        append_output("=" * 60 + "\n\n")
        
        all_results = []
        use_simple = (VALIDATION_MODE == 'simple')
        
        for file_idx, filepath in enumerate(files, start=1):
            filename = os.path.basename(filepath)
            test_state["progress"]["file_index"] = file_idx
            test_state["status"] = f"Processing file {file_idx}/{total_files}: {filename}"
            
            append_output(f"\n{'='*60}\n")
            append_output(f"FILE {file_idx}/{total_files}: {filename}\n")
            append_output(f"{'='*60}\n")
            append_output(f"Loading test cases from: {filepath}\n\n")
            
            try:
                tests = load_testcases(filepath)
                if not tests:
                    append_output(f"⚠ No test cases found in {filename}. Skipping...\n\n")
                    continue
                
                results = []
                total_tests = min(len(tests), MAX_TESTS)
                
                for idx, test_case in enumerate(tests, start=1):
                    if idx > MAX_TESTS:
                        break
                    
                    test_state["progress"] = {
                        "current": idx, 
                        "total": total_tests,
                        "file_index": file_idx,
                        "total_files": total_files
                    }
                    test_state["status"] = f"File {file_idx}/{total_files}: Test {idx}/{total_tests} - {filename}"
                    
                    question = test_case.get("question", "")
                    append_output(f"[{file_idx}/{total_files}] [{idx}/{total_tests}] Asking question: {question}\n")
                    
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
                    
                    # Calculate accuracy
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
                    
                    # Display analysis
                    from config import RESPONSE_PREVIEW_LENGTH
                    chatgpt_preview = chatgpt_answer[:RESPONSE_PREVIEW_LENGTH] + ("..." if len(chatgpt_answer) > RESPONSE_PREVIEW_LENGTH else "")
                    deepseek_preview = deepseek_answer[:RESPONSE_PREVIEW_LENGTH] + ("..." if len(deepseek_answer) > RESPONSE_PREVIEW_LENGTH else "")
                    
                    append_output(f"\nChatGPT Response: {chatgpt_preview}\n")
                    if chatgpt_expected_keywords:
                        append_output("ChatGPT Expected outputs:\n")
                        for i, keyword in enumerate(chatgpt_expected_keywords):
                            status = "True" if i < len(chatgpt_per_keyword) and chatgpt_per_keyword[i] else "False"
                            append_output(f"\t[{keyword} : {status}]\n")
                        chatgpt_matched = sum(1 for s in chatgpt_per_keyword if s) if chatgpt_per_keyword else 0
                        total = len(chatgpt_expected_keywords)
                        append_output(f"Total Correct: {chatgpt_matched} - {chatgpt_score:.1f}%.\n")
                    append_output(f"Validity of response: {chatgpt_validity}\n")
                    append_output(f"Reason: {chatgpt_validity_reason}.\n")
                    
                    append_output(f"\nDeepSeek Response: {deepseek_preview}\n")
                    if deepseek_expected_keywords:
                        append_output("DeepSeek Expected outputs:\n")
                        for i, keyword in enumerate(deepseek_expected_keywords):
                            status = "True" if i < len(deepseek_per_keyword) and deepseek_per_keyword[i] else "False"
                            append_output(f"\t[{keyword} : {status}]\n")
                        deepseek_matched = sum(1 for s in deepseek_per_keyword if s) if deepseek_per_keyword else 0
                        total = len(deepseek_expected_keywords)
                        append_output(f"Total Correct: {deepseek_matched} - {deepseek_score:.1f}%.\n")
                    append_output(f"Validity of response: {deepseek_validity}\n")
                    append_output(f"Reason: {deepseek_validity_reason}.\n")
                    append_output("\n\n")
                    
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
                
                # Save results for this file
                append_output(f"\nSaving results for {filename}...\n")
                base_name = os.path.splitext(filename)[0]
                try:
                    save_results(base_name, results)
                    append_output(f"✓ Saved: output/{base_name}.xlsx\n")
                except PermissionError as e:
                    append_output(f"✗ Permission denied saving {filename}: {str(e)}\n")
                    continue
                except Exception as e:
                    append_output(f"✗ Error saving {filename}: {str(e)}\n")
                    continue
                
                all_results.append({
                    "filename": filename,
                    "results": results
                })
                
            except Exception as e:
                error_msg = f"Error processing {filename}: {str(e)}"
                append_output(f"\n✗ {error_msg}\n")
                continue
        
        # Save console dump
        console_dump_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "batch_console_dump.txt")
        try:
            with open(console_dump_path, "w", encoding="utf-8") as f:
                f.write("\n".join(test_state["output"]))
        except PermissionError as e:
            append_output(f"⚠ Permission denied saving console dump: {str(e)}\n")
        except Exception as e:
            append_output(f"⚠ Error saving console dump: {str(e)}\n")
        
        append_output(f"\n{'='*60}\n")
        append_output(f"✓ Batch testing completed!\n")
        append_output(f"Processed {len(all_results)} file(s) successfully.\n")
        append_output(f"Console dump saved to: {console_dump_path}\n")
        append_output(f"{'='*60}\n")
        
        test_state["status"] = f"Batch testing completed! Processed {len(all_results)}/{total_files} file(s)"
        test_state["results_file"] = f"Multiple files - see output/ directory"
        
    except Exception as e:
        error_msg = f"Error during batch testing: {str(e)}"
        append_output(f"\n{error_msg}\n")
        test_state["status"] = "Error occurred"
    finally:
        test_state["is_running"] = False

def find_free_port(start_port=5001):
    """Find a free port starting from start_port (default 5001 to avoid macOS AirPlay on 5000)"""
    for port in range(start_port, start_port + 100):
        try:
            # Test if port is actually free
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_socket.bind(('127.0.0.1', port))
            test_socket.listen(1)
            test_socket.close()
            return port
        except OSError:
            test_socket.close()
            continue
    return None

def main():
    # Check directory permissions
    project_root = os.path.dirname(os.path.dirname(__file__))
    uploads_dir = os.path.join(project_root, 'uploads')
    output_dir = os.path.join(project_root, 'output')
    
    try:
        os.makedirs(uploads_dir, exist_ok=True, mode=0o755)
        os.makedirs(output_dir, exist_ok=True, mode=0o755)
    except PermissionError as e:
        print(f"\n✗ Permission Error: Cannot create directories")
        print(f"  Error: {str(e)}")
        print(f"\n  Try running: ./fix_permissions.sh")
        print(f"  Or manually: chmod 755 uploads output")
        return
    
    # Start from 5001 to avoid macOS AirPlay on port 5000
    # Start from 5001 to avoid macOS AirPlay on port 5000
    port = find_free_port(5001)
    if not port:
        print("Error: Could not find a free port (tried 5001-5100). Please close other applications.")
        return
    
    url = f"http://127.0.0.1:{port}"
    health_url = f"http://127.0.0.1:{port}/health"
    print(f"\n{'='*60}")
    print(f"AI Test Verification Tool - Web GUI")
    print(f"{'='*60}")
    print(f"Server starting on: {url}")
    print(f"Health check: {health_url}")
    print(f"Opening browser automatically...")
    print(f"\nIf browser doesn't open, manually visit: {url}")
    print(f"Press Ctrl+C to stop the server\n")
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(2.0)
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Could not open browser automatically: {e}")
            print(f"Please manually visit: {url}")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        # Use threaded=True to handle multiple requests
        app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False, threaded=True)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\nError: Port {port} is already in use.")
            print(f"Please close the application using that port or try again.")
        else:
            print(f"\nError starting server: {e}")
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()

