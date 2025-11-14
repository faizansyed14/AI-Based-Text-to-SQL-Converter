import { useState, useEffect } from 'react'
import axios from 'axios'
import './TableSelector.css'

interface ExcelTable {
  id: number
  table_name: string
  file_name: string
  columns: string[]
  row_count: number
  created_at: string
  updated_at: string
}

interface TableSelectorProps {
  onTableSelect: (tableName: string | null) => void
  refreshTrigger?: number
  onDeleteTable?: () => void
}

const TableSelector = ({ onTableSelect, refreshTrigger, onDeleteTable }: TableSelectorProps) => {
  const [tables, setTables] = useState<ExcelTable[]>([])
  const [selectedTable, setSelectedTable] = useState<string | null>(null)
  const [selectedTables, setSelectedTables] = useState<Set<string>>(new Set())
  const [isLoading, setIsLoading] = useState(false)
  const [isMultiSelect, setIsMultiSelect] = useState(false)

  useEffect(() => {
    loadTables()
    loadSelectedTable()
  }, [refreshTrigger])

  const loadTables = async () => {
    try {
      const response = await axios.get('/api/excel-tables')
      setTables(response.data)
    } catch (error) {
      console.error('Failed to load tables:', error)
    }
  }

  const loadSelectedTable = async () => {
    try {
      const response = await axios.get('/api/selected-table')
      if (response.data.selected_table) {
        setSelectedTable(response.data.selected_table)
        onTableSelect(response.data.selected_table)
      }
    } catch (error) {
      console.error('Failed to load selected table:', error)
    }
  }

  const handleTableSelect = async (tableName: string | null) => {
    if (isMultiSelect) {
      // Toggle selection in multi-select mode
      setSelectedTables(prev => {
        const newSet = new Set(prev)
        if (newSet.has(tableName || '')) {
          newSet.delete(tableName || '')
        } else if (tableName) {
          newSet.add(tableName)
        }
        return newSet
      })
    } else {
      // Single select mode
      setIsLoading(true)
      try {
        await axios.post('/api/select-table', { table_name: tableName })
        setSelectedTable(tableName)
        onTableSelect(tableName)
      } catch (error) {
        console.error('Failed to select table:', error)
      } finally {
        setIsLoading(false)
      }
    }
  }

  const handleDeleteTable = async (tableName: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!window.confirm(`Are you sure you want to delete table "${tableName}"?`)) {
      return
    }

    try {
      await axios.delete(`/api/excel-tables/${tableName}`)
      if (selectedTable === tableName) {
        setSelectedTable(null)
        onTableSelect(null)
      }
      if (selectedTables.has(tableName)) {
        setSelectedTables(prev => {
          const newSet = new Set(prev)
          newSet.delete(tableName)
          return newSet
        })
      }
      await loadTables()
      if (onDeleteTable) {
        onDeleteTable()
      }
    } catch (error) {
      console.error('Failed to delete table:', error)
      alert('Failed to delete table. Please try again.')
    }
  }

  const handleDeleteSelected = async () => {
    if (selectedTables.size === 0) return
    
    if (!window.confirm(`Are you sure you want to delete ${selectedTables.size} table(s)?`)) {
      return
    }

    try {
      for (const tableName of selectedTables) {
        await axios.delete(`/api/excel-tables/${tableName}`)
      }
      if (selectedTable && selectedTables.has(selectedTable)) {
        setSelectedTable(null)
        onTableSelect(null)
      }
      setSelectedTables(new Set())
      await loadTables()
      if (onDeleteTable) {
        onDeleteTable()
      }
    } catch (error) {
      console.error('Failed to delete tables:', error)
      alert('Failed to delete some tables. Please try again.')
    }
  }

  const refreshTables = () => {
    loadTables()
  }

  return (
    <div className="table-selector-container">
      <div className="table-selector-header">
        <h3>Select Table</h3>
        <div className="header-actions">
          <button 
            className={`multi-select-btn ${isMultiSelect ? 'active' : ''}`}
            onClick={() => {
              setIsMultiSelect(!isMultiSelect)
              if (!isMultiSelect) {
                setSelectedTables(new Set())
              }
            }}
            title="Multi-select mode"
          >
            ☑
          </button>
          {isMultiSelect && selectedTables.size > 0 && (
            <button 
              className="delete-selected-btn"
              onClick={handleDeleteSelected}
              title={`Delete ${selectedTables.size} selected`}
            >
              🗑️
            </button>
          )}
          <button className="refresh-button" onClick={refreshTables} title="Refresh">
            ↻
          </button>
        </div>
      </div>
      
      <div className="table-list">
        {!isMultiSelect && (
          <button
            className={`table-item ${selectedTable === null ? 'active' : ''}`}
            onClick={() => handleTableSelect(null)}
            disabled={isLoading}
          >
            <div className="table-item-content">
              <div className="table-name">All Tables (Default)</div>
              <div className="table-info">Query all database tables</div>
            </div>
          </button>
        )}

        {tables.length === 0 ? (
          <div className="no-tables">
            <p>No Excel tables uploaded yet</p>
            <span>Upload an Excel file to create a table</span>
          </div>
        ) : (
          tables.map((table) => (
            <div
              key={table.id}
              className={`table-item-wrapper ${isMultiSelect && selectedTables.has(table.table_name) ? 'selected' : ''} ${!isMultiSelect && selectedTable === table.table_name ? 'active' : ''}`}
            >
              <button
                className={`table-item ${!isMultiSelect && selectedTable === table.table_name ? 'active' : ''}`}
                onClick={() => handleTableSelect(table.table_name)}
                disabled={isLoading}
              >
                <div className="table-item-content">
                  {isMultiSelect && (
                    <input
                      type="checkbox"
                      checked={selectedTables.has(table.table_name)}
                      onChange={() => handleTableSelect(table.table_name)}
                      className="table-checkbox"
                    />
                  )}
                  <div className="table-info-main">
                    <div className="table-name">{table.table_name}</div>
                    <div className="table-info">
                      {table.row_count} rows • {table.columns.length} columns
                    </div>
                    <div className="table-columns">
                      Columns: {table.columns.slice(0, 3).join(', ')}
                      {table.columns.length > 3 && ` +${table.columns.length - 3} more`}
                    </div>
                  </div>
                </div>
              </button>
              <button
                className="delete-table-btn"
                onClick={(e) => handleDeleteTable(table.table_name, e)}
                title="Delete table"
              >
                🗑️
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default TableSelector

