"""
Transformer-based implementation of the CommitmentIdentifiable interface using Hugging Face.

This adapter uses Hugging Face's transformer models for local processing
of natural language to identify commitments.
"""
from typing import List, Optional, Dict, Any, Tuple
import re
from datetime import datetime, timedelta
import logging

# Direct imports instead of conditional or lazy loading
from transformers.pipelines import pipeline
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
    r'(?:this|next|on)\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)', # on Friday, next Monday
    r'(?:this|tomorrow|tonight|today)?\s*(?:morning|afternoon|evening|night)', # this morning, tomorrow afternoon
    r'(?:morning|afternoon|evening|night)', # broader match for times of day
    r'(?:friday|monday|tuesday|wednesday|thursday|saturday|sunday)', # broader match for days
]

# Time of day mappings for implicit references
TIME_OF_DAY = {
    "morning": (9, 0),      # 9:00 AM
    "afternoon": (14, 0),   # 2:00 PM
    "evening": (18, 0),     # 6:00 PM
    "night": (20, 0),       # 8:00 PM
    "noon": (12, 0),        # 12:00 PM
    "midnight": (0, 0)      # 12:00 AM
}


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
            
            # Handle time-of-day references (morning, afternoon, evening)
            if not parsed_date:
                # Check for time of day references
                for time_name, (hour, minute) in TIME_OF_DAY.items():
                    if time_name in time_expr.lower():
                        # First try to parse the whole expression without the time reference
                        base_expr = time_expr.lower().replace(time_name, "").strip()
                        if base_expr:
                            # Parse the base expression (e.g., "tomorrow" from "tomorrow morning")
                            base_date = dateparser.parse(base_expr, settings={
                                'PREFER_DATES_FROM': 'future',
                                'RELATIVE_BASE': datetime.now()
                            })
                            if base_date:
                                # Set the time portion using our time of day mapping
                                parsed_date = base_date.replace(hour=hour, minute=minute)
                                break
                        else:
                            # If just "morning", "afternoon", etc., use today's date
                            today = datetime.now().replace(hour=hour, minute=minute)
                            # If the time has already passed today, move to tomorrow
                            if today < datetime.now():
                                today = today + timedelta(days=1)
                            parsed_date = today
                            break
                            
                # Handle day of week without specific time
                if not parsed_date and any(day in time_expr.lower() for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
                    parsed_date = dateparser.parse(time_expr, settings={
                        'PREFER_DATES_FROM': 'future',
                        'RELATIVE_BASE': datetime.now()
                    })
                    
                    # Set a default time if only a day was specified (e.g., "Friday")
                    if parsed_date:
                        # Default to 9 AM for workdays, 10 AM for weekends
                        if parsed_date.weekday() < 5:  # Monday-Friday
                            parsed_date = parsed_date.replace(hour=9, minute=0)
                        else:  # Saturday, Sunday
                            parsed_date = parsed_date.replace(hour=10, minute=0)
            
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
        
        # Special case: if we have "this evening", "tomorrow morning", etc. but didn't match
        # Try to find these common time phrases directly
        if not time_entities:
            time_phrases = ["morning", "afternoon", "evening", "night", "tomorrow", "friday", "monday", "tuesday", "wednesday", "thursday"]
            for phrase in time_phrases:
                if phrase in text.lower():
                    # Parse the phrase
                    parsed_date = dateparser.parse(phrase, settings={
                        'PREFER_DATES_FROM': 'future',
                        'RELATIVE_BASE': datetime.now()
                    })
                    
                    if parsed_date:
                        # If it's a time of day reference, set appropriate hour
                        if phrase in TIME_OF_DAY:
                            hour, minute = TIME_OF_DAY[phrase]
                            parsed_date = parsed_date.replace(hour=hour, minute=minute)
                        
                        time_entity = {
                            'entity': 'TIME',
                            'word': phrase,
                            'start': text.lower().find(phrase),
                            'end': text.lower().find(phrase) + len(phrase),
                            'parsed_datetime': parsed_date,
                            'score': 0.9  # Slightly lower confidence for this fallback
                        }
                        time_entities.append(time_entity)
                        break
        
        return time_entities
    
    def _extract_person_entities(self, text: str, standard_entities: List[Dict[str, Any]]) -> Optional[str]:
        """
        Extract person entities from text using sophisticated NER processing.
        
        Args:
            text: The text to analyze
            standard_entities: Already extracted NER entities
            
        Returns:
            The name of the person mentioned or None if not found
        """
        # Process NER results for person entities
        person_spans = []  # Store (entity, start_pos, end_pos, score)
        
        # First, gather all person entity spans from the NER results
        for entity in standard_entities:
            if entity['entity'] in ('PER', 'B-PER', 'I-PER', 'PERSON'):
                # Add the span with its position information and score
                person_spans.append((
                    entity['word'],
                    entity['start'],
                    entity['end'],
                    entity.get('score', 1.0)  # Default score of 1.0 if not provided
                ))
        
        if not person_spans:
            # No person entities found by the NER model
            return None
        
        # Now intelligently merge adjacent person entities
        merged_spans = []
        current_span = None
        
        # Sort spans by start position
        person_spans.sort(key=lambda x: x[1])
        
        for span in person_spans:
            word, start, end, score = span
            
            if current_span is None:
                current_span = [word, start, end, score]
            else:
                # Check if this span is adjacent or very close to the current span
                curr_word, curr_start, curr_end, curr_score = current_span
                
                # If spans are adjacent or very close (allowing for small gaps)
                if start <= curr_end + 2:  # Allow for spaces or small gaps
                    # Merge spans
                    current_span = [
                        f"{curr_word} {word}",  # Combine text with space
                        curr_start,  # Keep original start
                        end,  # Use latest end
                        min(curr_score, score)  # Use minimum score as confidence
                    ]
                else:
                    # Not adjacent, store current and start new
                    merged_spans.append(tuple(current_span))
                    current_span = [word, start, end, score]
        
        # Don't forget the last span
        if current_span is not None:
            merged_spans.append(tuple(current_span))
        
        if not merged_spans:
            return None
        
        # Process and clean up the merged entities
        processed_names = []
        for word, _, _, score in merged_spans:
            # Clean up the name - remove extra spaces, normalize capitalization
            name = ' '.join(word.strip().split())
            
            # Basic heuristic to determine if it looks like a name
            # - Must contain at least one capital letter
            # - Should not be too long (most names are 1-3 words)
            if any(c.isupper() for c in name) and len(name.split()) <= 3:
                processed_names.append((name, score))
        
        if not processed_names:
            return None
            
        # Sort by score (higher is better) and choose the highest scoring name
        processed_names.sort(key=lambda x: x[1], reverse=True)
        return processed_names[0][0]
    
    def _has_commitment_intent(self, text: str) -> bool:
        """
        Determine if the text contains a commitment intent.
        """
        commitment_phrases = [
            "will", "i'll", "going to", "meet", "plan to", 
            "attend", "submit", "promise", "promised", "agreed", "need to",
            "must", "have to", "should", "discuss", "by friday", 
            "tomorrow", "this evening", "morning", "afternoon",
            "checkup", "recital", "report"
        ]
        return any(phrase in text.lower() for phrase in commitment_phrases)
    
    def _extract_activity(self, text: str, standard_entities: List[Dict[str, Any]]) -> str:
        """
        Extract the activity from the text.
        
        Args:
            text: The text to analyze
            standard_entities: Already extracted NER entities
            
        Returns:
            The activity described or a default value
        """
        # Common activities to look for
        activities = [
            "call", "meet", "meeting", "appointment", "lunch", "dinner", 
            "breakfast", "submit", "report", "presentation", "review", 
            "interview", "discuss", "discussion", "check", "checkup", 
            "exam", "examination", "attend", "event", "conference", 
            "recital", "performance", "game", "match", "delivery"
        ]
        
        # Look for these activities in the text
        for activity in activities:
            if re.search(r'\b' + activity + r'\b', text, re.IGNORECASE):
                return activity.capitalize()
        
        # Default if no specific activity found
        return "Meeting or appointment"
    
    def _get_time_range(self, time_entity: Dict[str, Any], activity: str) -> Tuple[datetime, datetime]:
        """
        Convert a time entity to a start time and end time.
        
        This method determines an appropriate duration for different activities
        and time references, creating a realistic time range.
        
        Args:
            time_entity: The time entity extracted from text
            activity: The identified activity
            
        Returns:
            A tuple of (start_time, end_time) for the commitment
        """
        start_time = time_entity['parsed_datetime']
        time_word = time_entity['word'].lower()
        
        # Set default duration based on the activity and time reference
        duration = timedelta(minutes=60)  # Default 1 hour for most commitments
        
        # Adjust duration based on the activity
        if any(act in activity.lower() for act in ["lunch", "dinner", "breakfast"]):
            duration = timedelta(minutes=90)  # Meals typically take longer
        elif any(act in activity.lower() for act in ["meeting", "discuss"]):
            duration = timedelta(minutes=60)  # Standard meeting length
        elif any(act in activity.lower() for act in ["call"]):
            duration = timedelta(minutes=30)  # Calls are typically shorter
        elif any(act in activity.lower() for act in ["checkup", "appointment"]):
            duration = timedelta(minutes=45)  # Medical appointments
        elif any(act in activity.lower() for act in ["recital", "concert", "performance"]):
            duration = timedelta(hours=2)  # Performances are longer
            
        # Adjust for time of day references
        if "morning" in time_word:
            # For morning references (e.g., "tomorrow morning"), create a broader range
            # If it's a specific time in the morning, keep the default duration
            if re.search(r'\d{1,2}:\d{2}|\d{1,2}\s*(am|pm)', time_word, re.IGNORECASE) is None:
                # No specific time, make it a 3-hour window in the morning
                end_time = start_time + timedelta(hours=3)
                return start_time, end_time
                
        elif "afternoon" in time_word:
            if re.search(r'\d{1,2}:\d{2}|\d{1,2}\s*(am|pm)', time_word, re.IGNORECASE) is None:
                # No specific time, make it a 4-hour window in the afternoon
                end_time = start_time + timedelta(hours=4)
                return start_time, end_time
                
        elif "evening" in time_word:
            if re.search(r'\d{1,2}:\d{2}|\d{1,2}\s*(am|pm)', time_word, re.IGNORECASE) is None:
                # No specific time, make it a 3-hour window in the evening
                end_time = start_time + timedelta(hours=3)
                return start_time, end_time
                
        # For day references without time (e.g., "Friday")
        elif any(day in time_word for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
            if re.search(r'\d{1,2}:\d{2}|\d{1,2}\s*(am|pm)', time_word, re.IGNORECASE) is None:
                # If it's a workday, make it a workday-length commitment (8 hours)
                if start_time.weekday() < 5:  # Monday-Friday
                    end_time = start_time + timedelta(hours=8)
                else:  # Weekend days
                    end_time = start_time + timedelta(hours=4)  # Shorter commitment on weekends
                return start_time, end_time
        
        # Default case: use the calculated duration
        end_time = start_time + duration
        return start_time, end_time
            
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
        
        # Extract standard named entities (locations, organizations, etc.)
        standard_entities = self.ner_pipeline(text)
        
        # Extract time entities using dateparser and our enhanced logic
        time_entities = self._extract_time_entities(text)
        
        # Find location entities from standard entities
        location_entity = None
        for entity in standard_entities:
            if entity['entity'] in ('LOC', 'B-LOC', 'I-LOC', 'LOCATION'):
                location_entity = entity
                break
        
        # Extract person entities
        person = self._extract_person_entities(text, standard_entities)
        
        # If no person found from NER, use the recipient
        if not person:
            person = communication.recipient
        
        # Extract the activity
        activity = self._extract_activity(text, standard_entities)
        
        # If we found a time entity, create a commitment
        if time_entities:
            # Use the first time entity found
            time_entity = time_entities[0]
            
            # Get appropriate start and end times
            start_time, end_time = self._get_time_range(time_entity, activity)
            
            # Extract location if available
            where = "location mentioned in message"
            if location_entity:
                where = location_entity['word']
            
            # Create commitment with time range
            commitment = Commitment(
                start_time=start_time,
                end_time=end_time,
                who=person,
                what=activity,
                where=where
            )
            
            return [commitment]
        
        # No valid time entity found
        return []