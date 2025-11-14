import { useState, useEffect } from 'react'
import axios from 'axios'
import './ConnectionStatus.css'

interface ConnectionStatusProps {
  className?: string
}

interface HealthStatus {
  status: string
  sqlserver_connected: boolean
  sqlserver_message: string
  postgres_connected: boolean
}

const ConnectionStatus = ({ className = '' }: ConnectionStatusProps) => {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [isChecking, setIsChecking] = useState(true)

  const checkHealth = async () => {
    try {
      const response = await axios.get<HealthStatus>('/api/health')
      setHealth(response.data)
    } catch (error) {
      setHealth({
        status: 'error',
        sqlserver_connected: false,
        sqlserver_message: 'Connection check failed',
        postgres_connected: false
      })
    } finally {
      setIsChecking(false)
    }
  }

  useEffect(() => {
    checkHealth()
    const interval = setInterval(checkHealth, 30000) // Check every 30 seconds
    return () => clearInterval(interval)
  }, [])

  if (isChecking) {
    return (
      <div className={`connection-status ${className}`}>
        <span className="status-indicator checking"></span>
        <span className="status-text">Checking connection...</span>
      </div>
    )
  }

  if (!health) {
    return null
  }

  const isConnected = health.sqlserver_connected

  return (
    <div className={`connection-status ${className} ${isConnected ? 'connected' : 'disconnected'}`}>
      <span className={`status-indicator ${isConnected ? 'online' : 'offline'}`}></span>
      <span className="status-text">
        {isConnected 
          ? 'Connected to VikasAI Database' 
          : 'Connection to VikasAI Database Lost'}
      </span>
      {!isConnected && health.sqlserver_message && (
        <span className="status-error">({health.sqlserver_message})</span>
      )}
    </div>
  )
}

export default ConnectionStatus

