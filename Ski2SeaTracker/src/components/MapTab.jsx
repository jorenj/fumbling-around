import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { TRANSITIONS } from '../lib/constants';
import { getDisplayName } from '../lib/utils';

export default function MapTab({ memberLocations }) {
  return (
    <div>
      <div className="card" style={{ padding: '0.75rem' }}>
        <h3 className="section-title">🗺️ Race Map & Transition Zones</h3>
        <p className="subtext" style={{ marginBottom: '0.5rem' }}>
          Teal pins show live checked-in members. Circle colors indicate GPS freshness.
        </p>
        <LiveMap memberLocations={memberLocations} />
        
        <div style={{ display: 'flex', gap: '15px', marginTop: '10px', fontSize: '0.75rem', justifyContent: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#14b8a6' }}></div>
            <span>Active (&lt;2m)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#f59e0b' }}></div>
            <span>Delayed (&lt;5m)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#94a3b8' }}></div>
            <span>Stale (&gt;5m)</span>
          </div>
        </div>
      </div>
      
      <div className="card">
        <h3 className="section-title">📍 Transition Locations</h3>
        <div style={{ maxHeight: '200px', overflowY: 'auto', fontSize: '0.85rem' }}>
          {TRANSITIONS.map((t, idx) => (
            <div key={idx} style={{ padding: '0.5rem 0', borderBottom: idx < TRANSITIONS.length - 1 ? '1px solid hsl(var(--border) / 0.5)' : 'none' }}>
              <div style={{ fontWeight: '600' }}>{t.name}</div>
              <div style={{ color: '#06b6d4', fontSize: '0.75rem' }}>Transition: {t.leg}</div>
              <div className="subtext" style={{ fontSize: '0.8rem' }}>{t.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function LiveMap({ memberLocations }) {
  const mapRef = useRef(null);
  const leafletMap = useRef(null);
  const markersRef = useRef({});

  useEffect(() => {
    if (!leafletMap.current && mapRef.current) {
      // Centered on the Nooksack River area between Mt Baker and Bellingham Bay
      leafletMap.current = L.map(mapRef.current).setView([48.86, -122.15], 9);
      
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
      }).addTo(leafletMap.current);

      // Plot transition zone markers
      TRANSITIONS.forEach(t => {
        const transIcon = L.divIcon({
          className: 'transition-marker',
          html: `<div style="background-color: #3b82f6; width: 14px; height: 14px; border-radius: 50%; border: 2.5px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.5);"></div>`,
          iconSize: [14, 14],
          iconAnchor: [7, 7]
        });

        L.marker([t.lat, t.lng], { icon: transIcon })
          .addTo(leafletMap.current)
          .bindPopup(`<b>${t.name}</b><br/>Transition: ${t.leg}<br/>${t.desc}`);
      });
    }
  }, []);

  // Update live markers when location coordinates change
  useEffect(() => {
    if (leafletMap.current && memberLocations) {
      // Clear old live markers
      Object.keys(markersRef.current).forEach(key => {
        markersRef.current[key].remove();
      });
      markersRef.current = {};

      // Draw new live markers
      Object.entries(memberLocations).forEach(([name, loc]) => {
        const timeDiffMins = Math.floor((Date.now() - loc.timestamp) / 60000);
        
        let markerColor = '#94a3b8'; // stale >= 5m (grey)
        if (timeDiffMins < 2) markerColor = '#14b8a6'; // active < 2m (teal)
        else if (timeDiffMins < 5) markerColor = '#f59e0b'; // warning < 5m (amber)

        const customIcon = L.divIcon({
          className: 'custom-live-marker',
          html: `<div class="pulse-marker" style="background-color: ${markerColor}; border-color: ${markerColor === '#14b8a6' ? 'white' : '#cbd5e1'};"></div>`,
          iconSize: [20, 20],
          iconAnchor: [10, 10]
        });

        const m = L.marker([loc.lat, loc.lng], { icon: customIcon })
          .addTo(leafletMap.current)
          .bindTooltip(`<b>${getDisplayName(name)}</b><br/>${timeDiffMins} min${timeDiffMins === 1 ? '' : 's'} ago<br/>Accuracy: ${loc.accuracy != null ? Math.round(loc.accuracy) + 'm' : 'Unknown'}`, {
            permanent: false,
            direction: 'top'
          });

        markersRef.current[name] = m;
      });
    }
  }, [memberLocations]);

  return <div ref={mapRef} className="map-view-container" />;
}
