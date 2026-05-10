// src/hooks/useCurrencyConversion.ts
import { useState, useEffect, useCallback } from 'react';
import { ConversionParams, ConversionResult, CurrencyState } from './currency.types';
import { DEFAULT_CURRENCIES } from '../utils/currencyUtils';

export const useCurrencyConversion = () => {
  const [state, setState] = useState<CurrencyState>({
    currencies: [],
    isLoading: false,
    error: null,
    conversionResult: null,
    amount: 1,
    fromCurrency: DEFAULT_CURRENCIES[0],
    toCurrency: DEFAULT_CURRENCIES[1],
  });

  const fetchConversion = useCallback(async (params: ConversionParams) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      // In a real app, this would be an API call to /convert endpoint
      // For this example, we'll use fixed rates
      const rates = {
        EUR: { USD: 1.08, MAD: 10.5 },
        USD: { EUR: 0.93, MAD: 9.72 },
        MAD: { EUR: 0.095, USD: 0.103 },
      };

      if (!rates[params.from] || !rates[params.from][params.to]) {
        throw new Error('Conversion rate not available');
      }

      const rate = rates[params.from][params.to];
      const convertedAmount = params.amount * rate;

      setState(prev => ({
        ...prev,
        conversionResult: {
          amount: params.amount,
          fromCurrency: params.from,
          toCurrency: params.to,
          convertedAmount,
          rate,
          timestamp: new Date().toISOString(),
        },
        error: null,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
        conversionResult: null,
      }));
    } finally {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, []);

  const handleAmountChange = (amount: number) => {
    setState(prev => ({ ...prev, amount }));
    fetchConversion({
      amount,
      from: state.fromCurrency,
      to: state.toCurrency,
    });
  };

  const handleCurrencyChange = (field: 'fromCurrency' | 'toCurrency', value: string) => {
    setState(prev => {
      const newState = { ...prev, [field]: value };

      // If we're changing the fromCurrency, ensure it's different from toCurrency
      if (field === 'fromCurrency' && value === prev.toCurrency) {
        newState.toCurrency = prev.fromCurrency;
      }

      fetchConversion({
        amount: prev.amount,
        from: newState.fromCurrency,
        to: newState.toCurrency,
      });

      return newState;
    });
  };

  return {
    state,
    handleAmountChange,
    handleCurrencyChange,
    fetchConversion,
  };
};