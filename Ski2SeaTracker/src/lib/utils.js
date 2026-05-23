import { 
  LEGS_CONFIG, 
  JACKSONS_2025_SPLITS, 
  RACE_START_2025, 
  LOGISTICS_DATA 
} from './constants.js';

export const parseTimeToSeconds = (timeStr) => {
  if (!timeStr || timeStr === "0" || timeStr === "—") return null;
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

export const formatDelta = (deltaSec) => {
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

export const getFallbackRacer = (bib, legId) => {
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

export const get2025LegStartTime = (legId) => {
  let cumulativeSec = 0;
  for (let i = 0; i < LEGS_CONFIG.length; i++) {
    const leg = LEGS_CONFIG[i];
    if (leg.id === legId) {
      return new Date(RACE_START_2025.getTime() + cumulativeSec * 1000);
    }
    const split2025 = JACKSONS_2025_SPLITS[leg.id];
    if (split2025) {
      cumulativeSec += split2025.seconds;
    }
  }
  return RACE_START_2025;
};

export const getDisplayName = (key) => {
  if (LOGISTICS_DATA[key]) return LOGISTICS_DATA[key].name;
  if (key === 'CAR_A') return "Iver's Model Y";
  if (key === 'CYBERTRUCK') return 'Cybertruck';
  if (key === 'CAR_C') return "Sam's Bronco";
  return key;
};

export const formatCountdown = (targetDate, now) => {
  const diff = targetDate - now;
  if (diff <= 0) return null;
  const totalSec = Math.floor(diff / 1000);
  const d = Math.floor(totalSec / 86400);
  const h = Math.floor((totalSec % 86400) / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  if (d > 0) return `${d}d ${h}h ${m}m ${s}s`;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  return `${m}m ${s}s`;
};

// Calculate team standing: returns completed leg count and cumulative time
export const getTeamStanding = (team) => {
  let completedLegCount = 0;
  let cumulativeTime = 0;
  for (let i = 0; i < LEGS_CONFIG.length; i++) {
    const splitVal = team[LEGS_CONFIG[i].splitKey];
    const sec = parseTimeToSeconds(splitVal);
    if (sec !== null && sec > 0) {
      completedLegCount = i + 1;
      cumulativeTime += sec;
    } else {
      break;
    }
  }
  return { completedLegCount, cumulativeTime };
};

// Return status of a leg for a team ('finished', 'progress', 'todo')
export const getLegStatus = (team, legIdx, now, raceStart) => {
  if (!team || !team.success) return 'todo';
  
  const currentLeg = LEGS_CONFIG[legIdx];
  const currentSplit = team[currentLeg.splitKey];

  if (currentSplit && currentSplit !== "0" && currentSplit !== "") {
    return 'finished';
  }

  // CRITICAL race-start logic (Task 1):
  // Force leg 0 to 'progress' if now >= raceStart and first split is not completed
  if (legIdx === 0) {
    const hasStarted = team.Started || now >= raceStart;
    return hasStarted ? 'progress' : 'todo';
  }

  const prevLeg = LEGS_CONFIG[legIdx - 1];
  const prevSplit = team[prevLeg.splitKey];
  if (prevSplit && prevSplit !== "0" && prevSplit !== "") {
    return 'progress';
  }

  return 'todo';
};

// Format seconds into a race time duration string (h:mm:ss.d or mm:ss.d)
export const formatSecondsToTime = (totalSeconds) => {
  if (totalSeconds === null || totalSeconds === undefined || isNaN(totalSeconds) || totalSeconds <= 0) return "—";
  
  // Round to nearest tenth first to avoid rollover issues during formatting
  const roundedSecs = Math.round(totalSeconds * 10) / 10;
  
  const hrs = Math.floor(roundedSecs / 3600);
  const mins = Math.floor((roundedSecs % 3600) / 60);
  const secs = Math.floor(roundedSecs % 60);
  const tenths = Math.round((roundedSecs % 1) * 10);
  
  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${tenths}`;
  }
  return `${mins}:${secs.toString().padStart(2, '0')}.${tenths}`;
};

