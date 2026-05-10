// src/types/currency.types.ts
export const CURRENCIES: Currency[] = [
  { code: 'EUR', name: 'Euro', symbol: '€' },
  { code: 'USD', name: 'US Dollar', symbol: '$' },
  { code: 'MAD', name: 'Moroccan Dirham', symbol: 'MAD' },
];

export const DEFAULT_CURRENCIES = ['EUR', 'USD', 'MAD'];

export const formatCurrency = (amount: number, currencyCode: string): string => {
  const currency = CURRENCIES.find(c => c.code === currencyCode);
  const symbol = currency?.symbol || '';

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currencyCode,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};

export const getCurrencyName = (code: string): string => {
  return CURRENCIES.find(c => c.code === code)?.name || code;
};