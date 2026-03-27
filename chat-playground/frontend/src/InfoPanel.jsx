import React, { useState } from 'react'
import MeterComponent from './MeterComponent'

export default function InfoPanel({
  power,
  temperature,
  tokensSec,
  powerData,
  temperatureData,
  tokensData,
  expanded,
  toggleExpanded,
  components = [],
  metricsData,
  gridColumns = 4,
  onSendMessage
}) {
  const [inputValue, setInputValue] = useState('')

  const handleSubmit = () => {
    if (inputValue.trim() && onSendMessage) {
      onSendMessage(inputValue.trim())
      setInputValue('')
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSubmit()
    }
  }
  return (
    <div style={{
      background: '#111',
      width: '100%',
      borderTop: '1px solid #333',
      padding: '20px'
    }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${gridColumns}, 1fr)`,
        gridAutoRows: '140px',
        gap: '20px',
        maxWidth: '1400px',
        margin: '0 auto'
      }}>
        {components.map(component => {
          const gridSpan = component.gridSpan || { columns: 1, rows: 1 }
          return (
            <div key={component.id} style={{
              background: '#222',
              borderRadius: '8px',
              padding: '15px',
              gridColumn: `span ${gridSpan.columns}`,
              gridRow: `span ${gridSpan.rows}`,
              display: 'flex',
              flexDirection: 'column'
            }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '10px'
              }}>
                <h3 style={{
                  color: '#fff',
                  margin: 0,
                  fontSize: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <div style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: component.color
                  }} />
                  {component.title}
                </h3>
                <div style={{
                  background: '#333',
                  color: '#999',
                  padding: '2px 6px',
                  borderRadius: '6px',
                  fontSize: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '3px'
                }}>
                  <span style={{ fontSize: '8px' }}>📐</span>
                  {gridSpan.columns}×{gridSpan.rows}
                </div>
              </div>
              <div style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <MeterComponent
                  component={component}
                  metricsData={metricsData}
                />
              </div>
            </div>
          )
        })}

        {components.length === 0 && (
          <div style={{
            gridColumn: 'span 3',
            textAlign: 'center',
            color: '#666',
            padding: '40px'
          }}>
            <div style={{ fontSize: '18px', marginBottom: '10px' }}>⚙️</div>
            <div>Click the settings button to add components</div>
          </div>
        )}
      </div>

      {/* Bottom Input Area */}
      <div style={{
        marginTop: '20px',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        maxWidth: '1200px',
        margin: '20px auto 0'
      }}>
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="What does customer policy #345636 entail?"
          style={{
            flex: 1,
            padding: '12px',
            background: '#222',
            border: '1px solid #555',
            borderRadius: '8px',
            color: '#fff',
            outline: 'none'
          }}
        />
        <button style={{
          background: '#dc2626',
          color: '#fff',
          border: 'none',
          padding: '12px 20px',
          borderRadius: '6px',
          cursor: 'pointer',
          fontWeight: '600',
          fontSize: '14px',
          minWidth: '80px'
        }}>
          Pause
        </button>
        <label style={{
          display: 'flex',
          alignItems: 'center',
          color: '#fff',
          gap: '8px',
          cursor: 'pointer'
        }}>
          <input type="checkbox" defaultChecked />
          Continuous prompting
        </label>
      </div>
    </div>
  )
}
