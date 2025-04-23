"""
Controller for handling communication-related API requests.

This controller is responsible for processing incoming communication requests
and returning appropriate responses according to API contracts.
"""
from audhd_lifecoach.application.dtos.communication_dto import CommunicationRequestDTO, CommunicationResponseDTO
from audhd_lifecoach.application.use_cases.process_communication import ProcessCommunication


class CommunicationController:
    """
    Controller for handling communication-related API endpoints.
    
    This controller is responsible for receiving communication requests,
    delegating the processing to the appropriate use case, and returning
    the results as API responses.
    """
    
    def __init__(self, process_communication_use_case: ProcessCommunication):
        """
        Initialize the communication controller with required dependencies.
        
        Args:
            process_communication_use_case: The use case for processing communications
        """
        self.process_communication_use_case = process_communication_use_case
        
    def process_communication(self, communication_request: CommunicationRequestDTO) -> CommunicationResponseDTO:
        """
        Handle incoming communication API requests.
        
        Args:
            communication_request: The communication data sent to the API
            
        Returns:
            Response with processing results and created reminders
        """
        return self.process_communication_use_case.execute(communication_request)