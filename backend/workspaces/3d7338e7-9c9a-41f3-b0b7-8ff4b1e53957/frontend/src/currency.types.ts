// src/types/currency.types.ts
export interface Currency {
  code: string;
  name: string;
  symbol: string;
}

export interface ConversionResult {
  amount: number;
  fromCurrency: string;
  toCurrency: string;
  convertedAmount: number;
  rate: number;
  timestamp: string;
}

export interface ConversionParams {
  amount: number;
  from: string;
  to: string;
}

export interface CurrencyState {
  currencies: Currency[];
  isLoading: boolean;
  error: string | null;
  conversionResult: ConversionResult | null;
  amount: number;
  fromCurrency: string;
  toCurrency: string;
}