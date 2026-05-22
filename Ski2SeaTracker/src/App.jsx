import { useState, useEffect, useRef } from 'react';
import { useRaceData } from './hooks/useRaceData';
import { LOGISTICS_DATA } from './lib/constants';
import LeaderboardTab from './components/LeaderboardTab';
import MapTab from './components/MapTab';
import LogisticsTab from './components/LogisticsTab';
import CheckinTab from './components/CheckinTab';

export default function App() {
  const [activeTab, setActiveTab] = useState('leaderboard');
  const [year, setYear] = useState('2026');

  // Load custom hook to fetch results & locations
  const {
    teamsData,
    loadingResults,
    lastRefreshed,
    events,
    clearEvents,
    isOnline,
    memberLocations,
    fetchResults
  } = useRaceData(year);

  // Logistics state
  const [selectedRacerKey, setSelectedRacerKey] = useState(() => {
    return localStorage.getItem('ski2sea_selected_racer') || 'IVER';
  });
  const [checklist, setChecklist] = useState(() => {
    const saved = localStorage.getItem('ski2sea_checklist');
    return saved ? JSON.parse(saved) : {};
  });

  // Location sharing state
  const [activeCheckinUser, setActiveCheckinUser] = useState(() => {
    return localStorage.getItem('ski2sea_active_checkin_user') || 'IVER';
  });
  const [isSharingLocation, setIsSharingLocation] = useState(false);
  const [gpsStatus, setGpsStatus] = useState('inactive');
  const [lastGpsCoords, setLastGpsCoords] = useState(null);
  const watchIdRef = useRef(null);

  // Sync state modifications to local storage
  useEffect(() => {
    localStorage.setItem('ski2sea_selected_racer', selectedRacerKey);
  }, [selectedRacerKey]);

  useEffect(() => {
    localStorage.setItem('ski2sea_active_checkin_user', activeCheckinUser);
  }, [activeCheckinUser]);

  const handleSelectedRacerChange = (val) => {
    setSelectedRacerKey(val);
    if (activeCheckinUser !== val && LOGISTICS_DATA[val]) {
      setActiveCheckinUser(val);
    }
  };

  const handleActiveCheckinUserChange = (val) => {
    setActiveCheckinUser(val);
    if (LOGISTICS_DATA[val] && selectedRacerKey !== val) {
      setSelectedRacerKey(val);
    }
  };

  // Main clock tick to drive countdown timers and elapsed calculations
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const tick = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(tick);
  }, []);

  // Poll checklist state
  const fetchChecklist = async () => {
    try {
      const res = await fetch('/api/checklist');
      if (res.ok) {
        const data = await res.json();
        setChecklist(data);
      }
    } catch (err) {
      console.warn('Checklist fetch failed, using local state:', err);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchChecklist();
    const interval = setInterval(fetchChecklist, 10000);
    return () => clearInterval(interval);
  }, []);

  // Toggle checklist item — optimistic local update + server PATCH
  const toggleChecklistItem = async (racer, index) => {
    const key = `${racer}_${index}`;
    const newVal = !checklist[key];
    setChecklist(prev => ({ ...prev, [key]: newVal }));
    try {
      await fetch('/api/checklist', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, checked: newVal })
      });
    } catch (err) {
      console.error('Failed to sync checklist item:', err);
    }
  };

  // Location broadcasting GPS logic
  const sendLocationToServer = async (coords) => {
    try {
      const res = await fetch('/api/location', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          member: activeCheckinUser,
          lat: coords.latitude,
          lng: coords.longitude,
          accuracy: coords.accuracy
        })
      });
      if (res.ok) {
        setGpsStatus('reporting');
      } else {
        setGpsStatus('error');
      }
    } catch (err) {
      console.error("Failed to send location:", err);
      setGpsStatus('offline_save');
    }
  };

  const toggleLocationSharing = () => {
    if (isSharingLocation) {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
        watchIdRef.current = null;
      }
      setIsSharingLocation(false);
      setGpsStatus('inactive');
      setLastGpsCoords(null);
    } else {
      if (!navigator.geolocation) {
        alert("Geolocation is not supported by your browser");
        return;
      }

      setIsSharingLocation(true);
      setGpsStatus('acquiring');

      watchIdRef.current = navigator.geolocation.watchPosition(
        (position) => {
          const coords = position.coords;
          setLastGpsCoords(coords);
          setGpsStatus('active');
          sendLocationToServer(coords);
        },
        (error) => {
          console.error("GPS Error:", error);
          setGpsStatus('error');
          setIsSharingLocation(false);
          alert("GPS Permission denied or location unavailable.");
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      );
    }
  };

  // Clean up location watcher on unmount (Task 2)
  useEffect(() => {
    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, []);

  return (
    <div className="app-container">
      {/* Offline Banner */}
      {!isOnline && (
        <div className="alert-banner">
          <span>⚠️ App is offline. Showing cached results.</span>
        </div>
      )}

      {/* Header */}
      <header className="app-header">
        <div className="header-title-row">
          <h1 className="app-title">Ski2Sea Tracker</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <select 
              value={year} 
              onChange={(e) => setYear(e.target.value)}
              className="form-select"
              style={{ padding: '0.2rem 0.5rem', width: 'auto', fontSize: '0.8rem', height: '30px' }}
            >
              <option value="2026">2026 Live</option>
              <option value="2025">2025 Results</option>
              <option value="2024">2024 Test</option>
            </select>
            <span className="bib-badge">BIB 101</span>
          </div>
        </div>
        <p className="header-subtitle">Jacksons Speak Louder than Words</p>
      </header>

      {/* Main Tab Dashboard */}
      <main className="main-content">
        {activeTab === 'leaderboard' && (
          <LeaderboardTab
            teamsData={teamsData}
            loadingResults={loadingResults}
            lastRefreshed={lastRefreshed}
            events={events}
            clearEvents={clearEvents}
            now={now}
            memberLocations={memberLocations}
            year={year}
            fetchResults={fetchResults}
          />
        )}

        {activeTab === 'map' && (
          <MapTab memberLocations={memberLocations} />
        )}

        {activeTab === 'logistics' && (
          <LogisticsTab
            selectedRacerKey={selectedRacerKey}
            onSelectedRacerChange={handleSelectedRacerChange}
            checklist={checklist}
            toggleChecklistItem={toggleChecklistItem}
            now={now}
          />
        )}

        {activeTab === 'checkin' && (
          <CheckinTab
            activeCheckinUser={activeCheckinUser}
            onActiveCheckinUserChange={handleActiveCheckinUserChange}
            isSharingLocation={isSharingLocation}
            toggleLocationSharing={toggleLocationSharing}
            gpsStatus={gpsStatus}
            lastGpsCoords={lastGpsCoords}
          />
        )}
      </main>

      {/* Bottom Nav Bar */}
      <nav className="bottom-nav">
        <button 
          onClick={() => setActiveTab('leaderboard')} 
          className={`nav-item ${activeTab === 'leaderboard' ? 'active' : ''}`}
        >
          <span className="nav-icon">⏱️</span>
          <span>Results</span>
        </button>
        <button 
          onClick={() => setActiveTab('map')} 
          className={`nav-item ${activeTab === 'map' ? 'active' : ''}`}
        >
          <span className="nav-icon">🗺️</span>
          <span>Map</span>
        </button>
        <button 
          onClick={() => setActiveTab('logistics')} 
          className={`nav-item ${activeTab === 'logistics' ? 'active' : ''}`}
        >
          <span className="nav-icon">📋</span>
          <span>Logistics</span>
        </button>
        <button 
          onClick={() => setActiveTab('checkin')} 
          className={`nav-item ${activeTab === 'checkin' ? 'active' : ''}`}
        >
          <span className="nav-icon">📡</span>
          <span>Broadcast</span>
        </button>
      </nav>
    </div>
  );
}
