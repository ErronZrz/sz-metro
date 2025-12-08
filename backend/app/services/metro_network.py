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
    
    def get_reachable_stations(self, start: str) -> Set[str]:
        """Get all stations reachable from start station"""
        if self.graph is None:
            raise RuntimeError("Please build graph first")
        
        if start not in self.graph:
            raise ValueError(f"Station {start} not found in current graph")
        
        stack = [start]
        visited = {start}
        
        while stack:
            u = stack.pop()
            for nb in self.graph[u]:
                if nb not in visited:
                    visited.add(nb)
                    stack.append(nb)
        
        # Exclude start station itself
        visited.discard(start)
        return visited
    
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
        result = random.sample(comp, 2)
        return (result[0], result[1])
    
    def annotate_path_with_transfers(self, path: List[str], line_sequence: List[str]) -> str:
        """
        Annotate path with transfer information.
        
        Args:
            path: List of station names
            line_sequence: Optional pre-computed optimal line sequence from PathFinder.analyze_path_optimal()
                          If provided, uses this sequence; otherwise falls back to greedy selection.
        
        Returns:
            Annotated path string with transfer information
        """
        if not path or self.station_lines is None:
            return " → ".join(path)
        
        # If line_sequence is provided, use it directly
        if line_sequence is not None and len(line_sequence) == len(path):
            return self._annotate_with_line_sequence(path, line_sequence)
        
        # Fallback to greedy selection (for backward compatibility)
        return self._annotate_greedy(path)
    
    def _annotate_with_line_sequence(self, path: List[str], line_sequence: List[str]) -> str:
        """Annotate path using pre-computed optimal line sequence"""
        annotated = []
        
        for i in range(len(path)):
            station = path[i]
            current_line = line_sequence[i]
            
            if i == 0:
                annotated.append(station)
            else:
                prev_line = line_sequence[i - 1]
                
                # Check if transfer happened at previous station
                if prev_line is not None and current_line is not None and prev_line != current_line:
                    # Add transfer annotation to previous station
                    annotated[-1] = f"{annotated[-1]}({prev_line}换乘{current_line})"
                
                annotated.append(station)
        
        return " → ".join(annotated)
    
    def _annotate_greedy(self, path: List[str]) -> str:
        """Annotate path using greedy line selection (fallback method)"""
        assert self.station_lines is not None
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
                # Filter to only lines where stations are adjacent
                valid_lines = []
                for line_name in common_lines:
                    line_stations = self.lines[line_name]
                    try:
                        u_idx = line_stations.index(prev_station)
                        v_idx = line_stations.index(station)
                        # Check if stations are adjacent on this line
                        if abs(u_idx - v_idx) == 1:
                            valid_lines.append(line_name)
                    except ValueError:
                        continue
                
                if not valid_lines:
                    current_line = None
                else:
                    # Prefer to continue on the same line
                    if prev_line in valid_lines:
                        current_line = prev_line
                    else:
                        current_line = sorted(valid_lines)[0]
            
            # Check if transfer happened at previous station
            if prev_line is not None and current_line is not None and prev_line != current_line:
                # Add transfer annotation to previous station
                annotated[-1] = f"{annotated[-1]}({prev_line}换乘{current_line})"
            
            annotated.append(station)
            prev_line = current_line
        
        return " → ".join(annotated)
