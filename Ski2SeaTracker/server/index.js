/* global process */
import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { updateLocation, getAllLocations, getChecklist, setChecklistItem, replaceChecklist } from './db.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3001;

// Parse JSON bodies
app.use(express.json());

// Log requests
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  next();
});

// In-memory rate limiter for results proxy
const ipLimits = {};
const RATE_LIMIT_WINDOW = 60 * 1000; // 1 minute
const MAX_REQUESTS = 60; // 60 requests per minute per IP

const resultsRateLimiter = (req, res, next) => {
  const ip = req.ip || req.headers['x-forwarded-for'] || req.socket.remoteAddress;
  const now = Date.now();
  
  if (!ipLimits[ip]) {
    ipLimits[ip] = [];
  }
  
  // Filter timestamps within window
  ipLimits[ip] = ipLimits[ip].filter(timestamp => now - timestamp < RATE_LIMIT_WINDOW);
  
  if (ipLimits[ip].length >= MAX_REQUESTS) {
    return res.status(429).json({ error: 'Too many requests. Please try again later.' });
  }
  
  ipLimits[ip].push(now);
  next();
};

// API Key configuration on backend to keep keys secure
const RACERESULT_API_KEY = process.env.RACERESULT_API_KEY || "02PHAOGJWM5QHZELNBVH09BKZDMR3IWT";
const YEARS_CONFIG = {
  "2026": 399822,
  "2025": 340596,
  "2024": 291757
};

const VALID_IDENTITIES = new Set([
  'IVER', 'TAVIN', 'MAC', 'JONATHAN', 'CARMEN', 'YVETTE', 'DAVID', 'JOREN',
  'CAR_A', 'CYBERTRUCK', 'CAR_C'
]);

// GET Health API
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', uptime: process.uptime() });
});

// GET Checklist (returns full shared checklist state)
app.get('/api/checklist', (req, res) => {
  res.json(getChecklist());
});

// PATCH Checklist item
app.patch('/api/checklist', (req, res) => {
  try {
    const { key, checked } = req.body;
    if (typeof key !== 'string' || typeof checked !== 'boolean') {
      return res.status(400).json({ error: 'key (string) and checked (boolean) required' });
    }
    const updated = setChecklistItem(key, checked);
    res.json(updated);
  } catch (err) {
    console.error('Error updating checklist:', err);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

// PUT Checklist (full replace, e.g. reset)
app.put('/api/checklist', (req, res) => {
  try {
    const data = req.body;
    if (typeof data !== 'object') {
      return res.status(400).json({ error: 'Body must be a JSON object' });
    }
    const updated = replaceChecklist(data);
    res.json(updated);
  } catch (err) {
    console.error('Error replacing checklist:', err);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});


// GET Locations API
app.get('/api/location', (req, res) => {
  try {
    const locations = getAllLocations();
    res.json(locations);
  } catch (error) {
    console.error('Error fetching locations:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

// POST Location API
app.post('/api/location', (req, res) => {
  try {
    const { member, lat, lng, accuracy } = req.body;
    
    if (!member || typeof lat !== 'number' || typeof lng !== 'number') {
      return res.status(400).json({ error: 'Missing or invalid location parameters' });
    }

    const normalizedMember = member.toUpperCase();
    if (!VALID_IDENTITIES.has(normalizedMember)) {
      return res.status(400).json({ error: 'Invalid member identity' });
    }

    const updated = updateLocation(normalizedMember, lat, lng, accuracy);
    res.json({ success: true, data: updated });
  } catch (error) {
    console.error('Error updating location:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

// POST Overland GPS API
app.post('/api/overland', (req, res) => {
  try {
    const { locations } = req.body;
    if (!Array.isArray(locations)) {
      return res.status(400).json({ error: 'Missing locations array' });
    }

    let processedCount = 0;
    for (const loc of locations) {
      if (loc.geometry && loc.geometry.coordinates && loc.properties) {
        const [lng, lat] = loc.geometry.coordinates;
        const deviceId = loc.properties.device_id;
        const accuracy = loc.properties.horizontal_accuracy;
        const timestamp = loc.properties.timestamp ? new Date(loc.properties.timestamp).getTime() : Date.now();
        
        if (deviceId && typeof lat === 'number' && typeof lng === 'number') {
          const normalized = deviceId.toUpperCase();
          if (VALID_IDENTITIES.has(normalized)) {
            updateLocation(normalized, lat, lng, accuracy, timestamp);
            processedCount++;
          }
        }
      }
    }
    
    res.json({ result: "ok", processed: processedCount });
  } catch (error) {
    console.error('Error handling Overland post:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

// GET Race Results Proxy API
app.get('/api/results', resultsRateLimiter, async (req, res) => {
  try {
    const { year, fields, filterbib } = req.query;
    
    if (!year || !fields) {
      return res.status(400).json({ error: 'Missing year or fields query parameter' });
    }

    const raceId = YEARS_CONFIG[year];
    if (!raceId) {
      return res.status(400).json({ error: `Unsupported year: ${year}` });
    }

    const url = new URL(`https://api.raceresult.com/${raceId}/${RACERESULT_API_KEY}`);
    url.searchParams.append('listFormat', 'JSON');
    url.searchParams.append('fields', fields);
    if (filterbib) {
      url.searchParams.append('filterbib', filterbib);
    }

    const response = await fetch(url.toString(), {
      headers: {
        'User-Agent': 'Mozilla/5.0'
      }
    });

    if (!response.ok) {
      throw new Error(`Raceresult API returned status ${response.status}`);
    }

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('Error proxying results:', error);
    res.status(500).json({ error: 'Failed to fetch race results' });
  }
});

// Serve frontend static files from "dist"
const distPath = path.join(__dirname, '../dist');
app.use(express.static(distPath));

// Fallback all other routes to React's index.html
app.get('/{*path}', (req, res) => {
  res.sendFile(path.join(distPath, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
