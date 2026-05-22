import { LOGISTICS_DATA, BRIEFING_TIMES } from '../lib/constants';
import { formatCountdown } from '../lib/utils';

export default function LogisticsTab({
  selectedRacerKey,
  onSelectedRacerChange,
  checklist,
  toggleChecklistItem,
  now
}) {
  return (
    <div>
      <div className="form-group">
        <label className="form-label">Show Schedule For:</label>
        <select 
          value={selectedRacerKey} 
          onChange={(e) => onSelectedRacerChange(e.target.value)}
          className="form-select"
        >
          {Object.keys(LOGISTICS_DATA).map(key => (
            <option key={key} value={key}>{LOGISTICS_DATA[key].name} ({LOGISTICS_DATA[key].leg})</option>
          ))}
        </select>
      </div>

      {/* Individual Schedule Card */}
      {LOGISTICS_DATA[selectedRacerKey] && (
        <div>
          <div className="card">
            <h3 className="section-title">📋 {LOGISTICS_DATA[selectedRacerKey].name}</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', margin: '0.5rem 0 1rem' }}>
              <div>
                <p className="subtext">Race Leg</p>
                <p style={{ fontWeight: '600', fontSize: '0.9rem' }}>{LOGISTICS_DATA[selectedRacerKey].leg}</p>
              </div>
              <div>
                <p className="subtext">Vehicle</p>
                <p style={{ fontWeight: '600', fontSize: '0.9rem' }}>{LOGISTICS_DATA[selectedRacerKey].car}</p>
              </div>
            </div>
            <div style={{ borderTop: '1px solid hsl(var(--border))', paddingTop: '0.75rem' }}>
              <p className="subtext">Leg Briefing</p>
              <p style={{ fontWeight: '500', color: '#06b6d4', fontSize: '0.85rem' }}>{LOGISTICS_DATA[selectedRacerKey].briefing}</p>
              
              {/* Briefing countdown */}
              {BRIEFING_TIMES[selectedRacerKey] && (() => {
                const remaining = formatCountdown(BRIEFING_TIMES[selectedRacerKey], now);
                if (!remaining) {
                  return <p style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '2px' }}>Briefing time has passed.</p>;
                }
                const msLeft = BRIEFING_TIMES[selectedRacerKey] - now;
                const urgency = msLeft < 3600000; // < 1 hr
                return (
                  <div style={{
                    marginTop: '8px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '8px',
                    background: urgency ? 'rgba(239,68,68,0.12)' : 'rgba(20,184,166,0.1)',
                    border: `1px solid ${urgency ? 'rgba(239,68,68,0.3)' : 'rgba(20,184,166,0.25)'}`,
                    borderRadius: '8px',
                    padding: '4px 10px',
                    fontSize: '0.82rem',
                    fontWeight: '600',
                    color: urgency ? '#ef4444' : '#14b8a6',
                    fontFamily: 'var(--font-title)'
                  }}>
                    {urgency ? '⚡' : '⏰'} {remaining}
                  </div>
                );
              })()}
            </div>
          </div>

          {/* Checklist Card */}
          <div className="card">
            <h3 className="section-title" style={{ marginBottom: '1rem' }}>✅ Transition Checklist</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {LOGISTICS_DATA[selectedRacerKey].tasks.map((task, idx) => {
                const isChecked = !!checklist[`${selectedRacerKey}_${idx}`];
                return (
                  <label 
                    key={idx} 
                    style={{ 
                      display: 'flex', 
                      gap: '12px', 
                      alignItems: 'flex-start', 
                      cursor: 'pointer',
                      color: isChecked ? 'hsl(var(--text-muted))' : 'hsl(var(--text-primary))',
                      textDecoration: isChecked ? 'line-through' : 'none',
                      fontSize: '0.9rem',
                      transition: 'var(--transition-fast)'
                    }}
                  >
                    <input 
                      type="checkbox" 
                      checked={isChecked}
                      onChange={() => toggleChecklistItem(selectedRacerKey, idx)}
                      style={{ 
                        marginTop: '3px',
                        width: '18px', 
                        height: '18px', 
                        accentColor: '#14b8a6'
                      }}
                    />
                    <span>{task}</span>
                  </label>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
