import { Navigate, Route, Routes } from 'react-router-dom'
import { DigestPage } from './pages/DigestPage'
import { HomePage } from './pages/HomePage'
import './App.css'

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/digest" element={<DigestPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
