import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

BASE_URL = "https://supremevalues.com/mm2/"

CATEGORIES = [
    "commons",
    "uncommons",
    "pets",
    "rares",
    "legendaries",
    "godlies",
    "chromas",
    "vintages",
    "ancients",
    "uniques",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

all_items = {}

for category in CATEGORIES:
    url = BASE_URL + category

    print(f"Loading {url}")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text("\n", strip=True)

    # Ищем блоки с Value
    pattern = re.compile(
        r"(?P<name>[^\n]+?)\s+Value\s*-\s*(?P<value>[\d,]+)"
    )

    category_items = {}

    for match in pattern.finditer(text):
        name = match.group("name").strip()
        value = int(match.group("value").replace(",", ""))

        if not name:
            continue

        if len(name) > 100:
            continue

        category_items[name] = {
            "value": value,
            "category": category
        }

    all_items.update(category_items)

    print(f"{category}: {len(category_items)} items")


output = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "source": "Supreme Values",
    "items": all_items
}

with open("values.json", "w", encoding="utf-8") as f:
    json.dump(
        output,
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"TOTAL: {len(all_items)} items")
