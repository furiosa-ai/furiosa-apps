import React from 'react'
import { useRef, useEffect } from 'react'
import { Line, Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
)

// Format number with 3 significant figures for clean display
function formatNumber(value) {
  if (value === 0) return 0

  const absValue = Math.abs(value)

  // For numbers >= 100, no decimals
  if (absValue >= 100) {
    return Math.round(value)
  }
  // For numbers >= 10, 1 decimal
  else if (absValue >= 10) {
    return Math.round(value * 10) / 10
  }
  // For numbers >= 1, 2 decimals
  else if (absValue >= 1) {
    return Math.round(value * 100) / 100
  }
  // For small numbers, keep 3 significant figures
  else {
    const precision = 3
    return parseFloat(value.toPrecision(precision))
  }
}

export default function MeterComponent({ component, metricsData, preview = false }) {
  const getValue = () => {
    if (component.value !== undefined) return component.value
    if (component.dataKey && metricsData[component.dataKey]) {
      const data = metricsData[component.dataKey]
      if (Array.isArray(data)) {
        return data[data.length - 1] || 0
      }
      // Extract numeric value from strings like "60 ms" or "89"
      return parseFloat(data.toString().replace(/[^0-9.-]/g, '')) || 0
    }
    return 0
  }

  const getArrayData = () => {
    if (component.dataKey && metricsData[component.dataKey]) {
      return metricsData[component.dataKey]
    }
    return Array(10).fill(0)
  }

  const containerStyle = {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center'
  }

  switch (component.type) {
    case 'line-chart':
      return <LineChart component={component} data={getArrayData()} preview={preview} />
    case 'bar-chart':
      return <BarChart component={component} data={getArrayData()} preview={preview} />
    case 'gauge':
      return <GaugeChart component={component} value={getValue()} preview={preview} />
    case 'half-circle-gauge':
      return <HalfCircleGauge component={component} value={getValue()} preview={preview} metricsData={metricsData} />
    case 'thermometer':
      return <Thermometer component={component} value={getValue()} preview={preview} />
    case 'progress-bar':
      return <ProgressBar component={component} value={getValue()} preview={preview} />
    case 'speedometer':
      return <Speedometer component={component} value={getValue()} preview={preview} />
    case 'number-only':
      return <NumberOnly component={component} value={getValue()} preview={preview} />
    case 'line-with-number':
      return <LineWithNumber component={component} data={getArrayData()} value={getValue()} preview={preview} metricsData={metricsData} />
    case 'new-number-only':
      return <NewNumberOnly component={component} value={getValue()} preview={preview} />
    default:
      return (
        <div style={containerStyle}>
          <div style={{ color: '#666', fontSize: '14px' }}>
            Unknown component type: {component.type}
          </div>
        </div>
      )
  }
}

function LineChart({ component, data, preview }) {
  const chartData = {
    labels: data.map((_, i) => i),
    datasets: [
      {
        data: data,
        borderColor: component.color,
        backgroundColor: `${component.color}30`,
        borderWidth: 1.5,
        fill: true,
        tension: 0,
        pointRadius: 0,
        pointHoverRadius: 0
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    transitions: {
      active: {
        animation: {
          duration: 0
        }
      }
    },
    scales: {
      x: {
        display: false,
        grid: { display: false }
      },
      y: {
        display: true,
        position: 'left',
        grid: { display: false },
        beginAtZero: true,
        ticks: {
          color: '#666',
          font: { size: 10 },
          maxTicksLimit: 4
        }
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: { enabled: false }
    },
    elements: {
      point: { radius: 0 }
    }
  }

  const currentValue = data[data.length - 1] || 0;

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1, position:'relative', minHeight:0 }}>
        <Line data={chartData} options={options} />
      </div>
      {component.showNumber && !preview && (
        <div style={{ textAlign: 'center', marginTop: 'auto' }}>
          <div style={{ fontSize: '2.5rem', fontWeight: 'normal', color: component.color, lineHeight: '1', fontFamily: 'monospace' }}>
            {formatNumber(currentValue)}
          </div>
          <div style={{ fontSize: '1rem', color: '#fff', marginTop: '2px' }}>
            {component.unit || ''}
          </div>
        </div>
      )}
    </div>
  )
}

