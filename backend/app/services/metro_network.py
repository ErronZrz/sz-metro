# -*- coding: utf-8 -*-
import json
import random
from collections import defaultdict
from decimal import Decimal, getcontext
from typing import Dict, List, Set, Tuple, Union
import os

# Set Decimal precision
getcontext().prec = 28


class MetroNetwork:
    """Shenzhen Metro Network class"""
    
    def __init__(self, json_file: str = None):
        """Initialize metro network"""
        if json_file is None:
            # Default to stations_coordinates.json in backend directory
            json_file = os.path.join(os.path.dirname(__file__), "..", "..", "stations_coordinates.json")
        self.lines = self._load_lines(json_file)
        self.graph = None
        self.station_lines = None
        self.transfer_penalty = Decimal("2.5")
    
    def _load_lines(self, json_file: str) -> Dict[str, Union[List[str], dict]]:
        """Load line data from JSON file (stations_coordinates.json)"""
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Extract the "lines" field from stations_coordinates.json
                # Format: {"lines": {"1号线": {"color": "#...", "stations": [...], "is_loop": false}, ...}}
                if "lines" in data:
                    return data["lines"]
                # Fallback: if it's the old lines.json format (direct line mapping)
                return data
        except Exception as e:
            raise RuntimeError(f"Cannot read stations_coordinates.json: {e}")
    
    def _get_line_stations(self, line_name: str) -> List[str]:
        """
        Get stations list for a line (supports both old and new format).
        Old format: {"1号线": ["站A", "站B", ...]}
        New format: {"1号线": {"stations": ["站A", "站B", ...], "is_loop": true}}
        """
        line_data = self.lines[line_name]
        if isinstance(line_data, dict):
            return line_data.get("stations", [])
        return line_data
    
    def _is_loop_line(self, line_name: str) -> bool:
        """
        Check if a line is a loop line.
        Returns False if is_loop is not specified (backward compatible).
        """
        line_data = self.lines[line_name]
        if isinstance(line_data, dict):
            return line_data.get("is_loop", False)
        return False
    
    def _are_adjacent_on_line(self, station_a: str, station_b: str, line_name: str) -> bool:
        """
        Check if two stations are adjacent on a given line (supports loop lines).
        """
        stations = self._get_line_stations(line_name)
        try:
            idx_a = stations.index(station_a)
            idx_b = stations.index(station_b)
        except ValueError:
            return False
        
        diff = abs(idx_a - idx_b)
        
        # Normal adjacent check
        if diff == 1:
            return True
        
        # For loop lines, first and last stations are also adjacent
        if self._is_loop_line(line_name) and diff == len(stations) - 1:
            return True
        
        return False

    def build_graph(self, selected_line_names: List[str]) -> None:
        """Build graph structure and station-line mapping"""
        if not self._validate_lines(selected_line_names):
            raise ValueError("Invalid line names")
        
        self.graph = defaultdict(set)
        self.station_lines = defaultdict(set)
        
        for line_name in selected_line_names:
            stations = self._get_line_stations(line_name)
            is_loop = self._is_loop_line(line_name)
            
            for s in stations:
                self.station_lines[s].add(line_name)
            
            # Connect adjacent stations
            for a, b in zip(stations, stations[1:]):
                self.graph[a].add(b)
                self.graph[b].add(a)
            
            # For loop lines, connect last station to first station
            if is_loop and len(stations) >= 2:
                self.graph[stations[-1]].add(stations[0])
                self.graph[stations[0]].add(stations[-1])
    
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
        return self._get_line_stations(line_name)
    
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
                    # Use the new adjacency method that supports loop lines
                    if self._are_adjacent_on_line(prev_station, station, line_name):
                        valid_lines.append(line_name)
                
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
    
    def build_structured_path(self, path: List[str], line_sequence: List[str]) -> dict:
        """
        Build structured path data for frontend visualization.
        
        Args:
            path: List of station names
            line_sequence: Pre-computed optimal line sequence from PathFinder
        
        Returns:
            Dictionary with:
            - annotated: Annotated path string (for text display)
            - stations: List of station names
            - lines: List of line names (one per station)
            - transfers: List of station indices where transfer happens
            - colors: List of line colors (one per station)
        """
        annotated = self.annotate_path_with_transfers(path, line_sequence)
        
        # Calculate transfer indices (where line changes)
        transfers = []
        for i in range(1, len(line_sequence)):
            prev_line = line_sequence[i - 1]
            curr_line = line_sequence[i]
            if prev_line and curr_line and prev_line != curr_line:
                # Transfer happens at station i-1 (the station before line change)
                transfers.append(i - 1)
        
        # Get colors for each station's line
        colors = []
        for line_name in line_sequence:
            if line_name and line_name in self.lines:
                # Try to get color from lines data
                # Color will be provided by coordinates data, use placeholder here
                colors.append(line_name)  # Frontend will map line name to color
            else:
                colors.append(None)
        
        return {
            "annotated": annotated,
            "stations": path,
            "lines": line_sequence,
            "transfers": transfers
        }
