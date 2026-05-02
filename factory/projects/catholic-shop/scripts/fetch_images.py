#!/usr/bin/env python3
"""Fetch Catholic devotional images from Wikimedia Commons and build product catalog."""
import json, sys, time, urllib.parse, urllib.request

UA = "CatholicMarket/1.0 (pi-telegram-bot; contact@optimizedworkflow.dev)"
BASE = "https://commons.wikimedia.org/w/api.php"

def api(params):
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)

def search_images(query, limit=4):
    """Search for CC-licensed images matching a query."""
    data = api({
        "action": "query", "list": "search",
        "srsearch": query, "srnamespace": "6", "format": "json",
        "srlimit": str(limit)
    })
    titles = [r["title"] for r in data.get("query", {}).get("search", [])]
    return titles

def get_image_urls(titles):
    """Get direct image URLs for file titles."""
    if not titles:
        return []
    data = api({
        "action": "query", "titles": "|".join(titles),
        "prop": "imageinfo", "iiprop": "url|size|mime",
        "format": "json"
    })
    urls = []
    for page in data.get("query", {}).get("pages", {}).values():
        ii = (page.get("imageinfo") or [])
        if ii:
            url = ii[0].get("url", "")
            mime = ii[0].get("mime", "")
            if url and mime.startswith("image/"):
                urls.append(url)
    return urls

# Product categories with search queries
PRODUCT_TYPES = {
    "rosary": ["catholic rosary beads", "rosary catholic prayer"],
    "crucifix": ["wooden crucifix", "catholic crucifix wall"],
    "icon": ["catholic icon mary", "religious icon orthodox"],
    "medal": ["saint benedict medal", "miraculous medal virgin"],
    "candle": ["catholic prayer candle", "church candle devotion"],
    "holy_water": ["lourdes water bottle", "holy water catholic"],
    "cross": ["olive wood cross", "tau franciscan cross"],
    "statue": ["virgin mary statue", "our lady fatima statue"],
    "incense": ["catholic church incense", "thurible incense"],
    "scapular": ["brown scapular our lady", "carmelite scapular"],
    "church_dest": ["catholic cathedral interior", "catholic basilica shrine", "lourdes sanctuary", "fatima sanctuary", "st peters basilica", "holy sepulchre jerusalem", "notre dame paris", "jasna gora czestochowa"],
}

all_images = {}

for category, queries in PRODUCT_TYPES.items():
    cat_images = []
    for q in queries:
        print(f"Searching: {q} ...", file=sys.stderr)
        try:
            titles = search_images(q, limit=3)
            urls = get_image_urls(titles)
            cat_images.extend(urls)
            time.sleep(0.3)  # Rate limit
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
    all_images[category] = cat_images[:6]  # Max 6 per category
    print(f"  → {len(cat_images[:6])} images found", file=sys.stderr)

# Output as JSON (one URL per category for reference)
out = {k: v[:3] for k, v in all_images.items()}
print(json.dumps(out, indent=2))
