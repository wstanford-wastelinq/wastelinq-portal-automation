from typing import Dict, Type
from base_mapper import BaseProfileMapper
from tradebe_mapper import TradebeProfileMapper

class MapperFactory:
    """Factory class for creating mappers"""
    
    _mappers: Dict[str, Type[BaseProfileMapper]] = {
        "tradebe": TradebeProfileMapper
    }
    
    @classmethod
    def get_mapper(cls, portal: str) -> BaseProfileMapper:
        """Get mapper instance for specified portal"""
        mapper_class = cls._mappers.get(portal.lower())
        if not mapper_class:
            raise ValueError(f"No mapper available for portal: {portal}")
            
        return mapper_class()