from datetime import datetime, timezone
import time

from ani_tracker import app, db, PipelineRun
from etl.extract import extract_top_anime
from etl.transform import transform_anime_data
from etl.validate import validate_anime_data
from etl.load import load_anime


def run_pipeline():

    start_time = time.perf_counter()
    started_at = datetime.now(timezone.utc)

    try:
        raw_anime = extract_top_anime(100)

        transformed_anime = transform_anime_data(raw_anime)

        valid_anime, rejected_anime = validate_anime_data(
            transformed_anime
        )

        inserted, updated = load_anime(valid_anime)

        end_time = time.perf_counter()
        runtime_ms = (end_time - start_time) * 1000

        with app.app_context():

            run = PipelineRun(
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                records_extracted=len(raw_anime),
                records_transformed=len(transformed_anime),
                records_valid=len(valid_anime),
                records_rejected=len(rejected_anime),
                records_inserted=inserted,
                records_updated=updated,
                status="SUCCESS",
                runtime_ms=runtime_ms
            )

            db.session.add(run)
            db.session.commit()

        print("ETL Pipeline Complete")
        print(f"Extracted: {len(raw_anime)}")
        print(f"Transformed: {len(transformed_anime)}")
        print(f"Valid: {len(valid_anime)}")
        print(f"Rejected: {len(rejected_anime)}")
        print(f"Inserted: {inserted}")
        print(f"Updated: {updated}")
        print(f"Runtime: {runtime_ms:.2f} ms")

    except Exception as error:

        end_time = time.perf_counter()
        runtime_ms = (end_time - start_time) * 1000

        with app.app_context():

            failed_run = PipelineRun(
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            status="FAILED",
            runtime_ms=runtime_ms,
            error_message=str(error)
        )

            db.session.add(failed_run)
            db.session.commit()

        print("ETL Pipeline Failed")
        print(f"Error: {error}")





if __name__ == "__main__":
    run_pipeline()