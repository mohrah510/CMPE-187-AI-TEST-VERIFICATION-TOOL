import sys
sys.dont_write_bytecode = True
import re

def clean_text(text):
    """Remove markdown formatting, asterisks, and other formatting from text."""
    if not text or not isinstance(text, str):
        return ""
    
    # Remove markdown bold/italic (**, __, *)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'\*([^*\n]+)\*', r'\1', text)
    text = re.sub(r'_([^_\n]+)_', r'\1', text)
    
    # Remove standalone asterisks (but not in middle of words)
    text = re.sub(r'\s+\*\s+', ' ', text)
    text = re.sub(r'\*\s+', '', text)
    text = re.sub(r'\s+\*', '', text)
    
    # Remove markdown headers (#)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # Remove markdown lists (-, *, 1.)
    text = re.sub(r'^[\s]*[-*•]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Remove markdown code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove common prefixes that LLMs add
    text = re.sub(r'^Based on the provided inputs and contexts[,\s:]+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^Here is[,\s:]+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^According to[,\s:]+', '', text, flags=re.IGNORECASE)
    
    # Remove extra whitespace
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Clean up quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    return text.strip()

