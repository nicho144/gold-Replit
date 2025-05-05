from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Union

class MarketInput(BaseModel):
    ticker_front: str = Field(..., description="Front month contract ticker (e.g., 'GC=F' for Gold Front Month)")
    ticker_next: str = Field(..., description="Next month contract ticker (e.g., 'GCM24.CMX')")
    physical_demand: str = Field(..., description="Physical demand trend", pattern="^(declining|stable|rising)$")
    price_breakout: bool = Field(..., description="Whether price has broken resistance level")
    
    @validator('physical_demand')
    def validate_physical_demand(cls, v):
        if v not in ["declining", "stable", "rising"]:
            raise ValueError("physical_demand must be 'declining', 'stable', or 'rising'")
        return v

class PriceData(BaseModel):
    front_contract: float
    next_contract: float
    contango_spread: float
    contango_percentage: float

class MarketAnalysis(BaseModel):
    signal: str
    reasons: List[str]
    recommendations: List[str]
    prices: Dict[str, Union[float, str]]
    market_condition: Optional[str] = None
    term_structure: Optional[str] = None
    confidence_score: Optional[int] = None
    analysis_timestamp: Optional[str] = None
