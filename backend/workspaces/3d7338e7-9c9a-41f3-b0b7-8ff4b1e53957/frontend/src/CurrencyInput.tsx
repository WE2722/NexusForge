// src/components/CurrencyInput.tsx
import React from 'react';
import { formatCurrency } from './currencyUtils';

export interface CurrencyInputProps {
  label: string;
  value: number;
  currency: string;
  onChange: (value: number) => void;
  onCurrencyChange: (currency: string) => void;
  currencies: Array<{ code: string; name: string }>;
  id: string;
}

export const CurrencyInput: React.FC<CurrencyInputProps> = ({
  label,
  value,
  currency,
  onChange,
  onCurrencyChange,
  currencies,
  id,
}) => {
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value) || 0;
    onChange(value);
  };

  return (
    <div className="currency-input">
      <label htmlFor={id}>{label}</label>
      <div className="input-group">
        <input
          id={id}
          type="number"
          min="0"
          step="0.01"
          value={value}
          onChange={handleInputChange}
          aria-label={`${label} amount`}
          className="amount-input"
        />
        <select
          value={currency}
          onChange={(e) => onCurrencyChange(e.target.value)}
          aria-label={`Select ${label} currency`}
        >
          {currencies.map((curr) => (
            <option key={curr.code} value={curr.code}>
              {curr.code} - {curr.name}
            </option>
          ))}
        </select>
      </div>
      <div className="formatted-amount">
        {formatCurrency(value, currency)}
      </div>
    </div>
  );
};