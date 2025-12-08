# -*- coding: utf-8 -*-
import heapq
from collections import defaultdict
from decimal import Decimal
from typing import List, Tuple
from app.services.metro_network import MetroNetwork


class PathFinder:
    """Path finding class using Dijkstra algorithm"""
    
    def __init__(self, metro_network: MetroNetwork):
        """Initialize path finder"""
        self.network = metro_network
        self._path_cache = {}  # Cache for path analysis results
    
    def find_all_shortest_paths(self, start: str, end: str) -> Tuple[List[List[str]], Decimal]:
        """Find all shortest paths using Dijkstra algorithm"""
        if self.network.graph is None or self.network.station_lines is None:
            raise RuntimeError("Please build metro network graph first")
        
        dist = defaultdict(lambda: Decimal("Infinity"))
        parents = defaultdict(list)
        
        pq = []
        dist[(start, None)] = Decimal("0")
        heapq.heappush(pq, (Decimal("0"), start, None))
        
        while pq:
            cur_cost, u, u_line = heapq.heappop(pq)
            
            if cur_cost != dist[(u, u_line)]:
                continue
            
            for v in self.network.graph[u]:
                # Find lines where u and v are both present
                common_lines = self.network.station_lines[u] & self.network.station_lines[v]
                
                # Filter to only lines where u and v are adjacent
                valid_lines = []
                for line_name in common_lines:
                    line_stations = self.network.lines[line_name]
                    try:
                        u_idx = line_stations.index(u)
                        v_idx = line_stations.index(v)
                        # Check if stations are adjacent on this line
                        if abs(u_idx - v_idx) == 1:
                            valid_lines.append(line_name)
                    except ValueError:
                        # Station not found in line (shouldn't happen)
                        continue
                
                # Only process valid adjacent connections
                for line in valid_lines:
                    cost = cur_cost + Decimal("1")
                    if u_line is not None and line != u_line:
                        cost += self.network.transfer_penalty
                    
                    if cost < dist[(v, line)]:
                        dist[(v, line)] = cost
                        parents[(v, line)] = [(u, u_line)]
                        heapq.heappush(pq, (cost, v, line))
                    
                    elif cost == dist[(v, line)]:
                        parents[(v, line)].append((u, u_line))
        
        # Find minimum cost for all (end, line) states
        best_cost = Decimal("Infinity")
        best_states = []
        for (node, line), c in dist.items():
            if node == end:
                if c < best_cost:
                    best_cost = c
                    best_states = [(node, line)]
                elif c == best_cost:
                    best_states.append((node, line))
        
        if best_cost == Decimal("Infinity"):
            return [], best_cost
        
        # Backtrack all shortest paths
        all_paths = []
        
        def backtrack(node, line, acc):
            if node == start:
                all_paths.append(list(reversed(acc + [node])))
                return
            for pnode, pline in parents[(node, line)]:
                backtrack(pnode, pline, acc + [node])
        
        for node, line in best_states:
            backtrack(node, line, [])
        
        return all_paths, best_cost
    
    def analyze_path_optimal(self, path: List[str]) -> Tuple[Decimal, List[str]]:
        """
        Analyze path using dynamic programming to find optimal line selection.
        Returns: (minimum_cost, optimal_line_sequence)
        
        This method finds the line sequence that minimizes transfers while
        looking ahead to avoid unnecessary transfers.
        """
        if len(path) <= 1:
            return Decimal("0"), []
        
        # Check cache
        path_key = tuple(path)
        if path_key in self._path_cache:
            return self._path_cache[path_key]
        
        n = len(path)
        # dp[i][line] = (minimum cost to reach station i using line, previous line)
        dp = [defaultdict(lambda: (Decimal("Infinity"), None)) for _ in range(n)]
        
        # Initialize first station (no cost, no line)
        dp[0][None] = (Decimal("0"), None)
        
        # Forward pass: compute minimum costs
        for i in range(n - 1):
            u, v = path[i], path[i + 1]
            common_lines = self.network.station_lines[u] & self.network.station_lines[v]
            
            # Find valid lines where u and v are adjacent
            valid_lines = []
            for line_name in common_lines:
                line_stations = self.network.lines[line_name]
                try:
                    u_idx = line_stations.index(u)
                    v_idx = line_stations.index(v)
                    if abs(u_idx - v_idx) == 1:
                        valid_lines.append(line_name)
                except ValueError:
                    continue
            
            if not valid_lines:
                # Invalid path
                self._path_cache[path_key] = (Decimal("Infinity"), [])
                return Decimal("Infinity"), []
            
            # Try all possible previous lines and current lines
            for prev_line, (prev_cost, _) in dp[i].items():
                if prev_cost == Decimal("Infinity"):
                    continue
                
                for curr_line in valid_lines:
                    # Cost = previous cost + 1 (travel) + transfer penalty (if needed)
                    new_cost = prev_cost + Decimal("1")
                    if prev_line is not None and prev_line != curr_line:
                        new_cost += self.network.transfer_penalty
                    
                    # Update if this is better
                    if new_cost < dp[i + 1][curr_line][0]:
                        dp[i + 1][curr_line] = (new_cost, prev_line)
        
        # Find the best ending state
        best_cost = Decimal("Infinity")
        best_end_line = None
        for line, (cost, _) in dp[n - 1].items():
            if cost < best_cost:
                best_cost = cost
                best_end_line = line
        
        if best_cost == Decimal("Infinity"):
            self._path_cache[path_key] = (Decimal("Infinity"), [])
            return Decimal("Infinity"), []
        
        # Backward pass: reconstruct optimal line sequence
        line_sequence = [None] * n
        current_line = best_end_line
        
        for i in range(n - 1, 0, -1):
            line_sequence[i] = current_line
            _, prev_line = dp[i][current_line]
            current_line = prev_line
        
        line_sequence[0] = None  # First station has no line
        
        # Cache result
        self._path_cache[path_key] = (best_cost, line_sequence)
        return best_cost, line_sequence
    
    def calculate_path_cost(self, path: List[str]) -> Decimal:
        """Calculate minimum cost for a given path"""
        cost, _ = self.analyze_path_optimal(path)
        return cost
