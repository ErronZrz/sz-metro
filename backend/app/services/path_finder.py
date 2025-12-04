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
                possible_lines = self.network.station_lines[u] & self.network.station_lines[v]
                
                for line in possible_lines:
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
    
    def calculate_path_cost(self, path: List[str]) -> Decimal:
        """Calculate cost for a given path"""
        if len(path) <= 1:
            return Decimal("0")
        
        cost = Decimal("0")
        prev_line = None
        
        for u, v in zip(path, path[1:]):
            lines = self.network.station_lines[u] & self.network.station_lines[v]
            if not lines:
                return Decimal("Infinity")  # Invalid path
            
            # Line selection logic
            if prev_line in lines:
                line = prev_line
            else:
                line = sorted(lines)[0]
            
            cost += Decimal("1")
            if prev_line is not None and line != prev_line:
                cost += self.network.transfer_penalty
            
            prev_line = line
        
        return cost
