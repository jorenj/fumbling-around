import { useState } from 'react';
import { LEGS_CONFIG, JACKSONS_2025_SPLITS, RACE_START } from '../lib/constants';
import { getLegStatus, parseTimeToSeconds, formatDelta, getFallbackRacer, get2025LegStartTime } from '../lib/utils';
import ActiveLegCard from './ActiveLegCard';

export default function LeaderboardTab({
  teamsData,
  loadingResults,
  lastRefreshed,
  events,
  clearEvents,
  now,
  memberLocations,
  year,
  fetchResults
}) {
  return (
    <div>
      <div className="refresh-indicator">
        {loadingResults ? "Refreshing..." : lastRefreshed ? `Last sync: ${lastRefreshed.toLocaleTimeString()}` : ""}
        <button 
          onClick={fetchResults} 
          disabled={loadingResults}
          style={{ marginLeft: '10px', background: 'none', border: 'none', color: '#14b8a6', cursor: 'pointer', textDecoration: 'underline', fontSize: '0.75rem' }}
        >
          Sync Now
        </button>
      </div>

      {/* Recent Activity Notifications */}
      {events.length > 0 && (
        <div className="card" style={{
          background: 'linear-gradient(135deg, rgba(6,182,212,0.06) 0%, rgba(20,184,166,0.03) 100%)',
          borderColor: 'rgba(6,182,212,0.25)',
          padding: '0.65rem 0.85rem',
          marginBottom: '0.75rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <h4 style={{ margin: 0, fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#06b6d4', display: 'flex', alignItems: 'center', gap: '4px' }}>
              🔔 Recent Updates
            </h4>
            <button 
              onClick={clearEvents}
              style={{ background: 'none', border: 'none', color: 'hsl(var(--text-muted))', fontSize: '0.65rem', cursor: 'pointer', textDecoration: 'underline' }}
            >
              Clear
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {events.map(evt => (
              <div key={evt.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem', padding: '2px 0', borderBottom: '1px solid hsl(var(--border) / 0.15)' }}>
                <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginRight: '8px' }}>
                  <span style={{ fontWeight: '600', color: '#14b8a6' }}>{evt.teamName}</span>
                  <span style={{ color: 'hsl(var(--text-muted))' }}>: </span>
                  <span>{evt.legName}</span>
                  <span style={{ color: 'hsl(var(--text-muted))' }}> in </span>
                  <span style={{ fontFamily: 'var(--font-title)', fontWeight: '600' }}>{evt.split}</span>
                </div>
                <span style={{ fontSize: '0.65rem', color: 'hsl(var(--text-muted))', whiteSpace: 'nowrap' }}>
                  {new Date(evt.timestamp).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', second: '2-digit' })}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active Leg Card — 2026 only */}
      <ActiveLegCard
        teamsData={teamsData}
        now={now}
        memberLocations={memberLocations}
        year={year}
      />

      {/* Competitor standings comparative table */}
      <div className="card">
        <h3 className="section-title">🏁 Head-to-Head</h3>
        <div style={{ overflowX: 'auto', marginTop: '0.5rem' }}>
          <table className="results-table">
            <thead>
              <tr>
                <th>Bib</th>
                <th>Team Name</th>
                <th>Last Split</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {teamsData.map(t => {
                // Find last completed leg split for this team
                let lastLeg = 'Not Started';
                let lastTime = '—';
                for (let i = LEGS_CONFIG.length - 1; i >= 0; i--) {
                  const splitVal = t[LEGS_CONFIG[i].splitKey];
                  if (splitVal && splitVal !== "" && splitVal !== "0") {
                    lastLeg = LEGS_CONFIG[i].name;
                    lastTime = splitVal;
                    break;
                  }
                }
                
                return (
                  <tr key={t.bib} style={t.isMain ? { backgroundColor: 'rgba(20, 184, 166, 0.08)' } : {}}>
                    <td style={{ fontWeight: 'bold' }}>{t.bib}</td>
                    <td>
                      <div style={{ fontWeight: t.isMain ? 'bold' : 'normal', fontSize: '0.9rem' }}>
                        {t.name}
                      </div>
                      {t.TeamName && t.TeamName.toLowerCase() !== t.name.toLowerCase() && (
                        <div className="subtext" style={{ fontSize: '0.7rem', fontStyle: 'italic' }}>
                          {year} BIB: {t.TeamName}
                        </div>
                      )}
                      <div className="subtext" style={{ fontSize: '0.75rem' }}>
                        {t.Division || "Competitive"}
                      </div>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: '#06b6d4' }}>{lastLeg}</td>
                    <td>
                      <div style={{ fontFamily: 'var(--font-title)', fontWeight: 'bold', fontSize: '0.85rem' }}>{lastTime}</div>
                      {t.overallRank && (
                        <div style={{ fontSize: '0.68rem', marginTop: '2px', color: 'hsl(var(--text-muted))', whiteSpace: 'nowrap' }}>
                          Pos: {t.overallRank} / {t.totalTeams}
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Live Legs Progress list */}
      <div className="card">
        <h3 className="section-title">⏱️ Leg Split Times</h3>
        <div style={{ marginTop: '0.5rem' }}>
          {LEGS_CONFIG.map((leg, legIdx) => {
            const mainTeam = teamsData.find(t => t.isMain);
            const status = getLegStatus(mainTeam, legIdx, now, RACE_START);
            const racer = mainTeam ? mainTeam[leg.racerKey] : null;
            const time = mainTeam ? mainTeam[leg.splitKey] : null;
            const rank = mainTeam ? mainTeam[leg.rankKey] : null;
            
            const displayRacer = (racer && racer !== 0 && racer !== '0')
              ? racer
              : (!mainTeam ? getFallbackRacer(101, leg.id) : '');
            
            return (
              <div key={leg.id} className="leg-row">
                <div className="leg-meta">
                  <span className="leg-name">{leg.name}</span>
                  {displayRacer && <span className="leg-racer">{displayRacer}</span>}
                </div>
                <div className="leg-stats">
                  {status === 'finished' ? (
                    <div style={{ textAlign: 'right' }}>
                      <span className="leg-time">{time}</span>
                      {year !== '2025' && JACKSONS_2025_SPLITS[leg.id] && (
                        <div className="subtext" style={{ fontSize: '0.72rem', marginTop: '2px', textAlign: 'right' }}>
                          <div style={{ whiteSpace: 'nowrap' }}>
                            2025: {JACKSONS_2025_SPLITS[leg.id].time}
                            {(() => {
                              const s26 = parseTimeToSeconds(time);
                              const s25 = parseTimeToSeconds(JACKSONS_2025_SPLITS[leg.id].time);
                              if (s26 !== null && s25 !== null) {
                                const diff = s26 - s25;
                                const color = diff <= 0 ? '#14b8a6' : '#f59e0b';
                                return <span style={{ marginLeft: '4px', color, fontWeight: '600' }}>({formatDelta(diff)})</span>;
                              }
                              return null;
                            })()}
                          </div>
                          <div style={{ fontSize: '0.65rem', opacity: 0.8, marginTop: '1px', whiteSpace: 'nowrap' }}>
                            2025 Start: {get2025LegStartTime(leg.id).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
                          </div>
                        </div>
                      )}
                      <div className="leg-rank" style={{ fontSize: '0.75rem', marginTop: '2px' }}>Rank: {rank && rank !== -1 ? rank : "—"}</div>
                    </div>
                  ) : status === 'progress' ? (
                    <div style={{ textAlign: 'right' }}>
                      <span className="status-badge status-progress">Racing</span>
                      {year !== '2025' && JACKSONS_2025_SPLITS[leg.id] && (
                        <div className="subtext" style={{ fontSize: '0.72rem', marginTop: '4px', textAlign: 'right' }}>
                          <div style={{ whiteSpace: 'nowrap' }}>2025: {JACKSONS_2025_SPLITS[leg.id].time}</div>
                          <div style={{ fontSize: '0.65rem', opacity: 0.8, marginTop: '1px', whiteSpace: 'nowrap' }}>
                            2025 Start: {get2025LegStartTime(leg.id).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{ textAlign: 'right' }}>
                      <span className="status-badge status-todo">Waiting</span>
                      {year !== '2025' && JACKSONS_2025_SPLITS[leg.id] && (
                        <div className="subtext" style={{ fontSize: '0.72rem', marginTop: '4px', textAlign: 'right' }}>
                          <div style={{ whiteSpace: 'nowrap' }}>2025: {JACKSONS_2025_SPLITS[leg.id].time}</div>
                          <div style={{ fontSize: '0.65rem', opacity: 0.8, marginTop: '1px', whiteSpace: 'nowrap' }}>
                            2025 Start: {get2025LegStartTime(leg.id).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Competitor full leg breakdowns */}
      {teamsData.filter(t => !t.isMain).map(t => (
        <CompetitorSplits key={t.bib} team={t} year={year} />
      ))}
    </div>
  );
}

// Collapsible competitor split breakdown
function CompetitorSplits({ team, year }) {
  const [expanded, setExpanded] = useState(false);

  // Find last completed leg
  let lastLegName = 'Not Started';
  for (let i = LEGS_CONFIG.length - 1; i >= 0; i--) {
    const splitVal = team[LEGS_CONFIG[i].splitKey];
    if (splitVal && splitVal !== "" && splitVal !== "0") {
      lastLegName = LEGS_CONFIG[i].name;
      break;
    }
  }

  return (
    <div className="card" style={{ padding: '0' }}>
      {/* Collapsible Header */}
      <button
        onClick={() => setExpanded(e => !e)}
        style={{
          width: '100%',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: '1rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          color: 'hsl(var(--text-primary))',
          textAlign: 'left',
        }}
      >
        <div>
          <div style={{ fontFamily: 'var(--font-title)', fontWeight: '600', fontSize: '0.95rem' }}>
            BIB {team.bib} — {team.name}
          </div>
          {team.TeamName && team.TeamName.toLowerCase() !== team.name.toLowerCase() && (
            <div className="subtext" style={{ fontSize: '0.7rem', fontStyle: 'italic' }}>
              {year} BIB: {team.TeamName}
            </div>
          )}
          <div className="subtext" style={{ fontSize: '0.75rem', marginTop: '2px' }}>
            Last: {lastLegName}
          </div>
        </div>
        <span style={{ fontSize: '1.1rem', color: 'hsl(var(--text-muted))', transform: expanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s ease' }}>
          ▾
        </span>
      </button>

      {/* Expanded Split Table */}
      {expanded && (
        <div style={{ borderTop: '1px solid hsl(var(--border))', padding: '0 1.25rem 1rem' }}>
          {LEGS_CONFIG.map((leg) => {
            const splitVal = team[leg.splitKey];
            const rankVal = team[leg.rankKey];
            const racerVal = team[leg.racerKey];
            const hasTime = splitVal && splitVal !== "" && splitVal !== "0";

            return (
              <div key={leg.id} className="leg-row" style={{ paddingTop: '0.6rem', paddingBottom: '0.6rem' }}>
                <div className="leg-meta">
                  <span className="leg-name" style={{ fontSize: '0.85rem' }}>{leg.name}</span>
                  {racerVal && typeof racerVal === 'string' && racerVal !== '0' && (
                    <span className="leg-racer">{racerVal}</span>
                  )}
                </div>
                <div className="leg-stats">
                  {hasTime ? (
                    <>
                      <span className="leg-time" style={{ fontSize: '0.88rem' }}>{splitVal}</span>
                      <br />
                      <span className="leg-rank">
                        {rankVal && rankVal !== -1 ? `Rank: ${rankVal}` : ''}
                      </span>
                    </>
                  ) : (
                    <span style={{ color: 'hsl(var(--text-muted))', fontSize: '0.8rem' }}>—</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
