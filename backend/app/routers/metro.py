# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Path
from typing import List
import json
import os
from app.models import (
    RandomStationsRequest,
    RandomStationsResponse,
    CalculatePathRequest,
    PathResponse,
    ValidatePathRequest,
    ValidationResponse,
    StationsResponse,
    ReachableStationsRequest
)
from app.services.metro_network import MetroNetwork
from app.services.path_finder import PathFinder
from app.services.path_validator import PathValidator

router = APIRouter()

# City data file mapping
CITY_DATA_FILES = {
    "sz": "stations_coordinates.json",      # Shenzhen
    "sh": "stations_coordinates_sh.json",   # Shanghai
    "cs": "stations_coordinates_cs.json",   # Changsha
}

CITY_NAMES = {
    "sz": "深圳",
    "sh": "上海",
    "cs": "长沙",
}

# Cache for metro networks (one per city)
_metro_networks = {}
_station_coordinates_cache = {}


def get_metro_network(city: str) -> MetroNetwork:
    """Get or create MetroNetwork instance for a city"""
    if city not in CITY_DATA_FILES:
        raise HTTPException(status_code=404, detail=f"City not supported: {city}")
    
    if city not in _metro_networks:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        json_file = os.path.join(base_dir, CITY_DATA_FILES[city])
        _metro_networks[city] = MetroNetwork(json_file)
    
    return _metro_networks[city]


def get_station_coordinates_data(city: str):
    """Load station coordinates from JSON file for a city"""
    if city not in CITY_DATA_FILES:
        raise HTTPException(status_code=404, detail=f"City not supported: {city}")
    
    if city not in _station_coordinates_cache:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        coords_file = os.path.join(base_dir, CITY_DATA_FILES[city])
        with open(coords_file, 'r', encoding='utf-8') as f:
            _station_coordinates_cache[city] = json.load(f)
    
    return _station_coordinates_cache[city]


@router.get("/{city}/lines", response_model=List[str])
async def get_lines(city: str = Path(..., description="City code: sz or sh")):
    """Get all available metro lines for a city"""
    try:
        metro_network = get_metro_network(city)
        return metro_network.get_all_lines()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{city}/lines/{line_name}/stations", response_model=List[str])
async def get_line_stations(
    city: str = Path(..., description="City code: sz or sh"),
    line_name: str = Path(..., description="Line name")
):
    """Get all stations for a specific line"""
    try:
        metro_network = get_metro_network(city)
        return metro_network.get_line_stations(line_name)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{city}/stations", response_model=StationsResponse)
async def get_stations(
    city: str = Path(..., description="City code: sz or sh"),
    lines: str = None
):
    """Get all stations, optionally filtered by lines"""
    try:
        metro_network = get_metro_network(city)
        if lines:
            line_list = [l.strip() for l in lines.split(',')]
            metro_network.build_graph(line_list)
            stations = sorted(metro_network.get_all_stations())
        else:
            # Return all stations from all lines
            all_stations = set()
            for line_name in metro_network.get_all_lines():
                all_stations.update(metro_network.get_line_stations(line_name))
            stations = sorted(all_stations)
        
        return StationsResponse(stations=stations)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{city}/game/random-stations", response_model=RandomStationsResponse)
async def random_stations(
    request: RandomStationsRequest,
    city: str = Path(..., description="City code: sz or sh")
):
    """Generate random start and end stations"""
    try:
        metro_network = get_metro_network(city)
        metro_network.build_graph(request.lines)
        start, end = metro_network.pick_two_random_stations()
        return RandomStationsResponse(start=start, end=end)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{city}/game/reachable-stations", response_model=StationsResponse)
