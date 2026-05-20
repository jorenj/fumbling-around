import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DATA_DIR = path.join(__dirname, 'data');
const DATA_FILE = path.join(DATA_DIR, 'locations.json');
const CHECKLIST_FILE = path.join(DATA_DIR, 'checklist.json');

// Ensure directory exists
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

// In-memory cache of locations: { [memberName]: { lat, lng, timestamp } }
let locationsCache = {};

// Load existing locations from file on startup
try {
  if (fs.existsSync(DATA_FILE)) {
    const rawData = fs.readFileSync(DATA_FILE, 'utf8');
    locationsCache = JSON.parse(rawData);
    console.log('Loaded locations from file:', Object.keys(locationsCache).length, 'entries');
  }
} catch (err) {
  console.error('Error loading locations file, starting fresh:', err);
}

// Save locations cache to file
const saveToFile = () => {
  try {
    fs.writeFileSync(DATA_FILE, JSON.stringify(locationsCache, null, 2), 'utf8');
  } catch (err) {
    console.error('Error saving locations to file:', err);
  }
};

/**
 * Updates a member's location.
 * @param {string} member Name of the team member
 * @param {number} lat Latitude
 * @param {number} lng Longitude
 * @param {number} accuracy GPS accuracy in meters (optional)
 */
export function updateLocation(member, lat, lng, accuracy = null, timestamp = null) {
  if (!member || typeof lat !== 'number' || typeof lng !== 'number') {
    throw new Error('Invalid location payload');
  }

  locationsCache[member] = {
    lat,
    lng,
    accuracy,
    timestamp: timestamp || Date.now()
  };

  saveToFile();
  return locationsCache[member];
}

/**
 * Returns all active locations.
 */
export function getAllLocations() {
  return locationsCache;
}

// ─── Shared Checklist ───────────────────────────────────────────────────────

// In-memory cache: { ["RACER_taskIndex"]: true|false }
let checklistCache = {};

try {
  if (fs.existsSync(CHECKLIST_FILE)) {
    const raw = fs.readFileSync(CHECKLIST_FILE, 'utf8');
    checklistCache = JSON.parse(raw);
    console.log('Loaded checklist from file:', Object.keys(checklistCache).length, 'entries');
  }
} catch (err) {
  console.error('Error loading checklist file, starting fresh:', err);
}

const saveChecklist = () => {
  try {
    fs.writeFileSync(CHECKLIST_FILE, JSON.stringify(checklistCache, null, 2), 'utf8');
  } catch (err) {
    console.error('Error saving checklist to file:', err);
  }
};

/**
 * Returns the full checklist state.
 */
export function getChecklist() {
  return checklistCache;
}

/**
 * Sets a single checklist key to true/false.
 * @param {string} key  e.g. "IVER_2"
 * @param {boolean} checked
 */
export function setChecklistItem(key, checked) {
  checklistCache[key] = !!checked;
  saveChecklist();
  return checklistCache;
}

/**
 * Bulk-replace the entire checklist (for reset operations).
 */
export function replaceChecklist(data) {
  checklistCache = data;
  saveChecklist();
  return checklistCache;
}
