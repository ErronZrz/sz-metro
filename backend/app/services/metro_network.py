# -*- coding: utf-8 -*-
import json
import random
from collections import defaultdict
from decimal import Decimal, getcontext
from typing import Dict, List, Set, Tuple
import os

# Set Decimal precision
getcontext().prec = 28


class MetroNetwork:
    """Shenzhen Metro Network class"""
    
    def __init__(self, json_file: str = None):
        """Initialize metro network"""
        if json_file is None:
            # Default to lines.json in backend directory
            json_file = os.path.join(os.path.dirname(__file__), "..", "..", "lines.json")
        self.lines = self._load_lines(json_file)
        self.graph = None
        self.station_lines = None
        self.transfer_penalty = Decimal("2.5")
    
    def _load_lines(self, json_file: str) -> Dict[str, List[str]]:
        """Load line data from JSON file"""
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Cannot read lines.json: {e}")
    
    def build_graph(self, selected_line_names: List[str]) -> None:
        """Build graph structure and station-line mapping"""
        if not self._validate_lines(selected_line_names):
            raise ValueError("Invalid line names")
        
        self.graph = defaultdict(set)
        self.station_lines = defaultdict(set)
        
        for line_name in selected_line_names:
            stations = self.lines[line_name]
            for s in stations:
                self.station_lines[s].add(line_name)
            
            for a, b in zip(stations, stations[1:]):
                self.graph[a].add(b)
                self.graph[b].add(a)
    
    def _validate_lines(self, user_lines: List[str]) -> bool:
        """Validate if line names exist"""
        for ln in user_lines:
            if ln not in self.lines:
                return False
        return True
    
    def get_all_stations(self) -> Set[str]:
        """Get all stations in current graph"""
        if self.graph is None:
            raise RuntimeError("Please build graph first")
        return set(self.graph.keys())
    
    def get_all_lines(self) -> List[str]:
        """Get all available line names"""
        return list(self.lines.keys())
    
    def get_line_stations(self, line_name: str) -> List[str]:
        """Get all stations for a specific line"""
        if line_name not in self.lines:
            raise ValueError(f"Line {line_name} not found")
        return self.lines[line_name]
    
    def is_reachable(self, start: str, end: str) -> bool:
        """Check if two stations are reachable"""
        if self.graph is None:
            raise RuntimeError("Please build graph first")
        
        stack = [start]
        visited = {start}
        
        while stack:
            u = stack.pop()
            if u == end:
                return True
            for nb in self.graph[u]:
                if nb not in visited:
                    visited.add(nb)
                    stack.append(nb)
        
        return False
    
    def pick_two_random_stations(self) -> Tuple[str, str]:
        """Randomly pick two reachable stations"""
        if self.graph is None:
            raise RuntimeError("Please build graph first")
        
        all_nodes = list(self.graph.keys())
        if len(all_nodes) < 2:
            raise RuntimeError("Not enough stations")
        
        visited = set()
        components = []
        
        for s in all_nodes:
            if s in visited:
                continue
            comp = []
            stack = [s]
            visited.add(s)
            while stack:
                v = stack.pop()
                comp.append(v)
                for nb in self.graph[v]:
                    if nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
            if len(comp) >= 2:
                components.append(comp)
        
        if not components:
            raise RuntimeError("No valid connected component")
        
        comp = random.choice(components)
        return random.sample(comp, 2)
    
    def annotate_path_with_transfers(self, path: List[str]) -> str:
        """Annotate path with transfer information"""
        if not path or self.station_lines is None:
            return " → ".join(path)
        
        annotated = []
        prev_line = None
        
        for i in range(len(path)):
            station = path[i]
            
            if i == 0:
                # First station
                annotated.append(station)
                continue
            
            # Find common lines between current and previous station
            prev_station = path[i - 1]
            common_lines = self.station_lines[prev_station] & self.station_lines[station]
            
            if not common_lines:
                current_line = None
            else:
                # Prefer to continue on the same line
                if prev_line in common_lines:
                    current_line = prev_line
                else:
                    current_line = sorted(common_lines)[0]
            
            # Check if transfer happened at previous station
            if prev_line is not None and current_line is not None and prev_line != current_line:
                # Add transfer annotation to previous station
                annotated[-1] = f"{annotated[-1]}({prev_line}换乘{current_line})"
            
            annotated.append(station)
            prev_line = current_line
        
        return " → ".join(annotated)
