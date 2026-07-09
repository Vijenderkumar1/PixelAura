# Google Sheets Email Database Setup Guide

Follow these steps to set up a completely free, automated database in **Google Sheets** to collect user emails when they log in to download wallpapers.

---

### Step 1: Create a Google Sheet
1. Go to **[sheets.google.com](https://sheets.google.com)** and create a new blank spreadsheet.
2. Rename the spreadsheet to something like `PixelAura Users`.
3. Add three headers in row 1:
   - **A1:** `Timestamp`
   - **B1:** `Email`
   - **C1:** `Name`

---

### Step 2: Open the Apps Script Editor
1. In the Google Sheets top menu, click on **Extensions** → **Apps Script**.
2. Delete any default code in the editor window.
3. Copy and paste the following code into the editor:

```javascript
function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var email = data.email;
    var name = data.name;
    var timestamp = new Date();
    
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    sheet.appendRow([timestamp, email, name]);
    
    return ContentService.createTextOutput(JSON.stringify({ "status": "success" }))
      .setMimeType(ContentService.MimeType.JSON)
      .setHeader('Access-Control-Allow-Origin', '*');
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({ "status": "error", "message": error.toString() }))
      .setMimeType(ContentService.MimeType.JSON)
      .setHeader('Access-Control-Allow-Origin', '*');
  }
}

// Enable CORS for testing options request
function doOptions(e) {
  return ContentService.createTextOutput("")
    .setMimeType(ContentService.MimeType.TEXT)
    .setHeader('Access-Control-Allow-Origin', '*')
    .setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
    .setHeader('Access-Control-Allow-Headers', 'Content-Type');
}
```

---

### Step 3: Deploy the Script as a Web App
1. Click the **Deploy** button at the top right of the Apps Script page, and select **New deployment**.
2. Click the gear icon next to "Select type" and select **Web app**.
3. Fill out the fields:
   - **Description:** `PixelAura Auth Webhook`
   - **Execute as:** `Me (your-email@gmail.com)`
   - **Who has access:** `Anyone` *(Crucial: This allows your website to send data securely to the sheet)*
4. Click **Deploy**.
5. Google will ask you to authorize the script. Click **Authorize access**, log in with your account, click **Advanced**, and click **Go to Untitled project (unsafe)** to approve the permissions.
6. Once deployed, copy the **Web app URL** (e.g., `https://script.google.com/macros/s/AKfycb.../exec`).

---

### Step 4: Add the URL to Your Website Configuration
1. Open the file `website/js/app.js`.
2. Locate the line containing `const SHEETS_WEBHOOK_URL = '...';` (around the top).
3. Replace the placeholder value with your copied **Web app URL**.
4. Save and deploy your site!
