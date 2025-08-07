from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional
from datetime import datetime
from .euribor import get_latest_euribor, get_historical_euribor
from .calculator import solve_for_unknown, simulate_amortization, parse_float
from pydantic import BaseModel

router = APIRouter()

class CalculationRequest(BaseModel):
    house_price: Optional[float] = None
    down_payment: Optional[float] = None
    loan_term: Optional[float] = None
    interest_rate: Optional[float] = None
    monthly_payment: Optional[float] = None
    bank_spread: Optional[float] = None
    bank_insurances: Optional[float] = 0
    extra_monthly: Optional[float] = 0
    extra_annual: Optional[float] = 0
    extra_fee_rate: Optional[float] = 0
    loan_type: str = "fixed"
    fixed_period: Optional[float] = None
    adjusted_interest_rate: Optional[float] = None
    table_view: str = "monthly"

class CalculationResponse(BaseModel):
    calculated_field: str
    calculated_value: float
    total_borrowed: Optional[float] = None
    amortization: List[Dict] = []
    total_interest: float = 0
    total_cost: float = 0
    duration: int = 0

@router.get("/euribor/latest")
async def get_latest_euribor_rate(tenor: str = Query("3M", description="EURIBOR tenor (1M, 3M, 6M, 12M)")):
    """
    Get the latest EURIBOR rate for a specific tenor.
    
    Args:
        tenor (str): EURIBOR tenor (1M, 3M, 6M, 12M)
        
    Returns:
        dict: Latest EURIBOR rate
    """
    try:
        rate = get_latest_euribor(tenor)
        if rate is None:
            raise HTTPException(status_code=404, detail=f"EURIBOR rate not found for tenor {tenor}")
        return {"tenor": tenor, "rate": rate, "timestamp": datetime.now()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching EURIBOR rate: {str(e)}")

@router.get("/euribor/history")
async def get_historical_euribor_rates(
    tenor: str = Query("3M", description="EURIBOR tenor (1M, 3M, 6M, 12M)"),
    from_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    to_date: str = Query(..., description="End date in YYYY-MM-DD format")
):
    """
    Get historical EURIBOR rates for a specific tenor within a date range.
    
    Args:
        tenor (str): EURIBOR tenor (1M, 3M, 6M, 12M)
        from_date (str): Start date in YYYY-MM-DD format
        to_date (str): End date in YYYY-MM-DD format
        
    Returns:
        dict: Historical EURIBOR rates
    """
    try:
        # Validate date format
        datetime.strptime(from_date, "%Y-%m-%d")
        datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    try:
        rates = get_historical_euribor(tenor, from_date, to_date)
        return {"tenor": tenor, "from_date": from_date, "to_date": to_date, "rates": rates}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching historical EURIBOR rates: {str(e)}")

@router.post("/calc", response_model=CalculationResponse)
async def calculate_mortgage(request: CalculationRequest):
    """
    Calculate mortgage details based on provided parameters.
    
    Args:
        request (CalculationRequest): Mortgage calculation parameters
        
    Returns:
        CalculationResponse: Detailed mortgage calculation results
    """
    try:
        # Convert Pydantic model to dict for compatibility with existing functions
        data = request.dict()
        
        # Solve for unknown field
        unknown_result = solve_for_unknown(data)
        
        # Calculate computed monthly payment if needed
        computed_monthly_payment = None
        if unknown_result and unknown_result["calculated_field"] == "monthly_payment":
            computed_monthly_payment = unknown_result["calculated_value"]
            data["monthly_payment"] = computed_monthly_payment
        else:
            computed_monthly_payment = parse_float(data.get("monthly_payment"))
        
        # Simulate amortization
        schedule, total_interest, total_cost, duration = simulate_amortization(
            data, computed_monthly_payment)
        
        # Calculate total borrowed
        house_price = parse_float(data.get("house_price"))
        down_payment = parse_float(data.get("down_payment"))
        total_borrowed = house_price - down_payment if house_price is not None and down_payment is not None else None
        
        return CalculationResponse(
            calculated_field=unknown_result["calculated_field"] if unknown_result else "None",
            calculated_value=unknown_result["calculated_value"] if unknown_result else 0,
            total_borrowed=total_borrowed,
            amortization=schedule,
            total_interest=total_interest,
            total_cost=total_cost,
            duration=duration
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating mortgage: {str(e)}")