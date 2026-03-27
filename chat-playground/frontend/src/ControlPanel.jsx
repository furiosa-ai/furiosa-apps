import React from 'react'
import logoImage from './assets/Symbol.png'

export default function ControlPanel({ windowWidth = 80, modelName = "" }) {
  return (
    <div style={{
      background: '#000',
      width: '100%',
      display: 'flex',
      justifyContent: 'center',
      borderBottom: '1px solid #444'
    }}>
      <div style={{
        width: `${windowWidth}%`,
        height: '70px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '10px'
      }}>
        {/* Left side - Logo and branding (aligned with chat column) */}
        <div style={{
          flex: 2,
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <img src={logoImage} alt="logo" style={{ height: '28px' }} />
          <span style={{
            color: '#fff',
            fontWeight: 'bold',
            fontSize: '1.2rem',
            letterSpacing: '0.5px'
          }}>
            Furiosa RNGD Chat
          </span>
          <span style={{
            background: '#cdbbff',
            color: '#000',
            padding: '2px 8px',
            borderRadius: '4px',
            fontSize: '11px',
            fontWeight: 'bold',
            letterSpacing: '0.5px'
          }}>
            DEMO
          </span>
        </div>

        {/* Right side - Model info (aligned with metrics column) */}
        <div style={{
          flex: 1,
          borderLeft: '1px solid #444',
          borderRight: '1px solid #444',
          height: '70px',
          display: 'flex',
          alignItems: 'center'
        }}>
          <div style={{
            color: '#fff',
            fontSize: '0.9rem',
            fontFamily: 'monospace',
            textAlign: 'center',
            height: '70px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '100%'
          }}>
            {modelName || "Loading..."}
          </div>
        </div>
      </div>
    </div>
  )
}
