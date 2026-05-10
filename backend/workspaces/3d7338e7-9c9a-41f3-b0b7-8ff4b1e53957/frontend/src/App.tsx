// src/App.tsx
import React from 'react';
import { CurrencyConverter } from './CurrencyConverter';
import './global.css';

const App: React.FC = () => {
  return (
    <div className="app">
      <CurrencyConverter />
    </div>
  );
};

export default App;