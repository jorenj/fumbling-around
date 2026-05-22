async function main() {
  const fields = [
    "BIB", "TeamName", "Division",
    "Rank", "OverallRank", "DivisionRank", "GenderRank",
    "Time", "TotalTime", "DecimalTime"
  ];
  
  const url = `https://api.raceresult.com/291757/02PHAOGJWM5QHZELNBVH09BKZDMR3IWT?listFormat=JSON&fields=${fields.join(',')}`;
  
  console.log("Fetching 2024 results...");
  const res = await fetch(url);
  const data = await res.json();
  
  const targetBibs = [458, 463, 101];
  const targetRows = data.filter(row => targetBibs.includes(parseInt(row[0], 10)));
  
  targetRows.forEach(row => {
    console.log("\n--------------------------------");
    console.log(`BIB: ${row[0]} | TeamName: ${row[1]} | Division: ${row[2]}`);
    console.log(`Rank:         ${row[3]}`);
    console.log(`OverallRank:  ${row[4]}`);
    console.log(`DivisionRank: ${row[5]}`);
    console.log(`GenderRank:   ${row[6]}`);
    console.log(`Time:         ${row[7]}`);
    console.log(`TotalTime:    ${row[8]}`);
    console.log(`DecimalTime:  ${row[9]}`);
  });
}

main();