function BarChart({ component, data, preview }) {
  const chartData = {
    labels: data.map((_, i) => i),
    datasets: [
      {
        data: data,
        backgroundColor: component.color,
        borderColor: component.color,
        borderWidth: 1
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: { display: !preview },
      y: {
        display: !preview,
        beginAtZero: true
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: { enabled: !preview }
    }
  }

  return (
    <div style={{ width: '100%', height: preview ? '80px' : '100%', minHeight:0 }}>
      <Bar data={chartData} options={options} />
    </div>
  )
}

function GaugeChart({ component, value, preview }) {
  const percentage = Math.min(Math.max(value / 100, 0), 1)
  const size = preview ? 80 : 120
  const strokeWidth = preview ? 8 : 12
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const strokeDasharray = circumference
  const strokeDashoffset = circumference - (percentage * circumference)

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      width: '100%',
      height: '100%',
      justifyContent: 'center'
    }}>
      <div style={{ position: 'relative' }}>
        <svg width={size} height={size}>
          <circle
            cx={size/2}
            cy={size/2}
            r={radius}
            stroke="#333"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          <circle
            cx={size/2}
            cy={size/2}
            r={radius}
            stroke={component.color}
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{
              transform: 'rotate(-90deg)',
              transformOrigin: '50% 50%',
              transition: 'stroke-dashoffset 0.5s ease'
            }}
          />
        </svg>
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center',
          color: '#fff'
        }}>

	  {component.unit == 'ms' ? <>
          <div style={{ fontSize: preview ? '14px' : '18px', fontWeight: 'bold', fontFamily: 'monospace' }}>
            {formatNumber(value/1000)}
          </div>
          {component.unit && (
            <div style={{ fontSize: preview ? '10px' : '12px', color: '#999' }}>
              {'s'}
            </div>
          )}

		  </>:<>

          <div style={{ fontSize: preview ? '14px' : '18px', fontWeight: 'bold', fontFamily: 'monospace' }}>
            {formatNumber(value)}
          </div>
          {component.unit && (
            <div style={{ fontSize: preview ? '10px' : '12px', color: '#999' }}>
              {component.unit}
            </div>
          )}
		  </>}

        </div>
      </div>
    </div>
  )
}

function HalfCircleGauge({ component, value, preview, metricsData }) {
  // Get max value from the data array for this component
  const dataArray = component.dataKey && metricsData && metricsData[component.dataKey] ? metricsData[component.dataKey] : [];
  const maxValue = dataArray.length > 0 ? Math.max(...dataArray) : 100;
  const percentage = Math.min(Math.max(value / maxValue, 0), 1)
  const size = preview ? 100 : 140
  const strokeWidth = preview ? 8 : 12
  const radius = (size - strokeWidth) / 2
  const circumference = Math.PI * radius // Half circle
  const strokeDasharray = circumference
  const strokeDashoffset = circumference - (percentage * circumference)

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      width: '100%',
      height: '100%',
      justifyContent: 'center'
    }}>
      <div style={{ position: 'relative' }}>
        <svg width={size} height={size/2 + 20}>
          <path
            d={`M ${strokeWidth/2} ${size/2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth/2} ${size/2}`}
            stroke="#333"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          <path
            d={`M ${strokeWidth/2} ${size/2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth/2} ${size/2}`}
            stroke={component.color}
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{
              transition: 'stroke-dashoffset 0.5s ease'
            }}
          />
        </svg>
        <div style={{
          position: 'absolute',
          bottom: '10px',
          left: '50%',
          transform: 'translateX(-50%)',
          textAlign: 'center',
          color: '#fff'
        }}>
          <div style={{ fontSize: preview ? '14px' : '18px', fontWeight: 'bold', fontFamily: 'monospace' }}>
            {formatNumber(value)}
          </div>
          {component.unit && (
            <div style={{ fontSize: preview ? '10px' : '12px', color: '#999' }}>
              {component.unit}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Thermometer({ component, value, preview }) {
  const height = preview ? 60 : 100
  const width = preview ? 20 : 30
  const percentage = Math.min(Math.max(value / 100, 0), 1)

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      width: '100%',
      height: '100%',
      justifyContent: 'center'
    }}>
      <div style={{
        width: width,
        height: height,
        background: '#333',
        borderRadius: `${width/2}px`,
        position: 'relative',
        border: '2px solid #555'
      }}>
        <div style={{
          position: 'absolute',
          bottom: '2px',
          left: '2px',
          right: '2px',
          height: `${percentage * (height - 4)}px`,
          background: `linear-gradient(to top, ${component.color}, ${component.color}AA)`,
          borderRadius: `${width/2 - 2}px`,
          transition: 'height 0.5s ease'
        }} />
      </div>
      <div style={{ color: '#fff', textAlign: 'center' }}>
        <div style={{ fontSize: preview ? '14px' : '16px', fontWeight: 'bold', fontFamily: 'monospace' }}>
          {formatNumber(value)}
        </div>
        {component.unit && (
          <div style={{ fontSize: preview ? '10px' : '12px', color: '#999' }}>
            {component.unit}
          </div>
        )}
      </div>
    </div>
  )
}

