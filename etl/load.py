from ani_tracker import app, db, AnimeCatalog 

def load_anime(anime_data):
    inserted = 0
    updated = 0

    with app.app_context():

        for anime in anime_data:

            existing_anime = AnimeCatalog.query.filter_by(mal_id=anime["mal_id"]).first()

            if existing_anime:

                existing_anime.title = anime["title"]
                existing_anime.title_english = anime["title_english"]
                existing_anime.image_url = anime["image_url"]
                existing_anime.type = anime["type"]
                existing_anime.episodes = anime["episodes"]
                existing_anime.status = anime["status"]
                existing_anime.score = anime["score"]
                existing_anime.rank = anime["rank"]
                existing_anime.popularity = anime["popularity"]
                existing_anime.year = anime["year"]
                existing_anime.season = anime["season"]
                existing_anime.genres = anime["genres"]
                existing_anime.studio = anime["studio"]

                updated += 1

            else:

                new_anime = AnimeCatalog(
                    mal_id=anime["mal_id"],
                    title=anime["title"],
                    title_english=anime["title_english"],
                    image_url=anime["image_url"],
                    type=anime["type"],
                    episodes=anime["episodes"],
                    status=anime["status"],
                    score=anime["score"],
                    rank=anime["rank"],
                    popularity=anime["popularity"],
                    year=anime["year"],
                    season=anime["season"],
                    genres=anime["genres"],
                    studio=anime["studio"]
                )

                db.session.add(new_anime)

                inserted += 1

        db.session.commit()

        return inserted, updated