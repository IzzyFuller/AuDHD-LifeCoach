"""
Transformer-based implementation of the CommitmentIdentifiable interface using Hugging Face.

This adapter uses Hugging Face's transformer models for local processing
of natural language to identify commitments.
"""
from typing import List, Optional
import re
from datetime import datetime
import logging

# Direct imports instead of conditional or lazy loading
from transformers import pipeline

from audhd_lifecoach.core.domain.entities.communication import Communication
from audhd_lifecoach.core.domain.entities.commitment import Commitment

logger = logging.getLogger(__name__)


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
            # Extract named entities
            entities = self.ner_pipeline(text)
            
            # Process entities to find times and locations
            time_entity = None
            location_entity = None
            
            for entity in entities:
                if entity['entity'] in ('TIME', 'B-TIME'):
                    time_entity = entity
                elif entity['entity'] in ('LOC', 'B-LOC', 'LOCATION'):
                    location_entity = entity
            
            # If we found a time entity, create a commitment
            if time_entity:
                time_tuple = self._extract_time_from_entity(time_entity['word'])
                
                if time_tuple:
                    hour, minute = time_tuple
                    when = datetime.now().replace(hour=hour, minute=minute)
                    
                    # Extract location if available
                    where = "location mentioned in message"
                    if location_entity:
                        where = location_entity['word']
                    
                    # Create commitment
                    commitment = Commitment(
                        when=when,
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