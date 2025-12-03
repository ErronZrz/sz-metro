# -*- coding: utf-8 -*-
import json
import random
from collections import defaultdict
import heapq
import sys
from decimal import Decimal, getcontext
from typing import Dict, List, Set, Tuple, Optional

# 设置 Decimal 精度
getcontext().prec = 28


class MetroNetwork:
    """深圳地铁网络类，封装地铁线路数据和相关操作"""
    
    def __init__(self, json_file="lines.json"):
        """初始化地铁网络，加载线路数据"""
        self.lines = self._load_lines(json_file)
        self.graph = None
        self.station_lines = None
        self.transfer_penalty = Decimal("2.5")
    
    def _load_lines(self, json_file: str) -> Dict[str, List[str]]:
        """加载线路数据"""
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            print("无法读取 lines.json 文件，请确认文件存在且格式正确。")
            sys.exit(1)
    
    def build_graph(self, selected_line_names: List[str]) -> None:
        """构建图结构和站点-线路映射"""
        if not self._validate_lines(selected_line_names):
            raise ValueError("包含无效线路")
        
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
        """验证线路名是否存在"""
        for ln in user_lines:
            if ln not in self.lines:
                print(f"❌ 无效线路：{ln}")
                return False
        return True
    
    def get_all_stations(self) -> Set[str]:
        """获取当前图中所有站点"""
        if self.graph is None:
            raise RuntimeError("请先构建图结构")
        return set(self.graph.keys())
    
    def is_reachable(self, start: str, end: str) -> bool:
        """检查两个站点是否可达"""
        if self.graph is None:
            raise RuntimeError("请先构建图结构")
        
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
        """随机选择两个可达的站点"""
        if self.graph is None:
            raise RuntimeError("请先构建图结构")
        
        all_nodes = list(self.graph.keys())
        if len(all_nodes) < 2:
            raise RuntimeError("站点不足两个。")
        
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
            raise RuntimeError("无有效连通分量。")
        
        comp = random.choice(components)
        return random.sample(comp, 2)


class PathFinder:
    """路径查找类，封装最短路径相关算法"""
    
    def __init__(self, metro_network: MetroNetwork):
        """初始化路径查找器"""
        self.network = metro_network
    
    def find_all_shortest_paths(self, start: str, end: str) -> Tuple[List[List[str]], Decimal]:
        """使用Dijkstra算法查找所有最短路径"""
        if self.network.graph is None or self.network.station_lines is None:
            raise RuntimeError("请先构建地铁网络图")
        
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
        
        # 找最小 cost 的所有 (end,line)
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
        
        # 回溯所有最短路径
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
        """计算给定路径的成本"""
        if len(path) <= 1:
            return Decimal("0")
        
        cost = Decimal("0")
        prev_line = None
        
        for u, v in zip(path, path[1:]):
            lines = self.network.station_lines[u] & self.network.station_lines[v]
            if not lines:
                return Decimal("Infinity")  # 非法路径
            
            # 选择线路逻辑
            if prev_line in lines:
                line = prev_line
            else:
                line = sorted(lines)[0]
            
            cost += Decimal("1")
            if prev_line is not None and line != prev_line:
                cost += self.network.transfer_penalty
            
            prev_line = line
        
        return cost


class PathValidator:
    """路径验证类，用于检查用户输入的路径是否合法"""
    
    def __init__(self, metro_network: MetroNetwork):
        """初始化路径验证器"""
        self.network = metro_network
    
    def validate_path(self, path: List[str], start: str, end: str) -> Tuple[bool, str]:
        """验证用户输入的路径是否合法"""
        if path[0] != start:
            return False, f"起点必须是：{start}"
        if path[-1] != end:
            return False, f"终点必须是：{end}"
        
        all_stations = self.network.get_all_stations()
        for p in path:
            if p not in all_stations:
                return False, f"不存在的站名：{p}"
        
        for a, b in zip(path, path[1:]):
            if b not in self.network.graph[a]:
                return False, f"站点不相邻：{a} → {b}"
        
        if len(path) != len(set(path)):
            return False, "路线中出现重复站点"
        
        return True, "OK"


class PathDisplay:
    """路径显示类，用于格式化输出路径信息"""
    
    @staticmethod
    def annotate_path_with_transfers(path: List[str], station_lines: Dict[str, Set[str]]) -> List[Tuple[str, Optional[str], Optional[str]]]:
        """为路径添加换乘信息"""
        annotated = []
        if not path:
            return annotated
        
        # 第一个站：还没有确定线路，也没有换乘
        annotated.append((path[0], None, None))
        prev_line = None
        
        for i in range(1, len(path)):
            u = path[i - 1]
            v = path[i]
            
            lines = station_lines[u] & station_lines[v]
            if not lines:
                # 理论上不会发生，因为路径已合法
                line = None
            else:
                # 优先沿用 prev_line
                if prev_line in lines:
                    line = prev_line
                else:
                    line = sorted(lines)[0]
            
            # 换乘发生在 u 这个站
            if prev_line is not None and line is not None and prev_line != line:
                u_station, _, _ = annotated[-1]
                annotated[-1] = (u_station, prev_line, f"{prev_line}换乘{line}")
            
            # 当前边走到 v，记录当前使用的 line
            annotated.append((v, line, None))
            prev_line = line
        
        return annotated
    
    @staticmethod
    def print_path_with_transfers(path: List[str], station_lines: Dict[str, Set[str]]) -> None:
        """打印带换乘信息的路径"""
        annotated = PathDisplay.annotate_path_with_transfers(path, station_lines)
        
        out_parts = []
        for station, _, transfer in annotated:
            if transfer is None:
                out_parts.append(station)
            else:
                out_parts.append(f"{station}({transfer})")
        
        print(" → ".join(out_parts))


