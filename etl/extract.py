import requests
import time

TOP_ANIME_URL = "https://api.tenrai.org/v1/top/anime"


def extract_top_anime(limit=100):
    anime_data = []
    page = 1

    while len(anime_data) < limit:

        max_retries = 3

        for attempt in range(max_retries):

            try:
                response = requests.get(
                    TOP_ANIME_URL,
                    params={"page": page},
                    timeout=10
                )

                response.raise_for_status()
                break

            except requests.exceptions.RequestException:

                if attempt == max_retries - 1:
                    raise

                time.sleep(2)

        data = response.json()

        

        if not data.get("data"):
            break

        anime_data.extend(data["data"])

        page += 1

       

    return anime_data[:limit]