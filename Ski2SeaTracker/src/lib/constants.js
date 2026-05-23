// Competitors to track
export const TARGET_TEAMS = [
  { bib: 101, name: "Jacksons Speak Louder than Words", isMain: true },
  { bib: 39, name: "No Bros, Just Pros" },
  { bib: 24, name: "Mentally Ready - Physically Not" },
  { bib: 32, name: "Daddy's Back, by Kenny Loggins" }
];

// Race start: May 24, 2026 at 7:30am Pacific (PDT = UTC-7)
export const RACE_START = new Date('2026-05-24T07:30:00-07:00');

// Briefing times per racer (PDT). Used to show countdown on their checklist.
export const BRIEFING_TIMES = {
  IVER:     new Date('2026-05-24T07:00:00-07:00'),
  TAVIN:    new Date('2026-05-24T07:00:00-07:00'),
  MAC:      new Date('2026-05-24T08:00:00-07:00'),
  JONATHAN: new Date('2026-05-24T09:00:00-07:00'),
  CARMEN:   new Date('2026-05-24T09:15:00-07:00'),
  YVETTE:   new Date('2026-05-24T09:15:00-07:00'),
  DAVID:    new Date('2026-05-24T11:45:00-07:00'),
  JOREN:    new Date('2026-05-24T11:00:00-07:00'),
};

// 7 Legs config in order
export const LEGS_CONFIG = [
  { id: 'xcski', name: 'XC Ski', racerKey: 'XC_Ski_Racer', splitKey: 'XCSKI_SPLIT', rankKey: 'XCSKIRank', desc: 'Cross Country Ski at Mt. Baker' },
  { id: 'dhski', name: 'DH Ski', racerKey: 'DH_Ski_Snowboard_Racer', splitKey: 'DHSKI_SPLIT', rankKey: 'DHSKIRank', desc: 'Downhill Ski/Snowboard at Mt. Baker' },
  { id: 'run', name: 'Run', racerKey: 'Run_Racer', splitKey: 'RUN_SPLIT', rankKey: 'RunRank', desc: 'Run down Mt. Baker Highway' },
  { id: 'bike', name: 'Road Bike', racerKey: 'RD_Bike_Racer', splitKey: 'ROADBIKE_SPLIT', rankKey: 'RoadBikeRank', desc: 'Road Bike to Everson' },
  { id: 'canoe', name: 'Canoe', racerKey: 'Canoers', splitKey: 'CANOE_SPLIT', rankKey: 'CanoeRank', desc: 'Canoe down Nooksack River to Hovander Park' },
  { id: 'cyclox', name: 'Cyclocross', racerKey: 'CX_Racer', splitKey: 'CYCLOCROSS_SPLIT', rankKey: 'CyclocrossRank', desc: 'Cyclocross Bike in Hovander Park' },
  { id: 'kayak', name: 'Kayak', racerKey: 'Kayak_Racer', splitKey: 'KAYAK_SPLIT', rankKey: 'KayakRank', desc: 'Sea Kayak to Bellingham Bay Finish' }
];

// Map transition zones
export const TRANSITIONS = [
  { name: "Mt. Baker Area", leg: "XC Ski, DH Ski, Run Start", lat: 48.857, lng: -121.679, desc: "Leg 1 (XC Ski) and Leg 2 (DH Ski) start/finish. Leg 3 (Run) starts. Mountain Road closes at 7:15am." },
  { name: "DOT Station (Canyon Creek)", leg: "Run to Road Bike", lat: 48.910, lng: -122.095, desc: "Leg 3 runner finishes, Leg 4 road biker launches." },
  { name: "Everson (Riverside Park)", leg: "Road Bike to Canoe", lat: 48.917, lng: -122.349, desc: "Leg 4 road biker finishes, Leg 5 canoeists launch." },
  { name: "Hovander Homestead Park (Ferndale)", leg: "Canoe to Cyclocross", lat: 48.836, lng: -122.594, desc: "Leg 5 canoeists finish, Leg 6 cyclocross biker launches." },
  { name: "Zuanich Park (Bellingham)", leg: "Cyclocross to Kayak", lat: 48.754, lng: -122.512, desc: "Leg 6 cyclocross biker finishes, Leg 7 kayaker launches." },
  { name: "Marine Park (Fairhaven)", leg: "Kayak Finish", lat: 48.719, lng: -122.516, desc: "Leg 7 kayaker finishes. Finish Line and celebration here!" }
];

// Maps leg id → LOGISTICS_DATA key(s) for GPS lookup
export const LEG_RACER_MAP = {
  xcski:  ['IVER'],
  dhski:  ['TAVIN'],
  run:    ['MAC'],
  bike:   ['JONATHAN'],
  canoe:  ['CARMEN', 'YVETTE'],
  cyclox: ['JOREN'],
  kayak:  ['DAVID'],
};

