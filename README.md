# Call Tracker

A tiny, zero-backend tool for tracking cold-call outreach. Add leads, mark call status, jot notes — everything stays on your own device.

**Live:** https://karahanjustin.github.io/call-tracker/

## Features

- **Find leads (OpenStreetMap)** - pick a niche and a US State + City, get a list of businesses (name, address, phone, website, email), edit or drop rows, then add the rest to your Un-called list in one click. Runs fully in the browser, no server. Phone/website/address come from OpenStreetMap; email is often missing there and stays editable.
- Track leads with name, phone, website, email, address, and site-quality tag
- Status workflow: Not called → No answer / Not interested / Interested / Closed
- Per-lead notes and callback dates (auto-set on No-answer / Interested)
- Live stats: total, called, interested, closed
- **CSV import** — drop a spreadsheet export, missing fields show as `???` and stay editable (now also recognizes an `address` column)
- Export / Import as JSON for backup or moving between devices

## CSV format

Header row is auto-detected. Recognized columns (any subset, any order):

```
name, phone, website, email, quality, notes
```

Quality values: `none`, `bad`, `ok` (anything else → `???`). Missing fields become `???` and can be edited inline later.

## Privacy

All data is stored in your browser's `localStorage`. It survives reboots, browser restarts, and shutdowns. It never leaves your device — there is no server.

Clearing your browser's site data for this domain will wipe your leads. Use **Export** regularly if your list matters.

## Run locally

It's a single `index.html` — open it in any browser. No build, no install.

```sh
open index.html
```

## License

MIT
