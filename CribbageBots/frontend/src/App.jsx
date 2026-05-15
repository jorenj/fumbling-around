import { useState, useRef, useEffect } from 'react'
import HumanInterface from './components/HumanInterface'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const HUMAN_OPTION = { value: 'human', label: 'Human (You)' }

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
  const [p1Type, setP1Type] = useState('human')
  const [p2Type, setP2Type] = useState('greedy')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [numGames, setNumGames] = useState(1)
  
  // Human mode states
  const [ws, setWs] = useState(null)
  const [gameLog, setGameLog] = useState([])
  const [humanState, setHumanState] = useState(null) // holds action requests like discard/peg
  const [humanGameResult, setHumanGameResult] = useState(null)
  const [p1Score, setP1Score] = useState(0)
  const [p2Score, setP2Score] = useState(0)
  const [isHumanMode, setIsHumanMode] = useState(false)

  const [botOptions, setBotOptions] = useState([HUMAN_OPTION])

  const logRef = useRef(null)

  useEffect(() => {
    fetch(`${API_BASE}/api/bots`)
      .then(res => res.json())
      .then(data => {
        const fetchedBots = data.bots || []
        setBotOptions([HUMAN_OPTION, ...fetchedBots])
        // If p2Type was hardcoded to something not yet loaded, or we want a default
        if (fetchedBots.length > 0 && p2Type === 'greedy') {
           // Keep greedy if it exists, otherwise pick first
           if (!fetchedBots.find(b => b.value === 'greedy')) {
             setP2Type(fetchedBots[0].value)
           }
        }
      })
      .catch(err => {
        console.error("Failed to fetch bots:", err)
        setError("Could not load bot options. Is the backend running?")
      })
  }, [])

  const p1Base = botOptions.find(b => b.value === p1Type)?.label ?? p1Type
  const p2Base = botOptions.find(b => b.value === p2Type)?.label ?? p2Type
  
  // Ensure unique IDs if both bots are the same type
  const p1Label = (p1Type === p2Type) ? `${p1Base} (P1)` : p1Base
  const p2Label = (p1Type === p2Type) ? `${p2Base} (P2)` : p2Base

  const runMatch = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    setGameLog([])
    setP1Score(0)
    setP2Score(0)
    setHumanState(null)
    setHumanGameResult(null)
    
    if (ws) {
      ws.close()
      setWs(null)
    }

    if (p1Type === 'human') {
      setIsHumanMode(true)
      const wsUrl = API_BASE.replace(/^http/, 'ws') + '/ws/human/' + p2Type
      const socket = new WebSocket(wsUrl)
      
      socket.onopen = () => setLoading(false)
      socket.onerror = () => {
        setError("WebSocket error")
        setLoading(false)
      }
      socket.onclose = () => {
        setLoading(false)
      }
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.action === "state_update") {
          setGameLog(prev => [...prev, data.event])
          if (data.event.p1_score !== undefined) setP1Score(data.event.p1_score)
          if (data.event.p2_score !== undefined) setP2Score(data.event.p2_score)
        } else if (data.action === "discard" || data.action === "peg") {
          setHumanState(data)
        } else if (data.action === "game_over") {
          setHumanState(null)
          setHumanGameResult(data)
        }
      }
      setWs(socket)
    } else if (parseInt(numGames, 10) > 1) {
      setIsHumanMode(false)
      const wsUrl = API_BASE.replace(/^http/, 'ws') + '/ws/tournament'
      const socket = new WebSocket(wsUrl)
      
      socket.onopen = () => {
        setLoading(true)
        socket.send(JSON.stringify({
          p1_type: p1Type,
          p2_type: p2Type,
          p1_id: p1Label,
          p2_id: p2Label,
          num_games: parseInt(numGames, 10) || 1,
        }))
      }
      
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.action === "progress" || data.action === "complete") {
          // Add empty games/log array to satisfy UI expectations for bulk results
          setResult({
            ...data,
            games: [],
            log: []
          })
          if (data.action === "complete") setLoading(false)
        } else if (data.error) {
          setError(data.error)
          setLoading(false)
        }
      }
      
      socket.onerror = () => {
        setError("WebSocket error during tournament")
        setLoading(false)
      }
    } else {
      setIsHumanMode(false)
      try {
        const res = await fetch(`${API_BASE}/api/tournament`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            p1_type: p1Type,
            p2_type: p2Type,
            p1_id: p1Label,
            p2_id: p2Label,
            num_games: parseInt(numGames, 10) || 1,
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
  }

  // Determine player scores from the response in a bot-ID-agnostic way
  const scoreEntries = (result && result.final_score) ? Object.entries(result.final_score) : []

  return (
    <main className="app-container">
      <header className="header">
        <h1>Cribbage Engine</h1>
        <p>Interactive Cribbage Platform</p>
      </header>

      <section aria-label="Match controls" className="controls">
        <label htmlFor="p1-select">Player 1</label>
        <select
          id="p1-select"
          value={p1Type}
          onChange={e => setP1Type(e.target.value)}
          disabled={loading}
        >
          {botOptions.map(b => (
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
          {botOptions.filter(b => b.value !== 'human').map(b => (
            <option key={b.value} value={b.value}>{b.label}</option>
          ))}
        </select>
        
        <label htmlFor="num-games">Games:</label>
        <input 
          id="num-games" 
          type="number" 
          min="1" 
          max="1000" 
          value={p1Type === 'human' || p2Type === 'human' ? 1 : numGames} 
          onChange={e => setNumGames(e.target.value)} 
          disabled={loading || p1Type === 'human' || p2Type === 'human'}
          style={{ width: '80px', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-subtle)', background: 'rgba(30, 41, 59, 0.8)', color: 'white' }}
        />

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

      {isHumanMode ? (
        <>
          {humanGameResult && (
            <div className="glass-panel winner-banner" style={{ margin: '1rem 0', textAlign: 'center', background: 'var(--accent-blue)', color: 'white' }}>
              <h2>🏆 Winner: {humanGameResult.winner}!</h2>
              {humanGameResult.reason && (
                <div style={{ opacity: 0.9, marginBottom: '0.5rem', fontWeight: 'bold' }}>
                  Reason: {humanGameResult.reason}
                </div>
              )}
              <button className="run-btn" onClick={runMatch} style={{ background: 'white', color: 'var(--accent-blue)', marginTop: '0.5rem' }}>Play Again</button>
            </div>
          )}
          <HumanInterface 
            ws={ws} 
            gameLog={gameLog} 
            humanState={humanState}
            p1Score={p1Score}
            p2Score={p2Score}
            setHumanState={setHumanState}
          />
        </>
      ) : result ? (
        <>
          {result?.games && result.games.length === 0 ? (
            <section aria-label="Bulk match results" className="glass-panel summary-section" style={{ marginTop: '2rem' }}>
              <h2>Tournament Summary Dashboard {loading && <Spinner />}</h2>
              {loading && result?.game && (
                <div style={{ textAlign: 'center', marginBottom: '1rem', color: 'var(--text-muted)', fontWeight: 'bold' }}>
                  Playing Game {result.game} / {result.total_games}...
                </div>
              )}
              <div style={{ display: 'flex', justifyContent: 'space-around', margin: '2rem 0' }}>
                <div style={{ textAlign: 'center' }}>
                  <h3 style={{ color: 'var(--accent-blue)' }}>{p1Label}</h3>
                  <div style={{ fontSize: '3rem', fontWeight: 'bold' }}>{result?.wins?.[p1Label] || 0} Wins</div>
                  <div>{result?.skunks?.[p1Label] || 0} Skunks</div>
                  <div style={{ marginTop: '1rem' }}>Total Points: {result?.total_score?.[p1Label] || 0}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', fontSize: '1.5rem', color: 'var(--text-muted)' }}>
                  VS
                </div>
                <div style={{ textAlign: 'center' }}>
                  <h3 style={{ color: 'var(--error-red)' }}>{p2Label}</h3>
                  <div style={{ fontSize: '3rem', fontWeight: 'bold' }}>{result?.wins?.[p2Label] || 0} Wins</div>
                  <div>{result?.skunks?.[p2Label] || 0} Skunks</div>
                  <div style={{ marginTop: '1rem' }}>Total Points: {result?.total_score?.[p2Label] || 0}</div>
                </div>
              </div>
              
              <div style={{ width: '100%', background: 'rgba(0,0,0,0.2)', height: '30px', borderRadius: '15px', overflow: 'hidden', display: 'flex' }}>
                {(() => {
                  const w1 = result?.wins?.[p1Label] || 0;
                  const w2 = result?.wins?.[p2Label] || 0;
                  const totalWins = w1 + w2;
                  const p1Pct = totalWins > 0 ? w1 / totalWins * 100 : 0;
                  const p2Pct = totalWins > 0 ? w2 / totalWins * 100 : 100 - p1Pct;
                  
                  return (
                    <>
                      <div style={{ width: `${p1Pct}%`, background: 'var(--accent-blue)', transition: 'width 1s', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '0.8rem', fontWeight: 'bold' }}>
                        {p1Pct.toFixed(1)}%
                      </div>
                      <div style={{ width: `${p2Pct}%`, background: 'var(--error-red)', transition: 'width 1s', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '0.8rem', fontWeight: 'bold' }}>
                        {p2Pct.toFixed(1)}%
                      </div>
                    </>
                  );
                })()}
              </div>

              {(() => {
                const w1 = result?.wins?.[p1Label] || 0;
                const w2 = result?.wins?.[p2Label] || 0;
                const totalWins = w1 + w2;
                if (totalWins < 10) return null;

                const n = totalWins;
                const k = Math.max(w1, w2);
                const p = 0.5;
                const z = (Math.abs(k - n * p) - 0.5) / Math.sqrt(n * p * (1 - p));
                
                // Safety check for NaN or Infinity
                if (!isFinite(z)) return null;

                const phi = 0.5 * (1 + Math.sign(z) * Math.sqrt(1 - Math.exp(-2 * z * z / Math.PI)));
                const pValue = 2 * (1 - phi);

                let sigLabel = "Not Significant";
                let sigColor = "rgba(255,255,255,0.2)";
                if (pValue < 0.01) {
                  sigLabel = "Highly Significant (p < 0.01)";
                  sigColor = "#10b981";
                } else if (pValue < 0.05) {
                  sigLabel = "Significant (p < 0.05)";
                  sigColor = "#34d399";
                } else if (pValue < 0.1) {
                  sigLabel = "Weakly Significant (p < 0.1)";
                  sigColor = "#fbbf24";
                }

                return (
                  <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
                    <div style={{ display: 'inline-block', padding: '0.4rem 1rem', borderRadius: '20px', background: sigColor, color: pValue < 0.1 ? 'white' : 'var(--text-muted)', fontWeight: 'bold', fontSize: '0.9rem' }}>
                      {sigLabel}
                    </div>
                    <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      p-value: {pValue.toFixed(4)} | z-score: {z.toFixed(2)}
                    </div>
                  </div>
                );
              })()}
            </section>
          ) : (
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
                    <LogEntry key={entry.id ?? i} entry={entry} index={i} />
                  ))}
                </div>
              </section>
            </>
          )}
        </>
      ) : null}
    </main>
  )
}
