async function main() {
  const fields = [
    "BIB", "TeamName",
    "XCSKI_SPLIT", "XC_Ski_Time",
    "DHSKI_SPLIT", "DH_Ski_Time",
    "RUN_SPLIT", "Run_Time",
    "ROADBIKE_SPLIT", "Road_Bike_Time",
    "CANOE_SPLIT", "Canoe_Time",
    "CYCLOCROSS_SPLIT", "Cyclocross_Time",
    "KAYAK_SPLIT", "Kayak_Time"
  ];
  
  const url = `https://api.raceresult.com/291757/02PHAOGJWM5QHZELNBVH09BKZDMR3IWT?listFormat=JSON&fields=${fields.join(',')}`;
  
  console.log("Fetching 2024 results...");
  const res = await fetch(url);
  const data = await res.json();
  
  const targetBibs = [458, 463, 101];
  const targetRows = data.filter(row => targetBibs.includes(parseInt(row[0], 10)));
  
  targetRows.forEach(row => {
    console.log("\n--------------------------------");
    console.log(`BIB: ${row[0]} | TeamName: ${row[1]}`);
    console.log(`Leg        | SPLIT      | Time`);
    console.log(`XC Ski     | ${row[2].padEnd(10)} | ${row[3]}`);
    console.log(`DH Ski     | ${row[4].padEnd(10)} | ${row[5]}`);
    console.log(`Run        | ${row[6].padEnd(10)} | ${row[7]}`);
    console.log(`Road Bike  | ${row[8].padEnd(10)} | ${row[9]}`);
    console.log(`Canoe      | ${row[10].padEnd(10)} | ${row[11]}`);
    console.log(`Cyclocross | ${row[12].padEnd(10)} | ${row[13]}`);
    console.log(`Kayak      | ${row[14].padEnd(10)} | ${row[15]}`);
  });
}

main();
