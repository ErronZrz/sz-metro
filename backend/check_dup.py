import json
from collections import defaultdict
from pathlib import Path


def load_stations(json_path: Path):
    """读取 JSON 文件并返回 stations 字典"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("stations", {})


def find_shared_coordinates(stations: dict):
    """
    查找共享 x 或 y 坐标的站点
    返回：
        shared_x: {x_value: [station1, station2, ...]}
        shared_y: {y_value: [station1, station2, ...]}
    """
    x_map = defaultdict(list)
    y_map = defaultdict(list)

    for station_name, info in stations.items():
        x = info.get("x")
        y = info.get("y")

        x_map[x].append(station_name)
        y_map[y].append(station_name)

    # 只保留真正“共享”的（>=2 个站）
    shared_x = {x: names for x, names in x_map.items() if len(names) > 1}
    shared_y = {y: names for y, names in y_map.items() if len(names) > 1}

    return shared_x, shared_y


def print_result(shared_x: dict, shared_y: dict):
    print("=== 共享相同 x 坐标的站点 ===")
    if not shared_x:
        print("无")
    else:
        for x, stations in shared_x.items():
            print(f"x = {x}: {stations}")

    print("\n=== 共享相同 y 坐标的站点 ===")
    if not shared_y:
        print("无")
    else:
        for y, stations in shared_y.items():
            print(f"y = {y}: {stations}")


if __name__ == "__main__":
    json_file = Path("stations_coordinates_sh.json")
    stations = load_stations(json_file)

    shared_x, shared_y = find_shared_coordinates(stations)
    print_result(shared_x, shared_y)
