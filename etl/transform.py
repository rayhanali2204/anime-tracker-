def transform_anime(anime):
    transformed = {
        "mal_id": anime.get("mal_id"),
        "title": anime.get("title"),
        "title_english": anime.get("title_english"),
        "image_url": anime.get("images", {}).get("jpg", {}).get("image_url"),
        "type": anime.get("type"),
        "episodes": anime.get("episodes"),
        "status": anime.get("status"),
        "score": anime.get("score"),
        "rank": anime.get("rank"),
        "popularity": anime.get("popularity"),
        "year": anime.get("year"),
        "season": anime.get("season"),
        "genres": [
            genre.get("name")
            for genre in anime.get("genres", [])
        ],
        "studio": (
            anime.get("studios", [{}])[0].get("name")
            if anime.get("studios")
            else None
        )
    }

    return transformed

def transform_anime_data(anime_data):
    transformed_data = []

    for anime in anime_data:
        transformed_anime = transform_anime(anime)
        transformed_data.append(transformed_anime)

    return transformed_data