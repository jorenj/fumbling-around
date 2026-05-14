import { useState } from 'react'

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const runTournament = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/tournament', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          p1_type: 'random',
          p2_type: 'greedy',
          num_games: 1
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to run tournament');
      }
      
      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
      
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>Cribbage Engine</h1>
        <p>AI vs AI Tournament Runner</p>
      </header>

      <div className="controls">
        <button onClick={runTournament} disabled={loading}>
          {loading ? 'Running Simulation...' : 'Run Match (Random vs Greedy)'}
        </button>
      </div>

      {error && (
        <div className="glass-panel" style={{ borderColor: '#ef4444', marginBottom: '2rem' }}>
          <h3 style={{ color: '#ef4444', margin: 0 }}>Connection Error</h3>
          <p>{error}</p>
          <small>Make sure the FastAPI backend is running on port 8000.</small>
        </div>
      )}

      {result && (
        <>
          <div className="dashboard">
            <div className="glass-panel stat-card">
              <h3>Winner</h3>
              <div className="value" style={{ fontSize: '2.5rem' }}>{result.winner}</div>
              {result.skunk && <p style={{ color: '#f59e0b' }}>🏆 Skunk Victory!</p>}
            </div>
            
            <div className="glass-panel stat-card">
              <h3>Player 1 Score</h3>
              <div className="value">{result.final_score["Player 1"]}</div>
            </div>
            
            <div className="glass-panel stat-card">
              <h3>Player 2 Score</h3>
              <div className="value">{result.final_score["Player 2"]}</div>
            </div>
          </div>

          <div className="glass-panel">
            <h2>Detailed Game Log</h2>
            <div className="game-log">
              {result.log.map((entry, i) => (
                <div 
                  className="log-entry" 
                  key={i}
                  style={{ animationDelay: `${Math.min(i * 0.05, 1)}s` }}
                >
                  <div className="log-type">{entry.type.replace('_', ' ')}</div>
                  <div className="log-message">
                    <strong>{entry.player_id ? `${entry.player_id}: ` : ''}</strong>
                    {entry.message}
                  </div>
                  <div className="log-scores">
                    P1: {entry.p1_score} | P2: {entry.p2_score}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default App
