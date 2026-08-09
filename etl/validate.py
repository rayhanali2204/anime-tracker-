def validate_anime(anime):

    if anime["mal_id"] is None:
        return False

    if not anime["title"]:
        return False

    if anime["rank"] is None:
        return False

    if anime["score"] is not None:
        if anime["score"] < 0 or anime["score"] > 10:
            return False

    if anime["episodes"] is not None:
        if anime["episodes"] < 0:
            return False

    return True

def validate_anime_data(anime_data):

    valid_anime = []
    rejected_anime = []

    for anime in anime_data:

        if validate_anime(anime):
            valid_anime.append(anime)

        else:
            rejected_anime.append(anime)

    return valid_anime, rejected_anime

