import { useMemo, useState, useEffect } from 'react';

const TOTAL_HOLES = 121;

const getHoleCoords = (index, playerIdx) => {
  const startX = 80;
  const spacingX = 15;
  const yTop = 40;
  const yMid = 100;
  const yBot = 160;
  const offset = playerIdx === 0 ? -6 : 6;

  // Starter holes outside the main track
  if (index === -1) return { x: startX - 35, y: yTop + offset };
  if (index === -2) return { x: startX - 55, y: yTop + offset };

  // Single final pip at the very end
  if (index === 119) {
    return { x: startX + 34 * spacingX + 30, y: yMid };
  }
  
  if (index < 35) {
    return { x: startX + index * spacingX, y: yTop + offset };
  } 
  
  if (index < 45) {
    const t = (index - 34) / 11;
    const angle = -Math.PI / 2 + t * Math.PI;
    const radius = (yBot - yTop) / 2;
    const cx = startX + 34 * spacingX;
    const cy = (yTop + yBot) / 2;
    return { 
      x: cx + Math.cos(angle) * (radius + offset), 
      y: cy + Math.sin(angle) * (radius + offset) 
    };
  } 
  
  if (index < 80) {
    return { x: startX + 34 * spacingX - (index - 45) * spacingX, y: yBot - offset };
  } 
  
  if (index < 85) {
    const t = (index - 79) / 6;
    const angle = Math.PI / 2 + t * Math.PI;
    const radius = (yBot - yMid) / 2;
    const cx = startX;
    const cy = (yBot + yMid) / 2;
    return { 
      x: cx + Math.cos(angle) * (radius - offset), 
      y: cy + Math.sin(angle) * (radius - offset) 
    };
  } 
  
  return { x: startX + (index - 85) * spacingX, y: yMid + offset };
};

const getDividerLine = (index) => {
  const startX = 80;
  const spacingX = 15;
  const yTop = 40;
  const yMid = 100;
  const yBot = 160;
  const hLen = 15;

  if (index < 35) {
    const x = startX + index * spacingX + 7.5;
    return { x1: x, y1: yTop - hLen, x2: x, y2: yTop + hLen };
  }
  if (index < 44) {
    const t = (index - 34) / 11;
    const angle = -Math.PI / 2 + t * Math.PI + (Math.PI / 22);
    const radius = (yBot - yTop) / 2;
    const cx = startX + 34 * spacingX;
    const cy = (yTop + yBot) / 2;
    return {
      x1: cx + Math.cos(angle) * (radius - hLen),
      y1: cy + Math.sin(angle) * (radius - hLen),
      x2: cx + Math.cos(angle) * (radius + hLen),
      y2: cy + Math.sin(angle) * (radius + hLen)
    };
  }
  if (index < 80) {
    const x = index === 44 ? startX + 34 * spacingX + 7.5 : startX + 34 * spacingX - (index - 45) * spacingX - 7.5;
    return { x1: x, y1: yBot - hLen, x2: x, y2: yBot + hLen };
  }
  if (index < 84) {
    const t = (index - 79) / 6;
    const angle = Math.PI / 2 + t * Math.PI + (Math.PI / 12);
    const radius = (yBot - yMid) / 2;
    const cx = startX;
    const cy = (yBot + yMid) / 2;
    return {
      x1: cx + Math.cos(angle) * (radius - hLen),
      y1: cy + Math.sin(angle) * (radius - hLen),
      x2: cx + Math.cos(angle) * (radius + hLen),
      y2: cy + Math.sin(angle) * (radius + hLen)
    };
  }
  const x = index === 84 ? startX - 7.5 : startX + (index - 85) * spacingX + 7.5;
  return { x1: x, y1: yMid - hLen, x2: x, y2: yMid + hLen };
};

