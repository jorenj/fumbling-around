import { 
  parseTimeToSeconds, 
  formatDelta, 
  getTeamStanding, 
  getLegStatus,
  formatSecondsToTime
} from '../src/lib/utils.js';
import { RACE_START } from '../src/lib/constants.js';

function runTests() {
  console.log("=== Running Utility Tests ===");

  // 1. parseTimeToSeconds
  console.assert(parseTimeToSeconds("49:44.2") === 2984.2, "parseTimeToSeconds MM:SS.d failed");
  console.assert(parseTimeToSeconds("1:44:27.8") === 6267.8, "parseTimeToSeconds HH:MM:SS.d failed");
  console.assert(parseTimeToSeconds("0") === null, "parseTimeToSeconds '0' failed");
  console.assert(parseTimeToSeconds("—") === null, "parseTimeToSeconds '—' failed");
  console.assert(parseTimeToSeconds("") === null, "parseTimeToSeconds empty string failed");
  console.log("✓ parseTimeToSeconds passed");

  // 2. formatDelta
  console.assert(formatDelta(125) === "+2:05", "formatDelta positive 2m5s failed");
  console.assert(formatDelta(-125) === "-2:05", "formatDelta negative 2m5s failed");
  console.assert(formatDelta(3665) === "+1:01:05", "formatDelta positive 1h1m5s failed");
  console.assert(formatDelta(0) === "-0:00", "formatDelta 0 failed"); // sign is - because 0 is not > 0
  console.log("✓ formatDelta passed");

  // 2.5. formatSecondsToTime
  console.assert(formatSecondsToTime(27155.8) === "7:32:35.8", `formatSecondsToTime(27155.8) expected "7:32:35.8", got "${formatSecondsToTime(27155.8)}"`);
  console.assert(formatSecondsToTime(30292.3) === "8:24:52.3", `formatSecondsToTime(30292.3) expected "8:24:52.3", got "${formatSecondsToTime(30292.3)}"`);
  console.assert(formatSecondsToTime(59.99) === "1:00.0", `formatSecondsToTime(59.99) expected "1:00.0", got "${formatSecondsToTime(59.99)}"`);
  console.assert(formatSecondsToTime(3599.99) === "1:00:00.0", `formatSecondsToTime(3599.99) expected "1:00:00.0", got "${formatSecondsToTime(3599.99)}"`);
  console.assert(formatSecondsToTime(0) === "—", `formatSecondsToTime(0) expected "—", got "${formatSecondsToTime(0)}"`);
  console.assert(formatSecondsToTime(null) === "—", `formatSecondsToTime(null) expected "—", got "${formatSecondsToTime(null)}"`);
  console.log("✓ formatSecondsToTime passed");

  // 3. getTeamStanding
  const mockTeamFinishedTwo = {
    XCSKI_SPLIT: "45:00.0",
    DHSKI_SPLIT: "30:00.0",
    RUN_SPLIT: "",
    ROADBIKE_SPLIT: ""
  };
  const standing = getTeamStanding(mockTeamFinishedTwo);
  console.assert(standing.completedLegCount === 2, `getTeamStanding completed legs count: ${standing.completedLegCount}`);
  console.assert(standing.cumulativeTime === 4500, `getTeamStanding cumulative time: ${standing.cumulativeTime}`);
  console.log("✓ getTeamStanding passed");

  // 4. getLegStatus (Race Start edge-cases)
  const mockTeamNotStarted = {
    success: true,
    Started: false,
    XCSKI_SPLIT: "",
  };

  // Case A: Before race start, not started in API
  const beforeRace = new Date(RACE_START.getTime() - 10000); // 10s before
  const statusBefore = getLegStatus(mockTeamNotStarted, 0, beforeRace, RACE_START);
  console.assert(statusBefore === 'todo', `getLegStatus before race should be 'todo', got '${statusBefore}'`);

  // Case B: After race start, but API Started flag is false/undefined (the bug!)
  const afterRace = new Date(RACE_START.getTime() + 10000); // 10s after
  const statusAfter = getLegStatus(mockTeamNotStarted, 0, afterRace, RACE_START);
  console.assert(statusAfter === 'progress', `getLegStatus after race (bugfix) should be 'progress', got '${statusAfter}'`);

  // Case C: Leg 0 has a split time
  const mockTeamFinishedOne = {
    success: true,
    Started: true,
    XCSKI_SPLIT: "50:00.0"
  };
  const statusFinished = getLegStatus(mockTeamFinishedOne, 0, afterRace, RACE_START);
  console.assert(statusFinished === 'finished', `getLegStatus finished should be 'finished', got '${statusFinished}'`);

  // Case D: Leg 1 in progress (since Leg 0 is finished)
  const statusLeg1 = getLegStatus(mockTeamFinishedOne, 1, afterRace, RACE_START);
  console.assert(statusLeg1 === 'progress', `getLegStatus Leg 1 should be 'progress', got '${statusLeg1}'`);

  console.log("✓ getLegStatus passed");
  console.log("=== All Tests Passed successfully! ===");
}

runTests();
