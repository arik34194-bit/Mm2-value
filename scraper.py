import json
import re
import time

from bs4 import BeautifulSoup
from curl_cffi import requests


BASE_URL = "https://supremevalues.com/mm2"

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


def parse_value(card):
    """
    Получает значение предмета.

    Сначала пробуем data-value.
    Если его нет, пытаемся найти видимое Value - ...
    """

    # Основной вариант: data-value
    raw = card.get("data-value")

    if raw is not None:
        raw = str(raw).strip()

        if raw.upper() == "N/A":
            return None

        # Числовое значение
        if re.fullmatch(r"\d+(?:\.\d+)?", raw):
            number = float(raw)

            if number.is_integer():
                return int(number)

            return number

    # Запасной вариант — ищем Value в тексте карточки
    text = card.get_text(" ", strip=True)

    match = re.search(
        r"Value\s*-\s*([\d,]+|x\d+\s+T1\s+\w+)",
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    value = match.group(1).strip()

    if value.upper() == "N/A":
        return None

    if re.fullmatch(r"[\d,]+", value):
        return int(value.replace(",", ""))

    return value


def scrape_category(category):
    url = f"{BASE_URL}/{category}"

    print(f"Scraping {category}: {url}")

    response = requests.get(
        url,
        impersonate="chrome120",
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    items = {}

    cards = soup.select(".itemcolumn")

    print(f"  Cards found: {len(cards)}")

    for card in cards:

        name_element = card.select_one(".itemhead")

        if not name_element:
            continue

        name = name_element.get_text(" ", strip=True)

        if not name:
            continue

        value = parse_value(card)

        # Пропускаем предметы без значения
        if value is None:
            continue

        items[name] = {
            "name": name,
            "value": value
        }

    result = list(items.values())

    print(f"  Items with values: {len(result)}")

    # Защита от поломки парсера
    if len(result) == 0:
        raise RuntimeError(
            f"No items found in category '{category}'. "
            "values.json will NOT be changed."
        )

    return result


def main():

    result = {}

    for category in CATEGORIES:

        result[category] = scrape_category(category)

        # Небольшая пауза между запросами
        time.sleep(2)

    total = sum(
        len(items)
        for items in result.values()
    )

    if total == 0:
        raise RuntimeError(
            "No items were scraped. "
            "values.json will NOT be changed."
        )

    # Записываем JSON только после успешного
    # получения всех категорий
    with open(
        "values.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("================================")
    print("SUCCESS!")
    print(f"Total items: {total}")
    print("================================")

    for category in CATEGORIES:
        print(
            f"{category}: "
            f"{len(result[category])}"
        )


if __name__ == "__main__":
    main()