class MetroGame:
    """地铁寻路游戏主类，协调各个组件"""
    
    def __init__(self):
        """初始化游戏"""
        self.metro_network = MetroNetwork()
        self.path_finder = PathFinder(self.metro_network)
        self.path_validator = PathValidator(self.metro_network)
        self.shortest_paths = None
        self.best_cost = None
        self.start = None
        self.end = None
    
    def setup_game(self) -> bool:
        """设置游戏参数"""
        # 1. 读取线路选择
        user_input = self._get_line_selection()
        if not user_input:
            return False
        
        # 2. 构建图
        try:
            self.metro_network.build_graph(user_input)
        except ValueError:
            return False
        
        # 3. 读取起点和终点
        if not self._get_start_end_stations():
            return False
        
        # 4. 计算最短路径
        self.shortest_paths, self.best_cost = self.path_finder.find_all_shortest_paths(self.start, self.end)
        if not self.shortest_paths:
            print("无可达路径。")
            return False
        
        return True
    
    def _get_line_selection(self) -> Optional[List[str]]:
        """获取用户选择的线路"""
        if len(sys.argv) > 1:
            user_input = sys.argv[1:]
            print(f"命令行指定线路：{' '.join(user_input)}")
        else:
            user_input = input("请输入要使用的线路名（空格分隔）：").strip().split()
        
        if not user_input:
            print("未选择线路")
            return None
        
        return user_input
    
    def _get_start_end_stations(self) -> bool:
        """获取用户选择的起点和终点"""
        print("\n可以输入两个站名作为起点与终点（空格分隔）。")
        print("直接按回车留空，将自动随机抽取两个站。")
        user_st = input("请输入起点和终点：").strip()
        
        if user_st == "":
            try:
                self.start, self.end = self.metro_network.pick_two_random_stations()
            except RuntimeError as e:
                print(f"无法生成题目：{e}")
                return False
        else:
            parts = user_st.split()
            if len(parts) != 2:
                print("❌ 必须输入两个站名，例如：前海湾 宝安中心")
                return False
            
            start, end = parts
            all_stations = self.metro_network.get_all_stations()
            
            if start not in all_stations:
                print(f"❌ 不存在的站点：{start}")
                return False
            if end not in all_stations:
                print(f"❌ 不存在的站点：{end}")
                return False
            if start == end:
                print("❌ 起点与终点不能相同")
                return False
            
            if not self.metro_network.is_reachable(start, end):
                print(f"❌ {start} 与 {end} 不可达，请检查线路范围。")
                return False
            
            self.start, self.end = start, end
        
        print(f"\n🎯 起点：{self.start}")
        print(f"🎯 终点：{self.end}\n")
        return True
    
    def play_game(self) -> None:
        """开始游戏主循环"""
        print(f"最短 cost 约为 {self.best_cost.to_integral_value()}\n")
        print("请尝试输入最短路线（站名空格分隔），放弃请输入：放弃\n")
        
        while True:
            user = input("请输入站名列表：").strip()
            
            if user == "放弃":
                self._show_all_solutions()
                break
            
            path = user.split()
            ok, msg = self.path_validator.validate_path(path, self.start, self.end)
            
            if not ok:
                print(f"❌ 路线不合法：{msg}\n")
                continue
            
            user_cost = self.path_finder.calculate_path_cost(path)
            
            if user_cost != self.best_cost:
                print(f"❌ 路线合法，但不是最短路线（你的 cost 为 {user_cost}）。\n")
                continue
            
            # cost 合法 → 还需匹配路径
            if path in self.shortest_paths:
                print("✅ 恭喜！你找到了一条最短路线。\n")
            else:
                print("⚠ cost 正确，但结构不是系统列出的路径之一。仍视为正确。\n")
            
            self._show_other_solutions(path)
            print("\n程序结束。")
            break
    
    def _show_all_solutions(self) -> None:
        """显示所有解决方案"""
        print("\n以下为所有最短路线：")
        for p in self.shortest_paths:
            PathDisplay.print_path_with_transfers(p, self.metro_network.station_lines)
        print(f"\n最短 cost = {self.best_cost}")
        print("\n已退出。")
    
    def _show_other_solutions(self, user_path: List[str]) -> None:
        """显示其他解决方案"""
        others = [p for p in self.shortest_paths if p != user_path]
        if others:
            print("其它最短路线：")
            for p in others:
                PathDisplay.print_path_with_transfers(p, self.metro_network.station_lines)
    
    def run(self) -> None:
        """运行游戏"""
        if self.setup_game():
            self.play_game()
        else:
            print("程序结束。")


def main():
    """主函数，启动游戏"""
    game = MetroGame()
    game.run()


if __name__ == "__main__":
    main()