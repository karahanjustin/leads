# Call Tracker

A tiny, zero-backend tool for tracking cold outreach, by phone or by email. Add leads, mark status, jot notes, everything stays on your own device.

**Live:** https://potsdam-media.de/leads/

## Features

- **Calls / Email mode switch** - one tool, two independent lists. Flip the toggle in the header between Call mode (Not called / No answer / Interested, callback dates) and Email mode (Not sent / No reply / Replied, follow-up dates). The active mode decides which list, labels, and stats you see; your choice is remembered.
- **Find leads** - pick a niche and a location (all 27 EU member states, Switzerland, Norway, the United Kingdom and the United States, then region + city), get a list of businesses (name, address, phone, website, email), edit or drop rows, then add the rest to the active list in one click. Runs fully in the browser, no server. Two sources are merged: OpenStreetMap (via Overpass) and [Overture Maps](https://overturemaps.org) places, read live from Overture's public PMTiles archive with ranged requests. Overture has far more small businesses (Bremen: 269 electricians vs. 24 in OSM) and phone numbers for almost all of them; duplicates are merged by phone or by name within 300 m. "City only" uses the real city boundary. A search loads roughly 5 MB (Graz) to 55 MB (Berlin) of Overture tiles.
- **Auction houses** - the niche "Auktionshaus" / "auction house" additionally uses a prebuilt list (`data/auctions-<country>.json` for every EU country and the US, from Overture via `tools/build_auction_data.py eu|us`, needs `pip install duckdb`), so wider radius searches also find them.
- **Result filters** - narrow a search to businesses without a website, with only a social media profile, with a phone number, or not yet in your list. Rows already in your list are greyed out. "Add" takes the filtered rows; the rest stays for another pass. Site quality is prefilled (no link = none, social link = bad), and a missing email becomes an `info@` guess at the business's own domain, marked with a dashed underline until you confirm or change it.
- **Tile cache** - Overture tiles are kept in the browser's Cache API, so a second niche in the same city downloads nothing. Size and a clear link are shown in the footer.
- **Call mode** - one lead at a time with a big tap-to-call number and the three outcomes as big buttons; keys 1 to 4, Space to skip, Esc to close. Due callbacks come first.
- **Backups** - a reminder appears when the list was never exported or the last export is a week old. In Chrome and Edge you can pick an automatic backup file that is rewritten after every change (both lists in one JSON; Import JSON restores it).
- **Move between lists** - a lead can be moved from the call list to the email list and back, keeping its notes.
- **Daily goal** - a "Today" counter with a progress bar (click to change the goal), plus keys c (start calling), f (find leads) and n (new lead).
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

It's a single `index.html` plus the auction lists in `data/`. Serve the folder so the page can load them (opened as a plain file, everything works except the auction lists):

```sh
python3 -m http.server 8190
```

## License

MIT
