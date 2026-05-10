// src/components/CurrencySelect.tsx
import React from 'react';

export interface CurrencySelectProps {
  value: string;
  onChange: (value: string) => void;
  currencies: Array<{ code: string; name: string }>;
  label: string;
  id: string;
}

export const CurrencySelect: React.FC<CurrencySelectProps> = ({
  value,
  onChange,
  currencies,
  label,
  id,
}) => {
  return (
    <div className="currency-select">
      <label htmlFor={id}>{label}</label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label={label}
      >
        {currencies.map((currency) => (
          <option key={currency.code} value={currency.code}>
            {currency.code} - {currency.name}
          </option>
        ))}
      </select>
    </div>
  );
};