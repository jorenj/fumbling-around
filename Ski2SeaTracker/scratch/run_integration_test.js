async function main() {
  console.log("=== Running GPS Endpoints Integration Test ===");
  
  // 1. Test OwnTracks POST endpoint
  const owntracksPayload = {
    _type: "location",
    lat: 48.857,
    lon: -121.679,
    acc: 8.5,
    tst: Math.floor(Date.now() / 1000),
    tid: "ot"
  };
  
  console.log("Sending OwnTracks request...");
  const otRes = await fetch("http://localhost:3001/api/owntracks?device_id=IVER", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(owntracksPayload)
  });
  
  const otJson = await otRes.json();
  console.log("OwnTracks Response Status:", otRes.status);
  console.log("OwnTracks Response Body:", otJson);
  console.assert(otRes.ok, "OwnTracks request failed");
  console.assert(otJson.success === true, "OwnTracks success flag should be true");
  console.assert(otJson.data.lat === 48.857, "OwnTracks lat incorrect");
  console.assert(otJson.data.lng === -121.679, "OwnTracks lng incorrect");
  console.assert(otJson.data.accuracy === 8.5, "OwnTracks accuracy incorrect");

  // 2. Test Traccar Client GET endpoint
  console.log("\nSending Traccar GET request...");
  const traccarQuery = new URLSearchParams({
    id: "TAVIN",
    lat: "48.858",
    lon: "-121.680",
    accuracy: "12",
    timestamp: Math.floor(Date.now() / 1000).toString()
  });
  
  const tcRes = await fetch(`http://localhost:3001/api/traccar?${traccarQuery.toString()}`);
  const tcJson = await tcRes.json();
  console.log("Traccar Response Status:", tcRes.status);
  console.log("Traccar Response Body:", tcJson);
  console.assert(tcRes.ok, "Traccar request failed");
  console.assert(tcJson.success === true, "Traccar success flag should be true");
  console.assert(tcJson.data.lat === 48.858, "Traccar lat incorrect");
  console.assert(tcJson.data.lng === -121.680, "Traccar lng incorrect");
  console.assert(tcJson.data.accuracy === 12, "Traccar accuracy incorrect");

  console.log("\n✓ All Integration Tests Passed successfully!");
}

main().catch(console.error);
