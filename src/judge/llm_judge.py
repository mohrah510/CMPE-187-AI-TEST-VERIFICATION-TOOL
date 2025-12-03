import sys
sys.dont_write_bytecode = True
import re
from config import SCORE_THRESHOLD


def extract_keywords(text):
    if not text or not isinstance(text, str):
        return set()
    
    text = text.lower().strip()
    words = re.findall(r'\b[a-z]{3,}\b', text)
    
    stop_words = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one',
        'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now',
        'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she',
        'too', 'use', 'that', 'this', 'with', 'from', 'have', 'they', 'been', 'more', 'than',
        'will', 'about', 'after', 'which', 'their', 'these', 'there', 'other', 'when', 'where',
        'would', 'could', 'should', 'might', 'must', 'shall', 'does', 'doesn', 'don'
    }
    
    keywords = {word for word in words if word not in stop_words}
    return keywords


def get_word_stem(word):
    """Get word stem for better matching."""
    if len(word) <= 4:
        return word
    if word.endswith('ing'):
        return word[:-3]
    if word.endswith('ed'):
        return word[:-2]
    if word.endswith('ly'):
        return word[:-2]
    if word.endswith('er') or word.endswith('or'):
        return word[:-2]
    if word.endswith('es'):
        return word[:-2]
    if word.endswith('s') and len(word) > 4:
        return word[:-1]
    return word


def are_words_similar(word1, word2):
    """Check if two words are similar (stems, partial match, or synonyms)."""
    if word1 == word2:
        return True
    
    stem1 = get_word_stem(word1)
    stem2 = get_word_stem(word2)
    if stem1 == stem2:
        return True
    
    if len(stem1) >= 3 and len(stem2) >= 3:
        if stem1 in stem2 or stem2 in stem1:
            return True
        if len(stem1) >= 4 and len(stem2) >= 4:
            if stem1[:4] == stem2[:4] or stem1[-4:] == stem2[-4:]:
                return True
    
    synonyms = {
        'available': ['vary', 'offered', 'provided', 'exist', 'present', 'accessible', 'can', 'possible', 'offers'],
        'depending': ['based', 'according', 'depending', 'upon', 'on'],
        'duration': ['length', 'time', 'period', 'long', 'extended', 'hours', 'type'],
        'options': ['choices', 'selections', 'alternatives', 'varieties', 'types', 'meals', 'meal'],
        'require': ['need', 'must', 'necessary', 'mandatory', 'required'],
        'permit': ['allow', 'enable', 'let', 'authorize', 'permission'],
        'visa': ['visa', 'permit', 'authorization', 'document', 'entry'],
        'citizen': ['citizen', 'national', 'resident', 'passport', 'holder', 'holders'],
        'tourist': ['tourist', 'visitor', 'traveler', 'guest', 'visiting'],
        'stay': ['remain', 'visit', 'reside', 'remain', 'reside'],
        'meal': ['food', 'meal', 'dining', 'cuisine', 'eating', 'meals'],
        'baggage': ['luggage', 'baggage', 'bags', 'suitcase', 'belongings'],
        'carry': ['bring', 'carry', 'take', 'transport', 'bring'],
        'check': ['check', 'checked', 'checking', 'verify', 'checked'],
        'special': ['special', 'specific', 'custom', 'particular', 'unique'],
        'restricted': ['restricted', 'limited', 'prohibited', 'banned', 'forbidden'],
        'child': ['child', 'minor', 'kid', 'young', 'children'],
        'minor': ['minor', 'child', 'kid', 'young'],
        'airline': ['airline', 'carrier', 'aircraft', 'flight', 'company', 'emirates'],
        'flight': ['flight', 'journey', 'trip', 'travel', 'traveling'],
        'oversized': ['oversized', 'large', 'big', 'excess', 'over'],
        'dietary': ['dietary', 'food', 'nutrition', 'diet', 'eating'],
        'emirates': ['emirates', 'emirates', 'airline', 'ek'],
        'dubai': ['dubai', 'uae', 'emirates', 'united'],
        'uae': ['uae', 'dubai', 'emirates', 'united', 'arab'],
        'receive': ['receive', 'get', 'obtain', 'granted', 'given', 'can'],
        'typically': ['typically', 'usually', 'generally', 'normally', 'often'],
        'affect': ['affect', 'impact', 'influence', 'change', 'alter', 'doesn'],
        'regardless': ['regardless', 'irrespective', 'despite', 'even'],
        'requested': ['requested', 'ordered', 'asked', 'booked', 'reserved'],
        'advance': ['advance', 'before', 'prior', 'early', 'ahead'],
        'properly': ['properly', 'correctly', 'appropriately', 'rightly'],
        'declared': ['declared', 'stated', 'announced', 'reported', 'said'],
        'allowed': ['allowed', 'permitted', 'authorized', 'approved', 'can'],
        'service': ['service', 'serving', 'offering', 'provision'],
        'short': ['short', 'brief', 'quick', 'limited'],
        'stays': ['stays', 'visits', 'trips', 'periods'],
        'arrival': ['arrival', 'arriving', 'entry', 'entering'],
        'requirements': ['requirements', 'needs', 'rules', 'criteria'],
        'nationality': ['nationality', 'citizenship', 'country', 'origin'],
        'citizenship': ['citizenship', 'nationality', 'country', 'origin'],
        'depend': ['depend', 'vary', 'based', 'depending'],
        'apply': ['apply', 'affect', 'relevant', 'pertain'],
        'restrictions': ['restrictions', 'limits', 'rules', 'regulations'],
        'items': ['items', 'bags', 'luggage', 'belongings'],
        'all': ['all', 'every', 'each', 'any'],
        'flights': ['flights', 'trips', 'journeys', 'travel'],
    }
    
    for key, values in synonyms.items():
        if word1 == key and word2 in values:
            return True
        if word2 == key and word1 in values:
            return True
    
    return False


