"""Build the static auction house lists in data/ from Overture Maps places.

OpenStreetMap has almost no auction houses mapped (none at all in Bremen as of
10/2026), so the lead finder adds these lists for the "Auktionshaus" niche.
Overture places are CDLA-Permissive-2.0, so the extract may be republished.

    python3 -m venv .venv && .venv/bin/pip install duckdb
    .venv/bin/python tools/build_auction_data.py                  # latest release, all countries
    .venv/bin/python tools/build_auction_data.py 2026-09-23.1 de at

Writes data/auctions-<cc>.json per country. The US scan alone takes 15+ minutes.
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

# Coarse lon/lat boxes so DuckDB can skip row groups; the country code filter is exact.
COUNTRIES = {
    'de': ('DE', (5.5, 45.5, 15.5, 55.5)),
    'at': ('AT', (9.3, 46.3, 17.3, 49.1)),
    'us': ('US', (-180.0, 15.0, -60.0, 72.0)),
}

NAME_RE = r'auktion|versteiger|auction|dorotheum'
EXCLUDE_RE = r'gericht|court|zwangsversteiger|foreclos'
FIELDS = ['name', 'street', 'postcode', 'city', 'region', 'lat', 'lon', 'phone', 'website', 'email']


def latest_release():
    with urllib.request.urlopen('https://stac.overturemaps.org/catalog.json', timeout=30) as r:
        return json.load(r)['latest']


def clean_phone(p, cc):
    if not p:
        return ''
    digits = re.sub(r'\D', '', p)
    dial = {'DE': '49', 'AT': '43', 'US': '1'}[cc]
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


def build(release, keys):
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial; SET s3_region='us-west-2';")
    src = f's3://overturemaps-us-west-2/release/{release}/theme=places/type=place/*.parquet'
    OUT.mkdir(exist_ok=True)
    for key in keys:
        cc, (x0, y0, x1, y1) = COUNTRIES[key]
        rows = con.execute(f"""
            SELECT names.primary, addresses[1].freeform, addresses[1].postcode, addresses[1].locality,
                   addresses[1].region, ST_Y(ST_Centroid(geometry)), ST_X(ST_Centroid(geometry)),
                   phones[1], websites[1], emails[1], confidence
            FROM read_parquet('{src}')
            WHERE bbox.xmin BETWEEN {x0} AND {x1} AND bbox.ymin BETWEEN {y0} AND {y1}
              AND addresses[1].country = '{cc}'
              AND coalesce(operating_status, 'open') NOT IN ('permanently_closed', 'closed')
              AND names.primary IS NOT NULL
              AND (taxonomy.primary ILIKE '%auction%'
                   OR list_contains(taxonomy.alternates, 'auction_house')
                   OR regexp_matches(lower(names.primary), '{NAME_RE}'))
              AND NOT regexp_matches(lower(names.primary), '{EXCLUDE_RE}')
            ORDER BY confidence DESC
        """).fetchall()
        seen, out = set(), []
        for name, street, post, city, region, lat, lon, phone, web, mail, conf in rows:
            k = (re.sub(r'\W', '', name.lower()), post or '')
            if k in seen:
                continue
            seen.add(k)
            out.append([name.strip(), street or '', post or '', city or '', region or '',
                        round(lat, 5), round(lon, 5), clean_phone(phone, cc), web or '', clean_email(mail)])
        out.sort(key=lambda r: (r[3].lower(), r[0].lower()))
        doc = {'source': f'Overture Maps Foundation, places {release} (CDLA-Permissive-2.0)',
               'built': datetime.date.today().isoformat(), 'fields': FIELDS, 'rows': out}
        path = OUT / f'auctions-{key}.json'
        path.write_text(json.dumps(doc, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        print(f'{key}: {len(out)} auction houses -> {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KB)', flush=True)


if __name__ == '__main__':
    args = sys.argv[1:]
    keys = [a for a in args if a in COUNTRIES] or list(COUNTRIES)
    rest = [a for a in args if a not in COUNTRIES]
    build(rest[0] if rest else latest_release(), keys)
