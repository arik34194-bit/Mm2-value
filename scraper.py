import json
import re
import requests
from bs4 import BeautifulSoup

CATEGORIES = {
    "pets": "https://supremevalues.com/mm2/pets",
    "uncommons": "https://supremevalues.com/mm2/uncommons",
    "rares": "https://supremevalues.com/mm2/rares",
    "legendaries": "https://supremevalues.com/mm2/legendaries",
    "godlies": "https://supremevalues.com/mm2/godlies",
    "chromas": "https://supremevalues.com/mm2/chromas",
    "vintages": "https://supremevalues.com/mm2/vintages",
    "ancients": "https://supremevalues.com/mm2/ancients",
    "uniques": "https://supremevalues.com/mm2/uniques",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def scrape_category(url):
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    items = []

    # Supreme Values displays each item with its name and Value.
    # Search through text blocks containing "Value -".
    for element in soup.find_all(string=re.compile(r"Value\s*-\s*[\d,]+")):
        value_text = element.strip()

        match = re.search(r"Value\s*-\s*([\d,]+)", value_text)
        if not match:
            continue

        value = int(match.group(1).replace(",", ""))

        # Find the nearest parent containing the item information.
        parent = element.parent

        for _ in range(5):
            if parent is None:
                break

            text = parent.get_text(" ", strip=True)

            if "Value -" in text:
                # Look for the text immediately before "Value -".
                name_match = re.search(
                    r"(?:\|\s*)?(.+?)\s+(?:Class\s*-\s*.+?\s+)?Value\s*-\s*[\d,]+",
                    text
                )

                if name_match:
                    name = name_match.group(1).strip()

                    # Remove common unwanted prefixes.
                    name = re.sub(r"^Image:\s*", "", name)
                    name = name.split("|")[-1].strip()

                    if name and len(name) < 100:
                        items.append({
                            "name": name,
                            "value": value
                        })
                        break

            parent = parent.parent

    # Remove duplicates.
    unique = {}
    for item in items:
        key = item["name"]
        unique[key] = item

    return list(unique.values())


def main():
    result = {}

    for category, url in CATEGORIES.items():
        print(f"Scraping {category}...")

        try:
            result[category] = scrape_category(url)
            print(f"Found {len(result[category])} items")
        except Exception as e:
            print(f"ERROR in {category}: {e}")
            result[category] = []

    with open("values.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("Done!")


if __name__ == "__main__":
    main()
