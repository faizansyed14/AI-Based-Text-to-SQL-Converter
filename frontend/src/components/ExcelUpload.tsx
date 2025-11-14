import { useState, useRef } from 'react'
import axios from 'axios'
import './ExcelUpload.css'

interface ExcelTable {
  id: number
  table_name: string
  file_name: string
  columns: string[]
  row_count: number
  created_at: string
  updated_at: string
}

interface ExcelUploadProps {
  onUploadSuccess: () => void
}

const ExcelUpload = ({ onUploadSuccess }: ExcelUploadProps) => {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<string | null>(null)
  const [showGuide, setShowGuide] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const uploadFile = async (file: File) => {
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      setUploadStatus('Please upload a valid Excel file (.xlsx or .xls)')
      return
    }

    setIsUploading(true)
    setUploadStatus(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post('/api/upload-excel', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setUploadStatus(`Successfully uploaded! Table "${response.data.table_name}" created with ${response.data.row_count} rows.`)
      onUploadSuccess()
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error: any) {
      setUploadStatus(error.response?.data?.detail || 'Error uploading file. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    await uploadFile(file)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const file = e.dataTransfer.files?.[0]
    if (file) {
      await uploadFile(file)
    }
  }

  return (
    <div className="excel-upload-container">
      <div className="excel-upload-header">
        <h3>Upload Excel Sheet</h3>
        <button 
          className="guide-toggle"
          onClick={() => setShowGuide(!showGuide)}
        >
          {showGuide ? 'Hide' : 'Show'} Format Guide
        </button>
      </div>

      {showGuide && (
        <div className="format-guide">
          <h4>Excel Format Requirements:</h4>
          <div className="guide-content">
            <div className="guide-section">
              <strong>Column Names (First Row):</strong>
              <ul>
                <li>First row must contain column names</li>
                <li>Column names should be clear and descriptive</li>
                <li>Examples: "Customer Name", "Order Date", "Price", "Quantity"</li>
                <li>Special characters will be converted to underscores</li>
              </ul>
            </div>
            <div className="guide-section">
              <strong>Data Format:</strong>
              <ul>
                <li>Each row represents one record</li>
                <li>Keep data consistent in each column</li>
                <li>Dates should be in standard format (YYYY-MM-DD or Excel date format)</li>
                <li>Numbers can be integers or decimals</li>
                <li>Text can be any string</li>
              </ul>
            </div>
            <div className="guide-section">
              <strong>Example Format:</strong>
              <div className="example-table">
                <table>
                  <thead>
                    <tr>
                      <th>Customer Name</th>
                      <th>Order Date</th>
                      <th>Product</th>
                      <th>Price</th>
                      <th>Quantity</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>John Doe</td>
                      <td>2024-01-15</td>
                      <td>Laptop</td>
                      <td>999.99</td>
                      <td>1</td>
                    </tr>
                    <tr>
                      <td>Jane Smith</td>
                      <td>2024-01-16</td>
                      <td>Mouse</td>
                      <td>29.99</td>
                      <td>2</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div className="guide-section">
              <strong>Important Notes:</strong>
              <ul>
                <li>If you upload an Excel with the same column names as an existing table, data will be appended</li>
                <li>If column names are different, a new table will be created</li>
                <li>Table names are generated from the filename</li>
                <li>Maximum file size: 10MB (recommended)</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      <div 
        className={`upload-area ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls"
          onChange={handleFileUpload}
          disabled={isUploading}
          className="file-input"
          id="excel-file-input"
        />
        <div className="drag-drop-zone">
          <div className="drag-drop-icon">📄</div>
          <p className="drag-drop-text">
            {isDragging ? 'Drop your Excel file here' : 'Drag and drop your Excel file here'}
          </p>
          <p className="drag-drop-or">or</p>
          <label htmlFor="excel-file-input" className="upload-button">
            {isUploading ? 'Uploading...' : 'Choose Excel File'}
          </label>
        </div>
      </div>

      {uploadStatus && (
        <div className={`upload-status ${uploadStatus.includes('Successfully') ? 'success' : 'error'}`}>
          {uploadStatus}
        </div>
      )}
    </div>
  )
}

export default ExcelUpload

