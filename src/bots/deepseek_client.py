import sys
sys.dont_write_bytecode = True
import requests
from config import DEEPSEEK_API_KEY
from utils.text_cleaner import clean_text

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

def ask_deepseek(question: str, input_1: str = "", input_2: str = "", input_3: str = "",
                 context_1: str = "", context_2: str = "", context_3: str = "",
                 test_set_type: str = "") -> str:
    prompt_parts = []
    
    if test_set_type == "airline_policy":
        prompt_parts.append("IMPORTANT: All questions are specifically about Emirates Airlines policies, services, and regulations. Please answer with Emirates Airlines-specific information only.")
    elif test_set_type == "visa_guidance":
        prompt_parts.append("IMPORTANT: All questions are specifically about UAE (United Arab Emirates) visa requirements, regulations, and policies. Please answer with UAE-specific information only.")
    
    prompt_parts.append(f"Question: {question}")
    
    if input_1:
        prompt_parts.append(f"Input 1: {input_1}")
    if input_2:
        prompt_parts.append(f"Input 2: {input_2}")
    if input_3:
        prompt_parts.append(f"Input 3: {input_3}")
    if context_1:
        prompt_parts.append(f"Context 1: {context_1}")
    if context_2:
        prompt_parts.append(f"Context 2: {context_2}")
    if context_3:
        prompt_parts.append(f"Context 3: {context_3}")
    
    prompt_parts.append("\nPlease provide a comprehensive answer based on the above information.")
    full_prompt = "\n".join(prompt_parts)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": full_prompt}]
    }

    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            error_msg = data["error"].get("message", str(data["error"]))
            return f"[DeepSeek Error] {error_msg}"
        
        if "choices" not in data or not data["choices"]:
            return f"[DeepSeek Error] No choices in response"
        
        raw_response = data["choices"][0]["message"]["content"].strip()
        return clean_text(raw_response)

    except requests.exceptions.HTTPError as e:
        try:
            error_data = e.response.json()
            error_msg = error_data.get("error", {}).get("message", str(e))
            return f"[DeepSeek Error] HTTP {e.response.status_code}: {error_msg}"
        except:
            return f"[DeepSeek Error] HTTP {e.response.status_code}: {str(e)}"
    except Exception as e:
        return f"[DeepSeek Error] {str(e)}"
