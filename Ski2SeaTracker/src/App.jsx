import { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Competitors to track
const TARGET_TEAMS = [
  { bib: 101, name: "Jacksons Speak Louder than Words", isMain: true },
  { bib: 39, name: "No Bros, Just Pros" },
  { bib: 24, name: "Mentally Ready - Physically Not" },
  { bib: 32, name: "Daddy's Back, by Kenny Loggins" }
];

// Race years config (API keys/ids moved to backend)
const YEARS_CONFIG = {
  "2026": { name: "2026 Live" },
  "2025": { name: "2025 Results" },
  "2024": { name: "2024 Test" }
};

// Race start: May 25, 2026 at 7:30am Pacific (PDT = UTC-7)
const RACE_START = new Date('2026-05-25T07:30:00-07:00');

// Briefing times per racer (PDT). Used to show countdown on their checklist.
const BRIEFING_TIMES = {
  IVER:     new Date('2026-05-25T07:00:00-07:00'),
  TAVIN:    new Date('2026-05-25T07:00:00-07:00'),
  MAC:      new Date('2026-05-25T08:00:00-07:00'),
  JONATHAN: new Date('2026-05-25T09:00:00-07:00'),
  CARMEN:   new Date('2026-05-25T09:15:00-07:00'),
  YVETTE:   new Date('2026-05-25T09:15:00-07:00'),
  DAVID:    new Date('2026-05-25T11:45:00-07:00'),
  JOREN:    new Date('2026-05-25T11:00:00-07:00'),
};

// 7 Legs config in order
const LEGS_CONFIG = [
  { id: 'xcski', name: 'XC Ski', racerKey: 'XC_Ski_Racer', splitKey: 'XCSKI_SPLIT', rankKey: 'XCSKIRank', desc: 'Cross Country Ski at Mt. Baker' },
  { id: 'dhski', name: 'DH Ski', racerKey: 'DH_Ski_Snowboard_Racer', splitKey: 'DHSKI_SPLIT', rankKey: 'DHSKIRank', desc: 'Downhill Ski/Snowboard at Mt. Baker' },
  { id: 'run', name: 'Run', racerKey: 'Run_Racer', splitKey: 'RUN_SPLIT', rankKey: 'RunRank', desc: 'Run down Mt. Baker Highway' },
  { id: 'bike', name: 'Road Bike', racerKey: 'RD_Bike_Racer', splitKey: 'ROADBIKE_SPLIT', rankKey: 'RoadBikeRank', desc: 'Road Bike to Everson' },
  { id: 'canoe', name: 'Canoe', racerKey: 'Canoers', splitKey: 'CANOE_SPLIT', rankKey: 'CanoeRank', desc: 'Canoe down Nooksack River to Hovander Park' },
  { id: 'cyclox', name: 'Cyclocross', racerKey: 'CX_Racer', splitKey: 'CYCLOCROSS_SPLIT', rankKey: 'CyclocrossRank', desc: 'Cyclocross Bike in Hovander Park' },
  { id: 'kayak', name: 'Kayak', racerKey: 'Kayak_Racer', splitKey: 'KAYAK_SPLIT', rankKey: 'KayakRank', desc: 'Sea Kayak to Bellingham Bay Finish' }
];

// Map transition zones
const TRANSITIONS = [
  { name: "Mt. Baker Area", leg: "XC & DH Ski", lat: 48.857, lng: -121.679, desc: "Leg 1 & 2 start/finish. Mountain Road closes at 7:15am." },
  { name: "DOT Station (Canyon Creek)", leg: "Run to Bike", lat: 48.910, lng: -122.095, desc: "Leg 3 runner finishes, Leg 4 road biker launches." },
  { name: "Everson (Riverside Park)", leg: "Bike to Canoe", lat: 48.974, lng: -122.351, desc: "Leg 4 biker finishes, Leg 5 canoeists launch." },
  { name: "Hovander Park (Ferndale)", leg: "Canoe to Cyclocross to Kayak", lat: 48.836, lng: -122.594, desc: "Leg 5 canoeists finish, Leg 6 cyclocross biker starts, Leg 7 kayaker launches." },
  { name: "Zuanich Park (Bellingham)", leg: "Kayak to Finish", lat: 48.754, lng: -122.512, desc: "Leg 7 kayaker finishes. Celebrate here!" }
];

// Logistics task lists
const LOGISTICS_DATA = {
  IVER: {
    name: "Iver Jackson",
    leg: "Cross Country Ski",
    briefing: "7:00am briefing @ Mt. Baker Ski Area",
    car: "Car A (with Tavin, Mac, Sam)",
    tasks: [
      "Drive up to Mt. Baker in Car A with Tavin, Mac, and Sam.",
      "Attend the 7:00am briefing and warmup.",
      "Ski super fast! (Leg 1)",
      "Wait for the mountain road to open after DH Ski.",
      "Drop Tavin off at Jonathan's trailer.",
      "Proceed to Hovander Park (Canoe/Cyclocross transition) to hang out.",
      "Drive Car A with Sam to the Cyclocross finish.",
      "Help David launch the kayak.",
      "Drive Car A to the finish line at Zuanich Point Park."
    ]
  },
  TAVIN: {
    name: "Tavin Jackson",
    leg: "Downhill Ski/Snowboard",
    briefing: "7:00am briefing @ Mt. Baker Ski Area",
    car: "Car A, then Jonathan's trailer, then Cybertruck",
    tasks: [
      "Drive up to Mt. Baker in Car A with Iver, Mac, and Sam.",
      "Attend the 7:00am briefing and boot pack super fast! (Leg 2)",
      "Get dropped off at Jonathan's trailer on the way back down.",
      "Drive Jonathan's trailer to Hovander Park (Canoe/Cyclocross transition) to hang out.",
      "Drive with Carmen and Mac in the Cybertruck to the finish line."
    ]
  },
  MAC: {
    name: "Mackenzie Brown (Mac)",
    leg: "Run",
    briefing: "8:00am briefing @ Mt. Baker Highway (DOT Station)",
    car: "Car A, then Cybertruck",
    tasks: [
      "Drive up to Mt. Baker in Car A, get dropped off at the run start (Canyon Lake / DOT).",
      "Run super fast! (Leg 3)",
      "Hang out in Jonathan's trailer until Tavin arrives.",
      "Drive with Tavin to Hovander Park.",
      "Drive with Carmen and Tavin in the Cybertruck to the finish line."
    ]
  },
  JONATHAN: {
    name: "Jonathan Anderson",
    leg: "Road Bike",
    briefing: "9:00am briefing @ Everson (Riverside Park)",
    car: "Trailer / Cybertruck",
    tasks: [
      "Sleep at the run/bike transition (DOT Station) in your trailer.",
      "Leave keys to the car/trailer for Tavin to pick up.",
      "Bike super fast to Everson! (Leg 4)",
      "Find the Cybertruck waiting for you in Everson.",
      "Drive the Cybertruck to Hovander Park where your trailer is waiting.",
      "Take your car/trailer + Yvette to the finish line."
    ]
  },
  CARMEN: {
    name: "Carmen Jackson",
    leg: "Canoe (Double)",
    briefing: "9:15am briefing @ Everson (Riverside Park)",
    car: "Cybertruck",
    tasks: [
      "Take the Cybertruck from the Airbnb to the Canoe start (Everson) in time for the 9:15am briefing.",
      "Canoe super fast with Yvette! (Leg 5)",
      "At the Canoe finish (Hovander Park), locate the Cybertruck (brought by Jonathan).",
      "Drive the Cybertruck with Tavin and Mac to the finish line."
    ]
  },
  YVETTE: {
    name: "Yvette Jackson",
    leg: "Canoe (Double)",
    briefing: "9:15am briefing @ Everson (Riverside Park)",
    car: "Cybertruck, then Jonathan's trailer",
    tasks: [
      "Ride in the Cybertruck with Carmen from the Airbnb to Everson in time for the 9:15am briefing.",
      "Canoe super fast with Carmen! (Leg 5)",
      "At the Canoe finish (Hovander Park), locate Jonathan's car/trailer.",
      "Ride with Jonathan to the finish line."
    ]
  },
  DAVID: {
    name: "David Jackson",
    leg: "Kayak",
    briefing: "11:45am briefing @ Zuanich Point Park",
    car: "Car C, then Car X",
    tasks: [
      "Drive Car C with Joren to Hovander Park in time for the 11:00am cyclocross briefing.",
      "Leave Hovander Park early in Car X to get to the Kayak launch.",
      "Attend the 11:45am kayak briefing.",
      "Kayak super fast! (Leg 7)",
      "Beers at the finish line!"
    ]
  },
  JOREN: {
    name: "Joren Jackson",
    leg: "Cyclocross",
    briefing: "11:00am briefing @ Hovander Park",
    car: "Car C",
    tasks: [
      "Drive in Car C with David to Hovander Park.",
      "Attend the 11:00am cyclocross briefing.",
      "Bike super fast! (Leg 6)",
      "Drive Car C to the finish line."
    ]
  }
};

const FIELDS = [
  "BIB", "id", "TeamName", "Division", "Started",
  "XC_Ski_Racer", "XCSKI_SPLIT", "XCSKIRank",
  "DH_Ski_Snowboard_Racer", "DHSKI_SPLIT", "DHSKIRank",
  "Run_Racer", "RUN_SPLIT", "RunRank",
  "RD_Bike_Racer", "ROADBIKE_SPLIT", "RoadBikeRank",
  "Canoers", "CANOE_SPLIT", "CanoeRank",
  "CX_Racer", "CYCLOCROSS_SPLIT", "CyclocrossRank",
  "Kayak_Racer", "KAYAK_SPLIT", "KayakRank"
];

// Fallback names in case results haven't loaded yet
const getFallbackRacer = (bib, legId) => {
  if (bib !== 101) return "";
  if (legId === 'xcski') return "Iver Jackson";
  if (legId === 'dhski') return "Tavin Jackson";
  if (legId === 'run') return "Mackenzie Brown";
  if (legId === 'bike') return "Jonathan Anderson";
  if (legId === 'canoe') return "Yvette / Carmen Jackson";
  if (legId === 'cyclox') return "Joren Jackson";
  if (legId === 'kayak') return "David Jackson";
  return "";
};

// 2025 Splits for Jacksons Speak Louder Than Words (BIB 471 in 2025)
const JACKSONS_2025_SPLITS = {
  xcski: { time: "49:44.2", seconds: 2984.2, rank: 258, racer: "Yvette Jackson" },
  dhski: { time: "30:50.7", seconds: 1850.7, rank: 82, racer: "Tavin Jackson" },
  run: { time: "50:49.4", seconds: 3049.4, rank: 136, racer: "Mackenzie Brown" },
  bike: { time: "1:44:27.8", seconds: 6267.8, rank: 44, racer: "Jonathan Anderson" },
  canoe: { time: "2:23:07.6", seconds: 8587.6, rank: 61, racer: "Carmen Jackson / David Jackson" },
  cyclox: { time: "43:23.1", seconds: 2603.1, rank: 91, racer: "Joren Jackson" },
  kayak: { time: "36:49.9", seconds: 2209.9, rank: 119, racer: "Iver Jackson" }
};

const parseTimeToSeconds = (timeStr) => {
  if (!timeStr || timeStr === "0" || timeStr === "—") return null;
  // Handle HH:MM:SS.d or MM:SS.d
  const parts = timeStr.split(':');
  if (parts.length === 3) {
    const hrs = parseFloat(parts[0]);
    const mins = parseFloat(parts[1]);
    const secs = parseFloat(parts[2]);
    if (isNaN(hrs) || isNaN(mins) || isNaN(secs)) return null;
    return hrs * 3600 + mins * 60 + secs;
  } else if (parts.length === 2) {
    const mins = parseFloat(parts[0]);
    const secs = parseFloat(parts[1]);
    if (isNaN(mins) || isNaN(secs)) return null;
    return mins * 60 + secs;
  } else if (parts.length === 1) {
    const secs = parseFloat(parts[0]);
    if (isNaN(secs)) return null;
    return secs;
  }
  return null;
};

const formatDelta = (deltaSec) => {
  if (deltaSec === null || isNaN(deltaSec)) return "";
  const sign = deltaSec > 0 ? "+" : "-";
  const absSec = Math.abs(deltaSec);
  const hrs = Math.floor(absSec / 3600);
  const mins = Math.floor((absSec % 3600) / 60);
  const secs = Math.floor(absSec % 60);
  
  if (hrs > 0) {
    return `${sign}${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${sign}${mins}:${secs.toString().padStart(2, '0')}`;
};

const getDisplayName = (key) => {
  if (LOGISTICS_DATA[key]) return LOGISTICS_DATA[key].name;
  if (key === 'CAR_A') return 'Car A';
  if (key === 'CYBERTRUCK') return 'Cybertruck';
  if (key === 'CAR_C') return 'Car C';
  return key;
};

export default function App() {
  const [activeTab, setActiveTab] = useState('leaderboard');
  const [year, setYear] = useState('2026');
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  
  // Leaderboard data
  const [teamsData, setTeamsData] = useState([]);
  const [loadingResults, setLoadingResults] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState(null);

  // Logistics state
  const [selectedRacerKey, setSelectedRacerKey] = useState(() => {
    return localStorage.getItem('ski2sea_selected_racer') || 'IVER';
  });
  const [checklist, setChecklist] = useState(() => {
    const saved = localStorage.getItem('ski2sea_checklist');
    return saved ? JSON.parse(saved) : {};
  });

  // Location sharing state
  const [activeCheckinUser, setActiveCheckinUser] = useState('IVER');
  const [isSharingLocation, setIsSharingLocation] = useState(false);
  const [gpsStatus, setGpsStatus] = useState('inactive');
  const [lastGpsCoords, setLastGpsCoords] = useState(null);
  const [memberLocations, setMemberLocations] = useState({});
  const watchIdRef = useRef(null);

  // Countdown timer state (fires every second)
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const tick = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(tick);
  }, []);

  // Helper: format seconds into Xd Xh Xm Xs string
  const formatCountdown = (targetDate) => {
    const diff = targetDate - now;
    if (diff <= 0) return null; // event has passed
    const totalSec = Math.floor(diff / 1000);
    const d = Math.floor(totalSec / 86400);
    const h = Math.floor((totalSec % 86400) / 3600);
    const m = Math.floor((totalSec % 3600) / 60);
    const s = totalSec % 60;
    if (d > 0) return `${d}d ${h}h ${m}m ${s}s`;
    if (h > 0) return `${h}h ${m}m ${s}s`;
    return `${m}m ${s}s`;
  };

  // Connection listener
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Fetch results from RaceResult via backend proxy
  const fetchResults = async () => {
    setLoadingResults(true);
    const results = [];

    try {
      for (const t of TARGET_TEAMS) {
        const queryParams = new URLSearchParams({
          year: year,
          fields: FIELDS.join(','),
          filterbib: t.bib
        });

        const res = await fetch(`/api/results?${queryParams.toString()}`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        
        if (data && data.length > 0) {
          const row = data[0];
          const mapped = {};
          FIELDS.forEach((f, idx) => {
            mapped[f] = row[idx];
          });
          results.push({ ...t, ...mapped, success: true });
        } else {
          // If no live data, create empty skeleton
          results.push({ ...t, success: false });
        }
      }
      setTeamsData(results);
      setLastRefreshed(new Date());
      localStorage.setItem(`ski2sea_results_${year}`, JSON.stringify(results));
    } catch (err) {
      console.error("Error fetching results, loading from cache:", err);
      const cached = localStorage.getItem(`ski2sea_results_${year}`);
      if (cached) {
        setTeamsData(JSON.parse(cached));
      }
    } finally {
      setLoadingResults(false);
    }
  };

  // Poll results and locations
  useEffect(() => {
    fetchResults();
    fetchLocations();

    const resultsInterval = setInterval(fetchResults, 30000);
    const locationsInterval = setInterval(fetchLocations, 15000);

    return () => {
      clearInterval(resultsInterval);
      clearInterval(locationsInterval);
    };
  }, [year]);

  // Fetch coordinates from local server
  const fetchLocations = async () => {
    try {
      const res = await fetch('/api/location');
      if (res.ok) {
        const data = await res.json();
        setMemberLocations(data);
      }
    } catch (err) {
      console.error("Failed to fetch coordinates:", err);
    }
  };

  // Save selected racer
  useEffect(() => {
    localStorage.setItem('ski2sea_selected_racer', selectedRacerKey);
  }, [selectedRacerKey]);

  // ─── Shared Checklist ─────────────────────────────────────────
  // Poll the server for latest checklist state
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
    // Sync from server on mount and every 10 seconds
    fetchChecklist();
    const interval = setInterval(fetchChecklist, 10000);
    return () => clearInterval(interval);
  }, []);

  // Toggle checklist item — optimistic local update + server PATCH
  const toggleChecklistItem = async (racer, index) => {
    const key = `${racer}_${index}`;
    const newVal = !checklist[key];
    // Optimistic update
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

  // Location broadcasting API helper
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

  // Toggle Location Sharing
  const toggleLocationSharing = () => {
    if (isSharingLocation) {
      // Turn off
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
        watchIdRef.current = null;
      }
      setIsSharingLocation(false);
      setGpsStatus('inactive');
      setLastGpsCoords(null);
    } else {
      // Turn on
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

  // Helper to compute leg progress based on splits
  const getLegStatus = (team, legIdx) => {
    if (!team || !team.success) return 'todo';
    
    const currentLeg = LEGS_CONFIG[legIdx];
    const currentSplit = team[currentLeg.splitKey];

    // If current leg has a split time, it is finished
    if (currentSplit && currentSplit !== "0" && currentSplit !== "") {
      return 'finished';
    }

    // If it's the first leg, and team has started but no split yet, it is in progress
    if (legIdx === 0) {
      return team.Started ? 'progress' : 'todo';
    }

    // For later legs, it is in progress if the previous leg is finished but this leg has no split yet
    const prevLeg = LEGS_CONFIG[legIdx - 1];
    const prevSplit = team[prevLeg.splitKey];
    if (prevSplit && prevSplit !== "0" && prevSplit !== "") {
      return 'progress';
    }

    return 'todo';
  };

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

            {/* Race Start Countdown Banner */}
            {year === '2026' && (() => {
              const remaining = formatCountdown(RACE_START);
              if (!remaining) return null;
              const urgency = (RACE_START - now) < 3600000; // < 1 hour
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
                      🏁 {remaining}
                    </div>
                  </div>
                  <div style={{ fontSize: '1.5rem' }}>{urgency ? '⚡' : '⏳'}</div>
                </div>
              );
            })()}

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
                            {/* Show actual API team name if different (e.g. in 2024 test mode) */}
                            {t.TeamName && t.TeamName.toLowerCase() !== t.name.toLowerCase() && (
                              <div className="subtext" style={{ fontSize: '0.7rem', fontStyle: 'italic' }}>
                                2024 BIB: {t.TeamName}
                              </div>
                            )}
                            <div className="subtext" style={{ fontSize: '0.75rem' }}>
                              {t.Division || "Competitive"}
                            </div>
                          </td>
                          <td style={{ fontSize: '0.8rem', color: '#06b6d4' }}>{lastLeg}</td>
                          <td style={{ fontFamily: 'var(--font-title)', fontWeight: 'bold', fontSize: '0.85rem' }}>{lastTime}</td>
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
                  const status = getLegStatus(mainTeam, legIdx);
                  const racer = mainTeam ? mainTeam[leg.racerKey] : null;
                  const time = mainTeam ? mainTeam[leg.splitKey] : null;
                  const rank = mainTeam ? mainTeam[leg.rankKey] : null;
                  // Fallback names only shown before first load; once API data
                  // is in, trust it — a zero/empty field means no name available
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
                              <div className="subtext" style={{ fontSize: '0.72rem', marginTop: '2px', whiteSpace: 'nowrap' }}>
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
                            )}
                            <div className="leg-rank" style={{ fontSize: '0.75rem', marginTop: '2px' }}>Rank: {rank && rank !== -1 ? rank : "—"}</div>
                          </div>
                        ) : status === 'progress' ? (
                          <div style={{ textAlign: 'right' }}>
                            <span className="status-badge status-progress">Racing</span>
                            {year !== '2025' && JACKSONS_2025_SPLITS[leg.id] && (
                              <div className="subtext" style={{ fontSize: '0.72rem', marginTop: '4px', whiteSpace: 'nowrap' }}>
                                2025: {JACKSONS_2025_SPLITS[leg.id].time}
                              </div>
                            )}
                          </div>
                        ) : (
                          <div style={{ textAlign: 'right' }}>
                            <span className="status-badge status-todo">Waiting</span>
                            {year !== '2025' && JACKSONS_2025_SPLITS[leg.id] && (
                              <div className="subtext" style={{ fontSize: '0.72rem', marginTop: '4px', whiteSpace: 'nowrap' }}>
                                2025: {JACKSONS_2025_SPLITS[leg.id].time}
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
        )}


        {activeTab === 'map' && (
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
                  <span>Active (&lt;5m)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#f59e0b' }}></div>
                  <span>Delayed (&lt;15m)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#94a3b8' }}></div>
                  <span>Stale (&gt;15m)</span>
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
        )}

        {activeTab === 'logistics' && (
          <div>
            <div className="form-group">
              <label className="form-label">Show Schedule For:</label>
              <select 
                value={selectedRacerKey} 
                onChange={(e) => setSelectedRacerKey(e.target.value)}
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
                      const remaining = formatCountdown(BRIEFING_TIMES[selectedRacerKey]);
                      if (!remaining) {
                        // Past — just show done
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
        )}

        {activeTab === 'checkin' && (
          <div>
            <div className="card">
              <h3 className="section-title">📡 Location Broadcast (GPS)</h3>
              <p className="subtext" style={{ marginBottom: '1rem' }}>
                Turn this on when it is your turn to race or support. Keep this browser page open in your pocket so teammates can track your live position.
              </p>

              <div className="form-group">
                <label className="form-label">Identify As:</label>
                <select 
                  value={activeCheckinUser} 
                  onChange={(e) => setActiveCheckinUser(e.target.value)}
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

              <div style={{ margin: '1.5rem 0 1rem' }}>
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
            
            <div className="card">
              <h3 className="section-title">🔌 Background GPS (Overland App)</h3>
              <p className="subtext" style={{ lineHeight: '1.4', marginBottom: '1rem' }}>
                For reliable background tracking while your phone is locked in your pocket, use the free <b>Overland</b> app.
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
                 <p className="subtext" style={{ fontSize: '0.75rem', marginTop: '4px', lineHeight: '1.5' }}>
                  1. Install <b>Overland</b> from iOS App Store.<br />
                  2. Select your identity above.<br />
                  3. Tap button above to configure.<br />
                  4. <b>iOS Settings:</b> Go to Settings → Overland → Location → select <b>"Always Allow"</b> (enables background tracking. Note: you may need to choose/trigger location settings twice to prompt/unlock the "Always Allow" option).<br />
                  5. <b>In Overland App:</b> Toggle the tracking switch at top to <b>ON</b>.
                </p>
              </div>
            </div>
            
            <div className="card">
              <h3 className="section-title">📱 iOS Standalone Instructions</h3>
              <p className="subtext" style={{ lineHeight: '1.4' }}>
                To use this as an App, tap the <b>Share</b> button in Safari and select <b>Add to Home Screen</b>.
                <br /><br />
                <b>Important:</b> iOS Safari suspends GPS updates when the screen is locked or app is closed. Make sure to keep the phone screen active with the app open during your leg to ensure continuous tracking.
              </p>
            </div>
          </div>
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
          {/* In test years, also show the actual team name from API */}
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

// Map Component nested to easily consume locations

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
        const timeDiffMins = Math.round((Date.now() - loc.timestamp) / 60000);
        
        let markerColor = '#94a3b8'; // stale > 15m (grey)
        if (timeDiffMins < 5) markerColor = '#14b8a6'; // active < 5m (teal)
        else if (timeDiffMins < 15) markerColor = '#f59e0b'; // warning < 15m (amber)

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
