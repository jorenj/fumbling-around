import { useState, useRef } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const BOT_OPTIONS = [
  { value: 'random', label: 'RandomBot' },
  { value: 'greedy', label: 'GreedyBot' },
]

const EVENT_COLORS = {
  score: 'score', peg_play: 'peg_play', peg_go: 'peg_go',
  discard: 'discard', deal: 'deal', cut: 'cut',
  forfeit: 'forfeit', game_over: 'game_over', game_start: 'game_start',
}

function Spinner() {
  return <span className="spinner" aria-hidden="true" />
}

function LogEntry({ entry, index }) {
  const typeClass = EVENT_COLORS[entry.type] || ''
  return (
    <div
      className="log-entry"
      style={{ animationDelay: `${Math.min(index * 0.025, 0.8)}s` }}
    >
      <div className={`log-type-badge ${typeClass}`}>
        {entry.type.replace(/_/g, ' ')}
      </div>
      <div className="log-message">
        {entry.player_id && <strong>{entry.player_id}: </strong>}
        {entry.message}
      </div>
      <div className="log-scores" aria-label={`Scores: ${entry.p1_score} to ${entry.p2_score}`}>
        {entry.p1_score} – {entry.p2_score}
      </div>
    </div>
  )
}

export default function App() {
  const [p1Type, setP1Type] = useState('random')
  const [p2Type, setP2Type] = useState('greedy')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const logRef = useRef(null)

  const p1Label = BOT_OPTIONS.find(b => b.value === p1Type)?.label ?? p1Type
  const p2Label = BOT_OPTIONS.find(b => b.value === p2Type)?.label ?? p2Type

  const runMatch = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await fetch(`${API_BASE}/api/tournament`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          p1_type: p1Type,
          p2_type: p2Type,
          p1_id: p1Label,
          p2_id: p2Label,
          num_games: 1,
        }),
      })

      if (!res.ok) {
        const text = await res.text()
        throw new Error(`Server error ${res.status}: ${text}`)
      }

      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setResult(data)

      // Scroll log into view after render
      setTimeout(() => logRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Determine player scores from the response in a bot-ID-agnostic way
  const scoreEntries = result ? Object.entries(result.final_score) : []

  return (
    <main className="app-container">
      <header className="header">
        <h1>Cribbage Engine</h1>
        <p>AI vs AI Tournament Runner</p>
      </header>

      <section aria-label="Match controls" className="controls">
        <label htmlFor="p1-select">Player 1</label>
        <select
          id="p1-select"
          value={p1Type}
          onChange={e => setP1Type(e.target.value)}
          disabled={loading}
        >
          {BOT_OPTIONS.map(b => (
            <option key={b.value} value={b.value}>{b.label}</option>
          ))}
        </select>

        <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>vs</span>

        <label htmlFor="p2-select">Player 2</label>
        <select
          id="p2-select"
          value={p2Type}
          onChange={e => setP2Type(e.target.value)}
          disabled={loading}
        >
          {BOT_OPTIONS.map(b => (
            <option key={b.value} value={b.value}>{b.label}</option>
          ))}
        </select>

        <button
          id="run-match-btn"
          className="run-btn"
          onClick={runMatch}
          disabled={loading}
          aria-label={loading ? 'Running match, please wait' : 'Run match'}
        >
          {loading ? <><Spinner /> Running…</> : '▶ Run Match'}
        </button>
      </section>

      {error && (
        <div className="glass-panel error-banner" role="alert">
          <h3>Error</h3>
          <p>{error}</p>
          <small>Make sure the FastAPI backend is running at <code>{API_BASE}</code></small>
        </div>
      )}

      {result && (
        <>
          <section aria-label="Match results">
            <div className="dashboard">
              <div className="glass-panel stat-card">
                <h3>Winner</h3>
                <div className="value winner-value">{result.winner}</div>
                {result.skunk && (
                  <div className="skunk-badge">🦨 Skunk!</div>
                )}
              </div>

              {scoreEntries.map(([pid, pts]) => (
                <div className="glass-panel stat-card" key={pid}>
                  <h3>{pid}</h3>
                  <div className="value">{pts}</div>
                </div>
              ))}
            </div>
          </section>

          <section aria-label="Game log" ref={logRef} className="glass-panel log-section">
            <h2>
              Game Log{' '}
              <span className="log-count">({result.log.length} events)</span>
            </h2>
            <div className="game-log" role="log" aria-live="polite">
              {result.log.map((entry, i) => (
                <LogEntry key={i} entry={entry} index={i} />
              ))}
            </div>
          </section>
        </>
      )}
    </main>
  )
}