async def reachable_stations(
    request: ReachableStationsRequest,
    city: str = Path(..., description="City code: sz or sh")
):
    """Get all stations reachable from start station within selected lines"""
    try:
        metro_network = get_metro_network(city)
        metro_network.build_graph(request.lines)
        
        # Validate start station exists
        all_stations = metro_network.get_all_stations()
        if request.start not in all_stations:
            raise HTTPException(status_code=400, detail=f"Start station not found: {request.start}")
        
        reachable = metro_network.get_reachable_stations(request.start)
        return StationsResponse(stations=sorted(reachable))
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{city}/game/calculate-path", response_model=PathResponse)
async def calculate_path(
    request: CalculatePathRequest,
    city: str = Path(..., description="City code: sz or sh")
):
    """Calculate shortest paths between two stations"""
    try:
        metro_network = get_metro_network(city)
        metro_network.build_graph(request.lines)
        
        # Validate stations exist
        all_stations = metro_network.get_all_stations()
        if request.start not in all_stations:
            raise HTTPException(status_code=400, detail=f"Start station not found: {request.start}")
        if request.end not in all_stations:
            raise HTTPException(status_code=400, detail=f"End station not found: {request.end}")
        
        # Check if reachable
        if not metro_network.is_reachable(request.start, request.end):
            raise HTTPException(status_code=400, detail="Stations are not reachable")
        
        # Find shortest paths
        path_finder = PathFinder(metro_network)
        paths, cost, paths_with_lines = path_finder.find_all_shortest_paths(request.start, request.end)
        
        if not paths:
            raise HTTPException(status_code=400, detail="No path found")
        
        # Build structured paths with line sequences (preserves transfer variants)
        # Use a set to deduplicate identical annotated paths
        seen_annotated = set()
        structured_paths = []
        for path, line_seq in paths_with_lines:
            structured = metro_network.build_structured_path(path, line_seq)
            # Use annotated string for deduplication
            if structured["annotated"] not in seen_annotated:
                seen_annotated.add(structured["annotated"])
                structured_paths.append(structured)
        
        return PathResponse(
            shortest_cost=float(cost),
            paths=structured_paths
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{city}/game/validate-path", response_model=ValidationResponse)
async def validate_path(
    request: ValidatePathRequest,
    city: str = Path(..., description="City code: sz or sh")
):
    """Validate user's path"""
    try:
        metro_network = get_metro_network(city)
        metro_network.build_graph(request.lines)
        
        # Validate path
        path_validator = PathValidator(metro_network)
        is_valid, msg = path_validator.validate_path(request.user_path, request.start, request.end)
        
        # Get shortest paths for comparison
        path_finder = PathFinder(metro_network)
        shortest_paths, shortest_cost, paths_with_lines = path_finder.find_all_shortest_paths(request.start, request.end)
        
        if not is_valid:
            # Provide detailed error reason
            error_reason = msg
            if "Start station must be" in msg:
                error_reason = f"起点错误：你的路径起点是 {request.user_path[0]}，但应该是 {request.start}"
            elif "End station must be" in msg:
                error_reason = f"终点错误：你的路径终点是 {request.user_path[-1]}，但应该是 {request.end}"
            elif "Station does not exist" in msg:
                error_reason = f"站点不存在：{msg.split(':')[1].strip()} 不在所选线路中"
            elif "not adjacent" in msg:
                stations = msg.split(':')[1].strip()
                error_reason = f"站点不相邻：{stations} 之间没有直接连接"
            elif "Duplicate stations" in msg:
                error_reason = "路径中有重复站点，请检查你的路径"
            
            return ValidationResponse(
                valid=False,
                is_shortest=False,
                user_cost=None,
                shortest_cost=float(shortest_cost),
                message="路径不合法",
                error_reason=error_reason,
                user_path_annotated=None,
                all_shortest_paths=[]
            )
        
        # Calculate user path cost and optimal line sequence (single computation)
        user_cost, user_line_sequence = path_finder.analyze_path_optimal(request.user_path)
        
        is_shortest = (user_cost == shortest_cost)
        
        # Build structured shortest paths with line sequences (preserves transfer variants)
        # Use a set to deduplicate identical annotated paths
        seen_annotated = set()
        structured_paths = []
        for path, line_seq in paths_with_lines:
            structured = metro_network.build_structured_path(path, line_seq)
            if structured["annotated"] not in seen_annotated:
                seen_annotated.add(structured["annotated"])
                structured_paths.append(structured)
        
        # Build structured user path with optimal line sequence
        user_path_structured = metro_network.build_structured_path(request.user_path, user_line_sequence)
        user_path_annotated = user_path_structured["annotated"]
        
        if is_shortest:
            message = "恭喜！这是最短路径之一！"
            error_reason = None
        else:
            message = "路径合法但不是最短"
            error_reason = f"你的路径成本是 {float(user_cost)}，但最短路径成本是 {float(shortest_cost)}。请尝试减少换乘或站点数量。"
        
        return ValidationResponse(
            valid=True,
            is_shortest=is_shortest,
            user_cost=float(user_cost),
            shortest_cost=float(shortest_cost),
            message=message,
            error_reason=error_reason,
            user_path_annotated=user_path_annotated,
            all_shortest_paths=structured_paths
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{city}/map/coordinates")
async def get_map_coordinates(city: str = Path(..., description="City code: sz or sh")):
    """Get station coordinates and line information for map visualization"""
    try:
        data = get_station_coordinates_data(city)
        lines_data = data.get("lines", {})
        
        # Process lines: merge branch lines (e.g., 5号线+) into main lines
        merged_lines = {}
        branch_lines = {}  # Temporarily store branch lines
        
        for line_name, line_info in lines_data.items():
            line_data = dict(line_info) if isinstance(line_info, dict) else {}
            # Set is_loop to False if not present (backward compatible)
            if "is_loop" not in line_data:
                line_data["is_loop"] = False
            
            if line_name.endswith("+"):
                # Store branch line for later merging
                branch_lines[line_name] = line_data
            else:
                merged_lines[line_name] = line_data
        
        # Merge branch lines into main lines
        for branch_name, branch_data in branch_lines.items():
            main_name = branch_name[:-1]  # Remove "+"
            if main_name in merged_lines:
                # Add branch stations info to main line
                main_line = merged_lines[main_name]
                if "branch_stations" not in main_line:
                    main_line["branch_stations"] = []
                # Store branch info: stations list (the branch line's stations)
                main_line["branch_stations"] = branch_data.get("stations", [])
        
        # Process stations: convert "+" line names to main line names in each station's lines array
        stations_data = data.get("stations", {})
        processed_stations = {}
        for station_name, station_info in stations_data.items():
            processed_station = dict(station_info)
            if "lines" in processed_station:
                # Remove "+" suffix from line names
                processed_station["lines"] = [
                    line[:-1] if line.endswith("+") else line
                    for line in processed_station["lines"]
                ]
                # Remove duplicates while preserving order
                seen = set()
                unique_lines = []
                for line in processed_station["lines"]:
                    if line not in seen:
                        seen.add(line)
                        unique_lines.append(line)
                processed_station["lines"] = unique_lines
            processed_stations[station_name] = processed_station
        
        return {
            "stations": processed_stations,
            "lines": merged_lines
        }
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Station coordinates data not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
