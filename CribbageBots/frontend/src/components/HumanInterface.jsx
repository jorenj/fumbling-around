import { useState, useEffect, useMemo } from 'react';
import Pegboard from './Pegboard';

const getCardValue = (cardStr) => {
  const rank = cardStr.slice(0, -1);
  if (['J', 'Q', 'K'].includes(rank)) return 10;
  if (rank === 'A') return 1;
  return parseInt(rank, 10);
};

const getNumericRank = (cardStr) => {
  const rank = cardStr.slice(0, -1);
  const map = { 'A': 1, 'J': 11, 'Q': 12, 'K': 13 };
  return map[rank] || parseInt(rank, 10);
};

const getSuitInfo = (cardStr) => {
  const suit = cardStr.slice(-1);
  const symbols = { 'H': '♥', 'D': '♦', 'C': '♣', 'S': '♠' };
  const color = (suit === 'H' || suit === 'D') ? '#ef4444' : '#1e293b';
  return { symbol: symbols[suit] || suit, color };
};

function Card({ cardStr, isSelected, onClick, disabled, mini, style, isFelt }) {
  const { symbol, color } = getSuitInfo(cardStr);
  const rank = cardStr.slice(0, -1);
  
  const cardStyle = {
    padding: '0.2rem',
    border: isSelected ? '2px solid var(--accent-blue)' : '1px solid var(--border-subtle)',
    // Felt cards should look vibrant even if disabled
    background: (disabled && !isFelt) ? '#f1f5f9' : 'white',
    color: (disabled && !isFelt) ? '#94a3b8' : color,
    borderRadius: '6px',
    cursor: (disabled || isFelt) ? 'default' : 'pointer',
    fontSize: mini ? '0.8rem' : '1.1rem',
    fontWeight: 'bold',
    minWidth: mini ? '45px' : '65px',
    height: mini ? '65px' : '95px',
    boxShadow: isSelected ? '0 0 10px rgba(59, 130, 246, 0.5)' : '0 2px 4px rgba(0,0,0,0.1)',
    display: 'flex',
    flexDirection: 'column',
    position: 'relative',
    transition: 'transform 0.2s, box-shadow 0.2s',
    ...style
  };

  return (
    <div onClick={(!disabled && !isFelt) ? onClick : undefined} className={`card-btn ${isSelected ? 'selected' : ''}`} style={cardStyle}>
      <div style={{ position: 'absolute', top: '2px', left: '4px', textAlign: 'center', lineHeight: 1 }}>
        <div>{rank}</div>
        <div style={{ fontSize: mini ? '0.7rem' : '0.9rem' }}>{symbol}</div>
      </div>
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: mini ? '1.5rem' : '2.2rem', marginTop: '5px' }}>
        {symbol}
      </div>
      <div style={{ position: 'absolute', bottom: '2px', right: '4px', textAlign: 'center', transform: 'rotate(180deg)', lineHeight: 1 }}>
        <div>{rank}</div>
        <div style={{ fontSize: mini ? '0.7rem' : '0.9rem' }}>{symbol}</div>
      </div>
    </div>
  );
}

