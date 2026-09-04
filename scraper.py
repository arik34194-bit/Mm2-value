import json
import re
import requests
from bs4 import BeautifulSoup

CATEGORIES = [
    "pets",
    "uncommons",
    "rares",
    "legendaries",
    "godlies",
    "chromas",
    "vintages",
    "ancients",
    "uniques",
]

BASE_URL = "https://supremevalues.com/mm2/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
}


def clean_value(value):
    value = value.strip()

    if value.upper() == "N/A":
        return None

    # Обычные числа: 750, 5500, 125
    if re.fullmatch(r"[\d,]+", value):
        return int(value.replace(",", ""))

    # Значения вроде x3 T1 Legendaries
    return value


def extract_items(html):
    soup = BeautifulSoup(html, "html.parser")

    # Берём текстовые куски страницы отдельно,
    # а не склеиваем всю страницу в одну строку.
    texts = [x.strip() for x in soup.stripped_strings if x.strip()]

    items = {}

    for i, text in enumerate(texts):

        if not text.startswith("Value -"):
            continue

        value_raw = text[len("Value -"):].strip()
        value = clean_value(value_raw)

        # N/A = непродаваемый предмет
        if value is None:
            continue

        name = None

        # Ищем название непосредственно перед Value -
        for previous in reversed(texts[max(0, i - 8):i]):

            # Формат:
            # Image: Zombie Dog | Zombie Dog Class - Common
            match = re.search(
                r"(?:Image:\s*)?.*?\|\s*(.*?)\s+Class\s*-\s*",
                previous
            )

            if match:
                name = match.group(1).strip()
                break

            # Запасной вариант:
            # Image: Name
            if previous.startswith("Image:"):
                candidate = previous[len("Image:"):].strip()

                if candidate and not candidate.startswith("This item is currently"):
                    name = candidate
                    break

        if not name:
            continue

        # Иногда перед названием остаётся Image:
        name = re.sub(r"^Image:\s*", "", name).strip()

        if not name:
            continue

        items[name] = {
            "name": name,
            "value": value
        }

    return list(items.values())


def scrape_category(category):
    url = BASE_URL + category

    print(f"Scraping {category}: {url}")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    items = extract_items(response.text)

    print(f"  Found: {len(items)} items")

    # КРИТИЧЕСКАЯ ЗАЩИТА:
    # если сайт изменился или парсер сломался,
    # НЕ разрешаем записать пустые данные.
    if len(items) == 0:
        raise RuntimeError(
            f"No items found in category '{category}'. "
            "Scraper stopped to prevent empty values.json."
        )

    return items


def main():
    result = {}

    for category in CATEGORIES:
        result[category] = scrape_category(category)

    # Дополнительная защита
    total = sum(len(items) for items in result.values())

    if total == 0:
        raise RuntimeError("TOTAL ITEMS = 0. Nothing will be written.")

    with open("values.json", "w", encoding="utf-8") as f:
        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("SUCCESS!")
    print(f"Total items: {total}")

    for category in CATEGORIES:
        print(f"{category}: {len(result[category])}")


if __name__ == "__main__":
    main()