export default function Pegboard({ p1Score, p2Score }) {
  // Each player has two persistent pegs (a and b). lastMoved tracks which is the "front" peg.
  const [p1Pegs, setP1Pegs] = useState({ a: -2, b: -1, front: 'b' });
  const [p2Pegs, setP2Pegs] = useState({ a: -2, b: -1, front: 'b' });

  useEffect(() => {
    if (p1Score === 0) {
      setP1Pegs({ a: -2, b: -1, front: 'b' });
    } else {
      const newIdx = Math.min(p1Score - 1, 119);
      if (p1Pegs.front === 'b' && p1Pegs.b !== newIdx) {
        setP1Pegs({ ...p1Pegs, a: newIdx, front: 'a' });
      } else if (p1Pegs.front === 'a' && p1Pegs.a !== newIdx) {
        setP1Pegs({ ...p1Pegs, b: newIdx, front: 'b' });
      }
    }
  }, [p1Score]);

  useEffect(() => {
    if (p2Score === 0) {
      setP2Pegs({ a: -2, b: -1, front: 'b' });
    } else {
      const newIdx = Math.min(p2Score - 1, 119);
      if (p2Pegs.front === 'b' && p2Pegs.b !== newIdx) {
        setP2Pegs({ ...p2Pegs, a: newIdx, front: 'a' });
      } else if (p2Pegs.front === 'a' && p2Pegs.a !== newIdx) {
        setP2Pegs({ ...p2Pegs, b: newIdx, front: 'b' });
      }
    }
  }, [p2Score]);

  const holes = useMemo(() => {
    const h = [];
    h.push({ i: -1, p1: getHoleCoords(-1, 0), p2: getHoleCoords(-1, 1) });
    h.push({ i: -2, p1: getHoleCoords(-2, 0), p2: getHoleCoords(-2, 1) });
    for (let i = 0; i < 119; i++) {
      h.push({ i, p1: getHoleCoords(i, 0), p2: getHoleCoords(i, 1) });
    }
    h.push({ i: 119, finish: getHoleCoords(119, 0) });
    return h;
  }, []);

  const dividers = useMemo(() => {
    const d = [];
    for (let i = 4; i < 119; i += 5) {
      d.push(getDividerLine(i));
    }
    return d;
  }, []);

  const renderPeg = (index, playerIdx, isFront) => {
    const pos = getHoleCoords(index, playerIdx);
    const color = playerIdx === 0 ? 'var(--accent-blue)' : '#ef4444';
    return (
      <g 
        key={`${playerIdx}-${isFront ? 'front' : 'rear'}`}
        style={{ transition: 'transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)' }} 
        transform={`translate(${pos.x}, ${pos.y})`}
      >
        <circle r={isFront ? "6" : "4.5"} fill={color} opacity={isFront ? 1 : 0.6} filter="drop-shadow(0 2px 4px rgba(0,0,0,0.5))" />
        <circle r="1.5" fill="white" opacity="0.4" />
      </g>
    );
  };

  return (
    <div className="pegboard-container glass-panel" style={{ padding: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem', color: 'var(--text-primary)' }}>
        <div style={{ color: 'var(--accent-blue)', fontWeight: 'bold' }}>P1: {p1Score}</div>
        <div style={{ fontWeight: 'bold', letterSpacing: '2px', opacity: 0.5 }}>CRIBBAGE BOARD</div>
        <div style={{ color: '#ef4444', fontWeight: 'bold' }}>P2: {p2Score}</div>
      </div>
      
      <div className="pegboard-svg-wrapper" style={{ overflowX: 'auto', background: 'rgba(15, 23, 42, 0.5)', borderRadius: '12px', padding: '1rem' }}>
        <svg width="720" height="200" viewBox="0 0 720 200">
          <path 
            d="M 80 40 L 590 40 A 60 60 0 0 1 590 160 L 80 160 A 30 30 0 0 1 80 100 L 620 100" 
            fill="none" 
            stroke="rgba(255,255,255,0.03)" 
            strokeWidth="52" 
            strokeLinecap="round" 
          />
          {dividers.map((d, idx) => (
            <line key={idx} {...d} stroke="rgba(255,255,255,0.15)" strokeWidth="1.5" />
          ))}
          {holes.map((h) => (
            h.finish ? (
              <circle key="finish" cx={h.finish.x} cy={h.finish.y} r="3.5" fill="rgba(255,255,255,0.3)" />
            ) : (
              <g key={h.i}>
                <circle cx={h.p1.x} cy={h.p1.y} r="2.5" fill="rgba(255,255,255,0.12)" />
                <circle cx={h.p2.x} cy={h.p2.y} r="2.5" fill="rgba(255,255,255,0.12)" />
              </g>
            )
          ))}
          {renderPeg(p1Pegs.a, 0, p1Pegs.front === 'a')}
          {renderPeg(p1Pegs.b, 0, p1Pegs.front === 'b')}
          {renderPeg(p2Pegs.a, 1, p2Pegs.front === 'a')}
          {renderPeg(p2Pegs.b, 1, p2Pegs.front === 'b')}
        </svg>
      </div>
    </div>
  );
}
