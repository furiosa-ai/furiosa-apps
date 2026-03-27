import React, { useState, useEffect, useRef } from 'react'
import MeterComponent from './MeterComponent'

const AVAILABLE_COMPONENTS = [
  { id: 'tps', type: 'line-chart', title: 'TPS', dataKey: 'tokensData', color: '#cdbbff', description: 'Tokens Per Second', gridSpan: { columns: 2, rows: 1 }, showNumber: false },
  { id: 'tps-with-number', type: 'line-with-number', title: 'TPS', dataKey: 'tokensData', color: '#cdbbff', description: 'TPS with Number Display', gridSpan: { columns: 1, rows: 1 }, unitDisplay: 'in-title', showMaxTps: true },
  { id: 'ttft', type: 'line-chart', title: 'TTFT', dataKey: 'ttftData', unit: 'ms', color: '#70e697', description: 'Time To First Token', gridSpan: { columns: 1, rows: 1 }, showNumber: true },
  { id: 'ttft-number', type: 'number-only', title: 'TTFT (s)', dataKey: 'ttftData', unit: 'ms', divider: 1000, color: '#70e697', description: 'Time To First Token (Number Only)', gridSpan: { columns: 1, rows: 1 } },
  { id: 'ttft-bar', type: 'bar-chart', title: 'TTFT', dataKey: 'ttftData', unit: 'ms', color: '#70e697', description: 'TTFT Bar Chart', gridSpan: { columns: 2, rows: 1 } },
  { id: 'tpot', type: 'line-chart', title: 'TPOT', dataKey: 'tpotData', unit: 'ms', color: '#4ade80', description: 'Time Per Output Token', gridSpan: { columns: 1, rows: 1 }, showNumber: true },
  { id: 'tpot-with-number', type: 'line-with-number', title: 'TPOT', dataKey: 'tpotData', unit: 'ms', color: '#4ade80', description: 'TPOT with Number Display', gridSpan: { columns: 1, rows: 1 }, unitDisplay: 'in-title' },
  { id: 'tpot-number', type: 'number-only', title: 'TPOT (ms)', dataKey: 'tpotData', unit: 'ms', color: '#4ade80', description: 'Time Per Output Token (Number Only)', gridSpan: { columns: 1, rows: 1 } },
  { id: 'tpot-bar', type: 'bar-chart', title: 'TPOT', dataKey: 'tpotData', unit: 'ms', color: '#4ade80', description: 'TPOT Bar Chart', gridSpan: { columns: 2, rows: 1 } },
  { id: 'efficiency', type: 'line-chart', title: 'Efficiency', dataKey: 'efficiencyData', unit: 'TPS/w', color: '#fec2a0', description: 'Processing Efficiency', gridSpan: { columns: 1, rows: 1 }, showNumber: true },
  { id: 'e2e', type: 'line-chart', title: 'E2E', dataKey: 'e2eData', unit: 'ms', color: '#fffa82', description: 'End to End Latency', gridSpan: { columns: 1, rows: 1 }, showNumber: true },
  { id: 'e2e-with-number', type: 'new-number-only', title: 'E2E', dataKey: 'e2eData', unit: 's', divider: 1000, color: '#fffa82', description: 'E2E Number Only Display', gridSpan: { columns: 1, rows: 1 }, unitDisplay: 'in-title' },
  { id: 'e2e-number', type: 'number-only', title: 'E2E (s)', dataKey: 'e2eData', unit: 'ms', divider: 1000, color: '#fffa82', description: 'End to End Latency (Number Only)', gridSpan: { columns: 1, rows: 1 } },
  { id: 'e2e-bar', type: 'bar-chart', title: 'E2E', dataKey: 'e2eData', unit: 'ms', color: '#fffa82', description: 'E2E Bar Chart', gridSpan: { columns: 2, rows: 1 } },
  { id: 'power', type: 'line-chart', title: 'Power', dataKey: 'powerData', unit: 'watts', color: '#76d6ff', description: 'Power Consumption', gridSpan: { columns: 1, rows: 1 }, showNumber: true },
  { id: 'power-number', type: 'new-number-only', title: 'Power / card', dataKey: 'powerData', unit: 'W', color: '#76d6ff', description: 'Power per Card Number Display', gridSpan: { columns: 1, rows: 1 }, unitDisplay: 'in-title' },
  { id: 'power-half', type: 'half-circle-gauge', title: 'Power', dataKey: 'powerData', unit: 'watts', color: '#76d6ff', description: 'Power (Half Circle)', gridSpan: { columns: 1, rows: 1 } },
  { id: 'temperature', type: 'thermometer', title: 'Temperature', dataKey: 'temperatureData', unit: '°C', color: '#ef4444', description: 'System Temperature', gridSpan: { columns: 1, rows: 1 } },
  { id: 'max-tps', type: 'new-number-only', title: 'Max TPS', dataKey: 'maxTps', color: '#cdbbff', description: 'Maximum TPS Capability', gridSpan: { columns: 1, rows: 1 }, unitDisplay: 'in-title' }
]