// Maps leg id → start/finish TRANSITIONS indices
export const LEG_TRANSITIONS = {
  xcski:  { start: 0, finish: 0 },
  dhski:  { start: 0, finish: 0 },
  run:    { start: 0, finish: 1 },
  bike:   { start: 1, finish: 2 },
  canoe:  { start: 2, finish: 3 },
  cyclox: { start: 3, finish: 4 },
  kayak:  { start: 4, finish: 5 },
};

// Logistics task lists
export const LOGISTICS_DATA = {
  IVER: {
    name: "Iver Jackson",
    leg: "Cross Country Ski",
    briefing: "7:00am briefing @ Mt. Baker Ski Area",
    car: "Iver's Model Y (with Tavin, Mac, Sam)",
    tasks: [
      "Drive up to Mt. Baker in Iver's Model Y with Tavin, Mac, and Sam.",
      "Attend the 7:00am briefing and warmup.",
      "Ski super fast! (Leg 1)",
      "Wait for the mountain road to open after DH Ski.",
      "Drop Tavin off at Jonathan's trailer.",
      "Proceed to Hovander Park (Canoe/Cyclocross transition) to hang out.",
      "Drive Iver's Model Y with Sam to the Cyclocross finish.",
      "Help David launch the kayak.",
      "Drive Iver's Model Y to the finish line at Marine Park."
    ]
  },
  TAVIN: {
    name: "Tavin Jackson",
    leg: "Downhill Ski/Snowboard",
    briefing: "7:00am briefing @ Mt. Baker Ski Area",
    car: "Iver's Model Y, then Jonathan's trailer, then Cybertruck",
    tasks: [
      "Drive up to Mt. Baker in Iver's Model Y with Iver, Mac, and Sam.",
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
    car: "Iver's Model Y, then Cybertruck",
    tasks: [
      "Drive up to Mt. Baker in Iver's Model Y, get dropped off at the run start (Canyon Lake / DOT).",
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
    car: "Sam's Bronco",
    tasks: [
      "Drive Sam's Bronco with Joren to Hovander Park in time for the 11:00am cyclocross briefing.",
      "Leave Hovander Park early in Sam's Bronco to get to the Kayak launch.",
      "Attend the 11:45am kayak briefing.",
      "Kayak super fast! (Leg 7)",
      "Beers at the finish line!"
    ]
  },
  JOREN: {
    name: "Joren Jackson",
    leg: "Cyclocross",
    briefing: "11:00am briefing @ Hovander Park",
    car: "Sam's Bronco",
    tasks: [
      "Drive in Sam's Bronco with David to Hovander Park.",
      "Attend the 11:00am cyclocross briefing.",
      "Bike super fast! (Leg 6)",
      "Drive Sam's Bronco to the finish line with Sam"
    ]
  }
};

export const FIELDS = [
  "BIB", "id", "TeamName", "Division", "Started",
  "XC_Ski_Racer", "XCSKI_SPLIT", "XCSKIRank",
  "DH_Ski_Snowboard_Racer", "DHSKI_SPLIT", "DHSKIRank",
  "Run_Racer", "RUN_SPLIT", "RunRank",
  "RD_Bike_Racer", "ROADBIKE_SPLIT", "RoadBikeRank",
  "Canoers", "CANOE_SPLIT", "CanoeRank",
  "CX_Racer", "CYCLOCROSS_SPLIT", "CyclocrossRank",
  "Kayak_Racer", "KAYAK_SPLIT", "KayakRank"
];

// 2025 Splits for Jacksons Speak Louder Than Words (BIB 471 in 2025)
export const JACKSONS_2025_SPLITS = {
  xcski: { time: "49:44.2", seconds: 2984.2, rank: 258, racer: "Yvette Jackson" },
  dhski: { time: "30:50.7", seconds: 1850.7, rank: 82, racer: "Tavin Jackson" },
  run: { time: "50:49.4", seconds: 3049.4, rank: 136, racer: "Mackenzie Brown" },
  bike: { time: "1:44:27.8", seconds: 6267.8, rank: 44, racer: "Jonathan Anderson" },
  canoe: { time: "2:23:07.6", seconds: 8587.6, rank: 61, racer: "Carmen Jackson / David Jackson" },
  cyclox: { time: "43:23.1", seconds: 2603.1, rank: 91, racer: "Joren Jackson" },
  kayak: { time: "36:49.9", seconds: 2209.9, rank: 119, racer: "Iver Jackson" }
};

// 2025 Race start
export const RACE_START_2025 = new Date('2025-05-25T07:30:00-07:00');
