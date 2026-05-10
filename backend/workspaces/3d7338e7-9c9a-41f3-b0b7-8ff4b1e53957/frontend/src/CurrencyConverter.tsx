// src/components/CurrencyConverter.tsx
import React from 'react';
import { useCurrencyConversion } from './useCurrencyConversion';
import { CurrencyInput } from './CurrencyInput';
import { ResultDisplay } from './ResultDisplay';
import { CURRENCIES } from './currencyUtils';
import { ErrorBoundary } from './ErrorBoundary';

export const CurrencyConverter: React.FC = () => {
  const {
    state,
    handleAmountChange,
    handleCurrencyChange,
  } = useCurrencyConversion();

  return (
    <div className="currency-converter">
      <header>
        <h1>Currency Converter</h1>
        <p>Convert between EUR, USD, and MAD in real-time</p>
      </header>

      <main>
        <div className="converter-form">
          <CurrencyInput
            label="Amount"
            value={state.amount}
            currency={state.fromCurrency}
            onChange={handleAmountChange}
            onCurrencyChange={(currency) => handleCurrencyChange('fromCurrency', currency)}
            currencies={CURRENCIES}
            id="amount-input"
          />

          <div className="swap-button">
            <button
              onClick={() => {
                handleCurrencyChange('fromCurrency', state.toCurrency);
                handleCurrencyChange('toCurrency', state.fromCurrency);
              }}
              aria-label="Swap currencies"
            >
              ⇄
            </button>
          </div>

          <CurrencyInput
            label="Convert to"
            value={state.conversionResult?.convertedAmount || 0}
            currency={state.toCurrency}
            onChange={() => {}}
            onCurrencyChange={(currency) => handleCurrencyChange('toCurrency', currency)}
            currencies={CURRENCIES}
            id="convert-to-input"
          />
        </div>

        <ErrorBoundary fallback={<div>Something went wrong with the conversion</div>}>
          <ResultDisplay
            result={state.conversionResult}
            isLoading={state.isLoading}
            error={state.error}
          />
        </ErrorBoundary>
      </main>

      <footer>
        <p>Fixed rates for EUR, USD, and MAD</p>
        <p>Last updated: {new Date().toLocaleString()}</p>
      </footer>
    </div>
  );
};