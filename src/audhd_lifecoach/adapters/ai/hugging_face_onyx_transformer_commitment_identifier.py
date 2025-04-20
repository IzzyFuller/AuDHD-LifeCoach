"""
Transformer-based implementation of the CommitmentIdentifiable interface using Hugging Face.

This adapter uses Hugging Face's transformer models for local processing
of natural language to identify commitments.
"""
from typing import List, Optional, Dict, Any, Tuple
import re
from datetime import datetime
import logging

# Direct imports instead of conditional or lazy loading
from transformers import pipeline
import dateparser

from audhd_lifecoach.core.domain.entities.communication import Communication
from audhd_lifecoach.core.domain.entities.commitment import Commitment

logger = logging.getLogger(__name__)

# Patterns to help identify potential time expressions for dateparser
TIME_PATTERNS = [
    r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?',          # 3:30 PM, 15:30
    r'(?:at|by|on|for)\s+\d{1,2}:\d{2}',           # at 3:30, by 15:30
    r'(?:at|by|on|for)\s+\d{1,2}\s*(?:AM|PM|am|pm)', # at 3 PM
    r'(?:at|by|on|for)\s+(?:noon|midnight)',       # at noon, by midnight
    r'(?:next|this|tomorrow|today)\s+\w+\s+(?:at|by)\s+\d{1,2}', # next Monday at 5
]


class HuggingFaceONYXTransformerCommitmentIdentifier:
    """
    Identifies commitments in communications using transformer models.
    
    This implementation uses Named Entity Recognition (NER) to extract dates, times,
    and locations from text, enabling accurate identification of commitments.
    """
    
    def __init__(self, model_name: str = "dslim/bert-base-NER", ner_pipeline=None):
        """
        Initialize the commitment identifier with transformer model.
        
        Args:
            model_name: The Hugging Face model name to use for NER
            ner_pipeline: Optional pre-configured pipeline for testing
        """
        self.model_name = model_name
        # Allow dependency injection for testing
        self._ner_pipeline = ner_pipeline
    
    @property
    def ner_pipeline(self):
        """Lazy loading of the NER pipeline."""
        if self._ner_pipeline is None:
            self._ner_pipeline = pipeline("ner", model=self.model_name)
            logger.info(f"Loaded NER model: {self.model_name}")
        return self._ner_pipeline
    
    def _extract_time_from_entity(self, entity_text: str) -> Optional[tuple]:
        """Extract hour and minute from a time entity string."""
        # Try to extract time format like "15:30" or "3:30"
        time_match = re.search(r'([0-1]?[0-9]|2[0-3]):([0-5][0-9])', entity_text)
        if time_match:
            return int(time_match.group(1)), int(time_match.group(2))
        return None
    
    def _extract_time_entities(self, text: str) -> List[Dict[str, Any]]:
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
                    'parsed_datetime': parsed_date,
                    'score': 1.0  # Confidence score for rule-based extraction
                }
                time_entities.append(time_entity)
        
        return time_entities
    
    def _has_commitment_intent(self, text: str) -> bool:
        """
        Determine if the text contains a commitment intent.
        """
        commitment_phrases = ["will", "i'll", "going to", "meet", "plan to"]
        return any(phrase in text.lower() for phrase in commitment_phrases)
    
    def identify_commitments(self, communication: Communication) -> List[Commitment]:
        """
        Identify any commitments contained within a communication.
        
        Args:
            communication: The communication to analyze
            
        Returns:
            A list of identified commitments (empty if none found)
        """
        text = communication.content
        
        # Skip processing if text is empty
        if not text:
            return []
        
        # Check for commitment intent first (cheaper operation)
        if not self._has_commitment_intent(text):
            return []
        
        try:
            # Extract standard named entities (locations, organizations, etc.)
            standard_entities = self.ner_pipeline(text)
            
            # Extract time entities using dateparser
            time_entities = self._extract_time_entities(text)
            
            # Find location entities from standard entities
            location_entity = None
            for entity in standard_entities:
                if entity['entity'] in ('LOC', 'B-LOC', 'I-LOC', 'LOCATION'):
                    location_entity = entity
                    break
            
            # If we found a time entity, create a commitment
            if time_entities:
                # Use the first time entity found
                time_entity = time_entities[0]
                parsed_datetime = time_entity['parsed_datetime']
                
                # Extract location if available
                where = "location mentioned in message"
                if location_entity:
                    where = location_entity['word']
                
                # Create commitment
                commitment = Commitment(
                    when=parsed_datetime,
                    who=communication.recipient,
                    what="Meeting or appointment",
                    where=where
                )
                
                return [commitment]
            
            # No valid time entity found
            return []
            
        except Exception as e:
            logger.error(f"Error processing text with transformer model: {str(e)}")
            return []