// Save this as superScraper.js and run with Node.js (Node 18+ has built-in fetch)
// No dependencies required!

const fs = require("fs/promises");

const outputFile = "enterpriseData.json";

// Get Bearer token from environment variable
const token = process.env.BEARER_TOKEN;
if (!token) {
  console.error("❌ Error: BEARER_TOKEN environment variable is required");
  console.log("Usage: BEARER_TOKEN=your_token node superScraper.js");
  process.exit(1);
}

const enterpriseIds = Array.from({ length: 10 }, (_, i) => 3220 - i); // Test first 10
const urls = [
  "https://account.kilimax.com/api/user/company/getAllCompanyPage",
  "https://account.kilimax.com/api/user/user/userPage"
];

async function main() {
  let data = {};
  try {
    const fileContent = await fs.readFile(outputFile, 'utf-8');
    data = JSON.parse(fileContent);
  } catch (err) {
    // File doesn't exist yet, start with empty data
    data = {};
  }

  for (const enterpriseId of enterpriseIds) {
    if (!data[enterpriseId]) data[enterpriseId] = {};
    for (const url of urls) {
      if (data[enterpriseId][url]) {
        console.log(`Already fetched ${enterpriseId} - ${url}`);
        continue;
      }
      const payload = {
        current: 1,
        size: 10,
        enterpriseId: enterpriseId.toString()
      };
      // Add extra fields depending on endpoint
      if (url.endsWith("/userPage")) payload.data = [], payload.roleIds = [];

      try {
        const res = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
            "Accept": "application/json"
          },
          body: JSON.stringify(payload)
        });

        const json = await res.json();
        data[enterpriseId][url] = json;
        await fs.writeFile(outputFile, JSON.stringify(data, null, 2), 'utf-8');
        console.log(`✅ Saved enterprise ${enterpriseId}, ${url}`);
        
        // Display first 10 results for company data
        if (url.includes("getAllCompanyPage") && json.data && json.data.info && json.data.info.records) {
          const records = json.data.info.records.slice(0, 10);
          console.log(`\n📊 First ${records.length} companies for enterprise ${enterpriseId}:`);
          records.forEach((record, idx) => {
            console.log(`  ${idx + 1}. ${record.companyName || 'N/A'} (ID: ${record.id}) - ${record.countryName || 'N/A'}`);
          });
          console.log('');
        }
      } catch (err) {
        console.error(`Error fetching ${enterpriseId} - ${url}:`, err.message);
      }
    }
  }

  console.log("All done!");
}

main();
