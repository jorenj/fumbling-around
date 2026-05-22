import { useState, useEffect, useCallback } from 'react';
import { FIELDS, TARGET_TEAMS, LEGS_CONFIG } from '../lib/constants';
import { getTeamStanding } from '../lib/utils';

export function useRaceData(year) {
  const [teamsData, setTeamsData] = useState([]);
  const [loadingResults, setLoadingResults] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState(null);
  const [events, setEvents] = useState([]);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [memberLocations, setMemberLocations] = useState({});

  // Reset/load cached data immediately on year change to prevent flashing stale data
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTeamsData([]);
    setLastRefreshed(null);
    
    const savedEvents = localStorage.getItem(`ski2sea_events_${year}`);
    setEvents(savedEvents ? JSON.parse(savedEvents) : []);

    const cachedResults = localStorage.getItem(`ski2sea_results_${year}`);
    if (cachedResults) {
      try {
        setTeamsData(JSON.parse(cachedResults));
      } catch {
        // Ignore
      }
    }
  }, [year]);

  // Connection monitoring
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

  // Fetch coordinates from local server
  const fetchLocations = useCallback(async () => {
    try {
      const res = await fetch('/api/location');
      if (res.ok) {
        const data = await res.json();
        setMemberLocations(data);
      }
    } catch (err) {
      console.error("Failed to fetch coordinates:", err);
    }
  }, []);

  // Fetch results from RaceResult via backend proxy
  const fetchResults = useCallback(async () => {
    setLoadingResults(true);
    try {
      const queryParams = new URLSearchParams({
        year: year,
        fields: FIELDS.join(',')
      });

      const res = await fetch(`/api/results?${queryParams.toString()}`);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      
      if (data && data.length > 0) {
        const allTeamsMapped = data.map(row => {
          const mapped = {};
          FIELDS.forEach((f, idx) => {
            mapped[f] = row[idx];
          });
          mapped.bib = parseInt(mapped.BIB, 10);
          return mapped;
        });

        // Precompute standing fields for sorting performance (Task 3)
        const teamsWithStanding = allTeamsMapped.map(team => {
          const { completedLegCount, cumulativeTime } = getTeamStanding(team);
          return {
            ...team,
            completedLegCount,
            cumulativeTime
          };
        });

        // Sort all teams to calculate overall position
        const sortedAllTeams = [...teamsWithStanding].sort((a, b) => {
          if (a.completedLegCount !== b.completedLegCount) {
            return b.completedLegCount - a.completedLegCount; // More completed legs first
          }
          return a.cumulativeTime - b.cumulativeTime; // Lower cumulative time first
        });

        // Assign overall position
        let currentRank = 1;
        const totalTeams = teamsWithStanding.length;
        sortedAllTeams.forEach((team, idx) => {
          team.totalTeams = totalTeams;
          if (team.completedLegCount === 0) {
            team.overallRank = null; // Has not started
          } else {
            if (idx > 0) {
              const prev = sortedAllTeams[idx - 1];
              if (prev.completedLegCount !== team.completedLegCount || prev.cumulativeTime !== team.cumulativeTime) {
                currentRank = idx + 1;
              }
            }
            team.overallRank = currentRank;
          }
        });

        // Map targeted teams
        const targetedResults = TARGET_TEAMS.map(t => {
          const found = teamsWithStanding.find(at => at.bib === t.bib);
          if (found) {
            return { ...t, ...found, success: true };
          }
          return { ...t, success: false };
        });

        // Filter and sort Family division teams (excluding all targeted teams)
        const familyCompetitors = teamsWithStanding.filter(t => {
          const isTargeted = TARGET_TEAMS.some(target => target.bib === t.bib);
          if (isTargeted) return false;
          return t.Division && t.Division.toLowerCase().includes('family');
        });

        familyCompetitors.sort((a, b) => {
          if (a.completedLegCount !== b.completedLegCount) {
            return b.completedLegCount - a.completedLegCount;
          }
          return a.cumulativeTime - b.cumulativeTime;
        });

        // Select top 2 family competitor teams
        const topFamily = familyCompetitors.slice(0, 2).map(t => ({
          bib: t.bib,
          name: t.TeamName || `Team ${t.bib}`,
          ...t,
          success: true,
          isFamilyCompetitor: true
        }));

        // Combine targeted teams + top 2 family competitors
        const finalResults = [...targetedResults, ...topFamily];

        // Event detection: compare against previously cached results
        let prevResults = [];
        const cachedResults = localStorage.getItem(`ski2sea_results_${year}`);
        if (cachedResults) {
          try {
            prevResults = JSON.parse(cachedResults);
          } catch {
            // Ignore
          }
        }

        if (prevResults && prevResults.length > 0) {
          const newEvents = [];
          finalResults.forEach(newTeam => {
            const prevTeam = prevResults.find(pt => pt.bib === newTeam.bib);
            if (prevTeam) {
              LEGS_CONFIG.forEach(leg => {
                const newVal = newTeam[leg.splitKey];
                const prevVal = prevTeam[leg.splitKey];
                const hasNewSplit = (newVal && newVal !== "0" && newVal !== "—" && newVal !== "") &&
                                    (!prevVal || prevVal === "0" || prevVal === "—" || prevVal === "");
                if (hasNewSplit) {
                  newEvents.push({
                    id: `${newTeam.bib}_${leg.id}_${Date.now()}`,
                    bib: newTeam.bib,
                    teamName: newTeam.name,
                    legName: leg.name,
                    split: newVal,
                    timestamp: Date.now()
                  });
                }
              });
            }
          });

          if (newEvents.length > 0) {
            setEvents(prev => {
              const updated = [...newEvents, ...prev].slice(0, 3);
              localStorage.setItem(`ski2sea_events_${year}`, JSON.stringify(updated));
              return updated;
            });
          }
        }

        setTeamsData(finalResults);
        setLastRefreshed(new Date());
        localStorage.setItem(`ski2sea_results_${year}`, JSON.stringify(finalResults));
      } else {
        throw new Error("No data returned from API");
      }
    } catch (err) {
      console.error("Error fetching results, loading from cache:", err);
      const cached = localStorage.getItem(`ski2sea_results_${year}`);
      if (cached) {
        setTeamsData(JSON.parse(cached));
      }
    } finally {
      setLoadingResults(false);
    }
  }, [year]);

  // Poll results and locations
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchResults();
    fetchLocations();

    const resultsInterval = setInterval(fetchResults, 7000);
    const locationsInterval = setInterval(fetchLocations, 15000);

    return () => {
      clearInterval(resultsInterval);
      clearInterval(locationsInterval);
    };
  }, [year, fetchResults, fetchLocations]);

  const clearEvents = useCallback(() => {
    setEvents([]);
    localStorage.removeItem(`ski2sea_events_${year}`);
  }, [year]);

  return {
    teamsData,
    loadingResults,
    lastRefreshed,
    events,
    clearEvents,
    isOnline,
    memberLocations,
    fetchResults,
    fetchLocations
  };
}