function ProgressBar({ component, value, preview }) {
  const percentage = Math.min(Math.max(value / 100, 0), 1)

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      width: '100%',
      height: '100%',
      justifyContent: 'center',
      padding: '10px'
    }}>
      <div style={{
        width: '100%',
        height: preview ? '12px' : '20px',
        background: '#333',
        borderRadius: '10px',
        overflow: 'hidden',
        border: '1px solid #555'
      }}>
        <div style={{
          height: '100%',
          width: `${percentage * 100}%`,
          background: `linear-gradient(90deg, ${component.color}, ${component.color}AA)`,
          transition: 'width 0.5s ease'
        }} />
      </div>
      <div style={{
        textAlign: 'center',
        marginTop: '8px',
        color: '#fff'
      }}>
        <span style={{ fontSize: preview ? '12px' : '14px', fontWeight: 'bold', fontFamily: 'monospace' }}>
          {formatNumber(value)}{component.unit}
        </span>
      </div>
    </div>
  )
}

function Speedometer({ component, value, preview }) {
  const percentage = Math.min(Math.max(value / 100, 0), 1)
  const angle = percentage * 180 - 90 // -90 to 90 degrees
  const size = preview ? 80 : 120

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      width: '100%',
      height: '100%',
      justifyContent: 'center'
    }}>
      <div style={{ position: 'relative' }}>
        <svg width={size} height={size/2 + 20}>
          <path
            d={`M 10 ${size/2} A ${size/2-10} ${size/2-10} 0 0 1 ${size-10} ${size/2}`}
            stroke="#333"
            strokeWidth="4"
            fill="transparent"
          />
          <path
            d={`M 10 ${size/2} A ${size/2-10} ${size/2-10} 0 0 1 ${size/2} 10`}
            stroke={component.color}
            strokeWidth="4"
            fill="transparent"
            opacity="0.7"
          />
          {/* Needle */}
          <line
            x1={size/2}
            y1={size/2}
            x2={size/2 + (size/3) * Math.cos(angle * Math.PI / 180)}
            y2={size/2 + (size/3) * Math.sin(angle * Math.PI / 180)}
            stroke="#fff"
            strokeWidth="3"
            strokeLinecap="round"
          />
          <circle
            cx={size/2}
            cy={size/2}
            r="4"
            fill="#fff"
          />
        </svg>
        <div style={{
          position: 'absolute',
          bottom: '0px',
          left: '50%',
          transform: 'translateX(-50%)',
          textAlign: 'center',
          color: '#fff'
        }}>
          <div style={{ fontSize: preview ? '12px' : '16px', fontWeight: 'bold', fontFamily: 'monospace' }}>
            {formatNumber(value)}{component.unit}
          </div>
        </div>
      </div>
    </div>
  )
}

function NumberOnly({ component, value, preview }) {
  // Apply divider if specified in component config
  const dividedValue = component.divider ? value / component.divider : value
  const displayValue = formatNumber(dividedValue)

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      width: '100%',
      height: '100%',
      justifyContent: 'center'
    }}>
      <div style={{ fontSize: preview ? '2rem' : '3rem', fontWeight: 'normal', color: component.color, lineHeight: '1', fontFamily: 'sans-serif' }}>
        {displayValue}
      </div>
    </div>
  )
}

