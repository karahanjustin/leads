"""Build the static auction house lists in data/ from Overture Maps places.

OpenStreetMap has almost no auction houses mapped (none at all in Bremen as of
10/2026), so the lead finder adds these lists for the "Auktionshaus" niche.
Overture places are CDLA-Permissive-2.0, so the extract may be republished.

    python3 -m venv .venv && .venv/bin/pip install duckdb
    .venv/bin/python tools/build_auction_data.py                  # latest release, EU + US
    .venv/bin/python tools/build_auction_data.py 2026-09-23.1 eu  # all EU countries, one scan
    .venv/bin/python tools/build_auction_data.py 2026-09-23.1 us

Writes data/auctions-<cc>.json per country. Each scan takes 10 to 25 minutes.
"""
import datetime
import json
import pathlib
import re
import sys
import urllib.request

import duckdb

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'data'

# Country calling codes; also the list of countries that get a file.
DIAL = {
    'at': '43', 'be': '32', 'bg': '359', 'cy': '357', 'cz': '420', 'de': '49', 'dk': '45', 'ee': '372',
    'es': '34', 'fi': '358', 'fr': '33', 'gr': '30', 'hr': '385', 'hu': '36', 'ie': '353', 'it': '39',
    'lt': '370', 'lu': '352', 'lv': '371', 'mt': '356', 'nl': '31', 'pl': '48', 'pt': '351', 'ro': '40',
    'se': '46', 'si': '386', 'sk': '421', 'us': '1',
}
EU = [k for k in DIAL if k != 'us']
# Coarse lon/lat boxes so DuckDB can skip row groups; the country code filter is exact.
# The EU box spans the Azores, the Canaries and Cyprus.
SCANS = {
    'eu': (EU, (-32.0, 27.0, 35.0, 71.5)),
    'us': (['us'], (-180.0, 15.0, -60.0, 72.0)),
}

# The taxonomy catches most auction houses; names catch the rest, in the local languages.
NAME_RE = (r'auktion|versteiger|auction|dorotheum|ench[eè]res|h[oô]tel des ventes|commissaire.priseur|'
           r'casa d.aste|\baste\b|subasta|veiling|aukcj|aukcyj|aukcij|aukce|aukční|aukci[oó]|árverés|'
           r'huutokauppa|leil[oõã]|licita[tț]ii')
EXCLUDE_RE = r'gericht|court|tribunal|zwangsversteiger|foreclos|notar'
FIELDS = ['name', 'street', 'postcode', 'city', 'region', 'lat', 'lon', 'phone', 'website', 'email']


def latest_release():
    with urllib.request.urlopen('https://stac.overturemaps.org/catalog.json', timeout=30) as r:
        return json.load(r)['latest']


def clean_phone(p, cc):
    if not p:
        return ''
    digits = re.sub(r'\D', '', p)
    dial = DIAL[cc.lower()]
    if p.strip().startswith('+'):
        return '+' + digits
    if digits.startswith('00' + dial):
        return '+' + digits[2:]
    # Overture often drops the "+": "494214585625" is +49 421 4585625.
    if cc != 'US' and digits.startswith(dial) and len(digits) >= 11:
        return '+' + digits
    # ...or prepends a trunk zero to the country code: "049421351008".
    if cc != 'US' and digits.startswith('0' + dial) and len(digits) >= 12:
        return '+' + digits[1:]
    if cc == 'US' and len(digits) == 11 and digits.startswith('1'):
        return '+' + digits
    return p.strip()


PLACEHOLDER_MAIL_RE = re.compile(r'johndoe|john\.doe|max\.?mustermann|@(domain|example|test|email)\.|^(test|email|mail)@', re.I)


def clean_email(m):
    m = (m or '').strip()
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[a-z]{2,}', m, re.I) or PLACEHOLDER_MAIL_RE.search(m):
        return ''
    return m


def build(release, scans):
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial; SET s3_region='us-west-2';")
    src = f's3://overturemaps-us-west-2/release/{release}/theme=places/type=place/*.parquet'
    OUT.mkdir(exist_ok=True)
    for scan in scans:
        keys, (x0, y0, x1, y1) = SCANS[scan]
        codes = ','.join(f"'{k.upper()}'" for k in keys)
        rows = con.execute(f"""
            SELECT addresses[1].country, names.primary, addresses[1].freeform, addresses[1].postcode,
                   addresses[1].locality, addresses[1].region, ST_Y(ST_Centroid(geometry)),
                   ST_X(ST_Centroid(geometry)), phones[1], websites[1], emails[1], confidence
            FROM read_parquet('{src}')
            WHERE bbox.xmin BETWEEN {x0} AND {x1} AND bbox.ymin BETWEEN {y0} AND {y1}
              AND addresses[1].country IN ({codes})
              AND coalesce(operating_status, 'open') NOT IN ('permanently_closed', 'closed')
              AND names.primary IS NOT NULL
              AND (taxonomy.primary ILIKE '%auction%'
                   OR list_contains(taxonomy.alternates, 'auction_house')
                   OR regexp_matches(lower(names.primary), '{NAME_RE}'))
              AND NOT regexp_matches(lower(names.primary), '{EXCLUDE_RE}')
            ORDER BY confidence DESC
        """).fetchall()
        seen, out = set(), {k: [] for k in keys}
        for cc, name, street, post, city, region, lat, lon, phone, web, mail, conf in rows:
            k = (cc, re.sub(r'\W', '', name.lower()), post or '')
            if k in seen:
                continue
            seen.add(k)
            out[cc.lower()].append([name.strip(), street or '', post or '', city or '', region or '',
                                    round(lat, 5), round(lon, 5), clean_phone(phone, cc), web or '', clean_email(mail)])
        for key in keys:
            rows_cc = sorted(out[key], key=lambda r: (r[3].lower(), r[0].lower()))
            doc = {'source': f'Overture Maps Foundation, places {release} (CDLA-Permissive-2.0)',
                   'built': datetime.date.today().isoformat(), 'fields': FIELDS, 'rows': rows_cc}
            path = OUT / f'auctions-{key}.json'
            path.write_text(json.dumps(doc, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
            print(f'{key}: {len(rows_cc)} auction houses -> {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KB)', flush=True)


if __name__ == '__main__':
    args = sys.argv[1:]
    scans = [a for a in args if a in SCANS] or list(SCANS)
    rest = [a for a in args if a not in SCANS]
    build(rest[0] if rest else latest_release(), scans)
