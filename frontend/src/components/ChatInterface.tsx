import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import Message from './Message'
import InputArea from './InputArea'
import HistorySidebar from './HistorySidebar'
import ExcelUpload from './ExcelUpload'
import TableSelector from './TableSelector'
import ConnectionStatus from './ConnectionStatus'
import './ChatInterface.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sqlQuery?: string
  data?: any[]
  formattedHtml?: string  // HTML formatted results
  summary?: any  // Analysis summary
  error?: string
  timestamp: Date
  modelUsed?: string  // Track which model was used
  hasMoreRecords?: boolean  // Indicates if there are more records
  totalCount?: number  // Total number of records
          showVisualization?: boolean  // Whether to show chart
          chartConfig?: any  // Chart configuration
          availableColumns?: string[]  // Available columns for visualization
        }

interface ChatSession {
  id: number
  title: string | null
  created_at: string
  updated_at: string
}

interface ChatInterfaceProps {
  showUpload: boolean
  onUploadToggle: (show: boolean) => void
  selectedModel: string
}

const ChatInterface = ({ showUpload, onUploadToggle, selectedModel }: ChatInterfaceProps) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [selectedTable, setSelectedTable] = useState<string | null>(null)
  const [selectedTableColumns, setSelectedTableColumns] = useState<string[]>([])
  const [isTableSelectorCollapsed, setIsTableSelectorCollapsed] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    const handleQueryExample = (event: CustomEvent) => {
      const question = event.detail
      if (question && !isLoading) {
        sendMessage(question)
      }
    }
    window.addEventListener('queryExampleSelected', handleQueryExample as EventListener)
    return () => window.removeEventListener('queryExampleSelected', handleQueryExample as EventListener)
  }, [isLoading])

  // Load chat sessions on mount
  useEffect(() => {
    loadSessions()
    loadSelectedTable()
  }, [])

  const loadSelectedTable = async () => {
    try {
      const response = await axios.get('/api/selected-table')
      if (response.data.selected_table) {
        setSelectedTable(response.data.selected_table)
        // Load table columns
        const schemaResponse = await axios.get(`/api/excel-tables/${response.data.selected_table}/schema`)
        setSelectedTableColumns(schemaResponse.data.columns.map((col: any) => col.name))
      }
    } catch (error) {
      console.error('Failed to load selected table:', error)
    }
  }

  const loadSessions = async () => {
    try {
      const response = await axios.get('/api/sessions')
      setSessions(response.data)
    } catch (error) {
      console.error('Failed to load sessions:', error)
    }
  }

  const loadSessionMessages = async (sessionId: number) => {
    try {
      const response = await axios.get(`/api/sessions/${sessionId}/messages`)
      console.log('Loaded messages response:', response.data)
      
      if (!response.data || response.data.length === 0) {
        setMessages([])
        return
      }
      
      const loadedMessages: Message[] = response.data.map((msg: any) => {
        // Handle data field - it might be an array or already parsed
        let messageData = undefined
        if (msg.data) {
          if (Array.isArray(msg.data)) {
            messageData = msg.data
          } else if (typeof msg.data === 'object') {
            // If it's an object, wrap it in an array
            messageData = [msg.data]
          } else {
            // Try to parse if it's a string
            try {
              const parsed = JSON.parse(msg.data)
              messageData = Array.isArray(parsed) ? parsed : [parsed]
            } catch {
              messageData = [msg.data]
            }
          }
        }
        
        return {
          role: msg.role as 'user' | 'assistant',
          content: msg.content,
          sqlQuery: msg.sql_query || msg.sqlQuery,
          data: messageData,
          error: msg.error,
          timestamp: new Date(msg.timestamp),
          modelUsed: msg.model_used || msg.modelUsed,
          hasMoreRecords: msg.has_more_records || msg.hasMoreRecords,
          totalCount: msg.total_count || msg.totalCount,
          showVisualization: msg.show_visualization || msg.showVisualization,
          chartConfig: msg.chart_config || msg.chartConfig,
          availableColumns: msg.available_columns || msg.availableColumns,
        }
      })
      
      console.log('Parsed messages:', loadedMessages)
      setMessages(loadedMessages)
    } catch (error) {
      console.error('Failed to load session messages:', error)
      setMessages([])
    }
  }

  const handleVisualize = async (xAxisColumn: string, yAxisColumn: string, sessionId?: number) => {
    if (!xAxisColumn || !yAxisColumn) return
    
    const targetSessionId = sessionId || currentSessionId
    if (!targetSessionId) {
      console.error('No session ID available for visualization')
      return
    }
    
    setIsLoading(true)
    
    try {
      const response = await axios.post('/api/visualize', {
        session_id: targetSessionId,
        x_axis_column: xAxisColumn,
        y_axis_column: yAxisColumn,
        chart_type: 'trend'
      })
      
      const visualizationMessage: Message = {
        role: 'assistant',
        content: response.data.message,
        sqlQuery: response.data.sql_query,
        data: response.data.data,
        formattedHtml: response.data.formatted_html,
        summary: response.data.summary,
        error: response.data.error,
        timestamp: new Date(),
        modelUsed: response.data.model_name,
        hasMoreRecords: response.data.has_more_records || false,
        totalCount: response.data.total_count || undefined,
        showVisualization: response.data.show_visualization,
        chartConfig: response.data.chart_config,
        availableColumns: response.data.available_columns,
      }
      
      setMessages((prev: Message[]) => [...prev, visualizationMessage])
      await loadSessions()
    } catch (error: any) {
      console.error('Visualization error:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error creating visualization: ${error.response?.data?.detail || error.message}`,
        error: error.response?.data?.detail || error.message,
        timestamp: new Date(),
      }
      setMessages((prev: Message[]) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleShowAllRecords = async (sqlQuery: string) => {
    if (!sqlQuery || isLoading) return

    // Remove TOP clause from SQL to get all records
    const allRecordsQuery = sqlQuery.replace(/\bTOP\s+\d+\b/gi, '').trim()
    
    // Send a message to execute the query without limit
    const userMessage: Message = {
      role: 'user',
      content: `Show all records`,
      timestamp: new Date(),
    }

    setMessages((prev: Message[]) => [...prev, userMessage])
    setIsLoading(true)

    try {
      const conversationHistory = messages.map((msg: Message) => ({
        role: msg.role,
        content: msg.content,
      }))

      // Execute the SQL query directly by asking to show all
      const response = await axios.post('/api/chat', {
        message: `Execute this query and show all results: ${allRecordsQuery}`,
        conversation_history: conversationHistory,
        session_id: currentSessionId,
        model: selectedModel,
      })

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.message,
        sqlQuery: response.data.sql_query,
        data: response.data.data,
        formattedHtml: response.data.formatted_html,
        summary: response.data.summary,
        error: response.data.error,
        timestamp: new Date(),
        modelUsed: response.data.model_name,
        hasMoreRecords: response.data.has_more_records || false,
        totalCount: response.data.total_count || undefined,
        showVisualization: response.data.show_visualization,
        chartConfig: response.data.chart_config,
        availableColumns: response.data.available_columns,
      }

      setMessages((prev: Message[]) => [...prev, assistantMessage])
      await loadSessions()
    } catch (error: any) {
      const errorMessage: Message = {
        role: 'assistant',
        content: error.response?.data?.detail || 'Sorry, something went wrong while loading all records.',
        error: error.message,
        timestamp: new Date(),
      }
      setMessages((prev: Message[]) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const createNewChat = async () => {
    try {
      const response = await axios.post('/api/sessions')
      const newSession = response.data
      setCurrentSessionId(newSession.id)
      setMessages([])
      await loadSessions()
    } catch (error) {
      console.error('Failed to create new chat:', error)
    }
  }

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return

    // Auto-create session if none exists
    let sessionId = currentSessionId
    if (!sessionId) {
      // Will be created by backend, but we need to track it
      sessionId = null
    }

    const userMessage: Message = {
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    }

    setMessages((prev: Message[]) => [...prev, userMessage])
    setIsLoading(true)

    try {
      const conversationHistory = messages.map((msg: Message) => ({
        role: msg.role,
        content: msg.content,
      }))

      const response = await axios.post('/api/chat', {
        message: content.trim(),
        conversation_history: conversationHistory,
        session_id: sessionId,
        model: selectedModel,
      })

      // Update current session ID if it was created
      if (response.data.session_id && !currentSessionId) {
        setCurrentSessionId(response.data.session_id)
      }

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.message,
        sqlQuery: response.data.sql_query,
        data: response.data.data,
        formattedHtml: response.data.formatted_html,
        summary: response.data.summary,
        error: response.data.error,
        timestamp: new Date(),
        modelUsed: response.data.model_name,  // Include model used
        hasMoreRecords: response.data.has_more_records || false,
        totalCount: response.data.total_count || undefined,
        showVisualization: response.data.show_visualization || false,
        chartConfig: response.data.chart_config || undefined,
      }
      

      setMessages((prev: Message[]) => [...prev, assistantMessage])
      
      // Reload sessions to update the list
      await loadSessions()
    } catch (error: any) {
      console.error('Error sending message:', error)
      
      // Check if it's an authentication error
      if (error.response?.status === 401) {
        // Don't show error message, let App.tsx handle auth redirect
        // Just clear loading state
        setIsLoading(false)
        return
      }
      
      // For other errors, show error message
      const errorMessage: Message = {
        role: 'assistant',
        content: error.response?.data?.detail || error.message || 'Sorry, something went wrong. Please try again.',
        error: error.message,
        timestamp: new Date(),
      }
      setMessages((prev: Message[]) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSelectSession = async (sessionId: number) => {
    console.log('Selecting session:', sessionId)
    setCurrentSessionId(sessionId)
    setMessages([]) // Clear messages first
    await loadSessionMessages(sessionId)
  }


  const handleDeleteSession = async (sessionId: number) => {
    try {
      await axios.delete(`/api/sessions/${sessionId}`)
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null)
        setMessages([])
      }
      await loadSessions()
    } catch (error) {
      console.error('Failed to delete session:', error)
    }
  }

  const [uploadRefresh, setUploadRefresh] = useState(0)

  const handleUploadSuccess = () => {
    // Refresh table selector after upload
    onUploadToggle(false)
    setUploadRefresh((prev: number) => prev + 1)
    // Reload sessions to refresh table list
    loadSessions()
  }

  const handleTableSelect = async (tableName: string | null) => {
    setSelectedTable(tableName)
    try {
      await axios.post('/api/select-table', { table_name: tableName })
      
      // Load table columns if table is selected
      if (tableName) {
        try {
          const response = await axios.get(`/api/excel-tables/${tableName}/schema`)
          setSelectedTableColumns(response.data.columns.map((col: any) => col.name))
        } catch (error) {
          console.error('Failed to load table schema:', error)
          setSelectedTableColumns([])
        }
      } else {
        setSelectedTableColumns([])
      }
    } catch (error) {
      console.error('Failed to select table:', error)
    }
  }

  return (
    <div className="chat-interface">
      <HistorySidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={createNewChat}
        onDeleteSession={handleDeleteSession}
      />
      <div className="chat-main">
        <div className="connection-status-container">
          <ConnectionStatus />
        </div>
        <div className="chat-messages-container">
          <div className="chat-messages" ref={chatContainerRef}>
            {messages.length === 0 && (
                <div className="welcome-message">
                <h2>Welcome to Alpha Data's AI Based SQL Query Generator</h2>
                <p>Ask questions about your VikasAI database in natural language</p>
                <div className="example-questions">
                  <p className="examples-title">Example queries:</p>
                  <ul>
                    <li onClick={() => sendMessage('Show me all brands')}>Show me all brands</li>
                    <li onClick={() => sendMessage('How many products are there?')}>How many products are there?</li>
                    <li onClick={() => sendMessage('List products with their categories')}>List products with their categories</li>
                    <li onClick={() => sendMessage('What are the top 10 products by price?')}>What are the top 10 products by price?</li>
                    <li onClick={() => sendMessage('Find all brands with SAS')}>Find all brands with SAS</li>
                    <li onClick={() => sendMessage('Count products by brand')}>Count products by brand</li>
                    <li onClick={() => sendMessage('Show stock transactions')}>Show stock transactions</li>
                    <li onClick={() => sendMessage('List all categories')}>List all categories</li>
                  </ul>
                </div>
              </div>
            )}
            {messages.map((message, index) => (
              <Message 
                key={index} 
                message={message} 
                onSuggestedQuestionClick={sendMessage}
                selectedTable={selectedTable}
                tableColumns={selectedTableColumns}
                onShowAllRecords={handleShowAllRecords}
                onVisualize={handleVisualize}
                sessionId={currentSessionId || undefined}
              />
            ))}
            {isLoading && (
              <div className="loading-message">
                <div className="ai-thinking">
                  <div className="ai-thinking-icon">
                    <img src="/alpha-data-logo.jpeg" alt="Alpha Data Logo" />
                  </div>
                  <div className="ai-thinking-text">AI is thinking...</div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
        <InputArea 
          onSendMessage={sendMessage} 
          disabled={isLoading}
          showUpload={showUpload}
          onUploadToggle={onUploadToggle}
        />
      </div>
      {showUpload && (
        <div className="right-panel upload-panel">
          <div className="panel-header">
            <h3>Upload Excel Sheet</h3>
            <button 
              className="panel-close-btn"
              onClick={() => onUploadToggle(false)}
              title="Close"
            >
              ×
            </button>
          </div>
          <div className="panel-content">
            <ExcelUpload onUploadSuccess={handleUploadSuccess} />
          </div>
        </div>
      )}
      <div className={`right-panel table-selector-panel ${isTableSelectorCollapsed ? 'collapsed' : ''}`}>
        <button 
          className="panel-toggle-btn"
          onClick={() => setIsTableSelectorCollapsed(!isTableSelectorCollapsed)}
          title={isTableSelectorCollapsed ? 'Expand Tables Panel' : 'Collapse Tables Panel'}
          aria-label={isTableSelectorCollapsed ? 'Expand Tables Panel' : 'Collapse Tables Panel'}
        >
          <span>{isTableSelectorCollapsed ? '▶' : '◀'}</span>
        </button>
        {!isTableSelectorCollapsed && (
          <>
            <div className="panel-header">
              <h3>Select Table</h3>
            </div>
            <div className="panel-content">
              <TableSelector 
                onTableSelect={handleTableSelect} 
                refreshTrigger={uploadRefresh}
                onDeleteTable={handleUploadSuccess}
              />
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default ChatInterface
