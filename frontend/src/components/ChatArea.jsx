import { useState, useRef, useEffect } from 'react'

const SUGGESTIONS = [
  'Which schools have the highest SAT math scores?',
  'Show me the top 10 schools by enrollment',
  'Find schools in Alameda with free meal eligibility > 50%',
  'List charter schools in San Francisco',
]

function SqlBlock({ sql }) {
  const [copied, setCopied] = useState(false)
  function copy() {
    navigator.clipboard.writeText(sql)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <div className="sql-block">
      <div className="sql-block-header">
        <span>Generated SQL</span>
        <button className="btn-copy" onClick={copy}>{copied ? '✓ Copied' : '⧉ Copy'}</button>
      </div>
      <pre>{sql}</pre>
    </div>
  )
}

function ResultTable({ columns, rows }) {
  const [page, setPage] = useState(0)
  const PAGE_SIZE = 10
  const totalPages = Math.ceil(rows.length / PAGE_SIZE)
  const visibleRows = rows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  return (
    <div className="result-table-wrap">
      <div className="result-table-header">
        <span className="result-table-title">📊 Query Results</span>
        <span className="result-table-badge">{rows.length} row{rows.length !== 1 ? 's' : ''}</span>
      </div>
      <div className="result-table-scroll">
        <table className="result-table">
          <thead>
            <tr>
              {columns.map(col => <th key={col}>{col}</th>)}
            </tr>
          </thead>
          <tbody>
            {visibleRows.map((row, ri) => (
              <tr key={ri}>
                {row.map((cell, ci) => (
                  <td key={ci}>{cell === null ? <span className="null-cell">NULL</span> : String(cell)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="result-table-pagination">
          <button className="btn-page" onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}>‹ Prev</button>
          <span className="page-info">Page {page + 1} of {totalPages}</span>
          <button className="btn-page" onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page === totalPages - 1}>Next ›</button>
        </div>
      )}
    </div>
  )
}

function Message({ msg }) {
  return (
    <div className={`message ${msg.role}`}>
      <div className="message-avatar">
        {msg.role === 'user' ? '👤' : '🤖'}
      </div>
      <div className="message-body">
        <div className="message-bubble">
          {msg.content}
          {msg.sql && <SqlBlock sql={msg.sql} />}
          {msg.columns?.length > 0 && msg.rows?.length > 0 && (
            <ResultTable columns={msg.columns} rows={msg.rows} />
          )}
        </div>
        <div className="message-time">{msg.time}</div>
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="message assistant">
      <div className="message-avatar">🤖</div>
      <div className="message-body">
        <div className="message-bubble">
          <div className="typing-indicator">
            <div className="typing-dot" />
            <div className="typing-dot" />
            <div className="typing-dot" />
          </div>
        </div>
      </div>
    </div>
  )
}

function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function ChatArea() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`
  }, [input])

  async function sendMessage(text) {
    if (!text.trim() || loading) return
    const userMsg = { role: 'user', content: text, time: now() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text }),
      })
      // Parse body as text first — guards against empty/non-JSON crash responses
      const raw = await res.text()
      let data = {}
      try { data = JSON.parse(raw) } catch { data = { detail: raw || 'Empty response from server' } }

      if (!res.ok) throw new Error(data.detail || `Server error ${res.status}`)

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer ?? 'Here is the SQL query I generated:',
          sql: data.sql ?? null,
          columns: data.columns ?? [],
          rows: data.rows ?? [],
          time: now(),
        },
      ])
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ Error: ${err.message}`,
          time: now(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const wsRef = useRef(null)

  async function toggleRecording() {
    if (isRecording) {
      // 1. Stop the microphone
      mediaRecorderRef.current?.stop()
      setIsRecording(false)

      // 2. Tell the backend we are done recording
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send("DONE")
        // Note: We DO NOT close the websocket here! We wait for the backend 
        // to send us the final SQL result before it closes the connection.
      }
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        const mediaRecorder = new MediaRecorder(stream)
        mediaRecorderRef.current = mediaRecorder

        // 1. Open the WebSocket connection
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        // In Vite, proxying websockets usually works on the same port, or we point to 5000 if not proxied
        const wsUrl = `${protocol}//${window.location.host}/api/ws-voice`
        const ws = new WebSocket(wsUrl)
        wsRef.current = ws

        ws.onopen = () => {
          mediaRecorder.start(250) // Emit chunks every 250ms
          setIsRecording(true)

          setMessages(prev => [
            ...prev,
            { role: 'user', content: '🎤 Listening...', time: now(), isLiveVoice: true }
          ])
        }

        ws.onmessage = (event) => {
          // This is triggered every time your backend runs `await websocket.send_text(...)`
          const incomingData = event.data

          try {
            // Check if backend sent the final JSON result containing SQL
            const data = JSON.parse(incomingData)
            if (data.sql !== undefined) {
              // It's the final CHESS SQL result!
              setMessages(prev => {
                const updated = [...prev]
                const lastMsg = updated[updated.length - 1]
                if (lastMsg && lastMsg.isLiveVoice) delete lastMsg.isLiveVoice // Remove typing effect
                return updated
              })

              setMessages(prev => [
                ...prev,
                {
                  role: 'assistant',
                  content: data.answer ?? 'Here is the SQL query I generated:',
                  sql: data.sql ?? null,
                  columns: data.columns ?? [],
                  rows: data.rows ?? [],
                  time: now(),
                },
              ])
              ws.close()
            }
          } catch (e) {
            // It's not JSON, so it must be a partial text transcript!
            // Update the live typing bubble with the transcript
            setMessages(prev => {
              const updated = [...prev]
              const lastMsg = updated[updated.length - 1]
              if (lastMsg && lastMsg.isLiveVoice) {
                lastMsg.content = `🎤 ${incomingData}`
              }
              return updated
            })
          }
        }

        ws.onerror = (err) => {
          console.error("WebSocket error", err)
          setMessages(prev => [
            ...prev,
            { role: 'assistant', content: `⚠️ WebSocket Error: Could not connect to voice streaming server.`, time: now() }
          ])
        }

        ws.onclose = () => {
          stream.getTracks().forEach(track => track.stop())
          setLoading(false)
        }

        mediaRecorder.ondataavailable = (event) => {
          // Send the raw audio binary chunk to the backend websocket
          if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
            ws.send(event.data)
          }
        }

      } catch (err) {
        console.error("Microphone error:", err)
        alert("Microphone access denied or not available.")
      }
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const isEmpty = messages.length === 0 && !loading

  return (
    <div className="chat-main">
      {/* Top bar */}
      <div className="chat-topbar">
        <div>
          <div className="chat-topbar-title">Query Interface</div>
          <div className="chat-topbar-sub">Ask anything about your database</div>
        </div>
        <span className="chat-topbar-badge">Step 2</span>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {isEmpty ? (
          <div className="chat-empty">
            <div className="chat-empty-icon">💬</div>
            <div className="chat-empty-title">Ask a question about your data</div>
            <div className="chat-empty-sub">
              Type any natural language question and CHESS SQL will generate the
              appropriate SQL query and return results.
            </div>
            <div className="chat-suggestions">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  className="suggestion-pill"
                  onClick={() => sendMessage(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => <Message key={i} msg={msg} />)
        )}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          <textarea
            id="chat-input"
            ref={textareaRef}
            className="chat-textarea"
            rows={1}
            placeholder="Ask a question about your database… (Shift+Enter for new line)"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <button
            id="btn-mic"
            className={`btn-mic ${isRecording ? 'recording' : ''}`}
            onClick={toggleRecording}
            disabled={loading}
            title={isRecording ? "Stop Recording" : "Record Voice"}
          >
            {isRecording ? '⏹' : '🎙️'}
          </button>
          <button
            id="btn-send"
            className="btn-send"
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || loading || isRecording}
            title="Send (Enter)"
          >
            ▲
          </button>
        </div>
        <div className="chat-input-hint">
          Enter to send · Shift+Enter for new line · CHESS SQL powered
        </div>
      </div>
    </div>
  )
}
