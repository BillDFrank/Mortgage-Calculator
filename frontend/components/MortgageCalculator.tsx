'use client';

import React, { useState } from 'react';
import { euriborService, calculatorService } from '../services/api';

interface FormData {
  housePrice: string;
  downPayment: string;
  loanTerm: string;
  interestRate: string;
  monthlyPayment: string;
  bankSpread: string;
  loanType: string;
}

interface CalculationResult {
  calculated_field: string;
  calculated_value: number;
  total_borrowed: number;
  total_interest: number;
  total_cost: number;
  duration: number;
}

export default function MortgageCalculator() {
  const [formData, setFormData] = useState<FormData>({
    housePrice: '',
    downPayment: '',
    loanTerm: '',
    interestRate: '',
    monthlyPayment: '',
    bankSpread: '',
    loanType: 'fixed',
  });

  const [result, setResult] = useState<CalculationResult | null>(null);
  const [euriborRate, setEuriborRate] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Fetch EURIBOR rate if needed
      if (!euriborRate) {
        const euriborData = await euriborService.getLatestRate('3M');
        setEuriborRate(euriborData.rate);
      }
      
      // Prepare data for calculation
      const calcData = {
        house_price: parseFloat(formData.housePrice) || null,
        down_payment: parseFloat(formData.downPayment) || null,
        loan_term: parseFloat(formData.loanTerm) || null,
        interest_rate: parseFloat(formData.interestRate) || null,
        monthly_payment: parseFloat(formData.monthlyPayment) || null,
        bank_spread: parseFloat(formData.bankSpread) || 0,
        loan_type: formData.loanType,
      };
      
      // Perform calculation
      const calcResult = await calculatorService.calculateMortgage(calcData);
      setResult(calcResult);
    } catch (error) {
      console.error('Error calculating mortgage:', error);
      alert('Error calculating mortgage. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-center mb-8">Mortgage Calculator</h1>
      
      <form onSubmit={handleCalculate} className="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="housePrice">
              House Price (€)
            </label>
            <input
              id="housePrice"
              name="housePrice"
              type="number"
              value={formData.housePrice}
              onChange={handleInputChange}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              placeholder="e.g., 300000"
            />
          </div>
          
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="downPayment">
              Down Payment (€)
            </label>
            <input
              id="downPayment"
              name="downPayment"
              type="number"
              value={formData.downPayment}
              onChange={handleInputChange}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              placeholder="e.g., 60000"
            />
          </div>
          
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="loanTerm">
              Loan Term (years)
            </label>
            <input
              id="loanTerm"
              name="loanTerm"
              type="number"
              value={formData.loanTerm}
              onChange={handleInputChange}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              placeholder="e.g., 30"
            />
          </div>
          
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="interestRate">
              Interest Rate (%)
            </label>
            <input
              id="interestRate"
              name="interestRate"
              type="number"
              step="0.01"
              value={formData.interestRate}
              onChange={handleInputChange}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              placeholder="e.g., 2.5"
            />
          </div>
          
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="monthlyPayment">
              Monthly Payment (€)
            </label>
            <input
              id="monthlyPayment"
              name="monthlyPayment"
              type="number"
              value={formData.monthlyPayment}
              onChange={handleInputChange}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              placeholder="Leave blank to calculate"
            />
          </div>
          
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="bankSpread">
              Bank Spread (%)
            </label>
            <input
              id="bankSpread"
              name="bankSpread"
              type="number"
              step="0.01"
              value={formData.bankSpread}
              onChange={handleInputChange}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              placeholder="e.g., 0.5"
            />
          </div>
          
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="loanType">
              Loan Type
            </label>
            <select
              id="loanType"
              name="loanType"
              value={formData.loanType}
              onChange={handleInputChange}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            >
              <option value="fixed">Fixed Rate</option>
              <option value="adjustable">Adjustable Rate</option>
              <option value="full_variable">Full Variable Rate</option>
            </select>
          </div>
        </div>
        
        <div className="flex items-center justify-between mt-6">
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50"
          >
            {loading ? 'Calculating...' : 'Calculate'}
          </button>
        </div>
      </form>
      
      {result && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4">
          <h2 className="text-xl font-bold mb-2">Calculation Results</h2>
          <p><strong>Calculated Field:</strong> {result.calculated_field}</p>
          <p><strong>Calculated Value:</strong> {result.calculated_value.toFixed(2)}</p>
          <p><strong>Total Borrowed:</strong> €{result.total_borrowed?.toFixed(2)}</p>
          <p><strong>Total Interest:</strong> €{result.total_interest.toFixed(2)}</p>
          <p><strong>Total Cost:</strong> €{result.total_cost.toFixed(2)}</p>
          <p><strong>Duration:</strong> {result.duration} months</p>
        </div>
      )}
    </div>
  );
}