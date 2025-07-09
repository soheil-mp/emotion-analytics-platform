import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import geminiSetup from './utils/geminiSetup';

// Make geminiSetup available globally for runtime configuration
window.geminiSetup = geminiSetup;

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
