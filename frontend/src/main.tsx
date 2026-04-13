import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { TabLabelsProvider } from './contexts/TabLabelsContext'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <TabLabelsProvider>
        <App />
      </TabLabelsProvider>
    </BrowserRouter>
  </StrictMode>,
)
