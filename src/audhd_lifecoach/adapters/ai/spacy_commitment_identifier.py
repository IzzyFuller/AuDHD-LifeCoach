"""
SpaCy-based implementation of the CommitmentIdentifiable interface.

This adapter uses SpaCy's transformer models for local processing
of natural language to identify commitments.
"""
import calendar
import re
from typing import List, Dict, Any, Tuple
from datetime import date, datetime, time, timedelta
import logging
import spacy
from spacy.tokens import Doc
import dateparser
from spacy.pipeline import EntityRuler

from audhd_lifecoach.core.domain.entities.communication import Communication
from audhd_lifecoach.core.domain.entities.commitment import Commitment

logger = logging.getLogger(__name__)


class SpaCyCommitmentIdentifier:
    """
    AI-powered implementation of the CommitmentIdentifiable protocol that extracts commitments from communications.
    
    This class uses spaCy's natural language processing capabilities to analyze the content
    of Communication objects to identify if the sender has made any commitments to the recipient,
    and extracts the relevant details to create properly formatted Commitment objects.
    """
    
    def __init__(self):
        """Initialize the CommitmentIdentifier with the spaCy NLP model."""
        self.nlp = spacy.load("en_core_web_trf")
        
        # Month names to numbers mapping
        self.month_names = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 
            'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        # Day of week abbreviations to full names
        self.day_map = {
            'mon': 'monday', 'tue': 'tuesday', 'wed': 'wednesday', 
            'thu': 'thursday', 'fri': 'friday', 'sat': 'saturday', 'sun': 'sunday'
        }
    
    def identify_commitments(self, communication: Communication) -> List[Commitment]:
        """
        Identify any commitments contained within a communication using NLP.
        
        This method analyzes the content of the given communication to identify
        if the sender has made any commitments to the recipient. It uses spaCy's
        natural language processing to extract the relevant details and creates
        properly formatted Commitment objects.
        
        Args:
            communication: The communication to analyze
            
        Returns:
            A list of identified commitments (empty if none found)
        """
        # Parse the communication content with spaCy
        doc = self.nlp(communication.content)
        
        # Extract sentences
        sentences = list(doc.sents)
        
        commitments = []
        
        for sentence in sentences:
            # Get segments from the sentence that might contain separate commitments
            segments = self._split_sentence_for_commitments(sentence.text)
            
            # Process each segment for commitments
            for segment in segments:
                # Check if this segment contains a commitment indicator
                # if not any(indicator.lower() in segment.lower() for indicator in self.commitment_indicators):
                #     continue
                
                # Parse the segment for NLP processing
                segment_doc = self.nlp(segment)
                
                # Extract commitment details from the segment
                what = self._extract_what(segment_doc)
                where = self._extract_where(segment_doc)
                time_info = self._extract_time_info(segment_doc, communication.timestamp)
                
                # Create commitment if we have the necessary information
                if what and time_info:
                    start_time, end_time = time_info
                    
                    commitment = Commitment(
                        start_time=start_time,
                        end_time=end_time,
                        who=communication.sender,
                        what=what,
                        where=where or "unspecified location"
                    )
                    
                    commitments.append(commitment)
        
        return commitments
    
    def _split_sentence_for_commitments(self, text: str) -> List[str]:
        """
        Split a sentence into segments that might contain separate commitments.
        
        This method looks for patterns like "I will X and I will Y" to identify
        multiple commitments within a single sentence.
        
        Args:
            text: The sentence text to analyze
            
        Returns:
            A list of segments that might contain individual commitments
        """
        segments = []
        
        # Try to identify common patterns with conjunctions separating commitments
        # First, see if we have any commitment indicators
        first_person_indicators = ["I will", "I'll", "I'm going", "I am going", "I can", 
                            "I promise", "I commit", "I agree", "I plan", "I intend", "I shall"]
        
        we_indicators = ["we can", "we will", "we'll", "we're going", "we are going", "let's"]
        
        # Check if any indicators are present
        has_first_person = any(ind.lower() in text.lower() for ind in first_person_indicators)
        has_we = any(ind.lower() in text.lower() for ind in we_indicators)
        
        # Special case: handle patterns like "I'll X and we can Y"
        if has_first_person and has_we:
            # Try to split on conjunctions followed by "we"
            for conj in ["and", "or", "then", "plus"]:
                pattern = rf'({conj}\s+we\s+(?:can|will|\'ll|\'re going|are going))'
                match = re.search(pattern, text, re.IGNORECASE)
                
                if match:
                    # Split the text at the conjunction
                    split_idx = match.start()
                    first_part = text[:split_idx].strip()
                    second_part = text[split_idx:].strip()
                    
                    # Add both parts if they contain commitment indicators
                    if any(ind.lower() in first_part.lower() for ind in first_person_indicators):
                        segments.append(first_part)
                    
                    if second_part:
                        segments.append(second_part)
                    
                    if segments:
                        return segments
        
        # More general case: look for any consecutive commitment indicators
        all_indicators = first_person_indicators + we_indicators
        
        # Find all indicators in the text
        indicator_positions = []
        for indicator in all_indicators:
            idx = text.lower().find(indicator.lower())
            if idx >= 0:
                indicator_positions.append((idx, indicator))
        
        # If no segments found, return the original text
        return segments if segments else [text]
    
    def _extract_what(self, doc: Doc) -> str|None:
        """
        Extract the action or task (what) from the sentence.
        
        Args:
            sentence: A spaCy sentence span
            
        Returns:
            The extracted action or task
        """
        
        # Use dependency parsing to find the main verb and its complements
        for token in doc:
            if (token.text.lower() in ("i", "we", "'s")) and token.dep_ == "nsubj":
                # Find the verb (head of "I")
                verb = token.head
                
                # Collect the verb phrase
                action_parts = []
                
                # Add the verb unless it's a modal
                if verb.lemma_ not in ["will", "shall", "can", "be", "have", "do", "would", "could", "should"]:
                    action_parts.append(verb.text)
                
                # Add direct objects and other complements
                for child in verb.children:
                    if child.dep_ in ["dobj", "pobj", "attr", "ccomp", "xcomp", "prep"]:
                        # Get the full subtree
                        phrase = " ".join([t.text for t in child.subtree])
                        action_parts.append(phrase)
                
                if action_parts:
                    return " ".join(action_parts)
        return
    
    def _extract_where(self, doc: Doc) -> str|None:
        """
        Extract the location (where) from the text.
        
        Args:
            text: The text to analyze
            
        Returns:
            The extracted location, or None if no location found
        """
        
        # Look for location entities
        for entity in doc.ents:
            if entity.label_ in ["LOC", "GPE", "FAC"]:
                return entity.text
        
        # Look for location phrases after prepositions like "at" or "in"
        location_patterns = [
            r"at\s+([^.,;]+)",
            r"in\s+([^.,;]+)",
            r"(?:the\s+)?location(?:\s+is|:)\s+([^.,;]+)",
            r"(?:the\s+)?place(?:\s+is|:)\s+([^.,;]+)",
            r"(?:the\s+)?venue(?:\s+is|:)\s+([^.,;]+)",
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, doc.text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                
                # Clean up the location
                location = re.sub(r'\b(?:on|this|next)\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Mon|Tue|Wed|Thu|Fri|Sat|Sun|weekend)\b', '', location, flags=re.IGNORECASE)
                location = re.sub(r'\b(today|tomorrow|tonight|next|this)\s+\w+\b', '', location, flags=re.IGNORECASE)
                location = re.sub(r'\b\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?\b', '', location, flags=re.IGNORECASE)
                location = re.sub(r'\b(morning|afternoon|evening|night|noon|midnight)\b', '', location, flags=re.IGNORECASE)
                location = re.sub(r'\bto\s+(?:discuss|review|talk|go|meet|work)\s+[^,;.]+', '', location, flags=re.IGNORECASE)
                
                # Final cleanup
                location = re.sub(r'\s+', ' ', location).strip()
                location = re.sub(r'\b(to|and|for|with)\s*$', '', location).strip()
                
                if location:
                    return location
        
        return None
    
    def _extract_time_info(self, segment: Doc, reference_time: datetime) -> Tuple[datetime, datetime]|None:
        """
        Extract time information from the text.
        
        Args:
            text: The text to analyze
            reference_time: The reference time (usually the communication timestamp)
            
        Returns:
            A tuple of (start_time, end_time) if found, None otherwise
        """
        # Extract date and time
        extracted_date = self._extract_date(segment, reference_time)
        extracted_time = self._extract_time(segment.text)
        
        # Set defaults if not found
        if extracted_date is None:
            extracted_date = reference_time.date()
        
        if extracted_time is None:
            # return 00:00 through 23:59
            extracted_time = time(0, 0)
            duration = timedelta(hours=23, minutes=59)
        else:
            # Extract duration
            duration = self._extract_duration(segment.text) 
        
        # Default duration is 1 hour if not specified
        if duration is None:
            duration = timedelta(hours=1)
        
        # Combine date and time
        start_time = datetime.combine(extracted_date, extracted_time)
        
        # Calculate end time
        end_time = start_time + duration
        
        return start_time, end_time
    
    def _extract_date(self, doc: Doc, reference_time: datetime) -> date | None:
        """
        Extract the date from the text using SpaCy's NLP capabilities.

        Args:
            doc: The SpaCy Doc object to analyze
            reference_time: The reference time

        Returns:
            The extracted date, or None if no date is found
        """
        # Look for DATE entities in the text
        for entity in doc.ents:
            if entity.label_ == "DATE":
                # Use dateparser to parse the date relative to the reference time
                parsed_date = dateparser.parse(entity.text, settings={
                    'PREFER_DATES_FROM': 'future',
                    'RELATIVE_BASE': reference_time
                })
                if parsed_date:
                    return parsed_date.date()

        # If no DATE entity is found, return None
        return None
    
    def _extract_time(self, text: str) -> time|None:
        """
        Extract the time from the text.
        
        Args:
            text: The text to analyze
            
        Returns:
            The extracted time, or None if no time found
        """
        # Check for specific times (3:30pm, 3pm, etc.)
        time_pattern = r"(\d{1,2})(?::(\d{2}))?(?:\s*(am|pm|AM|PM))"
        time_match = re.search(time_pattern, text)
        
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            am_pm = time_match.group(3).lower()
            
            # Convert to 24-hour format
            if am_pm == 'pm' and hour < 12:
                hour += 12
            elif am_pm == 'am' and hour == 12:
                hour = 0
            
            return time(hour, minute)
        
        # Check for named times (morning, afternoon, etc.)
        named_time_pattern = r"\b(morning|afternoon|evening|night|noon|midnight)\b"
        named_match = re.search(named_time_pattern, text, re.IGNORECASE)
        
        if named_match:
            time_name = named_match.group(1).lower()
            if time_name == 'morning':
                return time(9, 0)
            elif time_name == 'afternoon':
                return time(14, 0)
            elif time_name == 'evening':
                return time(18, 0)
            elif time_name == 'night':
                return time(20, 0)
            elif time_name == 'noon':
                return time(12, 0)
            elif time_name == 'midnight':
                return time(0, 0)
        
        return None
    
    def _extract_duration(self, text: str) -> timedelta|None:
        """
        Extract the duration from the text.
        
        Args:
            text: The text to analyze
            
        Returns:
            The extracted duration, or None if no duration found
        """
        # Check for explicit durations (for 30 minutes, 2 hours long)
        for pattern in [r"for\s+(\d+)\s+(minute|hour|day)s?", r"(\d+)\s+(minute|hour|day)s?\s+long"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = int(match.group(1))
                unit = match.group(2).lower()
                
                if unit == "minute":
                    return timedelta(minutes=amount)
                elif unit == "hour":
                    return timedelta(hours=amount)
                elif unit == "day":
                    return timedelta(days=amount)
        
        return None
