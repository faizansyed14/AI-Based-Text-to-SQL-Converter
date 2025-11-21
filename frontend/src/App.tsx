import { useState, useEffect } from 'react'
import axios from 'axios'
import ChatInterface from './components/ChatInterface'
import Login from './components/Login'
import Documentation from './components/Documentation'
import QueryExamples from './components/QueryExamples'
import './App.css'

function App() {
  const [isDarkMode, setIsDarkMode] = useState(true)
  const [showUpload, setShowUpload] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isCheckingAuth, setIsCheckingAuth] = useState(true)
  const [authToken, setAuthToken] = useState<string | null>(null)
  const [showDocumentation, setShowDocumentation] = useState(false)
  const [showQueryExamples, setShowQueryExamples] = useState(false)
  const [selectedModel, setSelectedModel] = useState<string>('gpt-4o-mini')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light')
  }, [isDarkMode])

  useEffect(() => {
    // Check if user is already authenticated
    const token = localStorage.getItem('auth_token')
    if (token) {
      verifyAuth(token)
    } else {
      setIsCheckingAuth(false)
    }
  }, [])

  const verifyAuth = async (token: string) => {
    try {
      const response = await axios.get('/api/auth/verify', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.data.authenticated) {
        setAuthToken(token)
        setIsAuthenticated(true)
        // Set token in axios defaults for all requests
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      } else {
        localStorage.removeItem('auth_token')
      }
    } catch (error) {
      localStorage.removeItem('auth_token')
    } finally {
      setIsCheckingAuth(false)
    }
  }

  const handleLoginSuccess = (token: string) => {
    setAuthToken(token)
    setIsAuthenticated(true)
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }

  const handleLogout = async () => {
    try {
      await axios.post('/api/auth/logout', {}, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      })
    } catch (error) {
      // Continue with logout even if API call fails
    }
    localStorage.removeItem('auth_token')
    setAuthToken(null)
    setIsAuthenticated(false)
    delete axios.defaults.headers.common['Authorization']
  }

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode)
  }

  if (isCheckingAuth) {
    return (
      <div className="app">
        <div className="loading-screen">
          <div className="loading-spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />
  }

  return (
    <div className="app">
      <div className="app-container">
        <header className="app-header">
          <div className="header-left">
            <div className="header-logo">
              <img src="/alpha-data-logo.jpeg" alt="Alpha Data Logo" />
            </div>
            <div>
              <h1>AI Based Text to SQL</h1>
              <p>Natural language to SQL query converter</p>
            </div>
          </div>
          <div className="header-controls">
            <button 
              className="privacy-button"
              onClick={() => setShowQueryExamples(true)}
              title="Query Examples & Tips"
            >
              💡 Query Examples
            </button>
            <button 
              className="privacy-button"
              onClick={() => setShowDocumentation(true)}
              title="Complete Documentation"
            >
              📚 Documentation
            </button>
            <div className="model-selector-container">
              <span className="model-label">Model:</span>
              <select 
                className="model-select"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                title="Select AI Model"
              >
                <option value="gpt-4o-mini">gpt-4o-mini - Fastest & Most Cost-Effective</option>
                <option value="gpt-4o">gpt-4o - Balanced Speed & Accuracy</option>
                <option value="gpt-4-turbo">gpt-4-turbo - High Accuracy</option>
                <option value="gpt-4">gpt-4 - Most Accurate (Slower)</option>
              </select>
            </div>
            <div className="theme-toggle-container">
              <button 
                className="theme-toggle"
                onClick={toggleTheme}
                title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {isDarkMode ? '🌙' : '☀️'}
              </button>
              <span className="theme-label">{isDarkMode ? 'Dark Mode' : 'Light Mode'}</span>
            </div>
            <button 
              className="logout-button"
              onClick={handleLogout}
              title="Logout"
            >
              Logout
            </button>
          </div>
        </header>
        <ChatInterface 
          showUpload={showUpload} 
          onUploadToggle={setShowUpload}
          selectedModel={selectedModel}
        />
        <Documentation isOpen={showDocumentation} onClose={() => setShowDocumentation(false)} />
        {showQueryExamples && (
          <div className="query-examples-overlay" onClick={() => {
            setShowQueryExamples(false)
            // Focus on chat input
            setTimeout(() => {
              const inputField = document.querySelector('.input-field') as HTMLTextAreaElement
              if (inputField) {
                inputField.focus()
              }
            }, 100)
          }}>
            <div className="query-examples-modal" onClick={(e) => e.stopPropagation()}>
              <div className="query-examples-header">
                <h2>💡 Query Examples & Tips</h2>
                <button 
                  className="query-examples-close" 
                  onClick={() => {
                    setShowQueryExamples(false)
                    // Focus on chat input
                    setTimeout(() => {
                      const inputField = document.querySelector('.input-field') as HTMLTextAreaElement
                      if (inputField) {
                        inputField.focus()
                      }
                    }, 100)
                  }}
                  title="Close and go to chat"
                >
                  ✕
                </button>
              </div>
              <div className="query-examples-content">
                <QueryExamples onQuestionClick={(question) => {
                  setShowQueryExamples(false)
                  const event = new CustomEvent('queryExampleSelected', { detail: question })
                  window.dispatchEvent(event)
                }} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
