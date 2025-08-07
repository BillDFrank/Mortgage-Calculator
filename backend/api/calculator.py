import math
from typing import Dict, List, Optional, Tuple

def parse_float(value) -> Optional[float]:
    """
    Parse a value to float.
    
    Args:
        value: Value to parse
        
    Returns:
        float or None if parsing fails
    """
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None

def effective_interest_rate(interest_rate: float, bank_spread: Optional[float]) -> Optional[float]:
    """
    Calculate effective monthly interest rate.
    
    Args:
        interest_rate: Base interest rate
        bank_spread: Bank spread to add to the interest rate
        
    Returns:
        Effective monthly interest rate or None if calculation fails
    """
    rate = parse_float(interest_rate)
    spread = parse_float(bank_spread) if bank_spread is not None else 0
    
    if rate is None:
        return None
    
    return (rate + spread) / 100 / 12

def calculate_monthly_payment(principal: float, monthly_rate: float, months: int) -> float:
    """
    Calculate monthly payment for a loan.
    
    Args:
        principal: Loan principal amount
        monthly_rate: Monthly interest rate
        months: Loan term in months
        
    Returns:
        Monthly payment amount
    """
    if monthly_rate == 0:
        return principal / months if months > 0 else 0
    return principal * monthly_rate * (1 + monthly_rate)**months / ((1 + monthly_rate)**months - 1)

def solve_for_unknown(data: Dict) -> Dict:
    """
    Solve for the unknown field in mortgage calculation.
    
    Args:
        data: Dictionary containing mortgage calculation parameters
        
    Returns:
        Dictionary with calculated field and value
    """
    house_price = parse_float(data.get("house_price"))
    down_payment = parse_float(data.get("down_payment"))
    loan_term = parse_float(data.get("loan_term"))
    interest_rate = parse_float(data.get("interest_rate"))
    monthly_payment = parse_float(data.get("monthly_payment"))
    bank_spread = parse_float(data.get("bank_spread"))
    
    inputs = {
        "house_price": house_price,
        "down_payment": down_payment,
        "loan_term": loan_term,
        "interest_rate": interest_rate,
        "monthly_payment": monthly_payment
    }
    
    missing = [k for k, v in inputs.items() if v is None]
    
    if len(missing) > 1:
        raise ValueError(
            "Please leave exactly one required field empty (for auto-calculation).")
    if len(missing) == 0:
        raise ValueError(
            "Please leave exactly one required field empty so that it can be calculated automatically.")
    
    unknown = missing[0]
    
    if unknown == "house_price":
        r = effective_interest_rate(interest_rate, bank_spread)
        n = int(loan_term * 12) if loan_term is not None else 0
        principal = monthly_payment * \
            ((1 + r)**n - 1) / (r * (1 + r)**n) if r != 0 and r is not None else (monthly_payment * n if monthly_payment is not None and n is not None else 0)
        calc = down_payment + principal if down_payment is not None and principal is not None else 0
    elif unknown == "down_payment":
        r = effective_interest_rate(interest_rate, bank_spread)
        n = int(loan_term * 12) if loan_term is not None else 0
        principal = monthly_payment * \
            ((1 + r)**n - 1) / (r * (1 + r)**n) if r != 0 and r is not None else (monthly_payment * n if monthly_payment is not None and n is not None else 0)
        calc = house_price - principal if house_price is not None and principal is not None else 0
    elif unknown == "loan_term":
        r = effective_interest_rate(interest_rate, bank_spread)
        P = house_price - down_payment if house_price is not None and down_payment is not None else 0
        
        if monthly_payment is not None and r is not None and P is not None and monthly_payment <= P * r:
            raise ValueError("Monthly payment too low to pay the interest!")
        
        if r is not None and r != 0 and monthly_payment is not None and P is not None:
            n = math.log(monthly_payment / (monthly_payment - P * r)) / math.log(1 + r)
            calc = n / 12
        else:
            calc = 0
    elif unknown == "interest_rate":
        P = house_price - down_payment if house_price is not None and down_payment is not None else 0
        n = int(loan_term * 12) if loan_term is not None else 0

        def f(r):
            if r == 0:
                return monthly_payment - P / n if monthly_payment is not None and P is not None and n > 0 else 0
            return monthly_payment - (P * r * (1 + r)**n) / ((1 + r)**n - 1) if monthly_payment is not None and P is not None and n > 0 else 0

        def fprime(r):
            h = 1e-6
            return (f(r + h) - f(r - h)) / (2 * h)
        
        r_guess = 0.01
        for i in range(100):
            f_val = f(r_guess)
            fp = fprime(r_guess)
            if fp == 0:
                break
            r_new = r_guess - f_val / fp
            if abs(r_new - r_guess) < 1e-8:
                r_guess = r_new
                break
            r_guess = r_new
        
        calc = r_guess * 12 * 100 - \
            (bank_spread if bank_spread is not None else 0)
    elif unknown == "monthly_payment":
        r = effective_interest_rate(interest_rate, bank_spread)
        n = int(loan_term * 12) if loan_term is not None else 0
        P = house_price - down_payment if house_price is not None and down_payment is not None else 0
        calc = calculate_monthly_payment(P, r, n) if P is not None and r is not None and n is not None else 0
    else:
        calc = 0
    
    return {"calculated_field": unknown, "calculated_value": calc}

