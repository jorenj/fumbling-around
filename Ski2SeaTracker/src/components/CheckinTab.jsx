import { useState } from 'react';
import { LOGISTICS_DATA } from '../lib/constants';

export default function CheckinTab({
  activeCheckinUser,
  onActiveCheckinUserChange,
  isSharingLocation,
  toggleLocationSharing,
  gpsStatus,
  lastGpsCoords
}) {
  const [selectedGpsApp, setSelectedGpsApp] = useState('owntracks');

  return (
    <div>
      {/* Identity Card */}
      <div className="card">
        <h3 className="section-title">👤 Select Identity</h3>
        <div className="form-group" style={{ marginTop: '0.5rem' }}>
          <label className="form-label">Identify As:</label>
          <select 
            value={activeCheckinUser} 
            onChange={(e) => onActiveCheckinUserChange(e.target.value)}
            disabled={isSharingLocation}
            className="form-select"
          >
            {Object.keys(LOGISTICS_DATA).map(key => (
              <option key={key} value={key}>{LOGISTICS_DATA[key].name} ({LOGISTICS_DATA[key].leg})</option>
            ))}
            <option disabled>──────────</option>
            <option value="CAR_A">🚗 Iver's Model Y (Support)</option>
            <option value="CYBERTRUCK">📐 Cybertruck (Support)</option>
            <option value="CAR_C">🚙 Sam's Bronco (Support)</option>
          </select>
        </div>
      </div>

      {/* Option 1: Background GPS (Recommended) */}
      <div className="card" style={{ 
        border: '1px solid rgba(20, 184, 166, 0.35)', 
        background: 'linear-gradient(135deg, rgba(20, 184, 166, 0.08) 0%, rgba(6, 182, 212, 0.03) 100%)' 
      }}>
        <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#14b8a6', marginBottom: '0.75rem' }}>
          🔌 Option 1: Background GPS (Recommended)
        </h3>

        {/* Tab Selector */}
        <div style={{ display: 'flex', borderBottom: '1px solid hsl(var(--border) / 0.5)', marginBottom: '1rem', gap: '2px', overflowX: 'auto' }}>
          <button
            onClick={() => setSelectedGpsApp('owntracks')}
            style={{
              padding: '0.5rem 0.65rem',
              background: 'none',
              border: 'none',
              borderBottom: selectedGpsApp === 'owntracks' ? '2.5px solid #14b8a6' : '2.5px solid transparent',
              color: selectedGpsApp === 'owntracks' ? '#14b8a6' : 'hsl(var(--text-muted))',
              fontWeight: '600',
              fontSize: '0.78rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              whiteSpace: 'nowrap'
            }}
          >
            🗺️ OwnTracks (Global)
          </button>
          <button
            onClick={() => setSelectedGpsApp('traccar')}
            style={{
              padding: '0.5rem 0.65rem',
              background: 'none',
              border: 'none',
              borderBottom: selectedGpsApp === 'traccar' ? '2.5px solid #14b8a6' : '2.5px solid transparent',
              color: selectedGpsApp === 'traccar' ? '#14b8a6' : 'hsl(var(--text-muted))',
              fontWeight: '600',
              fontSize: '0.78rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              whiteSpace: 'nowrap'
            }}
          >
            🛰️ Traccar (Global)
          </button>
          <button
            onClick={() => setSelectedGpsApp('overland')}
            style={{
              padding: '0.5rem 0.65rem',
              background: 'none',
              border: 'none',
              borderBottom: selectedGpsApp === 'overland' ? '2.5px solid #14b8a6' : '2.5px solid transparent',
              color: selectedGpsApp === 'overland' ? '#14b8a6' : 'hsl(var(--text-muted))',
              fontWeight: '600',
              fontSize: '0.78rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              whiteSpace: 'nowrap'
            }}
          >
            🔌 Overland (US iOS)
          </button>
        </div>

        {/* Tab Content: OwnTracks */}
        {selectedGpsApp === 'owntracks' && (
          <div>
            <p className="subtext" style={{ lineHeight: '1.4', marginBottom: '1.25rem', color: 'hsl(var(--text-primary))' }}>
              <b>OwnTracks</b> is free, open source, available globally (including Canada), and runs reliably in the background on both <b>iOS</b> and <b>Android</b>.
            </p>
            <p className="subtext" style={{ fontSize: '0.75rem', lineHeight: '1.6', marginBottom: '1.25rem' }}>
              1. Install <b>OwnTracks</b> from your app store.<br />
              2. <a 
                href={`owntracks:///config?inline=${btoa(JSON.stringify({
                  _type: 'configuration',
                  mode: 3,
                  url: `${window.location.origin}/api/owntracks?device_id=${activeCheckinUser}`,
                  tid: activeCheckinUser.substring(0, 2)
                }))}`}
                style={{ 
                  display: 'inline-block',
                  margin: '4px 0',
                  padding: '4px 10px',
                  background: 'linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)', 
                  color: 'white',
                  borderRadius: '4px',
                  textDecoration: 'none',
                  fontWeight: 'bold',
                  fontSize: '0.72rem',
                  boxShadow: '0 2px 8px rgba(20, 184, 166, 0.25)'
                }}
              >
                📲 Tap here to Auto-Configure OwnTracks App
              </a> (or manually copy-paste the connection parameters below with Mode set to HTTP).<br />
              3. <b>Configure iOS Settings (Critical for background updates):</b><br />
              &nbsp;&nbsp;&nbsp;a. Open the iOS <b>Settings</b> app (or try this <a href="App-Prefs:root=Privacy&path=LOCATION" style={{ color: '#06b6d4', textDecoration: 'underline', fontWeight: 'bold' }}>Settings Link</a>).<br />
              &nbsp;&nbsp;&nbsp;b. Scroll down to the bottom list of applications and tap <b>OwnTracks</b>.<br />
              &nbsp;&nbsp;&nbsp;c. Tap <b>Location</b> and select <b>Always</b> (if "Always" is missing, open OwnTracks first and allow location once to trigger iOS prompts).<br />
              &nbsp;&nbsp;&nbsp;d. Ensure <b>Background App Refresh</b>, <b>Motion & Fitness</b>, and <b>Cellular Data</b> are all toggled <b>ON</b>.<br />
              4. <b>Configure Android Settings:</b> Go to Settings → Apps → OwnTracks → Permissions → Location → select <b>"Allow all the time"</b>.
            </p>
            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '0.75rem', borderRadius: 'var(--radius)', border: '1px solid hsl(var(--border) / 0.5)', marginBottom: '0.5rem' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 'bold', color: '#14b8a6', marginBottom: '4px' }}>📋 OwnTracks HTTP Parameters (Manual Setup)</div>
              <div style={{ display: 'grid', gridTemplateColumns: '60px 1fr', gap: '4px', fontSize: '0.72rem', fontFamily: 'monospace' }}>
                <span style={{ color: 'hsl(var(--text-muted))' }}>Mode:</span>
                <span>HTTP</span>
                <span style={{ color: 'hsl(var(--text-muted))' }}>URL:</span>
                <span style={{ wordBreak: 'break-all', color: '#06b6d4' }}>{`${window.location.origin}/api/owntracks?device_id=${activeCheckinUser}`}</span>
              </div>
            </div>
          </div>
        )}

        {/* Tab Content: Traccar */}
        {selectedGpsApp === 'traccar' && (
          <div>
            <p className="subtext" style={{ lineHeight: '1.4', marginBottom: '1rem', color: 'hsl(var(--text-primary))' }}>
              <b>Traccar Client</b> is free, open source, lightweight, available globally, and works on both <b>iOS</b> and <b>Android</b>.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', margin: '0.5rem 0 1rem 0', background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: 'var(--radius)', border: '1px solid hsl(var(--border) / 0.3)' }}>
              <div style={{ fontSize: '0.7rem', fontWeight: 'bold', color: 'hsl(var(--text-muted))', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Scan QR Code inside Traccar Client app</div>
              <img 
                src={`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(`url=${window.location.origin}/api/traccar&id=${activeCheckinUser}&interval=60`)}`}
                alt="Traccar Setup QR Code"
                style={{ borderRadius: '4px', border: '4px solid white', width: '120px', height: '120px' }}
              />
            </div>
            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '0.75rem', borderRadius: 'var(--radius)', border: '1px solid hsl(var(--border) / 0.5)', marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 'bold', color: '#14b8a6', marginBottom: '4px' }}>📋 Traccar Parameters (Manual Setup)</div>
              <div style={{ display: 'grid', gridTemplateColumns: '100px 1fr', gap: '4px', fontSize: '0.72rem', fontFamily: 'monospace' }}>
                <span style={{ color: 'hsl(var(--text-muted))' }}>Server URL:</span>
                <span style={{ wordBreak: 'break-all', color: '#06b6d4' }}>{`${window.location.origin}/api/traccar`}</span>
                <span style={{ color: 'hsl(var(--text-muted))' }}>Device ID:</span>
                <span style={{ color: '#14b8a6', fontWeight: 'bold' }}>{activeCheckinUser}</span>
              </div>
            </div>
            <p className="subtext" style={{ fontSize: '0.75rem', lineHeight: '1.5' }}>
              1. Install <b>Traccar Client</b> from your app store.<br />
              2. Open the app and scan the QR code above, or manually fill in the URL and Device ID.<br />
              3. Set **Frequency** to **60** seconds.<br />
              4. Toggle the <b>Service Status</b> switch at the top to <b>ON</b>.
            </p>
          </div>
        )}

        {/* Tab Content: Overland */}
        {selectedGpsApp === 'overland' && (
          <div>
            <p className="subtext" style={{ lineHeight: '1.4', marginBottom: '1rem', color: 'hsl(var(--text-primary))' }}>
              Use the free <b>Overland GPS Tracker</b> app. It runs in the background and sends GPS updates even when your phone is locked. <i>Note: Available on US App Store only.</i>
            </p>
            <p className="subtext" style={{ fontSize: '0.75rem', lineHeight: '1.6' }}>
              1. Install <a href="https://apps.apple.com/us/app/overland-gps-tracker/id1452445362" target="_blank" rel="noopener noreferrer" style={{ color: '#06b6d4', textDecoration: 'underline', fontWeight: 'bold' }}>Overland GPS Tracker</a> (US iOS).<br />
              2. <a 
                href={`overland://setup?url=${encodeURIComponent(window.location.origin + '/api/overland')}&device_id=${activeCheckinUser}`}
                style={{ 
                  display: 'inline-block',
                  margin: '4px 0',
                  padding: '4px 10px',
                  background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)', 
                  color: 'white',
                  borderRadius: '4px',
                  textDecoration: 'none',
                  fontWeight: 'bold',
                  fontSize: '0.72rem',
                  boxShadow: '0 2px 8px rgba(6, 182, 212, 0.25)'
                }}
              >
                📲 Tap here to Auto-Configure Overland App
              </a>.<br />
              3. Go to Settings → Overland → Location → select <b>"Always Allow"</b>.<br />
              4. On the <b>"Tracker"</b> page, set the <b>Send Interval</b> to <b>1m</b>, then toggle tracking <b>ON</b>.
            </p>
          </div>
        )}
      </div>
      
      {/* Option 2: Temporary Browser Broadcast */}
      <div className="card" style={{ opacity: 0.85 }}>
        <h3 className="section-title">🌐 Option 2: Temporary Browser Broadcast</h3>
        <p className="subtext" style={{ marginBottom: '1rem', lineHeight: '1.4' }}>
          <b>⚠️ Temporary Only:</b> Broadcasts GPS directly from this browser page. <b>Will stop working</b> as soon as you lock your screen, close this tab, or switch apps.
        </p>

        <div style={{ margin: '1rem 0' }}>
          <button 
            onClick={toggleLocationSharing} 
            className="btn-primary"
            style={isSharingLocation ? { background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)', boxShadow: '0 4px 15px rgba(239, 68, 68, 0.3)' } : {}}
          >
            {isSharingLocation ? "🔴 Stop Broadcasting" : "🟢 Start Broadcasting"}
          </button>
        </div>

        <p className="subtext" style={{ fontSize: '0.75rem', lineHeight: '1.5', marginTop: '0.5rem', marginBottom: '1rem' }}>
          1. Ensure the correct identity is selected in the <b>Select Identity</b> card above.<br />
          2. Tap the button above to start/stop broadcasting your location.
        </p>

        {/* Status details */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '1rem', borderTop: '1px solid hsl(var(--border))', paddingTop: '1rem', fontSize: '0.85rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span className="subtext">GPS Status:</span>
            <span style={{ fontWeight: 'bold', color: getGpsStatusColor(gpsStatus) }}>
              {getGpsStatusText(gpsStatus)}
            </span>
          </div>
          {lastGpsCoords && (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="subtext">Latitude:</span>
                <span>{lastGpsCoords.latitude.toFixed(6)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="subtext">Longitude:</span>
                <span>{lastGpsCoords.longitude.toFixed(6)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="subtext">Accuracy:</span>
                <span>±{Math.round(lastGpsCoords.accuracy)} meters</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// Helpers for GPS status
const getGpsStatusColor = (status) => {
  switch(status) {
    case 'inactive': return 'hsl(var(--text-muted))';
    case 'acquiring': return '#f59e0b';
    case 'active': return '#06b6d4';
    case 'reporting': return '#14b8a6';
    case 'offline_save': return '#ec4899';
    case 'error': return '#ef4444';
    default: return 'white';
  }
};

const getGpsStatusText = (status) => {
  switch(status) {
    case 'inactive': return 'Offline / Stopped';
    case 'acquiring': return 'Searching GPS Signal...';
    case 'active': return 'GPS Lock Acquired';
    case 'reporting': return 'Broadcasting Coordinates Live';
    case 'offline_save': return 'Server Error: Offline Backup';
    case 'error': return 'GPS Error / Permissions Denied';
    default: return 'Unknown';
  }
};
