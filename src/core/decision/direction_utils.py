import re

def get_word_pattern(word: str) -> str:
    """
    Generates a word-boundary-safe regex pattern that supports standard suffixes
    (like s, es, d, ed, ing) to match inflected forms of the business keywords.
    """
    if word.endswith('e'):
        stem = word[:-1]
        return rf"\b{stem}(?:e|es|ed|ing)?\b"
    elif word.endswith('y'):
        stem = word[:-1]
        return rf"\b{stem}(?:y|ies|ied|ying)?\b"
    elif word in ["drop", "cut"]:
        return rf"\b{word}s?\b|\b{word}{word[-1]}ing\b|\b{word}{word[-1]}ed\b"
    else:
        return rf"\b{word}(?:s|es|d|ed|ing)?\b"

def parse_direction(text: str) -> str:
    """
    Parses the business impact or shock direction from text (user queries or hypothesis titles).
    Returns:
        "positive": for increases, improvements, up, etc.
        "negative": for decreases, cuts, drops, down, erosion, etc.
        "neutral": if direction is ambiguous or not mentioned.
    """
    text_lower = text.lower()
    neg_words = [
        "decrease", "drop", "lower", "down", "reduce", "cut", "erode", 
        "decline", "deteriorate", "fall", "loss", "negative", 
        "abandonment", "friction", "degradation", "depress"
    ]
    pos_words = [
        "increase", "improve", "rise", "up", "growth", "boost", 
        "higher", "elevated", "more", "positive"
    ]
    
    for word in neg_words:
        if re.search(get_word_pattern(word), text_lower):
            return "negative"
            
    for word in pos_words:
        if re.search(get_word_pattern(word), text_lower):
            return "positive"
            
    return "neutral"

def parse_query_driver_direction(query: str, driver_keyword: str) -> str:
    """
    Locates the driver keyword in the query and parses the direction from its local context.
    Looks at the words immediately surrounding (preceding/succeeding) the driver keyword.
    """
    query_lower = query.lower()
    idx = query_lower.find(driver_keyword.lower())
    if idx == -1:
        return "neutral"
        
    # Check preceding context (up to 4 words)
    prefix = query_lower[:idx].strip()
    prefix_words = prefix.split()
    pre_window = " ".join(prefix_words[-4:]) if len(prefix_words) >= 4 else prefix
    direction = parse_direction(pre_window)
    if direction != "neutral":
        return direction
        
    # Check succeeding context (up to 3 words after driver keyword)
    suffix = query_lower[idx + len(driver_keyword):].strip()
    suffix_words = suffix.split()
    post_window = " ".join(suffix_words[:3]) if len(suffix_words) >= 3 else suffix
    return parse_direction(post_window)

def parse_hypothesis_direction(title: str, driver_keyword: str) -> str:
    """
    Analyzes the hypothesis title suffix (after the driver keyword) and yields direction
    based on the keyword closest to the KPI at the end of the sentence.
    """
    title_lower = title.lower()
    idx = title_lower.find(driver_keyword.lower())
    if idx == -1:
        return parse_direction(title)
        
    suffix = title_lower[idx + len(driver_keyword):].strip()
    
    neg_words = [
        "decrease", "drop", "lower", "down", "reduce", "cut", "erode", 
        "decline", "deteriorate", "fall", "loss", "negative", 
        "abandonment", "friction", "degradation", "depress"
    ]
    pos_words = [
        "increase", "improve", "rise", "up", "growth", "boost", 
        "higher", "elevated", "more", "positive"
    ]
    
    neg_idx = -1
    for word in neg_words:
        match = list(re.finditer(get_word_pattern(word), suffix))
        if match:
            neg_idx = max(neg_idx, match[-1].start())
            
    pos_idx = -1
    for word in pos_words:
        match = list(re.finditer(get_word_pattern(word), suffix))
        if match:
            pos_idx = max(pos_idx, match[-1].start())
            
    if neg_idx != -1 and pos_idx != -1:
        return "negative" if neg_idx > pos_idx else "positive"
    elif neg_idx != -1:
        return "negative"
    elif pos_idx != -1:
        return "positive"
    return "neutral"