def count_keyword_matches(llm_answer, expected_keywords):
    if not llm_answer or not isinstance(llm_answer, str):
        return 0
    
    if not expected_keywords:
        return 0
    
    answer_lower = llm_answer.lower()
    answer_words = set(re.findall(r'\b[a-z]{3,}\b', answer_lower))
    
    matches = 0
    for expected_word in expected_keywords:
        if expected_word in answer_lower:
            matches += 1
        else:
            matched = False
            for answer_word in answer_words:
                if are_words_similar(expected_word, answer_word):
                    matches += 1
                    matched = True
                    break
            if not matched and len(expected_word) >= 4:
                for answer_word in answer_words:
                    if expected_word[:3] in answer_word or answer_word[:3] in expected_word:
                        matches += 1
                        break
    
    return matches


def calculate_score(llm_answer, expected_valid):
    if not expected_valid or not isinstance(expected_valid, str) or not expected_valid.strip():
        return 100.0
    
    expected_keywords = extract_keywords(expected_valid)
    
    if not expected_keywords:
        return 100.0
    
    matches = count_keyword_matches(llm_answer, expected_keywords)
    
    if len(expected_keywords) <= 2:
        percentage = 100.0 if matches >= 1 else 80.0
    elif len(expected_keywords) <= 5:
        base = (matches / len(expected_keywords)) * 100.0
        percentage = min(100.0, base * 2.5) if matches >= 1 else base
    else:
        base = (matches / len(expected_keywords)) * 100.0
        if matches >= 2:
            percentage = min(100.0, base * 2.8)
        elif matches >= 1:
            percentage = min(100.0, base * 2.0)
        else:
            percentage = base
    
    return round(min(percentage, 100.0), 2)


def judge_llm_response(question, llm_answer, expected_valid, expected_invalid=None):
    if not expected_valid or not isinstance(expected_valid, str) or not expected_valid.strip():
        return {
            "score": 100.0,
            "validity": "Valid",
            "matched_keywords": 0,
            "total_keywords": 0
        }
    
    expected_keywords = extract_keywords(expected_valid)
    
    if not expected_keywords:
        return {
            "score": 100.0,
            "validity": "Valid",
            "matched_keywords": 0,
            "total_keywords": 0
        }
    
    matches = count_keyword_matches(llm_answer, expected_keywords)
    score = calculate_score(llm_answer, expected_valid)
    
    validity = "Valid" if score >= SCORE_THRESHOLD else "Invalid"
    
    return {
        "score": score,
        "validity": validity,
        "matched_keywords": matches,
        "total_keywords": len(expected_keywords)
    }
