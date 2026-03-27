import React, { useState, useEffect, useCallback } from "react"
import useWebSocket from "react-use-websocket"
import ChatRenderer from "./ChatRenderer"
import ControlPanel from "./ControlPanel"
import ComponentSelector from "./ComponentSelector"
import MeterComponent from "./MeterComponent"
import "./App.css"

let globalIndex = 0;
const ZERO_SERIES = Array(10).fill(0)
const SOCKET_OPEN = 1

export default function App() {
  const [messages, setMessages] = useState({})
  const [continuousPrompting, setContinuousPrompting] = useState(true)
  const [showComponentSelector, setShowComponentSelector] = useState(false)
  const [suggestedPrompts, setSuggestedPrompts] = useState([
    "Explain the difference between transformers and RNNs",
    "How does gradient descent work in neural networks?",
    "What are the key components of a GPT architecture?",
    "What is the attention mechanism in deep learning?",
    "How does backpropagation update neural network weights?",
    "What are the advantages of using convolutional layers?"
  ])
  const [currentPromptIndex, setCurrentPromptIndex] = useState(0)
  const [waitingForCompletion, setWaitingForCompletion] = useState(false)
  const [animatingPrompt, setAnimatingPrompt] = useState(null)
  const [inputValue, setInputValue] = useState("")
  const [removingPrompt, setRemovingPrompt] = useState(false)
  const [inputFocused, setInputFocused] = useState(false)
  const [power, setPower] = useState("0 W")
  const [temperature, setTemperature] = useState("0 °C")
  const [tokensSec, setTokensSec] = useState("0")
  const [powerData, setPowerData] = useState(ZERO_SERIES)
  const [temperatureData, setTemperatureData] = useState(ZERO_SERIES)
  const [tokensData, setTokensData] = useState(ZERO_SERIES)
  const [memoryUsage, setMemoryUsage] = useState("0 %")
  const [cpuUsage, setCpuUsage] = useState("0 %")
  const [memoryData, setMemoryData] = useState(ZERO_SERIES)
  const [cpuData, setCpuData] = useState(ZERO_SERIES)
  const [ttftData, setTtftData] = useState(ZERO_SERIES)
  const [efficiencyData, setEfficiencyData] = useState(ZERO_SERIES)
  const [e2eData, setE2eData] = useState(ZERO_SERIES)
  const [tpotData, setTpotData] = useState(ZERO_SERIES)
  const [maxTps, setMaxTps] = useState(0)  // Max TPS from backend
  const [modelName, setModelName] = useState("")  // Model name from LLM server
  const [gridColumns, setGridColumns] = useState(1)
  const [chatFontSize, setChatFontSize] = useState(1) // Font size in rem
  const [windowWidth, setWindowWidth] = useState(80) // Window width percentage
  const [isRTL, setIsRTL] = useState(false)
  const [rightPanelComponents, setRightPanelComponents] = useState([
    // { id: 'max-tps', type: 'new-number-only', title: 'Max TPS', dataKey: 'maxTps', gridSpan: { columns: 1, rows: 1 }, unitDisplay: 'in-title' },
    { id: 'tps', type: 'line-with-number', title: 'TPS', dataKey: 'tokensData', gridSpan: { columns: 1, rows: 1 }, unitDisplay: 'in-title' },
    { id: 'tpot', type: 'line-with-number', title: 'TPOT', dataKey: 'tpotData', unit: 'ms', gridSpan: { columns: 1, rows: 1 }, unitDisplay: 'in-title' },
    { id: 'e2e', type: 'new-number-only', title: 'E2E', dataKey: 'e2eData', unit: 's', divider: 1000, gridSpan: { columns: 1, rows: 1 }, unitDisplay: 'in-title' },
    { id: 'power', type: 'new-number-only', title: 'Power / card', dataKey: 'powerData', unit: 'W', gridSpan: { columns: 1, rows: 1 }, unitDisplay: 'in-title' }
  ])

  const getAPIBaseURL = () => window.location.origin
  const getWebSocketURL = () => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    return `${protocol}//${window.location.host}/updates`
  }

  const { lastJsonMessage, readyState, sendJsonMessage } = useWebSocket(getWebSocketURL(), { shouldReconnect: () => true })

  // Fetch model info on mount
  useEffect(() => {
    const fetchModelInfo = async () => {
      try {
        const response = await fetch(`${getAPIBaseURL()}/api/model_info`)
        if (response.ok) {
          const data = await response.json()
          setModelName(data.model_id || "Unknown")
        }
      } catch (error) {
        console.error("Failed to fetch model info:", error)
      }
    }
    fetchModelInfo()
  }, [])

  const handleSendMessage = useCallback((message, addToSuggestions = true) => {
    if (readyState !== SOCKET_OPEN) {
      return
    }

    sendJsonMessage({ action: "SEND_MESSAGE", message })

    // Add to suggestions if it's a new user input and not already in the list
    if (addToSuggestions && !suggestedPrompts.includes(message)) {
      setSuggestedPrompts(prev => [...prev, message])
    }
  }, [readyState, sendJsonMessage, suggestedPrompts])

  const removeSuggestion = useCallback((index) => {
    setSuggestedPrompts(prev => prev.filter((_, i) => i !== index))
    // Reset current index if we removed the current or earlier prompt
    if (index <= currentPromptIndex) {
      setCurrentPromptIndex(0)
    }
  }, [currentPromptIndex])

  // Continuous prompting effect - send next prompt when previous is completed
  useEffect(() => {
    if (!continuousPrompting || waitingForCompletion || suggestedPrompts.length === 0 || readyState !== SOCKET_OPEN) return

    const timeout = setTimeout(() => {
      const prompt = suggestedPrompts[currentPromptIndex]
      // Start animation
      setAnimatingPrompt(prompt)

      // Animate typing the prompt into input
      let i = 0
      const typePrompt = () => {
        if (i <= prompt.length) {
          setInputValue(prompt.substring(0, i))
          i++
          setTimeout(typePrompt, 30) // Typing speed
        } else {
          // Send message after typing completes
          setTimeout(() => {
            handleSendMessage(prompt, false)
            setWaitingForCompletion(true)

            // Start list removal animation
            setRemovingPrompt(true)
            setTimeout(() => {
              setAnimatingPrompt(null)
              setRemovingPrompt(false)
            }, 500) // Animation duration

            setInputValue("")
          }, 300)
        }
      }
      typePrompt()
    }, 100)

    return () => clearTimeout(timeout)
  }, [continuousPrompting, currentPromptIndex, suggestedPrompts, handleSendMessage, readyState, waitingForCompletion])

  // Handle completion and move to next prompt
  useEffect(() => {
    if (!continuousPrompting || !waitingForCompletion) return

    // Check if there are any incomplete messages
    const hasIncompleteMessages = Object.values(messages).some(msg => !msg.completed && !msg.failed)

    if (!hasIncompleteMessages) {
      // All messages are complete, wait 5 seconds then move to next prompt
      const timeout = setTimeout(() => {
        setCurrentPromptIndex((prev) => (prev + 1) % suggestedPrompts.length)
        setWaitingForCompletion(false)
      }, 15000)

      return () => clearTimeout(timeout)
    }
  }, [messages, continuousPrompting, waitingForCompletion, suggestedPrompts.length])


  useEffect(() => {
    if (!lastJsonMessage) return
    const dataArray = Array.isArray(lastJsonMessage) ? lastJsonMessage : [lastJsonMessage]
    dataArray.forEach(handleWebSocketMessage)
  }, [lastJsonMessage])

  const handleWebSocketMessage = (data) => {
    switch (data.action) {
      case "INIT":
        setMessages({})
        break
      case "CREATE":
        setMessages((prev) => {
          if (!prev[data.request_id]) {
            return { ...prev, [data.request_id]: { request_id: data.request_id, chunks: [], reasoning_chunks: [], time: Date.now(), gi: globalIndex++, user_message: data.user_message } }
          }
          return prev
        })
        break
      case "UPDATE":
        setMessages((prev) => {
          const t = prev[data.request_id]
          if (!t) return prev

          // Handle reasoning chunks
          if (data.reasoning_chunk) {
            return { ...prev, [data.request_id]: { ...t, reasoning_chunks: [...(t.reasoning_chunks || []), data.reasoning_chunk] } }
          }
          // Handle regular chunks
          return { ...prev, [data.request_id]: { ...t, chunks: [...(t.chunks || []), data.chunk] } }
        })
        break
      case "COMPLETED":
        setMessages((prev) => {
          const t = prev[data.request_id]
          if (!t) return prev
          return { ...prev, [data.request_id]: { ...t, completed: true } }
        })
        break
      case "FAILED":
        setMessages((prev) => {
          const t = prev[data.request_id]
          if (!t) return prev
          return { ...prev, [data.request_id]: { ...t, failed: data.error } }
        })
        break
      case "INFO_UPDATE":
        updateInfo(data)
        break
      case "TIMING_UPDATE":
        updateTimingInfo(data)
        break
      default:
        break
    }
  }

  const updateInfo = (info) => {
    const powerValue = info.power ?? 0
    const temperatureValue = info.temperature ?? 0
    const tokensValue = info.tokens_per_sec ?? 0
    const memoryValue = info.memory_usage ?? 0
    const cpuValue = info.cpu_usage ?? 0
    const efficiencyValue = info.efficiency ?? 0

    setPower(`${powerValue} W`)
    setTemperature(`${temperatureValue} °C`)
    setTokensSec(`${tokensValue}`)
    setMemoryUsage(`${memoryValue} %`)
    setCpuUsage(`${cpuValue} %`)

    // Update max TPS if provided
    if (info.max_tps !== undefined) {
      setMaxTps(info.max_tps)
    }

    setPowerData((p) => {
      const next = [...p, powerValue]
      if (next.length > 20) next.shift()
      return next
    })
    setTemperatureData((p) => {
      const next = [...p, temperatureValue]
      if (next.length > 20) next.shift()
      return next
    })
    setTokensData((p) => {
      const next = [...p, tokensValue]
      if (next.length > 20) next.shift()
      return next
    })
    setMemoryData((p) => {
      const next = [...p, memoryValue]
      if (next.length > 20) next.shift()
      return next
    })
    setCpuData((p) => {
      const next = [...p, cpuValue]
      if (next.length > 20) next.shift()
      return next
    })
    setEfficiencyData((p) => {
      const next = [...p, efficiencyValue]
      if (next.length > 20) next.shift()
      return next
    })
  }

  const updateTimingInfo = (data) => {
    // Update TTFT data
    setTtftData((p) => {
      const next = [...p, data.ttft ?? 0]
      if (next.length > 20) next.shift()
      return next
    })

    // Update E2E data
    setE2eData((p) => {
      const next = [...p, data.e2e_latency ?? 0]
      if (next.length > 20) next.shift()
      return next
    })

    // Update TPOT data
    if (data.tpot !== undefined) {
      setTpotData((p) => {
        const next = [...p, data.tpot ?? 0]
        if (next.length > 20) next.shift()
        return next
      })
    }

    // Update message with token information if provided
    if (data.request_id && (data.tokens_prompt || data.tokens_reasoning || data.tokens_response || data.tokens_total)) {
      setMessages(prev => ({
        ...prev,
        [data.request_id]: {
          ...prev[data.request_id],
          tokens_prompt: data.tokens_prompt,
          tokens_reasoning: data.tokens_reasoning,
          tokens_response: data.tokens_response,
          tokens_total: data.tokens_total
        }
      }))
    }
  }

  const metricsData = {
    power: power,
    temperature: temperature,
    tokensSec: tokensSec,
    memoryUsage: memoryUsage,
    cpuUsage: cpuUsage,
    powerData: powerData,
    temperatureData: temperatureData,
    tokensData: tokensData,
    memoryData: memoryData,
    cpuData: cpuData,
    ttftData: ttftData,
    efficiencyData: efficiencyData,
    e2eData: e2eData,
    tpotData: tpotData,
    maxTps: maxTps  // Add max TPS to metrics data
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", position: "relative", width: "100%", overflow: "hidden" }}>
      <ControlPanel windowWidth={windowWidth} modelName={modelName} />
      <div style={{ flex: 1, display: "flex", overflow: "hidden", width: `${windowWidth}%`, margin: "0 auto", paddingBottom: "20px", gap: "10px" }}>
        {/* Left Column - Chat/Config */}
        <div style={{ flex: 2, overflow: "hidden", minWidth: 0, boxSizing: "border-box", paddingTop: "20px" }}>
          <ChatRenderer messages={messages} fontSize={chatFontSize} isRTL={isRTL} />
        </div>

        {/* Right Column - Metrics Dashboard */}
        <div style={{
          flex: 1,
          overflow: "hidden",
          boxSizing: "border-box",
          borderLeft: "1px solid #444",
          borderRight: "1px solid #444",
          direction: "ltr" // Metrics should always be LTR
        }}>
          <div style={{ padding: "10px" }}>
            <MetricsDashboard components={rightPanelComponents} metricsData={metricsData} gridColumns={gridColumns} />
          </div>
        </div>
      </div>

      {/* Bottom Input Area */}
      <div style={{
        background: '#000',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{
          width: `${windowWidth}%`,
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '20px 0 10px 0'
        }}>
        <div style={{
          position: 'relative',
          flex: 1
        }}>
          <input
            type="text"
            placeholder="Type your prompt here or enable Auto Prompt"
            value={continuousPrompting && (!animatingPrompt || removingPrompt) ? suggestedPrompts[currentPromptIndex] : inputValue}
            readOnly={animatingPrompt && continuousPrompting}
            onChange={(e) => !animatingPrompt && setInputValue(e.target.value)}
            onFocus={() => {
              setContinuousPrompting(false)
              setInputFocused(true)
            }}
            onBlur={() => setInputFocused(false)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && e.target.value.trim() && !animatingPrompt) {
                handleSendMessage(e.target.value.trim())
                setInputValue('')
              }
            }}
            style={{
              width: '100%',
              padding: '12px 90px 12px 12px', // Extra right padding for button
              background: '#000',
              border: '1px solid #fff',
              borderRadius: '8px',
              color: (() => {
                const hasIncompleteMessages = Object.values(messages).some(msg => !msg.completed && !msg.failed)

                if (hasIncompleteMessages && !inputFocused && !animatingPrompt) {
                  return '#8c8c8c'
                }
                return '#fff'
              })(),
              outline: 'none',
              fontSize: '1.3rem',
              //borderColor: continuousPrompting ? '#10b981' : '#fff',
              borderColor:'#fff',
              transition: 'border-color 0.3s ease, color 0.3s ease',
              boxSizing: 'border-box',
              direction: isRTL ? 'rtl' : 'ltr',
              textAlign: isRTL ? 'right' : 'left'
            }}
          />
          <button
            onClick={() => {
              if (continuousPrompting) {
                setContinuousPrompting(false)
                // Focus input when pausing continuous prompting
                setTimeout(() => document.querySelector('input').focus(), 100)
              } else {
                // Manual enter functionality
                const currentInput = document.querySelector('input').value;
                if (currentInput.trim()) {
                  handleSendMessage(currentInput.trim())
                  setInputValue('')
                }
              }
            }}
            style={{
              position: 'absolute',
              right: '8px',
              top: '50%',
              transform: 'translateY(-50%)',
              background: '#dc2626',
              color: '#fff',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '12px'
            }}
          >
            {continuousPrompting ? 'Pause' : 'Enter'}
          </button>
        </div>
        </div>
        <div style={{
          width: `${windowWidth}%`,
          padding: '0 0 10px 0'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start'
          }}>
            {/* Suggested Prompts - Left Side */}
            <div style={{
              paddingLeft: '12px'
            }}>
              {(() => {
                const startIndex = animatingPrompt ? currentPromptIndex : (currentPromptIndex + 1) % suggestedPrompts.length;
                return suggestedPrompts.slice(startIndex).concat(suggestedPrompts.slice(0, startIndex)).slice(0, 3).map((prompt, displayIndex) => {
                  const actualIndex = (startIndex + displayIndex) % suggestedPrompts.length;
                  const normalOpacity = 0.55 - (displayIndex * 0.15); // Gradation: 0.55, 0.4, 0.25

                  return (
                    <div
                    key={`${actualIndex}-${displayIndex}`}
                    style={{
                      fontSize: '14px',
                      marginBottom: '4px',
                      opacity: displayIndex === 0 && removingPrompt ? 0 : normalOpacity,
                      color: '#fff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      transform: removingPrompt ? 'translateY(-1.5rem)' : 'translateY(0)',
                      transition: removingPrompt ? (displayIndex === 0 ? 'transform 0.5s ease-out' : 'all 0.5s ease-out') : 'none'
                    }}
                  >
                    <span
                      style={{
                        cursor: continuousPrompting ? 'default' : 'pointer',
                        flex: 1
                      }}
                      onClick={!continuousPrompting ? () => handleSendMessage(prompt, false) : undefined}
                    >
                      {displayIndex === 0 && animatingPrompt ? prompt.substring(inputValue.length) : prompt}
                    </span>
                    <button
                      onClick={() => removeSuggestion(actualIndex)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#666',
                        cursor: 'pointer',
                        fontSize: '12px',
                        marginLeft: '8px',
                        padding: '2px 4px',
                        borderRadius: '2px'
                      }}
                      onMouseOver={(e) => e.target.style.color = '#fff'}
                      onMouseOut={(e) => e.target.style.color = '#666'}
                    >
                      ×
                    </button>
                  </div>
                  );
                });
              })()}
            </div>

            {/* Continuous prompting checkbox - Right Side */}
            <label
              htmlFor="continuous-prompting-checkbox"
              style={{
                display: 'flex',
                alignItems: 'center',
                color: '#fff',
                gap: '8px',
                cursor: 'pointer'
              }}>
              <input
                type="checkbox"
                checked={continuousPrompting}
                onChange={(e) => setContinuousPrompting(e.target.checked)}
                style={{ display: 'none' }}
                id="continuous-prompting-checkbox"
              />
              <div
                style={{
                  width: '16px',
                  height: '16px',
                  border: '1px solid #fff',
                  borderRadius: '3px',
                  background: '#000',
                  cursor: 'pointer',
                  position: 'relative',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundImage: continuousPrompting ? 'url("data:image/svg+xml,%3csvg width=\'12\' height=\'9\' viewBox=\'0 0 12 9\' fill=\'none\' xmlns=\'http://www.w3.org/2000/svg\'%3e%3cpath d=\'M1 4L4.5 7.5L11 1\' stroke=\'%23ffffff\' stroke-width=\'1.5\' stroke-linecap=\'round\' stroke-linejoin=\'round\'/%3e%3c/svg%3e")' : 'none',
                  backgroundRepeat: 'no-repeat',
                  backgroundPosition: 'center',
                  backgroundSize: '10px 8px',
                  userSelect: 'none'
                }}
              >
              </div>
              Auto Prompt
            </label>
          </div>
        </div>
      </div>

      {/* Settings Cog Button - Bottom Right */}
      <button
        onClick={() => setShowComponentSelector(!showComponentSelector)}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          background: '#1a1a1a',
          border: '1px solid #2a2a2a',
          color: '#444',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '16px',
          transition: 'all 0.3s ease',
          opacity: 0.3,
          zIndex: 1000
        }}
        onMouseEnter={(e) => {
          e.target.style.opacity = '0.6'
          e.target.style.color = '#666'
        }}
        onMouseLeave={(e) => {
          e.target.style.opacity = '0.3'
          e.target.style.color = '#444'
        }}
      >
        ⚙️
      </button>

      {/* Component Selector Panel */}
      {showComponentSelector && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '50%',
          height: '100vh',
          background: '#0a0a0a',
          border: '1px solid #222',
          zIndex: 2000,
          overflow: 'hidden'
        }}>
          <button
            onClick={() => setShowComponentSelector(false)}
            style={{
              position: 'absolute',
              top: '15px',
              right: '15px',
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              background: '#2a2a2a',
              border: 'none',
              color: '#666',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '14px',
              zIndex: 2001
            }}
          >
            ×
          </button>
          <ComponentSelector
            components={rightPanelComponents}
            setComponents={setRightPanelComponents}
            metricsData={metricsData}
            gridColumns={gridColumns}
            setGridColumns={setGridColumns}
            chatFontSize={chatFontSize}
            setChatFontSize={setChatFontSize}
            windowWidth={windowWidth}
            setWindowWidth={setWindowWidth}
            suggestedPrompts={suggestedPrompts}
            setSuggestedPrompts={setSuggestedPrompts}
            isRTL={isRTL}
            setIsRTL={setIsRTL}
          />
        </div>
      )}

    </div>
  )
}

function MetricsDashboard({ components, metricsData, gridColumns = 2 }) {
  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      gap: "10px",
      height: "100%",
      overflowY: "auto"
    }}>
      {components.map((component) => {
        // Determine height based on component type
        let containerHeight = 'auto';
        if (component.type === 'new-number-only') {
          containerHeight = '70px'; // Reduced height for number-only
        } else if (component.type === 'line-with-number') {
          containerHeight = '200px'; // Component height
        }

        return (
          <div
            key={component.id}
            style={{
              background: '#151515',
              border: '1px solid #444',
              borderRadius: '8px',
              padding: '15px',
              minWidth: 0,
              height: containerHeight
            }}
          >
            <MeterComponent
              component={component}
              metricsData={metricsData}
            />
          </div>
        )
      })}
    </div>
  )
}
