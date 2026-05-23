import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { 
  RACE_START, 
  LEGS_CONFIG, 
  LEG_RACER_MAP, 
  LEG_TRANSITIONS, 
  TRANSITIONS, 
  LOGISTICS_DATA, 
  JACKSONS_2025_SPLITS 
} from '../lib/constants';
import { getLegStatus, parseTimeToSeconds, formatCountdown } from '../lib/utils';

export default function ActiveLegCard({ teamsData, now, memberLocations, year }) {
  if (year !== '2026') return null;

  const mainTeam = teamsData.find(t => t.isMain);

  // Pre-race or loading: show countdown banner
  if (now < RACE_START) {
    const remaining = formatCountdown(RACE_START, now);
    const urgency = remaining && (RACE_START - now) < 3600000;
    return (
      <div style={{
        background: urgency
          ? 'linear-gradient(135deg, rgba(239,68,68,0.15) 0%, rgba(220,38,38,0.08) 100%)'
          : 'linear-gradient(135deg, rgba(20,184,166,0.12) 0%, rgba(6,182,212,0.06) 100%)',
        border: `1px solid ${urgency ? 'rgba(239,68,68,0.35)' : 'rgba(20,184,166,0.3)'}`,
        borderRadius: 'var(--radius)',
        padding: '0.75rem 1rem',
        marginBottom: '0.75rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem'
      }}>
        <div>
          <div style={{ fontSize: '0.7rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Race Start · May 25 · 7:30am PDT</div>
          <div style={{ fontSize: '1.1rem', fontWeight: '700', fontFamily: 'var(--font-title)', color: urgency ? '#ef4444' : '#14b8a6', marginTop: '2px' }}>
            🏁 {remaining || 'Starting soon…'}
          </div>
        </div>
        <div style={{ fontSize: '1.5rem' }}>{urgency ? '⚡' : '⏳'}</div>
      </div>
    );
  }

  if (!mainTeam || !mainTeam.success) {
    return (
      <div style={{
        background: 'linear-gradient(135deg, rgba(20,184,166,0.12) 0%, rgba(6,182,212,0.06) 100%)',
        border: '1px solid rgba(20,184,166,0.3)',
        borderRadius: 'var(--radius)',
        padding: '0.75rem 1rem',
        marginBottom: '0.75rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem'
      }}>
        <div>
          <div style={{ fontSize: '0.7rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Race Status</div>
          <div style={{ fontSize: '1.1rem', fontWeight: '700', fontFamily: 'var(--font-title)', color: '#14b8a6', marginTop: '2px' }}>
            🔄 Loading Race Results…
          </div>
        </div>
        <div style={{ fontSize: '1.5rem' }}>⏳</div>
      </div>
    );
  }

  // Find the active leg index
  let activeLegIdx = -1;
  for (let i = 0; i < LEGS_CONFIG.length; i++) {
    const s = getLegStatus(mainTeam, i, now, RACE_START);
    if (s === 'progress') { activeLegIdx = i; break; }
  }

  // All legs finished
  if (activeLegIdx === -1) {
    const allFinished = LEGS_CONFIG.every((_, i) => getLegStatus(mainTeam, i, now, RACE_START) === 'finished');
    if (allFinished) {
      return (
        <div style={{
          background: 'linear-gradient(135deg, rgba(20,184,166,0.15) 0%, rgba(6,182,212,0.08) 100%)',
          border: '1px solid rgba(20,184,166,0.4)',
          borderRadius: 'var(--radius)',
          padding: '0.75rem 1rem',
          marginBottom: '0.75rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem'
        }}>
          <div>
            <div style={{ fontSize: '0.7rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Race Status</div>
            <div style={{ fontSize: '1.1rem', fontWeight: '700', fontFamily: 'var(--font-title)', color: '#14b8a6', marginTop: '2px' }}>
              🎉 Race Finished — All Legs Complete!
            </div>
          </div>
          <div style={{ fontSize: '1.5rem' }}>🏆</div>
        </div>
      );
    } else {
      // Race has started, but no legs are in progress yet? Let's default to leg 0 as started.
      activeLegIdx = 0;
    }
  }

  const leg = LEGS_CONFIG[activeLegIdx];

  // Compute start time = RACE_START + sum of prior actual split seconds
  let cumulativeSec = 0;
  for (let i = 0; i < activeLegIdx; i++) {
    const splitVal = mainTeam[LEGS_CONFIG[i].splitKey];
    const sec = parseTimeToSeconds(splitVal);
    if (sec !== null) cumulativeSec += sec;
  }
  const legStartTime = new Date(RACE_START.getTime() + cumulativeSec * 1000);
  const elapsedSec = Math.max(0, Math.floor((now - legStartTime) / 1000));

  // Format elapsed as h:mm:ss or m:ss
  const fmtElapsed = (s) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    if (h > 0) return `${h}:${m.toString().padStart(2,'0')}:${sec.toString().padStart(2,'0')}`;
    return `${m}:${sec.toString().padStart(2,'0')}`;
  };

  // GPS lookup
  const racerKeys = LEG_RACER_MAP[leg.id] || [];
  const TEN_MIN_MS = 10 * 60 * 1000;
  const gpsPoints = racerKeys
    .map(k => ({ key: k, loc: memberLocations[k] }))
    .filter(({ loc }) => loc && (now - loc.timestamp) < TEN_MIN_MS);

  // 2025 comparison
  const split2025 = JACKSONS_2025_SPLITS[leg.id];
  const elapsedDelta = split2025 ? elapsedSec - split2025.seconds : null;
  const deltaColor = elapsedDelta !== null ? (elapsedDelta <= 0 ? '#14b8a6' : '#f59e0b') : null;
  const showMap = gpsPoints.length > 0;
  const legTransition = LEG_TRANSITIONS[leg.id];
  const startTrans = TRANSITIONS[legTransition.start];
  const finishTrans = TRANSITIONS[legTransition.finish];
  const racerNames = racerKeys.map(k => LOGISTICS_DATA[k]?.name || k).join(' & ');

  return (
    <div className="card" style={{
      border: '1px solid rgba(20,184,166,0.5)',
      background: 'linear-gradient(135deg, rgba(20,184,166,0.1) 0%, rgba(6,182,212,0.04) 100%)',
      marginBottom: '0.75rem'
    }}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <div>
          <div style={{ fontSize: '0.65rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '2px' }}>
            Leg {activeLegIdx + 1} of {LEGS_CONFIG.length} · Active Now
          </div>
          <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: '700', fontFamily: 'var(--font-title)', color: '#14b8a6' }}>
            🏃 {leg.name}
          </h3>
        </div>
        <div style={{
          background: 'rgba(20,184,166,0.2)',
          borderRadius: '999px',
          padding: '4px 10px',
          fontSize: '0.7rem',
          fontWeight: '600',
          color: '#14b8a6',
          whiteSpace: 'nowrap'
        }}>RACING</div>
      </div>

      {/* Stats grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem 1rem', marginBottom: showMap ? '0.75rem' : 0 }}>
        <div>
          <div style={{ fontSize: '0.65rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Racer</div>
          <div style={{ fontSize: '0.88rem', fontWeight: '600', marginTop: '2px' }}>{racerNames}</div>
        </div>
        <div>
          <div style={{ fontSize: '0.65rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Est. Start</div>
          <div style={{ fontSize: '0.88rem', fontWeight: '600', marginTop: '2px' }}>
            {legStartTime.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })} PDT
          </div>
        </div>
        <div>
          <div style={{ fontSize: '0.65rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Elapsed</div>
          <div style={{ fontSize: '1.15rem', fontWeight: '700', fontFamily: 'var(--font-title)', color: '#14b8a6', marginTop: '2px' }}>
            ⏱ {fmtElapsed(elapsedSec)}
          </div>
        </div>
        {split2025 && (
          <div>
            <div style={{ fontSize: '0.65rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', letterSpacing: '0.07em' }}>2025 Time</div>
            <div style={{ fontSize: '0.88rem', fontWeight: '600', marginTop: '2px' }}>
              {split2025.time}
              {elapsedDelta !== null && (
                <span style={{ marginLeft: '6px', fontSize: '0.8rem', color: deltaColor, fontWeight: '700' }}>
                  ({elapsedDelta > 0 ? '+' : ''}{fmtElapsed(Math.abs(elapsedDelta))})
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Mini map */}
      {showMap && (
        <div style={{ borderRadius: 'var(--radius)', overflow: 'hidden', border: '1px solid hsl(var(--border))' }}>
          <ActiveLegMiniMap
            legId={leg.id}
            startTransition={startTrans}
            finishTransition={finishTrans}
            gpsPoints={gpsPoints}
          />
        </div>
      )}
      {!showMap && (
        <div style={{ fontSize: '0.72rem', color: 'hsl(var(--text-muted))', marginTop: '0.5rem', textAlign: 'center' }}>
          📡 Live map will appear when GPS data is available
        </div>
      )}
    </div>
  );
}

// Mini-map for the Active Leg card
function ActiveLegMiniMap({ legId, startTransition, finishTransition, gpsPoints }) {
  const mapRef = useRef(null);
  const leafletMap = useRef(null);

  useEffect(() => {
    if (!mapRef.current || leafletMap.current) return;
    leafletMap.current = L.map(mapRef.current, {
      zoomControl: false,
      attributionControl: false,
      dragging: false,
      scrollWheelZoom: false,
      doubleClickZoom: false,
      boxZoom: false,
      keyboard: false,
    });
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 18,
    }).addTo(leafletMap.current);
    return () => {
      if (leafletMap.current) { 
        leafletMap.current.remove(); 
        leafletMap.current = null; 
      }
    };
  }, []);

  useEffect(() => {
    if (!leafletMap.current) return;

    // Clear existing layers except tile layer
    leafletMap.current.eachLayer(layer => {
      if (!(layer instanceof L.TileLayer)) leafletMap.current.removeLayer(layer);
    });

    // Fetch and render the active leg route
    fetch('/data/route.geojson')
      .then(res => {
        if (!res.ok) throw new Error('Route file not found');
        return res.json();
      })
      .then(data => {
        const activeFeature = data.features.find(f => f.properties.leg === legId);
        if (activeFeature && leafletMap.current) {
          L.geoJSON(activeFeature, {
            style: {
              color: activeFeature.properties.color || '#14b8a6',
              weight: 5,
              opacity: 0.85,
              dashArray: legId === 'xcski' ? '5, 5' : null
            }
          }).addTo(leafletMap.current);
        }
      })
      .catch(err => {
        console.warn('MiniMap route track not loaded:', err.message);
      });

    const points = [];

    // Start pin
    const startSame = startTransition === finishTransition;
    const startIcon = L.divIcon({
      className: '',
      html: `<div style="background:#14b8a6;color:white;border-radius:50%;width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-size:13px;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.5)">🚩</div>`,
      iconSize: [26, 26], iconAnchor: [13, 13]
    });
    L.marker([startTransition.lat, startTransition.lng], { icon: startIcon })
      .addTo(leafletMap.current)
      .bindTooltip(`Start: ${startTransition.name}`, { direction: 'top' });
    points.push([startTransition.lat, startTransition.lng]);

    // Finish pin
    if (!startSame) {
      const finishIcon = L.divIcon({
        className: '',
        html: `<div style="background:#f59e0b;color:white;border-radius:50%;width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-size:13px;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.5)">🏁</div>`,
        iconSize: [26, 26], iconAnchor: [13, 13]
      });
      L.marker([finishTransition.lat, finishTransition.lng], { icon: finishIcon })
        .addTo(leafletMap.current)
        .bindTooltip(`Finish: ${finishTransition.name}`, { direction: 'top' });
      points.push([finishTransition.lat, finishTransition.lng]);
    }

    // GPS racer pins
    gpsPoints.forEach(({ key, loc }) => {
      const gpIcon = L.divIcon({
        className: 'custom-live-marker',
        html: `<div class="pulse-marker" style="background-color:#14b8a6;border-color:white;"></div>`,
        iconSize: [20, 20], iconAnchor: [10, 10]
      });
      const label = key === 'CARMEN' ? 'Carmen' : key === 'YVETTE' ? 'Yvette' :
        key.charAt(0) + key.slice(1).toLowerCase();
      L.marker([loc.lat, loc.lng], { icon: gpIcon })
        .addTo(leafletMap.current)
        .bindTooltip(`📍 ${label}`, { direction: 'top' });
      points.push([loc.lat, loc.lng]);
    });

    if (points.length > 1) {
      leafletMap.current.fitBounds(L.latLngBounds(points), { padding: [30, 30] });
    } else if (points.length === 1) {
      leafletMap.current.setView(points[0], 13);
    }
  }, [legId, startTransition, finishTransition, gpsPoints]);

  return <div ref={mapRef} style={{ height: '200px', width: '100%' }} />;
}
