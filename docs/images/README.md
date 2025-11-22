# Screenshots Directory

This directory contains screenshots for the project documentation.

## Required Screenshots

Place the following screenshot files here:

1. **`dashboard.png`** - Dashboard page showing KPI cards and network overview
2. **`device-details.png`** - Device details page with metrics and charts
3. **`alerts.png`** - Alert management page
4. **`settings.png`** - Settings/configuration page
5. **`login.png`** - Login page

## Guidelines for Screenshots

- **Format:** PNG or JPG
- **Resolution:** 1920x1080 or higher recommended
- **Content:**
  - Use sample/demo data (not real network information)
  - Ensure UI is clean and professional
  - Capture in light mode for consistency
  - Avoid sensitive information (IP addresses, email addresses, etc.)

## How to Take Screenshots

1. Start the application (`make dev`)
2. Navigate to each page
3. Use browser's full-page screenshot tool or:
   - **macOS:** `Cmd + Shift + 4`
   - **Windows:** `Win + Shift + S`
   - **Linux:** `gnome-screenshot` or `flameshot`
4. Save screenshots with the exact filenames listed above
5. Place them in this directory

## Example

```
docs/images/
├── README.md          # This file
├── dashboard.png      # Your screenshot here
├── device-details.png # Your screenshot here
├── alerts.png         # Your screenshot here
├── settings.png       # Your screenshot here
└── login.png          # Your screenshot here
```

Once screenshots are added, they will automatically appear in the main README.md.
