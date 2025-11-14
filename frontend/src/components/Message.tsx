import { useState } from 'react'
import './Message.css'

interface MessageProps {
  message: {
    role: 'user' | 'assistant'
    content: string
    sqlQuery?: string
    data?: any[]
    formattedHtml?: string
    summary?: any
    error?: string
    timestamp: Date
    modelUsed?: string  // Track which model was used
  }
  onSuggestedQuestionClick?: (question: string) => void
  selectedTable?: string | null
  tableColumns?: string[]
}

const getSuggestedQuestions = (selectedTable: string | null, columns: string[] = []): string[] => {
  if (selectedTable && columns.length > 0) {
    // Generate questions based on table columns
    const columnNames = columns.join(', ')
    return [
      `Show me all data from ${selectedTable}`,
      `How many rows are in ${selectedTable}?`,
      `What are the unique values in ${columns[0] || 'the first column'}?`,
      `Show me the first 10 rows from ${selectedTable}`,
      `What is the total count of records?`,
      `List all distinct ${columns[0] || 'values'}`,
      `Show me data sorted by ${columns[0] || 'the first column'}`,
      `What are the top 5 records?`
    ]
  }
  
  // Default questions for VikasAI database
  return [
    'Show me all brands',
    'How many products are there?',
    'List products with their descriptions',
    'What are the top 10 products?',
    'Find all brands with SAS',
    'Count products by category',
    'Show stock transactions',
    'List all categories',
    'What products are in stock?',
    'Show products with their prices'
  ]
}

const Message = ({ message, onSuggestedQuestionClick, selectedTable, tableColumns }: MessageProps) => {
  const [showSql, setShowSql] = useState(false)
  const [copied, setCopied] = useState(false)
  const suggestedQuestions = getSuggestedQuestions(selectedTable || null, tableColumns || [])

  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="message message-user">
        <div className="message-avatar">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
        </div>
        <div className="message-content">
          <div className="message-text">{message.content}</div>
          <div className="message-time">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="message message-assistant">
      <div className="message-avatar">
        <img src="/alpha-data-logo.jpeg" alt="Alpha Data Logo" />
      </div>
      <div className="message-content">
        {/* Model indicator */}
        {message.modelUsed && (
          <div className="model-indicator">
            <span className="model-badge">
              {message.modelUsed === 'llama3.2:1b' ? '🟢 Ollama (Llama 3.2:1B)' : '🔵 OpenAI (GPT-4o-mini)'}
            </span>
          </div>
        )}
        {/* Show formatted HTML results if available, otherwise fallback to table */}
        {message.formattedHtml ? (
          <div className="formatted-results-container">
            <div 
              className="formatted-results" 
              dangerouslySetInnerHTML={{ __html: message.formattedHtml }}
            />
            {message.data && message.data.length > 0 && (
              <div className="results-footer">
                <div className="results-stats">
                  <span className="results-count">Total Rows: {message.data.length}</span>
                  <span className="results-count">Columns: {message.data[0] ? Object.keys(message.data[0]).length : 0}</span>
                </div>
              </div>
            )}
          </div>
        ) : message.data && message.data.length > 0 ? (
          <div className="data-results">
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    {Object.keys(message.data[0] || {}).map((key) => (
                      <th key={key}>{key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {message.data.map((row, idx) => (
                    <tr key={idx}>
                      {Object.values(row).map((value: any, colIdx) => (
                        <td key={colIdx}>
                          {value === null || value === undefined ? (
                            <span className="null-value">null</span>
                          ) : (
                            String(value)
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="results-footer">
              <div className="results-stats">
                <span className="results-count">Total Rows: {message.data.length}</span>
                <span className="results-count">Columns: {message.data[0] ? Object.keys(message.data[0]).length : 0}</span>
              </div>
            </div>
          </div>
        ) : null}

        {message.data && message.data.length === 0 && (
          <div className="no-results">
            <p>No results found</p>
          </div>
        )}

        {/* Show SQL query after results */}
        {message.sqlQuery && (
          <div className="sql-section">
            <div className="sql-header">
              <span className="sql-label">SQL Query</span>
              <div className="sql-header-buttons">
                <button
                  className={`copy-button ${copied ? 'copied' : ''}`}
                  onClick={async () => {
                    try {
                      await navigator.clipboard.writeText(message.sqlQuery!)
                      setCopied(true)
                      setTimeout(() => setCopied(false), 2000)
                    } catch (err) {
                      console.error('Failed to copy:', err)
                    }
                  }}
                  title="Copy SQL query"
                >
                  {copied ? 'Copied!' : 'Copy'}
                </button>
                <button
                  className="sql-toggle"
                  onClick={() => setShowSql(!showSql)}
                >
                  {showSql ? 'Hide' : 'Show'} Query
                </button>
              </div>
            </div>
            {showSql && (
              <div className="sql-query">
                <pre><code>{message.sqlQuery}</code></pre>
              </div>
            )}
          </div>
        )}

        {message.error && (
          <div className={`error-message ${message.error.toLowerCase().includes('read-only') ? 'read-only-error' : ''}`}>
            {message.error.toLowerCase().includes('read-only') ? (
              <>
                <div className="error-icon">🔒</div>
                <div className="error-content">
                  <strong>Read-Only Access</strong>
                  <p>{message.error}</p>
                  <div className="error-suggestion">
                    You can only query and view data using SELECT statements. Write operations (DELETE, UPDATE, INSERT, TRUNCATE, DROP, ALTER, CREATE) are not permitted.
                  </div>
                </div>
              </>
            ) : (
              <>
                <strong>Error:</strong> {message.error}
              </>
            )}
          </div>
        )}

        {/* Suggested Questions */}
        {!message.error && message.data !== undefined && (
          <div className="suggested-questions">
            <div className="suggested-questions-header">Suggested Questions:</div>
            <div className="suggested-questions-list">
              {suggestedQuestions.slice(0, 4).map((question, idx) => (
                <button
                  key={idx}
                  className="suggested-question-btn"
                  onClick={() => onSuggestedQuestionClick?.(question)}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="message-time">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  )
}

export default Message
