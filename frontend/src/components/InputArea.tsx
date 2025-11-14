import { useState, KeyboardEvent } from 'react'
import './InputArea.css'

interface InputAreaProps {
  onSendMessage: (message: string) => void
  disabled: boolean
  showUpload?: boolean
  onUploadToggle?: (show: boolean) => void
}

const InputArea = ({ onSendMessage, disabled, showUpload = false, onUploadToggle }: InputAreaProps) => {
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSendMessage(input)
      setInput('')
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleUploadClick = () => {
    if (onUploadToggle) {
      onUploadToggle(!showUpload)
    }
  }

  return (
    <div className="input-area">
      <div className="input-container">
        <button
          onClick={handleUploadClick}
          className="upload-excel-btn"
          title="Upload Excel Sheet"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
          <span>Upload Excel</span>
        </button>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a question about your database..."
          rows={1}
          disabled={disabled}
          className="input-field"
        />
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className="send-button"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </div>
      <div className="input-hint">
        Press Enter to send, Shift+Enter for new line
      </div>
    </div>
  )
}

export default InputArea

