import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const euriborService = {
  getLatestRate: async (tenor: string) => {
    try {
      const response = await api.get(`/api/euribor/latest?tenor=${tenor}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching EURIBOR rate:', error);
      throw error;
    }
  },

  getHistoricalRates: async (tenor: string, fromDate: string, toDate: string) => {
    try {
      const response = await api.get(`/api/euribor/history?tenor=${tenor}&from_date=${fromDate}&to_date=${toDate}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching historical EURIBOR rates:', error);
      throw error;
    }
  },
};

export const calculatorService = {
  calculateMortgage: async (data: any) => {
    try {
      const response = await api.post('/api/calc', data);
      return response.data;
    } catch (error) {
      console.error('Error calculating mortgage:', error);
      throw error;
    }
  },
};

export default api;