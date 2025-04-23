"""
Service for processing communications into reminders.

This service orchestrates the flow from Communication to Commitment to Reminder,
handling the extraction of commitments from communications and the creation
of reminders from those commitments.
"""
from typing import List

from audhd_lifecoach.core.domain.entities.communication import Communication
from audhd_lifecoach.core.domain.entities.commitment import Commitment
from audhd_lifecoach.core.domain.entities.reminder import Reminder
from audhd_lifecoach.core.interfaces.commitment_identifiable import CommitmentIdentifiable


class CommunicationProcessor:
    """
    Service that processes communications to extract commitments and create reminders.
    
    This service orchestrates the flow from Communication to Reminder by:
    1. Using a commitment identifier to extract commitments from communications
    2. Creating reminders from the identified commitments
    """
    
    def __init__(self, commitment_identifier: CommitmentIdentifiable):
        """
        Initialize the communication processor with a commitment identifier.
        
        Args:
            commitment_identifier: Component that identifies commitments in communications
        """
        self.commitment_identifier = commitment_identifier
    
    def process_communication(self, communication: Communication) -> List[Reminder]:
        """
        Process a communication to create reminders from any commitments it contains.
        
        Args:
            communication: The communication to process
            
        Returns:
            List of reminders created from the communication (empty if no commitments found)
        """
        # Extract commitments from the communication
        commitments = self.commitment_identifier.identify_commitments(communication)
        
        # Create reminders from the extracted commitments
        reminders = []
        for commitment in commitments:
            reminder = Reminder.from_commitment(commitment)
            reminders.append(reminder)
        
        return reminders