export default function HumanInterface({ ws, gameLog, humanState, p1Score, p2Score, setHumanState }) {
  const [selectedCards, setSelectedCards] = useState([]);
  const [orderedHand, setOrderedHand] = useState([]);
  const [draggedIdx, setDraggedIdx] = useState(null);

  const latestEvent = gameLog[gameLog.length - 1];
  const phase = latestEvent?.phase;
  // Only show cut card if we are in CUT, PEGGING, or COUNTING phases
  const cutCard = (phase !== 'DEAL' && phase !== 'DISCARD') ? latestEvent?.cut_card : null;
  const peggedCards = latestEvent?.pegged_cards || [];
  const dealerId = latestEvent?.dealer_id || "Player 1";
  
  const currentCount = humanState?.current_count ?? latestEvent?.current_count ?? 0;

  const isCountingPhase = latestEvent?.type === 'count_hand_request';
  const countingHand = latestEvent?.data?.hand || [];
  const countingPlayer = latestEvent?.player_id;
  const isCrib = latestEvent?.data?.is_crib;

  const p1Pegged = useMemo(() => peggedCards.filter(p => p.player_id === "Player 1"), [peggedCards]);
  const p2Pegged = useMemo(() => peggedCards.filter(p => p.player_id !== "Player 1"), [peggedCards]);

  useEffect(() => {
    if (humanState?.hand) {
      const currentHandSet = new Set(humanState.hand);
      if (humanState.hand.length === 6 && humanState.action === 'discard') {
         const sorted = [...humanState.hand].sort((a, b) => getNumericRank(a) - getNumericRank(b));
         setOrderedHand(sorted);
         return;
      }
      const newOrder = orderedHand.filter(c => currentHandSet.has(c));
      const existingCardsSet = new Set(newOrder);
      humanState.hand.forEach(c => {
        if (!existingCardsSet.has(c)) newOrder.push(c);
      });
      setOrderedHand(newOrder);
    }
  }, [humanState?.hand]);

  useEffect(() => {
    if (latestEvent?.type === 'game_start') setOrderedHand([]);
  }, [latestEvent?.type]);

  useEffect(() => {
    setSelectedCards([]);
  }, [humanState]);

  const toggleCardSelection = (cardStr) => {
    if (humanState?.action === 'discard') {
      if (selectedCards.includes(cardStr)) {
        setSelectedCards(selectedCards.filter(c => c !== cardStr));
      } else if (selectedCards.length < 2) {
        setSelectedCards([...selectedCards, cardStr]);
      }
    } else if (humanState?.action === 'peg') {
      const val = getCardValue(cardStr);
      if (currentCount + val <= 31) {
        setSelectedCards([cardStr]);
      }
    }
  };

  const handleDragStart = (e, index) => {
    setDraggedIdx(index);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    if (draggedIdx === null || draggedIdx === index) return;
    const newOrder = [...orderedHand];
    const draggedItem = newOrder[draggedIdx];
    newOrder.splice(draggedIdx, 1);
    newOrder.splice(index, 0, draggedItem);
    setDraggedIdx(index);
    setOrderedHand(newOrder);
  };

  const handleDragEnd = () => setDraggedIdx(null);

  const handleDiscard = () => {
    if (selectedCards.length === 2 && ws) {
      ws.send(JSON.stringify({ cards: selectedCards }));
      // Optimistic UI: remove from hand immediately
      setOrderedHand(prev => prev.filter(c => !selectedCards.includes(c)));
      setHumanState(null);
    }
  };

  const handlePeg = () => {
    if (selectedCards.length === 1 && ws) {
      ws.send(JSON.stringify({ card: selectedCards[0] }));
      // Optimistic UI: remove from hand immediately
      setOrderedHand(prev => prev.filter(c => c !== selectedCards[0]));
      setHumanState(null);
    }
  };

  const handleGo = () => {
    if (ws) {
      ws.send(JSON.stringify({ card: null }));
      setHumanState(null);
    }
  };

  const handleResumeCount = () => {
    if (ws) {
      ws.send(JSON.stringify({ action: 'resume_count' }));
    }
  };

  const hasLegalMoves = humanState?.action === 'peg' && 
    humanState.hand?.some(card => currentCount + getCardValue(card) <= 31);

  return (
    <div className="human-interface" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <Pegboard p1Score={p1Score} p2Score={p2Score} />

      <div className="table-area glass-panel" style={{ 
        height: '340px', 
        background: 'radial-gradient(circle, #065f46 0%, #064e3b 100%)', 
        borderRadius: '24px', 
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '1rem',
        border: '8px solid #3d2b1f',
        boxShadow: 'inset 0 0 50px rgba(0,0,0,0.5), 0 10px 25px rgba(0,0,0,0.3)'
      }}>
        {/* Dealer / Crib Indicator */}
        <div style={{ position: 'absolute', top: '1.5rem', left: '2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
           <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#fbbf24', boxShadow: '0 0 8px #fbbf24' }} />
           <div style={{ color: 'white', fontWeight: 'bold', fontSize: '0.9rem', opacity: 0.9 }}>
             DEALER: {dealerId === "Player 1" ? "YOU" : "BOT"}
           </div>
        </div>

        {/* Cut Card */}
        <div style={{ position: 'absolute', left: '2rem', top: '50%', transform: 'translateY(-50%)', textAlign: 'center' }}>
          <div style={{ color: 'white', opacity: 0.6, fontSize: '0.8rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>CUT</div>
          {cutCard ? (
            <Card cardStr={cutCard} isFelt />
          ) : (
            <div style={{ width: '65px', height: '95px', border: '2px dashed rgba(255,255,255,0.2)', borderRadius: '8px' }} />
          )}
        </div>

        {isCountingPhase ? (
          <div style={{ textAlign: 'center', zIndex: 10 }}>
            <h2 style={{ color: 'white', marginBottom: '0.2rem', textShadow: '0 2px 4px rgba(0,0,0,0.5)' }}>
              {countingPlayer === "Player 1" ? "Your" : "Bot's"} {isCrib ? 'Crib' : 'Hand'}: {latestEvent.data.points} Points
            </h2>
            <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.9rem', fontStyle: 'italic', marginBottom: '1rem' }}>
              {latestEvent.data.breakdown}
            </div>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '1.5rem' }}>
              {countingHand.map((c, i) => (
                <Card key={i} cardStr={c} isFelt />
              ))}
            </div>
            <button onClick={handleResumeCount} className="run-btn" style={{ background: 'white', color: '#064e3b', fontSize: '1.2rem', padding: '0.8rem 2rem' }}>
              Submit Points
            </button>
          </div>
        ) : (
          <>
            <div style={{ 
              background: 'rgba(0,0,0,0.4)', 
              padding: '0.5rem 1.5rem', 
              borderRadius: '20px', 
              color: 'white', 
              fontWeight: 'bold', 
              fontSize: '1.5rem',
              marginBottom: '1rem',
              border: '1px solid rgba(255,255,255,0.1)'
            }}>
              {currentCount} / 31
            </div>

            <div style={{ display: 'flex', gap: '8rem', width: '100%', justifyContent: 'center' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{ color: 'white', opacity: 0.6, fontSize: '0.8rem', marginBottom: '0.5rem' }}>BOT (P2)</div>
                <div style={{ position: 'relative', width: '100px', height: '100px' }}>
                  {p2Pegged.map((p, i) => (
                    <Card key={`p2-${i}`} cardStr={p.card} mini isFelt style={{ position: 'absolute', left: `${i * 15}px`, top: `${i * 5}px`, zIndex: i, transform: `rotate(${i * 3 - 5}deg)` }} />
                  ))}
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{ color: 'white', opacity: 0.6, fontSize: '0.8rem', marginBottom: '0.5rem' }}>YOU (P1)</div>
                <div style={{ position: 'relative', width: '100px', height: '100px' }}>
                  {p1Pegged.map((p, i) => (
                    <Card key={`p1-${i}`} cardStr={p.card} mini isFelt style={{ position: 'absolute', left: `${i * 15}px`, top: `${i * 5}px`, zIndex: i, transform: `rotate(${i * 3 - 5}deg)` }} />
                  ))}
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      <div className="game-status glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <h4 style={{ margin: '0 0 0.5rem 0', opacity: 0.7 }}>YOUR HAND</h4>
            <div className="hand-view" style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {orderedHand.length > 0 ? orderedHand.map((cardStr, idx) => {
                const isSelected = selectedCards.includes(cardStr);
                const val = getCardValue(cardStr);
                const isPlayable = !humanState || humanState.action !== 'peg' || (currentCount + val <= 31);
                return (
                  <div key={cardStr} draggable onDragStart={(e) => handleDragStart(e, idx)} onDragOver={(e) => handleDragOver(e, idx)} onDragEnd={handleDragEnd} style={{ opacity: draggedIdx === idx ? 0.5 : 1 }}>
                    <Card cardStr={cardStr} isSelected={isSelected} onClick={() => toggleCardSelection(cardStr)} disabled={!isPlayable} />
                  </div>
                );
              }) : <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>Dealing...</div>}
            </div>
          </div>

          {humanState && (
            <div className="action-controls" style={{ marginLeft: '2rem', textAlign: 'right' }}>
              <div style={{ color: 'var(--accent-blue)', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                {humanState.action.toUpperCase()}
              </div>
              <div className="action-buttons">
                {humanState.action === 'discard' && (
                  <button onClick={handleDiscard} disabled={selectedCards.length !== 2} className="run-btn">Discard 2</button>
                )}
                {humanState.action === 'peg' && (
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button onClick={handlePeg} disabled={selectedCards.length !== 1} className="run-btn">Play</button>
                    <button onClick={handleGo} disabled={hasLegalMoves} className="run-btn" style={{ background: hasLegalMoves ? '#64748b' : 'var(--error-red)' }}>Go</button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
