import { useState } from 'react'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts'
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
    hasMoreRecords?: boolean  // Indicates if there are more records
    totalCount?: number  // Total number of records
    showVisualization?: boolean  // Whether to show chart
    chartConfig?: any  // Chart configuration
    availableColumns?: string[]  // Available columns for visualization
  }
  onSuggestedQuestionClick?: (question: string) => void
  selectedTable?: string | null
  tableColumns?: string[]
  onShowAllRecords?: (sqlQuery: string) => void  // Callback to request all records
  onVisualize?: (xAxisColumn: string, yAxisColumn: string, sessionId?: number) => void  // Callback to create visualization
  sessionId?: number  // Current session ID
}

const Message = ({ message, onSuggestedQuestionClick, selectedTable, tableColumns, onShowAllRecords, onVisualize, sessionId }: MessageProps) => {
  const [showSql, setShowSql] = useState(false)
  const [copied, setCopied] = useState(false)
  const [isChartExpanded, setIsChartExpanded] = useState(false)
  const [showVisualizationSelector, setShowVisualizationSelector] = useState(false)
  const [selectedXAxis, setSelectedXAxis] = useState<string>('')
  const [selectedYAxis, setSelectedYAxis] = useState<string>('')
  
  const isUser = message.role === 'user'
  
  // Check if this is an analysis message
  const isAnalysisMessage = message.content && message.content.includes('📊 **Data Analysis:**')
  const analysisText = isAnalysisMessage 
    ? message.content.replace('📊 **Data Analysis:**\n\n', '').replace(/\*\*/g, '')
    : null

  // Chart rendering function with improved accuracy
  const renderChart = (chartConfig: any, data: any[]) => {
    if (!chartConfig || !data || data.length === 0) return null

    const chartType = chartConfig.type
    const numericColumns = chartConfig.numericColumns || []
    const categoryColumns = chartConfig.categoryColumns || []
    const dateColumn = chartConfig.dateColumn
    const xAxisColumn = chartConfig.xAxisColumn  // User-specified X-axis column
    const yAxisColumn = chartConfig.yAxisColumn  // User-specified Y-axis column

    // Use user-specified columns if provided, otherwise infer them
    let valueColumn = yAxisColumn  // Y-axis is the value column
    let nameColumn = xAxisColumn    // X-axis is the name/label column

    // If Y-axis not specified, find the best value column
    if (!valueColumn) {
      valueColumn = numericColumns.find((col: string) => {
        const colLower = col.toLowerCase()
        return colLower.includes('landed_cost') || colLower.includes('landed cost') || 
               colLower.includes('selling_price') || colLower.includes('selling price') ||
               colLower.includes('fob_price') || colLower.includes('fob price') ||
               colLower.includes('cost') || colLower.includes('price')
      }) || numericColumns.find((col: string) => {
        const colLower = col.toLowerCase()
        return colLower.includes('qty') || colLower.includes('quantity') || colLower.includes('stock') || 
               colLower.includes('value') || colLower.includes('amount') || colLower.includes('total')
      }) || numericColumns[0] || Object.keys(data[0]).find(key => {
        const val = data[0][key]
        return val !== null && !isNaN(Number(val))
      })
    }

    // If X-axis not specified, find the best name/label column
    if (!nameColumn) {
      nameColumn = categoryColumns.find((col: string) => {
        const colLower = col.toLowerCase()
        return colLower.includes('desc') || colLower.includes('name') || colLower.includes('product')
      }) || categoryColumns[0] || (dateColumn ? dateColumn : Object.keys(data[0]).find(key => key !== valueColumn) || Object.keys(data[0])[0])
    }

    // Detect if value column is a price/cost column for currency formatting
    const isPriceColumn = valueColumn && (
      valueColumn.toLowerCase().includes('price') || 
      valueColumn.toLowerCase().includes('cost') || 
      valueColumn.toLowerCase().includes('amount') ||
      valueColumn.toLowerCase().includes('value') ||
      valueColumn.toLowerCase().includes('fob') ||
      valueColumn.toLowerCase().includes('selling')
    )

    // Format column names for display
    const formatColumnName = (col: string) => {
      return col.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    }

    // Get a descriptive chart title
    const getChartTitle = () => {
      if (valueColumn && nameColumn) {
        const valueLabel = formatColumnName(valueColumn)
        const nameLabel = formatColumnName(nameColumn)
        if (chartType === 'trend' || chartType === 'line') {
          return `${valueLabel} by ${nameLabel}`
        } else if (chartType === 'bar') {
          return `Top Items: ${valueLabel}`
        } else if (chartType === 'pie') {
          return `Distribution: ${valueLabel}`
        }
      }
      return chartType === 'trend' || chartType === 'line' ? '📈 Trends' : 
             chartType === 'bar' ? '📊 Bar Chart' : 
             chartType === 'pie' ? '🥧 Distribution' : '📊 Chart'
    }

    // Prepare chart data - sort by value for better visualization
    const chartData = data.map(row => {
      const item: any = {}
      const nameVal = row[nameColumn]
      item.name = nameVal ? String(nameVal).substring(0, 30) : 'N/A' // Truncate long names
      
      if (valueColumn) {
        const val = row[valueColumn]
        if (val !== null && val !== undefined) {
          const numVal = typeof val === 'number' ? val : parseFloat(String(val).replace(/[^0-9.-]/g, ''))
          item.value = isNaN(numVal) ? 0 : numVal
        } else {
          item.value = 0
        }
      } else {
        item.value = 0
      }
      return item
    }).filter(item => !isNaN(item.value) && item.value !== null)

    // Sort by value descending for bar charts, by name for trend charts
    if (chartType === 'bar') {
      chartData.sort((a, b) => b.value - a.value)
    } else if (chartType === 'trend' || chartType === 'line') {
      // For trend charts, keep original order or sort by name for consistency
      chartData.sort((a, b) => a.name.localeCompare(b.name))
    }

    if (chartData.length === 0) return null

    // Color palette
    const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#ff7300']

    const chartHeight = isChartExpanded ? 600 : 500
    
    // Format value for display (currency or number)
    const formatValue = (value: any) => {
      if (isPriceColumn) {
        return new Intl.NumberFormat('en-AE', {
          style: 'currency',
          currency: 'AED',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0
        }).format(value)
      }
      return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
      }).format(value)
    }

    // Format Y-axis ticks
    const formatYAxisTick = (value: any) => {
      if (isPriceColumn) {
        if (value >= 1000000) return `AED ${(value / 1000000).toFixed(1)}M`
        if (value >= 1000) return `AED ${(value / 1000).toFixed(0)}K`
        return `AED ${value.toFixed(0)}`
      }
      if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`
      if (value >= 1000) return `${(value / 1000).toFixed(0)}K`
      return value.toFixed(0)
    }

    const chartContent = (
      <>
        {chartType === 'trend' || chartType === 'line' ? (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <AreaChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis 
                dataKey="name" 
                angle={-45}
                textAnchor="end"
                height={100}
                interval="preserveStartEnd"
                label={{ value: formatColumnName(nameColumn || 'Category'), position: 'insideBottom', offset: -10, style: { textAnchor: 'middle', fill: '#666', fontSize: '12px' } }}
                tick={{ fontSize: 11 }}
              />
              <YAxis 
                label={{ value: formatColumnName(valueColumn || 'Value'), angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#666', fontSize: '12px' } }}
                tickFormatter={formatYAxisTick}
                tick={{ fontSize: 11 }}
              />
              <Tooltip 
                formatter={(value: any) => formatValue(value)}
                labelFormatter={(label) => `${formatColumnName(nameColumn || 'Item')}: ${label}`}
                contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', border: '1px solid #ccc', borderRadius: '4px' }}
              />
              <Legend 
                formatter={() => formatColumnName(valueColumn || 'Value')}
                wrapperStyle={{ paddingTop: '10px' }}
              />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke="#0088FE" 
                fill="#0088FE" 
                fillOpacity={0.6}
                name={formatColumnName(valueColumn || 'Value')}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : chartType === 'bar' ? (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <BarChart data={chartData} layout="horizontal" margin={{ top: 20, right: 30, left: 180, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis 
                type="number"
                tickFormatter={formatYAxisTick}
                label={{ value: formatColumnName(valueColumn || 'Value'), position: 'insideBottom', offset: -10, style: { textAnchor: 'middle', fill: '#666', fontSize: '12px' } }}
                tick={{ fontSize: 11 }}
              />
              <YAxis 
                dataKey="name" 
                type="category" 
                width={170}
                tick={{ fontSize: 11 }}
                label={{ value: formatColumnName(nameColumn || 'Item'), angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#666', fontSize: '12px' } }}
              />
              <Tooltip 
                formatter={(value: any) => formatValue(value)}
                labelFormatter={(label) => `${formatColumnName(nameColumn || 'Item')}: ${label}`}
                contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', border: '1px solid #ccc', borderRadius: '4px' }}
              />
              <Legend 
                formatter={() => formatColumnName(valueColumn || 'Value')}
                wrapperStyle={{ paddingTop: '10px' }}
              />
              <Bar 
                dataKey="value" 
                fill="#0088FE"
                name={formatColumnName(valueColumn || 'Value')}
                radius={[0, 4, 4, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        ) : chartType === 'pie' ? (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent, value }) => {
                  const displayName = name.length > 12 ? name.substring(0, 12) + '...' : name
                  return `${displayName}\n${(percent * 100).toFixed(1)}% (${formatValue(value)})`
                }}
                outerRadius={chartHeight / 4}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value: any) => formatValue(value)}
                labelFormatter={(label) => `${formatColumnName(nameColumn || 'Item')}: ${label}`}
                contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', border: '1px solid #ccc', borderRadius: '4px' }}
              />
              <Legend 
                formatter={(entry) => `${entry.name}: ${formatValue(chartData.find(d => d.name === entry.name)?.value || 0)}`}
                wrapperStyle={{ paddingTop: '10px' }}
              />
            </PieChart>
          </ResponsiveContainer>
        ) : null}
      </>
    )

    const chartTitle = getChartTitle()
    const chartDescription = valueColumn && nameColumn ? 
      `This chart shows ${formatColumnName(valueColumn)} values for each ${formatColumnName(nameColumn).toLowerCase()}. ${chartType === 'trend' ? 'Use this to see trends and patterns over categories.' : chartType === 'bar' ? 'Items are sorted by value, with the highest values at the top.' : 'Each slice represents the proportion of total value.'}` : 
      'Data visualization'

    return (
      <div className={`chart-wrapper ${isChartExpanded ? 'chart-expanded' : ''}`}>
        <div className="chart-header">
          <div className="chart-title-section">
            <h4 className="chart-title">{chartTitle}</h4>
            <p className="chart-description">{chartDescription}</p>
          </div>
          <button 
            className="chart-expand-btn"
            onClick={() => setIsChartExpanded(!isChartExpanded)}
            title={isChartExpanded ? 'Minimize chart' : 'Expand chart to fullscreen'}
          >
            {isChartExpanded ? '⤓ Minimize' : '⤢ Expand'}
          </button>
        </div>
        {chartContent}
        <div className="chart-footer">
          <div className="chart-info">
            <span className="chart-info-item">
              <strong>Data Points:</strong> {chartData.length}
            </span>
            {valueColumn && (
              <span className="chart-info-item">
                <strong>Value Column:</strong> {formatColumnName(valueColumn)}
              </span>
            )}
            {nameColumn && (
              <span className="chart-info-item">
                <strong>Category Column:</strong> {formatColumnName(nameColumn)}
              </span>
            )}
            {chartData.length > 0 && (
              <span className="chart-info-item">
                <strong>Max Value:</strong> {formatValue(Math.max(...chartData.map(d => d.value)))}
              </span>
            )}
            {chartData.length > 0 && (
              <span className="chart-info-item">
                <strong>Min Value:</strong> {formatValue(Math.min(...chartData.map(d => d.value)))}
              </span>
            )}
          </div>
        </div>
      </div>
    )
  }

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
              🔵 OpenAI ({message.modelUsed})
            </span>
          </div>
        )}
        {/* Show analysis */}
        {isAnalysisMessage && analysisText && (
          <div className="message-text-content analysis-content">
            <div className="analysis-header">📊 Data Analysis</div>
            <div className="message-text analysis-text">
              <div>{analysisText}</div>
            </div>
          </div>
        )}

        {/* Show message content (for clarification questions or text responses) */}
        {message.content && !isAnalysisMessage && (!message.data || message.data.length === 0) && !message.formattedHtml && !message.error && (
          <div className="message-text-content">
            <div className="message-text">{message.content}</div>
          </div>
        )}

        {/* Visualization Selector - Show when data is available and not already visualizing */}
        {!isUser && message.data && message.data.length > 0 && !message.showVisualization && (
          <div className="visualization-selector">
            <button 
              className="visualize-btn"
              onClick={() => {
                const columns = message.availableColumns || (message.data && message.data.length > 0 ? Object.keys(message.data[0]) : [])
                if (columns.length > 0) {
                  // Auto-select first categorical and first numeric column
                  const numericCols = columns.filter((col: string) => {
                    const sample = message.data?.[0]?.[col]
                    return sample !== null && sample !== undefined && !isNaN(Number(sample))
                  })
                  const categoricalCols = columns.filter((col: string) => !numericCols.includes(col))
                  
                  setSelectedXAxis(categoricalCols[0] || columns[0] || '')
                  setSelectedYAxis(numericCols[0] || columns[1] || columns[0] || '')
                  setShowVisualizationSelector(true)
                }
              }}
            >
              📊 Visualize
            </button>
            
            {showVisualizationSelector && (
              <div className="visualization-modal">
                <div className="visualization-modal-content">
                  <h3>Select Columns for Visualization</h3>
                  <div className="column-selectors">
                    <div className="selector-group">
                      <label>X-Axis (Category/Label):</label>
                      <select 
                        value={selectedXAxis} 
                        onChange={(e) => setSelectedXAxis(e.target.value)}
                        className="column-select"
                      >
                        <option value="">Select column...</option>
                        {(message.availableColumns || (message.data && message.data.length > 0 ? Object.keys(message.data[0]) : [])).map((col: string) => (
                          <option key={col} value={col}>{col.replace(/_/g, ' ')}</option>
                        ))}
                      </select>
                    </div>
                    <div className="selector-group">
                      <label>Y-Axis (Value):</label>
                      <select 
                        value={selectedYAxis} 
                        onChange={(e) => setSelectedYAxis(e.target.value)}
                        className="column-select"
                      >
                        <option value="">Select column...</option>
                        {(message.availableColumns || (message.data && message.data.length > 0 ? Object.keys(message.data[0]) : [])).map((col: string) => (
                          <option key={col} value={col}>{col.replace(/_/g, ' ')}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="modal-actions">
                    <button 
                      className="btn-primary"
                      onClick={() => {
                        if (selectedXAxis && selectedYAxis && onVisualize) {
                          onVisualize(selectedXAxis, selectedYAxis, sessionId)
                          setShowVisualizationSelector(false)
                        }
                      }}
                      disabled={!selectedXAxis || !selectedYAxis}
                    >
                      Create Visualization
                    </button>
                    <button 
                      className="btn-secondary"
                      onClick={() => setShowVisualizationSelector(false)}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Show chart if visualization is requested */}
        {message.showVisualization && message.chartConfig && message.data && message.data.length > 0 && (
          <div className="chart-container">
            {renderChart(message.chartConfig, message.data)}
          </div>
        )}

        {/* Show formatted HTML results if available, otherwise fallback to table - HIDE if visualization is shown */}
        {!message.showVisualization && message.formattedHtml ? (
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
                {/* Visualization button in results footer */}
                {!message.showVisualization && (
                  <div className="visualization-selector" style={{ marginTop: '12px' }}>
                    <button 
                      className="visualize-btn"
                      onClick={() => {
                        const columns = message.availableColumns || (message.data && message.data.length > 0 ? Object.keys(message.data[0]) : [])
                        if (columns.length > 0) {
                          // Auto-select first categorical and first numeric column
                          const numericCols = columns.filter((col: string) => {
                            const sample = message.data?.[0]?.[col]
                            return sample !== null && sample !== undefined && !isNaN(Number(sample))
                          })
                          const categoricalCols = columns.filter((col: string) => !numericCols.includes(col))
                          
                          setSelectedXAxis(categoricalCols[0] || columns[0] || '')
                          setSelectedYAxis(numericCols[0] || columns[1] || columns[0] || '')
                          setShowVisualizationSelector(true)
                        }
                      }}
                    >
                      📊 Visualize
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : !message.showVisualization && message.data && message.data.length > 0 ? (
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
                <tfoot>
                  <tr>
                    {Object.keys(message.data[0] || {}).map((key) => (
                      <th key={key}>{key}</th>
                    ))}
                  </tr>
                </tfoot>
              </table>
            </div>
            <div className="results-footer">
              <div className="results-stats">
                <span className="results-count">Total Rows: {message.data.length}</span>
                <span className="results-count">Columns: {message.data[0] ? Object.keys(message.data[0]).length : 0}</span>
              </div>
            </div>
            {/* Visualization button in results footer */}
            {!message.showVisualization && (
              <div className="visualization-selector" style={{ marginTop: '12px' }}>
                <button 
                  className="visualize-btn"
                  onClick={() => {
                    const columns = message.availableColumns || (message.data && message.data.length > 0 ? Object.keys(message.data[0]) : [])
                    if (columns.length > 0) {
                      // Auto-select first categorical and first numeric column
                      const numericCols = columns.filter((col: string) => {
                        const sample = message.data?.[0]?.[col]
                        return sample !== null && sample !== undefined && !isNaN(Number(sample))
                      })
                      const categoricalCols = columns.filter((col: string) => !numericCols.includes(col))
                      
                      setSelectedXAxis(categoricalCols[0] || columns[0] || '')
                      setSelectedYAxis(numericCols[0] || columns[1] || columns[0] || '')
                      setShowVisualizationSelector(true)
                    }
                  }}
                >
                  📊 Visualize
                </button>
              </div>
            )}
          </div>
        ) : null}

        {message.data && message.data.length === 0 && (
          <div className="no-results">
            <p>No results found</p>
          </div>
        )}

        {/* Show "Show All Records" button if there are more records */}
        {message.hasMoreRecords && message.sqlQuery && (
          <div className="show-all-records-section">
            <div className="show-all-message">
              {message.totalCount ? (
                <p>Showing 1,000 of {message.totalCount.toLocaleString()} results.</p>
              ) : (
                <p>Showing 1,000 results. There may be more records.</p>
              )}
            </div>
            <button
              className="show-all-button"
              onClick={() => {
                if (message.sqlQuery && onShowAllRecords) {
                  onShowAllRecords(message.sqlQuery)
                }
              }}
              title="Load all records"
            >
              📊 Show All Records
            </button>
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


        <div className="message-time">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  )
}

export default Message
