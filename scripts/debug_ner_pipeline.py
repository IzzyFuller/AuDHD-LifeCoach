"""
Debug script to test the NER pipeline directly with enhanced time entity extraction.

This script bypasses the rest of the application logic and directly tests
the transformer model's ability to recognize entities in text, with added
time expression extraction using dateparser.
"""
import logging
import sys
import os
import re
from typing import Dict, List, Any, Optional, Tuple

# Add the project root to the path so we can access our project modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from transformers import pipeline
import dateparser
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test phrases with various entity types (people, places, organizations, times, etc.)
TEST_PHRASES = [
    # Original time expressions
    "I'll call you at 15:30 tomorrow.",
    "Let's meet at 3:30 PM at the coffee shop.",
    "The meeting is scheduled for 10:00 AM on Monday.",
    "I need to finish this by 17:45 today.",
    "Don't forget our appointment at nine thirty.",
    
    # More complex phrases with multiple entity types
    "Sarah Johnson from Microsoft will meet John Smith at Central Park at 2:00 PM on Friday.",
    "The conference in New York City starts at 9:00 AM and Apple will be presenting their new products.",
    "Dr. Williams prescribed medication that needs to be taken every day at 8:00 AM and 8:00 PM.",
    "The flight to London Heathrow Airport departs at 10:45 PM from Terminal B at JFK International.",
    "Please remind Thomas that he has a meeting with CEO Lisa Brown from Google next Thursday at noon."
]

# Patterns to help identify potential time expressions for dateparser
TIME_PATTERNS = [
    r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?',          # 3:30 PM, 15:30
    r'(?:at|by|on|for)\s+\d{1,2}:\d{2}',           # at 3:30, by 15:30
    r'(?:at|by|on|for)\s+\d{1,2}\s*(?:AM|PM|am|pm)', # at 3 PM
    r'(?:at|by|on|for)\s+(?:noon|midnight)',       # at noon, by midnight
    r'(?:at|by|on|for)\s+\w+\s+\w+\s+(?:AM|PM|am|pm)', # at nine thirty am
    r'(?:next|this|tomorrow|today)\s+\w+\s+(?:at|by)\s+\d{1,2}', # next Monday at 5
    r'(?:every|each)\s+\w+\s+(?:at|by)\s+\d{1,2}', # every day at 8
]

def extract_time_entities(text: str) -> List[Dict[str, Any]]:
    """
    Extract time entities from text using dateparser and pattern matching.
    
    Args:
        text: The input text to extract time entities from
        
    Returns:
        List of dictionaries containing time entity information
    """
    time_entities = []
    
    # Use regex patterns to find potential time expressions
    potential_times = []
    for pattern in TIME_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            potential_times.append((match.group(0), match.start(), match.end()))
    
    # Process each potential time expression
    for time_expr, start, end in potential_times:
        # Try to parse the time expression
        parsed_date = dateparser.parse(time_expr, settings={
            'PREFER_DATES_FROM': 'future',
            'RELATIVE_BASE': datetime.now()
        })
        
        if parsed_date:
            time_entity = {
                'entity': 'TIME',
                'word': time_expr,
                'start': start,
                'end': end,
                'parsed_datetime': parsed_date.strftime('%Y-%m-%d %H:%M:%S'),
                'score': 1.0  # Confidence score for rule-based extraction
            }
            time_entities.append(time_entity)
    
    return time_entities

def main():
    """Run tests on the NER pipeline with enhanced time entity extraction."""
    try:
        logger.info("Loading NER pipeline...")
        # Use the same model as in your actual implementation
        ner_pipeline = pipeline("ner", model="dslim/bert-base-NER")
        logger.info("NER pipeline loaded successfully")
        
        # Test each phrase
        for phrase in TEST_PHRASES:
            logger.info(f"\nTesting phrase: '{phrase}'")
            
            # 1. Get standard entities using the transformer model
            standard_entities = ner_pipeline(phrase)
            logger.info(f"Standard NER entities: {standard_entities}")
            
            if standard_entities:
                for entity in standard_entities:
                    logger.info(f"Entity: {entity['word']}, Type: {entity['entity']}, Score: {entity['score']:.4f}")
            else:
                logger.info("No standard entities detected for this phrase")
            
            # 2. Extract time entities using dateparser
            time_entities = extract_time_entities(phrase)
            logger.info(f"Time entities: {time_entities}")
            
            if time_entities:
                for entity in time_entities:
                    logger.info(f"Time Entity: '{entity['word']}', Parsed as: {entity['parsed_datetime']}")
            else:
                logger.info("No time entities detected for this phrase")
                
    except Exception as e:
        logger.error(f"Error running enhanced NER pipeline: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
if __name__ == "__main__":
    main()