def simulate_amortization(data: Dict, computed_monthly_payment: Optional[float]) -> Tuple[List[Dict], float, float, int]:
    """
    Simulate amortization schedule.
    
    Args:
        data: Dictionary containing mortgage calculation parameters
        computed_monthly_payment: Pre-computed monthly payment if available
        
    Returns:
        Tuple of (schedule, total_interest, total_cost, duration)
    """
    house_price = parse_float(data.get("house_price"))
    down_payment = parse_float(data.get("down_payment"))
    loan_term = parse_float(data.get("loan_term"))
    interest_rate = parse_float(data.get("interest_rate"))
    bank_spread = parse_float(data.get("bank_spread"))
    monthly_payment = parse_float(data.get("monthly_payment"))
    bank_insurances = parse_float(data.get("bank_insurances")) or 0
    extra_monthly = parse_float(data.get("extra_monthly")) or 0
    extra_annual = parse_float(data.get("extra_annual")) or 0
    extra_fee_rate = parse_float(data.get("extra_fee_rate")) or 0
    loan_type = data.get("loan_type", "fixed")
    fixed_period = parse_float(data.get("fixed_period")) if data.get("fixed_period") else None
    adjusted_interest_rate = parse_float(data.get("adjusted_interest_rate")) if data.get("adjusted_interest_rate") else None
    table_view = data.get("table_view", "monthly")
    
    principal = house_price - down_payment if house_price is not None and down_payment is not None else 0
    balance = principal
    schedule = []
    total_interest = 0
    total_fee = 0
    month = 0
    n = int(loan_term * 12) if loan_term is not None else 0
    
    # Determine interest rate behavior based on loan type:
    if loan_type == "adjustable" and fixed_period is not None and adjusted_interest_rate is not None:
        fixed_months = int(fixed_period * 12) if fixed_period is not None else 0
        r_fixed = effective_interest_rate(interest_rate, bank_spread)
        r_adjusted = (adjusted_interest_rate +
                      (bank_spread if bank_spread else 0)) / 100 / 12
    elif loan_type == "full_variable":
        fixed_months = 0
        r_fixed = effective_interest_rate(interest_rate, bank_spread)
        r_adjusted = r_fixed
    else:
        fixed_months = n
        r_fixed = effective_interest_rate(interest_rate, bank_spread)
        r_adjusted = r_fixed
    
    if monthly_payment is None:
        monthly_payment = computed_monthly_payment
    
    monthly_schedule = []
    while balance > 0.01 and month < 1000:
        month += 1
        current_r = r_fixed if month <= fixed_months else r_adjusted
        interest = balance * current_r if balance is not None and current_r is not None else 0
        principal_payment = monthly_payment - interest if monthly_payment is not None and interest is not None else 0
        extra = extra_monthly
        if month % 12 == 0:
            extra += extra_annual
        fee = extra * (extra_fee_rate / 100) if extra > 0 and extra_fee_rate is not None else 0
        
        if principal_payment + extra > balance and balance is not None:
            principal_payment = balance
            extra = 0
            fee = 0
            payment = balance + interest if balance is not None and interest is not None else 0
        else:
            payment = monthly_payment if monthly_payment is not None else 0
        
        balance = balance - (principal_payment + extra) if balance is not None and principal_payment is not None and extra is not None else 0
        total_interest += interest if interest is not None else 0
        total_fee += fee if fee is not None else 0
        
        monthly_schedule.append({
            "month": month,
            "payment": payment,
            "extra": extra,
            "fee": fee,
            "interest": interest,
            "principal": principal_payment + extra,
            "balance": max(balance, 0) if balance is not None else 0
        })
    
    aggregated_schedule = []
    if table_view == "yearly":
        current_year = 1
        year_data = {"payment": 0, "extra": 0, "fee": 0,
                     "interest": 0, "principal": 0, "balance": None}
        for row in monthly_schedule:
            year_data["payment"] += row["payment"]
            year_data["extra"] += row["extra"]
            year_data["fee"] += row["fee"]
            year_data["interest"] += row["interest"]
            year_data["principal"] += row["principal"]
            year_data["balance"] = row["balance"]
            if row["month"] % 12 == 0:
                aggregated_schedule.append({
                    "period": current_year,
                    "payment": year_data["payment"],
                    "extra": year_data["extra"],
                    "fee": year_data["fee"],
                    "interest": year_data["interest"],
                    "principal": year_data["principal"],
                    "balance": year_data["balance"]
                })
                current_year += 1
                year_data = {"payment": 0, "extra": 0, "fee": 0,
                             "interest": 0, "principal": 0, "balance": None}
        if monthly_schedule and monthly_schedule[-1]["month"] % 12 != 0:
            aggregated_schedule.append({
                "period": current_year,
                "payment": year_data["payment"],
                "extra": year_data["extra"],
                "fee": year_data["fee"],
                "interest": year_data["interest"],
                "principal": year_data["principal"],
                "balance": year_data["balance"]
            })
    else:
        for row in monthly_schedule:
            row["period"] = row["month"]
            aggregated_schedule.append(row)
    
    total_payments = sum([row["payment"] for row in monthly_schedule]) + bank_insurances * len(monthly_schedule) if monthly_schedule else 0
    total_cost = total_payments + total_fee
    return aggregated_schedule, total_interest, total_cost, month