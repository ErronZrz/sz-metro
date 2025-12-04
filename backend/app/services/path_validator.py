# -*- coding: utf-8 -*-
from typing import List, Tuple, Set
from app.services.metro_network import MetroNetwork


class PathValidator:
    """Path validation class"""
    
    def __init__(self, metro_network: MetroNetwork):
        """Initialize path validator"""
        self.network = metro_network
    
    def validate_path(self, path: List[str], start: str, end: str) -> Tuple[bool, str]:
        """Validate if user input path is legal"""
        if not path:
            return False, "Path cannot be empty"
        
        if path[0] != start:
            return False, f"Start station must be: {start}"
        
        if path[-1] != end:
            return False, f"End station must be: {end}"
        
        all_stations = self.network.get_all_stations()
        for p in path:
            if p not in all_stations:
                return False, f"Station does not exist: {p}"
        
        for a, b in zip(path, path[1:]):
            if b not in self.network.graph[a]:
                return False, f"Stations not adjacent: {a} → {b}"
        
        if len(path) != len(set(path)):
            return False, "Duplicate stations in path"
        
        return True, "OK"