export default function ComponentSelector({ components, setComponents, metricsData, gridColumns, setGridColumns, chatFontSize, setChatFontSize, windowWidth, setWindowWidth, suggestedPrompts, setSuggestedPrompts, isRTL, setIsRTL }) {
  const [selectedComponents, setSelectedComponents] = useState(new Set(components.map(c => c.id)))
  const [dragOverIndex, setDragOverIndex] = useState(null)
  const [draggedIndex, setDraggedIndex] = useState(null)
  const [promptsText, setPromptsText] = useState(suggestedPrompts?.join('\n') || '')

  // Sync promptsText when suggestedPrompts changes externally
  useEffect(() => {
    setPromptsText(suggestedPrompts?.join('\n') || '')
  }, [suggestedPrompts])

  const handleComponentToggle = (componentId) => {
    const newSelected = new Set(selectedComponents)
    if (newSelected.has(componentId)) {
      newSelected.delete(componentId)
      setComponents(prev => prev.filter(c => c.id !== componentId))
    } else {
      newSelected.add(componentId)
      const component = AVAILABLE_COMPONENTS.find(c => c.id === componentId)
      setComponents(prev => [...prev, component])
    }
    setSelectedComponents(newSelected)
  }


  const handleNumberToggle = (componentId) => {
    setComponents(prev => prev.map(comp => {
      if (comp.id === componentId) {
        return {
          ...comp,
          showNumber: !comp.showNumber
        }
      }
      return comp
    }))
  }

  const handleUnitDisplayToggle = (componentId) => {
    setComponents(prev => prev.map(comp => {
      if (comp.id === componentId) {
        return {
          ...comp,
          unitDisplay: comp.unitDisplay === 'in-title' ? 'after-number' : 'in-title'
        }
      }
      return comp
    }))
  }

  const handleMaxTpsToggle = (componentId) => {
    setComponents(prev => prev.map(comp => {
      if (comp.id === componentId) {
        return {
          ...comp,
          showMaxTps: !comp.showMaxTps
        }
      }
      return comp
    }))
  }

  const handleDragStart = (e, index) => {
    e.dataTransfer.setData('text/plain', index.toString())
    setDraggedIndex(index)
  }

  const handleDragEnd = () => {
    setDraggedIndex(null)
    setDragOverIndex(null)
  }

  const handleDragOver = (e, index) => {
    e.preventDefault()
    e.stopPropagation()

    // For items 0 to n-2: show indicator above item when in top half, between items when in bottom half
    // For last item (n-1): show indicator above when in top half, after all items when in bottom half
    const rect = e.currentTarget.getBoundingClientRect()
    const dragY = e.clientY
    const itemMiddle = rect.top + rect.height / 2

    const insertIndex = dragY > itemMiddle ? index + 1 : index

    // Don't show indicator at invalid positions:
    // - Same as dragged item position
    // - After last item when dragging the last item (would be same position)
    const isInvalidPosition = draggedIndex === insertIndex ||
                             (draggedIndex === components.length - 1 && insertIndex === components.length)

    if (dragOverIndex !== insertIndex && draggedIndex !== null && !isInvalidPosition) {
      setDragOverIndex(insertIndex)
    }
  }

  const handleDragLeave = (e) => {
    // Only clear drag over if we're actually leaving the container
    if (!e.currentTarget.contains(e.relatedTarget)) {
      setDragOverIndex(null)
    }
  }

  const handleDrop = (e, itemIndex) => {
    e.preventDefault()
    setDragOverIndex(null)
    setDraggedIndex(null)
    const dragIndex = parseInt(e.dataTransfer.getData('text/plain'))

    // Determine actual drop position using the same logic as handleDragOver
    const rect = e.currentTarget.getBoundingClientRect()
    const dragY = e.clientY
    const itemMiddle = rect.top + rect.height / 2
    const dropIndex = dragY > itemMiddle ? itemIndex + 1 : itemIndex

    // Don't drop at invalid positions
    const isInvalidDrop = dragIndex === dropIndex ||
                         (dragIndex === components.length - 1 && dropIndex === components.length)

    if (!isInvalidDrop) {
      const newComponents = [...components]
      const draggedComponent = newComponents[dragIndex]

      newComponents.splice(dragIndex, 1)
      // Adjust dropIndex if we removed an item before it
      const adjustedDropIndex = dragIndex < dropIndex ? dropIndex - 1 : dropIndex
      newComponents.splice(adjustedDropIndex, 0, draggedComponent)
      setComponents(newComponents)
    }
  }

  const handlePromptsUpdate = () => {
    const newPrompts = promptsText
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0)
    setSuggestedPrompts(newPrompts)
  }

  return (
    <div style={{
      height: '100%',
      background: '#111',
      padding: '20px',
      overflowY: 'auto',
      boxSizing: 'border-box'
    }}>
      <div style={{ marginBottom: '30px' }}>
        <h2 style={{ color: '#fff', marginBottom: '20px', fontSize: '24px' }}>
          Dashboard Configuration
        </h2>

        {/* Auto Prompts Control */}
        <div style={{
          background: '#2a2a2a',
          borderRadius: '8px',
          padding: '15px',
          marginBottom: '20px'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '15px'
          }}>
            <div style={{ color: '#fff', fontSize: '16px' }}>
              Auto Prompt Candidates
            </div>
            <button
              onClick={handlePromptsUpdate}
              style={{
                background: '#4ade80',
                color: '#000',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 'bold'
              }}
            >
              Apply Changes
            </button>
          </div>
          <textarea
            value={promptsText}
            onChange={(e) => setPromptsText(e.target.value)}
            placeholder="Enter one prompt per line..."
            style={{
              width: '100%',
              height: '200px',
              background: '#111',
              border: '1px solid #444',
              borderRadius: '6px',
              color: '#fff',
              padding: '12px',
              fontSize: '14px',
              fontFamily: 'inherit',
              resize: 'vertical',
              boxSizing: 'border-box'
            }}
          />
          <div style={{
            marginTop: '8px',
            fontSize: '12px',
            color: '#666'
          }}>
            {promptsText.split('\n').filter(line => line.trim().length > 0).length} prompts
          </div>
        </div>

        {/* Font Size Control Section */}
        <div style={{
          background: '#2a2a2a',
          borderRadius: '8px',
          padding: '15px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ color: '#fff', fontSize: '16px' }}>
            Chat/Reasoning Font Size
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <button
              onClick={() => setChatFontSize(prev => Math.max(0.7, prev - 0.1))}
              style={{
                background: '#444',
                border: 'none',
                color: '#fff',
                width: '32px',
                height: '32px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '18px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              -
            </button>
            <div style={{
              color: '#fff',
              fontSize: '14px',
              minWidth: '60px',
              textAlign: 'center'
            }}>
              {chatFontSize.toFixed(1)}rem
            </div>
            <button
              onClick={() => setChatFontSize(prev => Math.min(2.0, prev + 0.1))}
              style={{
                background: '#444',
                border: 'none',
                color: '#fff',
                width: '32px',
                height: '32px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '18px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              +
            </button>
          </div>
        </div>

        {/* Selected Components Section */}
        <div style={{
          background: 'linear-gradient(135deg, #2a2a2a, #222)',
          borderRadius: '12px',
          padding: '20px',
          border: components.length > 0 ? '2px solid #444' : '2px solid #333',
          marginBottom: '20px',
          boxShadow: components.length > 0 ? '0 8px 25px rgba(0,0,0,0.3)' : '0 4px 15px rgba(0,0,0,0.2)',
          transition: 'all 0.3s ease'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            marginBottom: '15px'
          }}>
            <div style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: components.length > 0 ? '#4ade80' : '#666'
            }} />
            <h3 style={{ color: '#fff', margin: 0, fontSize: '18px' }}>
              Selected Components ({components.length})
            </h3>
          </div>
          <div style={{ color: '#ccc' }}>
            {components.length === 0 ? (
              <p style={{
                color: '#666',
                fontStyle: 'italic',
                textAlign: 'center',
                padding: '20px 0'
              }}>
                Click components below to add them to your dashboard
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {components.map((comp, index) => (
                  <div
                    key={`wrapper-${comp.id}-${index}`}
                    onDragOver={(e) => handleDragOver(e, index)}
                    onDrop={(e) => handleDrop(e, index)}
                    style={{
                      position: 'relative'
                    }}
                  >
                    {/* Drop indicator above this item */}
                    <div style={{
                      position: 'absolute',
                      top: '-8px',
                      left: '-4px',
                      right: '-4px',
                      height: '4px',
                      background: dragOverIndex === index && draggedIndex !== index ? '#4ade80' : 'transparent',
                      borderRadius: '2px',
                      zIndex: 10,
                      pointerEvents: 'none',
                      transition: 'none',
                      willChange: 'background-color',
                      boxShadow: dragOverIndex === index && draggedIndex !== index ? '0 0 8px #4ade8080' : 'none'
                    }} />
                    <div
                      key={comp.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, index)}
                      onDragEnd={handleDragEnd}
                      onDragLeave={handleDragLeave}
                      style={{
                        background: `linear-gradient(135deg, ${comp.color}20, #333)`,
                        color: '#fff',
                        padding: '12px',
                        borderRadius: '8px',
                        border: `2px solid transparent`,
                        outline: `1px solid ${comp.color}40`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        cursor: 'grab',
                        opacity: draggedIndex === index ? 0.5 : 1,
                        transform: dragOverIndex === index && draggedIndex !== index ? 'translateY(-2px)' : 'translateY(0)',
                        transition: 'border-color 0.05s ease, opacity 0.1s ease',
                        willChange: 'transform, border-color, opacity'
                      }}
                    >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{
                        color: '#666',
                        cursor: 'grab',
                        fontSize: '14px',
                        userSelect: 'none'
                      }}>⋮⋮</span>
                      <div style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: comp.color
                      }} />
                      <span style={{ fontWeight: 'bold' }}>{comp.title}</span>
                    </div>

                    <div style={{ display: 'flex', gap: '12px' }}>
                      {comp.type === 'line-chart' && (
                        <label style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}>
                          <input
                            type="checkbox"
                            checked={comp.showNumber || false}
                            onChange={() => handleNumberToggle(comp.id)}
                            style={{ cursor: 'pointer' }}
                          />
                          Number
                        </label>
                      )}
                      {(comp.type === 'line-with-number' || comp.type === 'new-number-only') && comp.unit && (
                        <label style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}>
                          <input
                            type="checkbox"
                            checked={comp.unitDisplay === 'in-title'}
                            onChange={() => handleUnitDisplayToggle(comp.id)}
                            style={{ cursor: 'pointer' }}
                          />
                          Unit in Title
                        </label>
                      )}
                      {comp.type === 'line-with-number' && comp.dataKey === 'tokensData' && (
                        <label style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}>
                          <input
                            type="checkbox"
                            checked={comp.showMaxTps || false}
                            onChange={() => handleMaxTpsToggle(comp.id)}
                            style={{ cursor: 'pointer' }}
                          />
                          Max TPS Line
                        </label>
                      )}
                    </div>
                    </div>
                  </div>
                ))}
                {/* Drop indicator after the last item */}
                <div style={{
                  position: 'relative',
                  height: '4px',
                  marginTop: '4px'
                }}>
                  <div style={{
                    position: 'absolute',
                    top: '0',
                    left: '-4px',
                    right: '-4px',
                    height: '4px',
                    background: dragOverIndex === components.length && draggedIndex !== null ? '#4ade80' : 'transparent',
                    borderRadius: '2px',
                    zIndex: 10,
                    pointerEvents: 'none',
                    transition: 'none',
                    willChange: 'background-color',
                    boxShadow: dragOverIndex === components.length && draggedIndex !== null ? '0 0 8px #4ade8080' : 'none'
                  }} />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Grid Settings */}
        <div style={{
          background: 'linear-gradient(135deg, #2a2a2a, #222)',
          borderRadius: '12px',
          padding: '20px',
          border: '2px solid #444',
          marginBottom: '30px'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            marginBottom: '15px'
          }}>
            <div style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: '#3b82f6'
            }} />
            <h3 style={{ color: '#fff', margin: 0, fontSize: '16px' }}>
              Grid Layout
            </h3>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '20px',
            flexWrap: 'wrap'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}>
              <label style={{ color: '#ccc', fontSize: '14px' }}>
                Columns:
              </label>
              <div style={{ display: 'flex', gap: '8px' }}>
                {[2, 3, 4, 5, 6].map(cols => (
                  <button
                    key={cols}
                    onClick={() => setGridColumns(cols)}
                    style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '8px',
                      border: 'none',
                      background: gridColumns === cols ? '#3b82f6' : '#333',
                      color: gridColumns === cols ? '#fff' : '#ccc',
                      cursor: 'pointer',
                      fontSize: '14px',
                      fontWeight: gridColumns === cols ? 'bold' : 'normal',
                      transition: 'all 0.3s ease'
                    }}
                  >
                    {cols}
                  </button>
                ))}
              </div>
            </div>
          </div>

        </div>

        {/* Window Width Control */}
        <div style={{
          background: '#2a2a2a',
          borderRadius: '8px',
          padding: '15px',
          marginBottom: '30px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ color: '#fff', fontSize: '16px' }}>
            Window Width
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '15px'
          }}>
            <label style={{ color: '#ccc', fontSize: '14px', minWidth: '80px' }}>
              Width:
            </label>
            <select
              value={windowWidth}
              onChange={(e) => setWindowWidth(Number(e.target.value))}
              style={{
                padding: '8px 12px',
                background: '#222',
                border: '1px solid #444',
                borderRadius: '6px',
                color: '#fff',
                fontSize: '14px',
                minWidth: '100px'
              }}
            >
              <option value={50}>50%</option>
              <option value={60}>60%</option>
              <option value={70}>70%</option>
              <option value={80}>80%</option>
              <option value={90}>90%</option>
            </select>
          </div>
        </div>

        {/* RTL Control */}
        <div style={{
          background: '#2a2a2a',
          borderRadius: '8px',
          padding: '15px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ color: '#fff', fontSize: '16px' }}>
            Right-to-Left Layout (Arabic)
          </div>
          <label style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            cursor: 'pointer'
          }}>
            <input
              type="checkbox"
              checked={isRTL}
              onChange={(e) => setIsRTL(e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            <span style={{ color: '#ccc', fontSize: '14px' }}>Enable RTL</span>
          </label>
        </div>


        <h3 style={{ color: '#fff', marginBottom: '15px', fontSize: '18px' }}>
          Component Library
        </h3>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '15px'
      }}>
        {AVAILABLE_COMPONENTS.map(component => (
          <ComponentCard
            key={component.id}
            component={component}
            isSelected={selectedComponents.has(component.id)}
            onToggle={() => handleComponentToggle(component.id)}
            metricsData={metricsData}
          />
        ))}
      </div>
    </div>
  )
}

