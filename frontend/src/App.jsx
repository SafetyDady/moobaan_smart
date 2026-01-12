import { useState } from 'react'

function App() {
  const [healthStatus, setHealthStatus] = useState(null)
  const [loading, setLoading] = useState(false)

  // Use environment variable for API base URL with fallback
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

  const checkBackendHealth = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/health`)
      const data = await response.json()
      setHealthStatus(data)
    } catch (error) {
      setHealthStatus({ error: error.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ 
      padding: '2rem', 
      fontFamily: 'Arial, sans-serif',
      maxWidth: '600px',
      margin: '0 auto'
    }}>
      <h1>Moobaan Smart</h1>
      <p>Welcome to the Moobaan Smart application.</p>
      
      <div style={{ marginTop: '2rem' }}>
        <button 
          onClick={checkBackendHealth} 
          disabled={loading}
          style={{
            padding: '10px 20px',
            fontSize: '16px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Checking...' : 'Check Backend Health'}
        </button>
      </div>

      {healthStatus && (
        <div style={{
          marginTop: '1rem',
          padding: '1rem',
          backgroundColor: '#f8f9fa',
          border: '1px solid #dee2e6',
          borderRadius: '4px'
        }}>
          <h3>Backend Status:</h3>
          <pre style={{ margin: 0 }}>
            {JSON.stringify(healthStatus, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default App