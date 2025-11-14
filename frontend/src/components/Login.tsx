import { useState } from 'react'
import axios from 'axios'
import './Login.css'

interface LoginProps {
  onLoginSuccess: (token: string) => void
}

const Login = ({ onLoginSuccess }: LoginProps) => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await axios.post('/api/auth/login', {
        email: email.trim(),
        password: password
      })

      if (response.data.success && response.data.token) {
        // Store token in localStorage
        localStorage.setItem('auth_token', response.data.token)
        onLoginSuccess(response.data.token)
      } else {
        setError('Login failed. Please check your credentials.')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo">
            <div className="logo-icon">
              <img 
                src="/alpha-data-logo.jpeg" 
                alt="Alpha Data Logo" 
                loading="eager"
                style={{ display: 'block' }}
              />
            </div>
          </div>
          <h1>AI Based Text to SQL</h1>
          <p>Sign in to access VikasAI Database</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && (
            <div className="login-error">
              <span className="error-icon">⚠️</span>
              <span>{error}</span>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
              autoComplete="email"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              autoComplete="current-password"
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="login-button"
            disabled={loading || !email || !password}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div className="login-footer">
          <p>© 2025 Alpha Data. All rights reserved.</p>
        </div>
      </div>
    </div>
  )
}

export default Login