function ComponentCard({ component, isSelected, onToggle, metricsData }) {
  const [isHovered, setIsHovered] = useState(false)

  return (
    <div
      style={{
        background: isSelected ? `linear-gradient(135deg, ${component.color}15, #222)` : '#222',
        borderRadius: '6px',
        padding: '12px',
        border: isSelected
          ? `2px solid ${component.color}`
          : isHovered
            ? `2px solid ${component.color}40`
            : '2px solid #444',
        cursor: 'pointer',
        transition: 'all 0.3s ease',
        transform: isSelected ? 'translateY(-2px)' : 'translateY(0)',
        boxShadow: isSelected
          ? `0 8px 25px ${component.color}20, 0 0 0 1px ${component.color}30`
          : isHovered
            ? `0 4px 15px rgba(0,0,0,0.3)`
            : '0 2px 8px rgba(0,0,0,0.2)'
      }}
      onClick={onToggle}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '10px'
      }}>
        <h3 style={{
          color: isSelected ? component.color : '#fff',
          margin: 0,
          fontSize: '16px',
          fontWeight: 'bold',
          transition: 'color 0.3s ease'
        }}>
          {component.title}
        </h3>
        <div style={{
          width: '24px',
          height: '24px',
          borderRadius: '50%',
          border: `2px solid ${isSelected ? component.color : '#666'}`,
          background: isSelected ? component.color : 'transparent',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.3s ease'
        }}>
          {isSelected && (
            <span style={{
              color: '#fff',
              fontSize: '12px',
              fontWeight: 'bold'
            }}>
              ✓
            </span>
          )}
        </div>
      </div>

      <p style={{
        color: '#999',
        fontSize: '12px',
        margin: '0 0 15px 0'
      }}>
        {component.description}
      </p>

      <div style={{
        height: '80px',
        background: isSelected ? `linear-gradient(135deg, ${component.color}08, #111)` : '#111',
        borderRadius: '4px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: isSelected
          ? `1px solid ${component.color}40`
          : isHovered
            ? `1px solid ${component.color}20`
            : '1px solid #333',
        transition: 'all 0.3s ease'
      }}>
        <MeterComponent
          component={component}
          metricsData={metricsData}
          preview={true}
        />
      </div>

      <div style={{
        marginTop: '10px',
        fontSize: '11px',
        textAlign: 'center',
        display: 'flex',
        justifyContent: 'center',
        gap: '6px'
      }}>
        <span style={{
          background: isSelected ? component.color : '#333',
          color: isSelected ? '#fff' : '#999',
          padding: '4px 8px',
          borderRadius: '12px',
          transition: 'all 0.3s ease',
          fontWeight: isSelected ? 'bold' : 'normal'
        }}>
          {component.type.replace('-', ' ').toUpperCase()}
        </span>
      </div>
    </div>
  )
}
