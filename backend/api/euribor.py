import requests
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ECB SDW API endpoint for EURIBOR rates
ECB_API_URL = "https://sdw-wsrest.ecb.europa.eu/service/data"

# EURIBOR series keys for different tenors
EURIBOR_SERIES = {
    "1M": "EURIBOR1MD.",
    "3M": "EURIBOR3MD.",
    "6M": "EURIBOR6MD.",
    "12M": "EURIBOR12MD."
}

class EuriborAPI:
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(hours=6)  # Cache for 6 hours
    
    def get_latest_rate(self, tenor: str) -> Optional[float]:
        """
        Get the latest EURIBOR rate for a specific tenor.
        
        Args:
            tenor (str): EURIBOR tenor (1M, 3M, 6M, 12M)
            
        Returns:
            Optional[float]: Latest EURIBOR rate or None if not found
        """
        if tenor not in EURIBOR_SERIES:
            raise ValueError(f"Invalid tenor: {tenor}. Must be one of {list(EURIBOR_SERIES.keys())}")
        
        # Check cache first
        cache_key = f"latest_{tenor}"
        if cache_key in self.cache:
            cached_time, cached_value = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return cached_value
        
        try:
            # Fetch data from ECB API
            series_key = EURIBOR_SERIES[tenor]
            url = f"{ECB_API_URL}/FM/{series_key}"
            
            # For now, we'll return mock data since we need to implement the actual API call
            # This is a placeholder implementation
            latest_rate = self._fetch_from_ecb(series_key)
            
            # Cache the result
            self.cache[cache_key] = (datetime.now(), latest_rate)
            return latest_rate
            
        except Exception as e:
            logger.error(f"Error fetching EURIBOR rate for {tenor}: {str(e)}")
            # Try to return cached value if available
            return self._get_cached_value(cache_key)
    
    def get_historical_rates(self, tenor: str, from_date: str, to_date: str) -> List[Dict]:
        """
        Get historical EURIBOR rates for a specific tenor within a date range.
        
        Args:
            tenor (str): EURIBOR tenor (1M, 3M, 6M, 12M)
            from_date (str): Start date in YYYY-MM-DD format
            to_date (str): End date in YYYY-MM-DD format
            
        Returns:
            List[Dict]: List of historical rates with dates
        """
        if tenor not in EURIBOR_SERIES:
            raise ValueError(f"Invalid tenor: {tenor}. Must be one of {list(EURIBOR_SERIES.keys())}")
        
        # Check cache first
        cache_key = f"history_{tenor}_{from_date}_{to_date}"
        if cache_key in self.cache:
            cached_time, cached_value = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return cached_value
        
        try:
            # Fetch data from ECB API
            series_key = EURIBOR_SERIES[tenor]
            url = f"{ECB_API_URL}/FM/{series_key}"
            
            # For now, we'll return mock data since we need to implement the actual API call
            # This is a placeholder implementation
            historical_rates = self._fetch_historical_from_ecb(series_key, from_date, to_date)
            
            # Cache the result
            self.cache[cache_key] = (datetime.now(), historical_rates)
            return historical_rates
            
        except Exception as e:
            logger.error(f"Error fetching historical EURIBOR rates for {tenor}: {str(e)}")
            # Try to return cached value if available
            return self._get_cached_value(cache_key) or []
    
    def _fetch_from_ecb(self, series_key: str) -> float:
        """
        Fetch the latest rate from ECB API.
        This is a placeholder implementation.
        """
        # TODO: Implement actual ECB API call
        # For now, return a mock value
        import random
        return round(random.uniform(0.5, 3.0), 3)
    
    def _fetch_historical_from_ecb(self, series_key: str, from_date: str, to_date: str) -> List[Dict]:
        """
        Fetch historical rates from ECB API.
        This is a placeholder implementation.
        """
        # TODO: Implement actual ECB API call
        # For now, return mock data
        import random
        from datetime import datetime, timedelta
        
        start_date = datetime.strptime(from_date, "%Y-%m-%d")
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        
        rates = []
        current_date = start_date
        
        while current_date <= end_date:
            rates.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "rate": round(random.uniform(0.5, 3.0), 3)
            })
            current_date += timedelta(days=1)
        
        return rates
    
    def _get_cached_value(self, cache_key: str):
        """Get value from cache if it exists."""
        if cache_key in self.cache:
            return self.cache[cache_key][1]
        return None

# Initialize the EURIBOR API instance
euribor_api = EuriborAPI()

def get_latest_euribor(tenor: str) -> Optional[float]:
    """Get the latest EURIBOR rate for a specific tenor."""
    return euribor_api.get_latest_rate(tenor)

def get_historical_euribor(tenor: str, from_date: str, to_date: str) -> List[Dict]:
    """Get historical EURIBOR rates for a specific tenor within a date range."""
    return euribor_api.get_historical_rates(tenor, from_date, to_date)