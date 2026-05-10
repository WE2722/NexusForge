// src/components/ResultDisplay.tsx
import React from 'react';
import { ConversionResult } from './currency.types';
import { formatCurrency, getCurrencyName } from '../utils/currencyUtils';

export interface ResultDisplayProps {
  result: ConversionResult;
  isLoading: boolean;
  error: string | null;
}

export const ResultDisplay: React.FC<ResultDisplayProps> = ({
  result,
  isLoading,
  error,
}) => {
  if (isLoading) {
    return (
      <div className="result-display loading">
        <div className="spinner" aria-hidden="true"></div>
        <p>Converting...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="result-display error" role="alert">
        <span aria-hidden="true">⚠️</span>
        <p>{error}</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="result-display empty">
        <p>Enter amounts to see conversion results</p>
      </div>
    );
  }

  return (
    <div className="result-display">
      <h3>Conversion Result</h3>
      <div className="result-details">
        <p>
          <strong>{result.amount} {getCurrencyName(result.fromCurrency)}</strong>
        </p>
        <p>→</p>
        <p>
          <strong>{formatCurrency(result.convertedAmount, result.toCurrency)}</strong>
        </p>
      </div>
      <div className="conversion-rate">
        <p>1 {result.fromCurrency} = {result.rate.toFixed(4)} {result.toCurrency}</p>
        <p className="timestamp">Last updated: {new Date(result.timestamp).toLocaleTimeString()}</p>
      </div>
    </div>
  );
};