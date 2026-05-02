#!/usr/bin/env python3
"""Build the full Catholic Market product catalog with real images from Wikimedia."""
import json, sys, time, urllib.parse, urllib.request

UA = "CatholicMarket/1.0"
BASE = "https://commons.wikimedia.org/w/api.php"

def api(params):
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def fetch_one(query):
    """Fetch a single best image for a query."""
    data = api({"action":"query","list":"search","srsearch":query,"srnamespace":"6","format":"json","srlimit":"3"})
    titles = [r["title"] for r in data.get("query",{}).get("search",[])]
    if not titles: return ""
    data2 = api({"action":"query","titles":"|".join(titles),"prop":"imageinfo","iiprop":"url|mime","format":"json"})
    for page in data2.get("query",{}).get("pages",{}).values():
        for ii in page.get("imageinfo",[]):
            if ii.get("mime","") in ("image/jpeg","image/png"):
                return ii.get("url","")
    return ""

# Targeted product image searches
PRODUCT_QUERIES = [
    ("rosary_wood", "wooden rosary beads catholic close up"),
    ("rosary_blue", "blue rosary beads catholic"),
    ("crucifix_olive", "olive wood crucifix handheld"),
    ("crucifix_wall", "catholic crucifix wall home"),
    ("icon_madonna", "madonna and child icon catholic"),
    ("icon_christ", "christ pantocrator icon"),
    ("medal_benedict", "saint benedict medal close up"),
    ("medal_miraculous", "miraculous medal virgin mary"),
    ("scapular_brown", "brown scapular our lady mount carmel"),
    ("candle_devotional", "catholic devotional candle prayer"),
    ("holy_water_lourdes", "lourdes holy water bottle virgin"),
    ("cross_tau", "tau cross franciscan wooden"),
    ("statue_fatima", "our lady of fatima statue"),
    ("incense_church", "catholic incense thurible church"),
    ("prayer_card", "catholic prayer card saint holy"),
]

# Destination image searches
DEST_QUERIES = [
    ("lourdes", "sanctuary our lady of lourdes basilica"),
    ("fatima", "sanctuary our lady of fatima portugal"),
    ("rome", "st peters basilica vatican interior"),
    ("jerusalem", "holy sepulchre church jerusalem"),
    ("czestochowa", "jasna gora czestochowa poland"),
    ("guadalupe", "basilica our lady guadalupe mexico"),
    ("assisi", "basilica san francesco assisi italy"),
    ("krakow", "divine mercy sanctuary krakow lagiewniki"),
    ("santiago", "cathedral santiago compostela spain"),
    ("knock", "basilica our lady knock ireland"),
    ("montserrat", "montserrat monastery catalonia spain"),
    ("aparecida", "basilica nossa senhora aparecida brazil"),
]

print("Fetching product images...", file=sys.stderr)
product_images = {}
for key, query in PRODUCT_QUERIES:
    url = fetch_one(query)
    product_images[key] = url
    status = "✓" if url else "✗"
    print(f"  {status} {key}", file=sys.stderr)
    time.sleep(0.25)

print("Fetching destination images...", file=sys.stderr)
dest_images = {}
for key, query in DEST_QUERIES:
    url = fetch_one(query)
    dest_images[key] = url
    status = "✓" if url else "✗"
    print(f"  {status} {key}", file=sys.stderr)
    time.sleep(0.25)

print(json.dumps({"products": product_images, "destinations": dest_images}, indent=2))
