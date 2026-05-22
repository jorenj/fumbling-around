async function main() {
  const fields = ["BIB", "id", "TeamName", "Division"];
  const url = `https://api.raceresult.com/291757/02PHAOGJWM5QHZELNBVH09BKZDMR3IWT?listFormat=JSON&fields=${fields.join(',')}`;
  
  const res = await fetch(url);
  const data = await res.json();
  
  const matched = data.filter(row => {
    const name = row[2].toLowerCase();
    return name.includes("jackson") || name.includes("aleshop");
  });
  
  matched.forEach(row => {
    console.log(`BIB: ${row[0]} | Name: ${row[2]} | Division: ${row[3]}`);
  });
}

main();
