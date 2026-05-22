
// Yes, our Node version is 21.7.1, which has global fetch!

async function main() {
  const fields = [
    "BIB", "id", "TeamName", "Division", "Started",
    "XCSKI_SPLIT", "DHSKI_SPLIT", "RUN_SPLIT", "ROADBIKE_SPLIT", "CANOE_SPLIT", "CYCLOCROSS_SPLIT", "KAYAK_SPLIT"
  ];
  const url = `https://api.raceresult.com/291757/02PHAOGJWM5QHZELNBVH09BKZDMR3IWT?listFormat=JSON&fields=${fields.join(',')}`;
  
  console.log("Fetching 2024 results...");
  const res = await fetch(url);
  const data = await res.json();
  
  console.log(`Fetched ${data.length} teams.`);
  
  // Find Aleshops and Jacksons (or target bibs 101, 39, 24, 32)
  const targetBibs = [101, 39, 24, 32];
  const targetRows = data.filter(row => targetBibs.includes(parseInt(row[0], 10)) || row[2].toLowerCase().includes("aleshop") || row[2].toLowerCase().includes("jackson"));
  
  targetRows.forEach(row => {
    console.log("\n--------------------------------");
    console.log(`BIB: ${row[0]} | TeamName: ${row[2]} | Division: ${row[3]}`);
    console.log(`Splits:`);
    console.log(`  XC Ski:     ${row[5]}`);
    console.log(`  DH Ski:     ${row[6]}`);
    console.log(`  Run:        ${row[7]}`);
    console.log(`  Road Bike:  ${row[8]}`);
    console.log(`  Canoe:      ${row[9]}`);
    console.log(`  Cyclocross: ${row[10]}`);
    console.log(`  Kayak:      ${row[11]}`);
  });
}

main();
