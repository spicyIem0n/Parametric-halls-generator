import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'

// Wstawienie aplikacji React w element <div id="root"> w pliku index.html
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)