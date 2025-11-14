import { useState } from 'react'
import './HistorySidebar.css'

interface ChatSession {
  id: number
  title: string | null
  created_at: string
  updated_at: string
}

interface HistorySidebarProps {
  sessions: ChatSession[]
  currentSessionId: number | null
  onSelectSession: (sessionId: number) => void
  onNewChat: () => void
  onDeleteSession: (sessionId: number) => void
}

const HistorySidebar = ({ 
  sessions, 
  currentSessionId, 
  onSelectSession, 
  onNewChat,
  onDeleteSession 
}: HistorySidebarProps) => {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays === 1) {
      return 'Today'
    } else if (diffDays === 2) {
      return 'Yesterday'
    } else if (diffDays <= 7) {
      return `${diffDays - 1} days ago`
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
    }
  }

  const handleDelete = (e: React.MouseEvent, sessionId: number) => {
    e.stopPropagation()
    if (window.confirm('Are you sure you want to delete this chat?')) {
      onDeleteSession(sessionId)
    }
  }

  return (
    <div className="sidebar-wrapper">
      <div className={`history-sidebar ${isCollapsed ? 'collapsed' : ''}`}>
        <div className="history-header">
          {!isCollapsed && (
            <button className="new-chat-button" onClick={onNewChat} title="New Chat">
              + New Chat
            </button>
          )}
        </div>
        {!isCollapsed && (
          <div className="history-list">
            {sessions.length === 0 ? (
              <div className="history-empty">
                <p>No chats yet</p>
                <span>Start a new conversation to begin</span>
              </div>
            ) : (
              sessions.map((session) => (
                <div
                  key={session.id}
                  className={`history-item ${currentSessionId === session.id ? 'active' : ''}`}
                  onClick={() => onSelectSession(session.id)}
                >
                  <div className="history-item-content">
                    <div className="history-title">{session.title || 'New Chat'}</div>
                    <div className="history-time">{formatDate(session.updated_at)}</div>
                  </div>
                  <button
                    className="delete-button"
                    onClick={(e) => handleDelete(e, session.id)}
                    title="Delete chat"
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
        )}
      </div>
      <button 
        className="sidebar-toggle"
        onClick={() => setIsCollapsed(!isCollapsed)}
        title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {isCollapsed ? '>' : '<'}
      </button>
    </div>
  )
}

export default HistorySidebar

