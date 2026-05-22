import { FIELDS } from '../src/lib/constants.js';
import { getTeamStanding } from '../src/lib/utils.js';

async function main() {
  const url = `https://api.raceresult.com/291757/02PHAOGJWM5QHZELNBVH09BKZDMR3IWT?listFormat=JSON&fields=${FIELDS.join(',')}`;
  
  console.log("Fetching 2024 results...");
  const res = await fetch(url);
  const data = await res.json();
  
  console.log(`Fetched ${data.length} teams.`);
  
  const allTeamsMapped = data.map(row => {
    const mapped = {};
    FIELDS.forEach((f, idx) => {
      mapped[f] = row[idx];
    });
    mapped.bib = parseInt(mapped.BIB, 10);
    return mapped;
  });

  const teamsWithStanding = allTeamsMapped.map(team => {
    const { completedLegCount, cumulativeTime } = getTeamStanding(team);
    return {
      ...team,
      completedLegCount,
      cumulativeTime
    };
  });

  const sortedAllTeams = [...teamsWithStanding].sort((a, b) => {
    if (a.completedLegCount !== b.completedLegCount) {
      return b.completedLegCount - a.completedLegCount;
    }
    return a.cumulativeTime - b.cumulativeTime;
  });

  let currentRank = 1;
  const totalTeams = teamsWithStanding.length;
  sortedAllTeams.forEach((team, idx) => {
    team.totalTeams = totalTeams;
    if (team.completedLegCount === 0) {
      team.overallRank = null;
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

  // Find Aleshops (BIB 458) and Jacksons (BIB 463) and City Haul (BIB 101)
  const targetBibs = [458, 463, 101];
  targetBibs.forEach(bib => {
    const t = sortedAllTeams.find(x => x.bib === bib);
    if (t) {
      console.log(`BIB: ${t.bib} | Name: ${t.TeamName} | Division: ${t.Division} | Rank: ${t.overallRank} | Legs: ${t.completedLegCount} | Cumulative Time: ${t.cumulativeTime}s`);
    } else {
      console.log(`BIB: ${bib} not found`);
    }
  });
}

main();
