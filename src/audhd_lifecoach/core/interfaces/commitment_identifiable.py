"""
Interface for components that can identify commitments within communications.
"""
from typing import List, Protocol, runtime_checkable

from audhd_lifecoach.core.domain.entities.communication import Communication
from audhd_lifecoach.core.domain.entities.commitment import Commitment


@runtime_checkable
class CommitmentIdentifiable(Protocol):
    """
    Interface for components that can identify commitments within communications.
    
    This interface represents the ability to analyze communication content
    and extract any commitments that may be present.
    """
    
    def identify_commitments(self, communication: Communication) -> List[Commitment]:
        """
        Identify any commitments contained within a communication.
        
        Args:
            communication: The communication to analyze
            
        Returns:
            A list of identified commitments (empty if none found)
        """
        ...