function LineWithNumber({ component, data, value, preview, metricsData }) {
  // unitDisplay: 'after-number' (default) shows "Power  23.6 w"
  // unitDisplay: 'in-title' shows "Power (w)  23.6"
  const unitDisplay = component.unitDisplay || 'after-number';
  const maxTpsValue = component.dataKey === 'tokensData' && metricsData?.maxTps ? metricsData.maxTps : null;

  const datasets = [
    {
      data: data,
      borderColor: '#cdbbff',
      backgroundColor: 'transparent',
      borderWidth: 1.5,
      fill: false,
      tension: 0,
      pointRadius: 0,
      pointHoverRadius: 0
    }
  ];

  // Add max TPS line dataset for TPS component (if enabled)
  if (maxTpsValue && component.dataKey === 'tokensData' && component.showMaxTps !== false) {
    datasets.push({
      data: Array(data.length).fill(maxTpsValue),
      borderColor: '#cdbbff',
      backgroundColor: 'transparent',
      borderWidth: 2,
      borderDash: [5, 5],
      fill: false,
      tension: 0,
      pointRadius: 0,
      pointHoverRadius: 0
    });
  }

  const chartData = {
    labels: data.map((_, i) => i),
    datasets: datasets,
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    transitions: {
      active: {
        animation: {
          duration: 0
        }
      }
    },
    scales: {
      x: {
        display: false,
        grid: { display: false }
      },
      y: {
        display: true,
        position: 'left',
        grid: {
          display: false,
          drawBorder: false
        },
        beginAtZero: true,
        ticks: {
          color: '#666',
          font: { size: 10 },
          maxTicksLimit: 4,
          padding: 2
        }
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: { enabled: false }
    },
    elements: {
      point: { radius: 0 }
    }
  }

  const dividedValue = component.divider ? value / component.divider : value
  const displayValue = formatNumber(dividedValue)

  return (
    <div style={{
      width: '100%',
      position: 'relative',
      boxSizing: 'border-box'
    }}>
      {/* Header with title and number */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        height: '40px'
      }}>
        <div style={{
          fontSize: '1rem',
          color: '#76d6ff',
          fontWeight: '500'
        }}>
          {component.title}
          {unitDisplay === 'in-title' && component.unit && (
            <span style={{ color: '#76d6ff' }}>
              {` (${component.unit})`}
            </span>
          )}
        </div>
        <div style={{
          fontSize: '32px',
          color: '#fff',
          fontFamily: 'monospace',
          lineHeight: '1',
          fontWeight: 'normal'
        }}>
          {displayValue}
          {unitDisplay === 'after-number' && component.unit && (
            <span style={{ fontSize: '16px', color: '#888', marginLeft: '4px' }}>
              {component.unit}
            </span>
          )}
        </div>
      </div>
      {/* Line chart */}
      <div style={{
        height: '130px',
        width: '100%',
        position: 'relative'
      }}>
        <Line data={chartData} options={options} />
      </div>
    </div>
  )
}

function NewNumberOnly({ component, value, preview }) {
  // unitDisplay: 'after-number' (default) shows "Power  23.6 w"
  // unitDisplay: 'in-title' shows "Power (w)  23.6"
  const unitDisplay = component.unitDisplay || 'after-number';
  const dividedValue = component.divider ? value / component.divider : value
  const displayValue = formatNumber(dividedValue)

  return (
    <div style={{
      width: '100%',
      height: '40px',
      position: 'relative'
    }}>
      {/* Header with title and number */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start'
      }}>
        <div style={{
          fontSize: '1rem',
          color: '#76d6ff',
          fontWeight: '500'
        }}>
          {component.title}
          {unitDisplay === 'in-title' && component.unit && (
            <span style={{ color: '#76d6ff' }}>
              {` (${component.unit})`}
            </span>
          )}
        </div>
        <div style={{
          fontSize: '32px',
          color: '#fff',
          fontFamily: 'monospace',
          lineHeight: '1',
          fontWeight: 'normal'
        }}>
          {displayValue}
          {unitDisplay === 'after-number' && component.unit && (
            <span style={{ fontSize: '16px', color: '#888', marginLeft: '4px' }}>
              {component.unit}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
