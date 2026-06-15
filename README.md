# Call Tracker

A tiny, zero-backend tool for tracking cold outreach, by phone or by email. Add leads, mark status, jot notes, everything stays on your own device.

**Live:** https://potsdam-media.de/leads/

## Features

- **Calls / Email mode switch** - one tool, two independent lists. Flip the toggle in the header between Call mode (Not called / No answer / Interested, callback dates) and Email mode (Not sent / No reply / Replied, follow-up dates). The active mode decides which list, labels, and stats you see; your choice is remembered.
- **Find leads (OpenStreetMap)** - pick a niche and a US State + City, get a list of businesses (name, address, phone, website, email), edit or drop rows, then add the rest to the active list in one click. Runs fully in the browser, no server. Phone/website/address come from OpenStreetMap; email is often missing there and stays editable.
- Track leads with name, phone (call mode), website, email, address, and site-quality tag
- Status workflow per mode: Calls = Not called / No answer / Not interested / Interested / Closed; Email = Not sent / No reply / Not interested / Replied / Closed
- Per-lead notes and callback / follow-up dates (auto-set on no-answer-or-no-reply / interested-or-replied)
- Live stats: total, called-or-sent, interested-or-replied, closed

## Moving in from the old Email Tracker

Switch to **Email** mode, then use **Import JSON** and pick an export from the standalone Email Tracker. Its leads load straight into the email list (it shares the same JSON shape).
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
