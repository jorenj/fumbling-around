import { LOGISTICS_DATA } from '../lib/constants';

export default function CheckinTab({
  activeCheckinUser,
  onActiveCheckinUserChange,
  isSharingLocation,
  toggleLocationSharing,
  gpsStatus,
  lastGpsCoords
}) {
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
            <option value="CAR_A">🚗 Car A (Support)</option>
            <option value="CYBERTRUCK">📐 Cybertruck (Support)</option>
            <option value="CAR_C">🚙 Car C (Support)</option>
          </select>
        </div>
      </div>

      {/* Option 1: Background GPS (Recommended) */}
      <div className="card" style={{ 
        border: '1px solid rgba(20, 184, 166, 0.35)', 
        background: 'linear-gradient(135deg, rgba(20, 184, 166, 0.08) 0%, rgba(6, 182, 212, 0.03) 100%)' 
      }}>
        <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#14b8a6' }}>
          🔌 Option 1: Background GPS (Recommended)
        </h3>
        <p className="subtext" style={{ lineHeight: '1.4', marginBottom: '1rem', color: 'hsl(var(--text-primary))' }}>
          Use the free <b>Overland GPS Tracker</b> app. It runs in the background and sends GPS updates even when your phone is locked in your pocket.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <a 
            href={`overland://setup?url=${encodeURIComponent(window.location.origin + '/api/overland')}&device_id=${activeCheckinUser}`}
            className="btn-primary"
            style={{ 
              textDecoration: 'none', 
              textAlign: 'center', 
              background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)', 
              boxShadow: '0 4px 15px rgba(6, 182, 212, 0.3)',
              display: 'block',
              padding: '0.75rem'
            }}
          >
            📲 Auto-Configure Overland App
          </a>
          <p className="subtext" style={{ fontSize: '0.75rem', marginTop: '6px', lineHeight: '1.5' }}>
            1. Install <a href="https://apps.apple.com/us/app/overland-gps-tracker/id1452445362" target="_blank" rel="noopener noreferrer" style={{ color: '#06b6d4', textDecoration: 'underline', fontWeight: 'bold' }}>Overland GPS Tracker</a> from the iOS App Store.<br />
            2. Select your identity above.<br />
            3. Tap the button above to auto-configure the app.<br />
            4. <b>iOS Settings:</b> Go to Settings → Overland → Location → select <b>"Always Allow"</b> (enables background tracking. Note: you may need to choose/trigger location settings twice to prompt/unlock the "Always Allow" option).<br />
            5. <b>In Overland App:</b> On the <b>"Tracker"</b> page, set the <b>Send Interval</b> to <b>1m</b>, then in the "Settings" page slide the dot at the top of the screen to the right to enable settings changes, then toggle the tracking switch at the top to <b>ON</b>. 
          </p>
        </div>
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
