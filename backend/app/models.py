from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

class RandomStationsRequest(BaseModel):
    lines: List[str]

class CalculatePathRequest(BaseModel):
    lines: List[str]
    start: str
    end: str

class ValidatePathRequest(BaseModel):
    lines: List[str]
    start: str
    end: str
    user_path: List[str]

class PathResponse(BaseModel):
    shortest_cost: float
    paths: List  # Can be List[str] or List[dict] with transfer info

class ValidationResponse(BaseModel):
    valid: bool
    is_shortest: bool
    user_cost: Optional[float]
    shortest_cost: float
    message: str
    error_reason: Optional[str] = None  # Detailed error reason
    user_path_annotated: Optional[str] = None  # User path with transfer annotations
    all_shortest_paths: List  # Can be List[str] or formatted with transfers

class RandomStationsResponse(BaseModel):
    start: str
    end: str

class StationsResponse(BaseModel):
    stations: List[str]

class ReachableStationsRequest(BaseModel):
    lines: List[str]
    start: str
