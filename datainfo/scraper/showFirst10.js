// Display first 10 results from enterpriseData.json
const fs = require("fs-extra");

const outputFile = "enterpriseData.json";

async function displayFirst10() {
  if (!fs.existsSync(outputFile)) {
    console.log("❌ No enterpriseData.json file found.");
    console.log("💡 Please run superScraper.js first to fetch data.");
    console.log("\nTo run superScraper.js:");
    console.log("  BEARER_TOKEN=your_token_here node superScraper.js");
    console.log("  OR");
    console.log("  node superScraper.js (will prompt for token)");
    return;
  }

  const data = await fs.readJson(outputFile);
  const enterpriseIds = Object.keys(data).slice(0, 10);

  console.log("=".repeat(80));
  console.log(`📊 DISPLAYING FIRST 10 ENTERPRISES FROM enterpriseData.json`);
  console.log("=".repeat(80));
  console.log();

  enterpriseIds.forEach((enterpriseId, idx) => {
    console.log(`\n🏢 Enterprise #${idx + 1}: ID ${enterpriseId}`);
    console.log("-".repeat(80));

    const enterprise = data[enterpriseId];
    const urls = Object.keys(enterprise);

    urls.forEach((url) => {
      const response = enterprise[url];
      console.log(`\n📍 Endpoint: ${url}`);

      if (url.includes("getAllCompanyPage")) {
        if (response && response.data && response.data.info && response.data.info.records) {
          const records = response.data.info.records.slice(0, 10);
          console.log(`   Found ${response.data.info.total || records.length} total companies (showing first ${records.length}):`);
          records.forEach((record, i) => {
            console.log(`   ${i + 1}. ${record.companyName || "N/A"}`);
            console.log(`      ID: ${record.id}, Status: ${record.status}, Country: ${record.countryName || "N/A"}`);
            console.log(`      Currency: ${record.currencyCode || "N/A"}, Created: ${record.gmtCreate || "N/A"}`);
          });
        } else {
          console.log("   No company records found");
        }
      } else if (url.includes("userPage")) {
        if (response && response.data && response.data.info && response.data.info.records) {
          const records = response.data.info.records.slice(0, 10);
          console.log(`   Found ${response.data.info.total || records.length} total users (showing first ${records.length}):`);
          records.forEach((record, i) => {
            console.log(`   ${i + 1}. ${record.userName || record.email || "N/A"}`);
            console.log(`      ID: ${record.id}, Email: ${record.email || "N/A"}`);
            if (record.roles && record.roles.length > 0) {
              console.log(`      Roles: ${record.roles.map(r => r.roleName || r.name).join(", ")}`);
            }
          });
        } else {
          console.log("   No user records found");
        }
      } else {
        console.log(`   Response status: ${response.code || response.state || "unknown"}`);
      }
    });
  });

  console.log("\n" + "=".repeat(80));
  console.log(`✅ Displayed ${enterpriseIds.length} enterprises`);
  console.log("=".repeat(80));
}

displayFirst10().catch(console.error);
