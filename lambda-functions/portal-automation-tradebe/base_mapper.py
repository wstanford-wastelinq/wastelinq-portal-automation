from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseProfileMapper(ABC):
    """
    Abstract base class that defines the interface for all waste profile mappers.
    Each portal-specific mapper must implement these methods.
    """
    
    @abstractmethod
    def map_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps source portal data to target portal format.
        
        Args:
            data: Dictionary containing the source portal's profile data
            
        Returns:
            Dictionary containing mapped data in target portal's format
        """
        pass