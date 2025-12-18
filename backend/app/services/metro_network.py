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
        self.reverse_transfer_penalty = Decimal("1.5")  # Y-branch reverse transfer cost
        
        # Branch line info: maps branch line name to main line name
        # e.g., {"5号线+": "5号线"}
        self.branch_to_main = {}
        # Maps main line to its branch info
        # e.g., {"5号线": {"branch": "5号线+", "junction": "东川路", "main_start": "莘庄", "main_end": "奉贤新城", "branch_end": "闵行开发区"}}
        self.main_line_branches = {}
        # Track which stations are on which branch segment
        # e.g., {"5号线": {"main_segment": set(), "branch_segment": set()}}
        self.branch_segments = {}
        
        # Detect and setup branch lines
        self._detect_branch_lines()
    
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
        Check if two stations are adjacent on a given line (supports loop lines and virtual segments).
        
        For virtual line segments (e.g., "5号线:B"), we check adjacency on the base line.
        """
        # Handle virtual line segments (e.g., "5号线:B" -> "5号线")
        base_line_name = line_name.split(":")[0] if ":" in line_name else line_name
        
        # Check if base line exists
        if base_line_name not in self.lines:
            return False
        
        stations = self._get_line_stations(base_line_name)
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
        if self._is_loop_line(base_line_name) and diff == len(stations) - 1:
            return True
        
        return False

    def _detect_branch_lines(self) -> None:
        """
        Detect Y-shaped branch lines (e.g., 5号线 and 5号线+).
        Branch lines are identified by:
        1. Line name ends with "+"
        2. Has exactly one common station with main line
        3. The common station is at either end of the branch line
        """
        for line_name in list(self.lines.keys()):
            if not line_name.endswith("+"):
                continue
            
            main_line_name = line_name[:-1]  # Remove "+"
            if main_line_name not in self.lines:
                continue
            
            branch_stations = set(self._get_line_stations(line_name))
            main_stations = self._get_line_stations(main_line_name)
            main_stations_set = set(main_stations)
            
            # Find common stations (should be exactly 1)
            common = branch_stations & main_stations_set
            if len(common) != 1:
                continue
            
            junction = list(common)[0]
            branch_stations_list = self._get_line_stations(line_name)
            
            # Junction should be at either end of branch line
            if branch_stations_list[0] != junction and branch_stations_list[-1] != junction:
                continue
            
            # Determine branch end (the other end of branch line)
            if branch_stations_list[0] == junction:
                branch_end = branch_stations_list[-1]
            else:
                branch_end = branch_stations_list[0]
            
            # Determine main line start (from "start" field or first station)
            main_line_data = self.lines[main_line_name]
            if isinstance(main_line_data, dict) and "start" in main_line_data:
                main_start = main_line_data["start"]
            else:
                main_start = main_stations[0]
            
            # Determine main line end (the other end)
            if main_stations[0] == main_start:
                main_end = main_stations[-1]
            else:
                main_end = main_stations[0]
            
            # Store branch info
            self.branch_to_main[line_name] = main_line_name
            self.main_line_branches[main_line_name] = {
                "branch": line_name,
                "junction": junction,
                "main_start": main_start,
                "main_end": main_end,
                "branch_end": branch_end
            }
            
            # Calculate branch segments
            junction_idx = main_stations.index(junction)
            start_idx = main_stations.index(main_start)
            
            # Stations from junction to main_end (opposite direction from start)
            if start_idx < junction_idx:
                # main_start is before junction, so main_end segment is after junction
                main_end_segment = set(main_stations[junction_idx:])
            else:
                # main_start is after junction, so main_end segment is before junction
                main_end_segment = set(main_stations[:junction_idx + 1])
            
            # Branch segment (excluding junction)
            branch_segment = branch_stations - {junction}
            
            self.branch_segments[main_line_name] = {
                "main_end_segment": main_end_segment,  # Stations from junction to main_end
                "branch_segment": branch_segment,       # Stations on branch (excluding junction)
                "junction": junction
            }
    
    def _get_effective_line_name(self, line_name: str) -> str:
        """
        Get effective line name (maps branch lines to main line).
        e.g., "5号线+" -> "5号线"
        """
        return self.branch_to_main.get(line_name, line_name)
    
    def _is_branch_reverse_transfer(self, station: str, from_line: str, to_line: str) -> bool:
        """
        Check if transfer at station between from_line and to_line is a branch reverse transfer.
        This happens when traveling between main_end segment and branch segment of a Y-line.
        
        Returns True if this is a reverse transfer at branch junction.
        """
        # Get effective line names
        from_effective = self._get_effective_line_name(from_line)
        to_effective = self._get_effective_line_name(to_line)
        
        # Must be same effective line (both are part of the Y-line)
        if from_effective != to_effective:
            return False
        
        main_line = from_effective
        if main_line not in self.main_line_branches:
            return False
        
        branch_info = self.main_line_branches[main_line]
        
        # Must be at junction station
        if station != branch_info["junction"]:
            return False
        
        # Check if transferring between main line and branch line at junction
        from_is_branch = from_line.endswith("+")
        to_is_branch = to_line.endswith("+")
        
        # Transfer between main line and branch line at junction
        return from_is_branch != to_is_branch
    
    def _needs_branch_reverse_transfer(self, from_station: str, to_station: str, line_name: str) -> bool:
        """
        Check if traveling from from_station to to_station on line_name requires
        a branch reverse transfer (crossing the junction between main_end segment and branch segment).
        
        This is used when both stations are on the same effective line but on different branches.
        """
        effective_line = self._get_effective_line_name(line_name)
        
        if effective_line not in self.branch_segments:
            return False
        
        segments = self.branch_segments[effective_line]
        main_end_segment = segments["main_end_segment"]
        branch_segment = segments["branch_segment"]
        junction = segments["junction"]
        
        # Check if one station is in main_end_segment and the other in branch_segment
        from_in_main_end = from_station in main_end_segment and from_station != junction
        from_in_branch = from_station in branch_segment
        to_in_main_end = to_station in main_end_segment and to_station != junction
        to_in_branch = to_station in branch_segment
        
        # Reverse transfer needed if crossing between segments
        return (from_in_main_end and to_in_branch) or (from_in_branch and to_in_main_end)
    
    def build_graph(self, selected_line_names: List[str]) -> None:
        """Build graph structure and station-line mapping
        
        For Y-branch lines, stations are assigned to virtual line segments:
        - Stations from main_start to junction: use main line name (e.g., "5号线")
        - Stations from junction to main_end: use main line + ":B" (e.g., "5号线:B")
        - Stations on branch line: use branch line name (e.g., "5号线+")
        - Junction station belongs to all three: "5号线", "5号线:B", "5号线+"
        
        This allows proper detection of reverse transfers at the junction.
        """
        # Auto-include branch lines when main line is selected
        expanded_lines = list(selected_line_names)
        for line_name in selected_line_names:
            if line_name in self.main_line_branches:
                branch_line = self.main_line_branches[line_name]["branch"]
                if branch_line not in expanded_lines:
                    expanded_lines.append(branch_line)
        
        if not self._validate_lines(expanded_lines):
            raise ValueError("Invalid line names")
        
        self.graph = defaultdict(set)
        self.station_lines = defaultdict(set)
        
        # Track which lines are actually selected (for branch line handling)
        self._selected_lines = set(expanded_lines)
        
        for line_name in expanded_lines:
            stations = self._get_line_stations(line_name)
            is_loop = self._is_loop_line(line_name)
            effective_line = self._get_effective_line_name(line_name)
            
            # Check if this is a Y-branch main line with branch segment info
            if line_name in self.main_line_branches and line_name in self.branch_segments:
                branch_info = self.main_line_branches[line_name]
                segments = self.branch_segments[line_name]
                junction = branch_info["junction"]
                main_end_segment = segments["main_end_segment"]
                
                # Assign stations to appropriate virtual line segments
                for s in stations:
                    if s == junction:
                        # Junction belongs to both main line and :B segment
                        self.station_lines[s].add(line_name)  # 5号线
                        self.station_lines[s].add(f"{line_name}:B")  # 5号线:B
                    elif s in main_end_segment:
                        # B segment (from junction to main_end)
                        self.station_lines[s].add(f"{line_name}:B")  # 5号线:B
                    else:
                        # A segment (from main_start to junction)
                        self.station_lines[s].add(line_name)  # 5号线
            elif line_name in self.branch_to_main:
                # This is a branch line (e.g., 5号线+)
                main_line = self.branch_to_main[line_name]
                if main_line in self.main_line_branches:
                    junction = self.main_line_branches[main_line]["junction"]
                    for s in stations:
                        self.station_lines[s].add(line_name)  # 5号线+
                        if s == junction:
                            # Junction also belongs to main line and :B
                            self.station_lines[s].add(main_line)  # 5号线
                            self.station_lines[s].add(f"{main_line}:B")  # 5号线:B
                else:
                    for s in stations:
                        self.station_lines[s].add(line_name)
            else:
                # Normal line (no Y-branch)
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
    
    def get_all_lines(self, include_branch_lines: bool = False) -> List[str]:
        """Get all available line names
        
        Args:
            include_branch_lines: If True, include branch lines (e.g., '5号线+')
                                  If False (default), only return main lines
        """
        if include_branch_lines:
            return list(self.lines.keys())
        # Filter out branch lines (ending with '+')
        return [line for line in self.lines.keys() if not line.endswith('+')]
    
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
    
    def get_transfer_cost(self, station: str, from_line: str, to_line: str) -> Decimal:
        """
        Get the transfer cost at a station between two lines.
        
        For Y-branch lines, the reverse transfer cost is handled separately
        by using virtual line segments (e.g., "5号线:B" for main_end segment).
        
        Returns:
        - 0 if no transfer (same line)
        - reverse_transfer_penalty (1.5) for Y-branch reverse transfer (between virtual segments)
        - transfer_penalty (2.5) for normal transfer
        """
        if from_line is None or to_line is None:
            return Decimal("0")
        
        # Same line, no transfer cost
        if from_line == to_line:
            return Decimal("0")
        
        # Check if this is a Y-branch reverse transfer (between virtual segments)
        # Virtual segments are like "5号线:B" and "5号线+"
        from_base = from_line.split(":")[0] if ":" in from_line else from_line
        to_base = to_line.split(":")[0] if ":" in to_line else to_line
        
        from_effective = self._get_effective_line_name(from_base)
        to_effective = self._get_effective_line_name(to_base)
        
        # Same Y-branch line system: check for reverse transfer
        if from_effective == to_effective and from_effective in self.main_line_branches:
            branch_info = self.main_line_branches[from_effective]
            junction = branch_info["junction"]
            
            # At junction, switching between main_end segment (:B) and branch (+) costs 1.5
            if station == junction:
                from_is_b_segment = ":B" in from_line
                to_is_b_segment = ":B" in to_line
                from_is_branch = from_base.endswith("+")
                to_is_branch = to_base.endswith("+")
                
                # Reverse transfer: B segment <-> branch segment
                if (from_is_b_segment and to_is_branch) or (from_is_branch and to_is_b_segment):
                    return self.reverse_transfer_penalty
            
            # Same Y-branch system but no reverse transfer needed
            return Decimal("0")
        
        # Normal transfer between different lines
        return self.transfer_penalty
    
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
    
    def _get_display_line_name(self, line_name: str) -> str:
        """
        Get display-friendly line name.
        Converts virtual segment names like "5号线:B" to "5号线".
        Converts branch line names like "5号线+" to "5号线".
        """
        if line_name is None:
            return None
        # Remove virtual segment suffix (e.g., "5号线:B" -> "5号线")
        if ":" in line_name:
            return line_name.split(":")[0]
        # Remove branch line suffix (e.g., "5号线+" -> "5号线")
        if line_name.endswith("+"):
            return line_name[:-1]
        return line_name
    
    def _is_y_branch_continuation(self, from_line: str, to_line: str) -> bool:
        """
        Check if switching from from_line to to_line is a Y-branch continuation
        (same direction, no actual transfer needed).
        
        Examples:
        - "5号线" -> "5号线+": continuation (A to C direction)
        - "5号线+" -> "5号线": continuation (C to A direction)
        - "5号线:B" -> "5号线+": NOT continuation (B to C, needs reverse)
        - "5号线+" -> "5号线:B": NOT continuation (C to B, needs reverse)
        """
        if from_line is None or to_line is None:
            return False
        
        # Get base names
        from_base = from_line.split(":")[0] if ":" in from_line else from_line
        to_base = to_line.split(":")[0] if ":" in to_line else to_line
        
        from_effective = self._get_effective_line_name(from_base)
        to_effective = self._get_effective_line_name(to_base)
        
        # Must be same Y-branch system
        if from_effective != to_effective:
            return False
        if from_effective not in self.main_line_branches:
            return False
        
        # Check for reverse transfer (B <-> branch)
        from_is_b = ":B" in from_line
        to_is_b = ":B" in to_line
        from_is_branch = from_base.endswith("+")
        to_is_branch = to_base.endswith("+")
        
        # Reverse transfer (not continuation): B segment <-> branch segment
        if (from_is_b and to_is_branch) or (from_is_branch and to_is_b):
            return False
        
        # All other Y-branch switches are continuations
        return True
    
    def _is_y_branch_reverse_transfer(self, from_line: str, to_line: str) -> bool:
        """
        Check if switching from from_line to to_line is a Y-branch reverse transfer.
        This is when going from B segment to branch segment (or vice versa).
        """
        if from_line is None or to_line is None:
            return False
        
        from_base = from_line.split(":")[0] if ":" in from_line else from_line
        to_base = to_line.split(":")[0] if ":" in to_line else to_line
        
        from_effective = self._get_effective_line_name(from_base)
        to_effective = self._get_effective_line_name(to_base)
        
        if from_effective != to_effective:
            return False
        if from_effective not in self.main_line_branches:
            return False
        
        from_is_b = ":B" in from_line
        to_is_b = ":B" in to_line
        from_is_branch = from_base.endswith("+")
        to_is_branch = to_base.endswith("+")
        
        return (from_is_b and to_is_branch) or (from_is_branch and to_is_b)
    
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
                    # Check for Y-branch continuation (no actual transfer)
                    if self._is_y_branch_continuation(prev_line, current_line):
                        # No transfer annotation needed
                        pass
                    elif self._is_y_branch_reverse_transfer(prev_line, current_line):
                        # Reverse transfer at Y-branch junction
                        # Use only the main line name (they're the same after display conversion)
                        line_display = self._get_display_line_name(prev_line)
                        annotated[-1] = f"{annotated[-1]}({line_display}反向换乘)"
                    else:
                        # Normal transfer between different lines
                        prev_display = self._get_display_line_name(prev_line)
                        curr_display = self._get_display_line_name(current_line)
                        if prev_display != curr_display:
                            annotated[-1] = f"{annotated[-1]}({prev_display}换乘{curr_display})"
                
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
        
        # Convert line sequence to display-friendly names
        display_lines = [self._get_display_line_name(ln) for ln in line_sequence]
        
        # Calculate transfer indices (where actual transfer happens)
        # Exclude Y-branch continuations (same direction, no actual transfer)
        transfers = []
        for i in range(1, len(line_sequence)):
            prev_line = line_sequence[i - 1]
            curr_line = line_sequence[i]
            if prev_line and curr_line and prev_line != curr_line:
                # Skip Y-branch continuations
                if self._is_y_branch_continuation(prev_line, curr_line):
                    continue
                # Transfer happens at station i-1 (the station before line change)
                transfers.append(i - 1)
        
        return {
            "annotated": annotated,
            "stations": path,
            "lines": display_lines,  # Use display-friendly line names
            "transfers": transfers
        }
