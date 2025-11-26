"""
Import Friends speaker data from TSV into the episode_speakers table.

This script is idempotent and safe to run multiple times.
It uses UPSERT logic to update existing records and insert new ones.

Data source: backend/data/friends_speakers.tsv
Format: episode<TAB>speaker<TAB>utterances

Usage:
    docker-compose exec backend python scripts/import_speakers.py

    # Or locally (with DATABASE_URL set):
    python scripts/import_speakers.py
"""

import csv
import os
import re
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.models import EpisodeSpeaker
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Path to TSV file (relative to backend directory)
DATA_FILE = Path(__file__).parent.parent / "data" / "friends_speakers.tsv"

# Pre-compiled regex for parsing episode format (e.g., "s01e05")
EPISODE_PATTERN = re.compile(r"^s(\d+)e(\d+)$", re.IGNORECASE)


def normalize_speaker_name(raw_name: str) -> str:
    """
    Normalize speaker names to title case.

    Handles special cases like honorifics and multi-word names.

    Examples:
        monica -> Monica
        mrs. geller -> Mrs. Geller
        mr. heckles -> Mr. Heckles
        dr. burke -> Dr. Burke
        chrissy on three's company -> Chrissy On Three's Company

    Args:
        raw_name: Raw speaker name from TSV (typically lowercase)

    Returns:
        Title-cased speaker name
    """
    return raw_name.strip().title()


def parse_episode(episode_str: str) -> tuple[int, int]:
    """
    Parse episode string to season and episode numbers.

    Args:
        episode_str: Episode in format 's01e01', 's10e18', etc.

    Returns:
        (season, episode_number) tuple

    Raises:
        ValueError: If episode format is invalid

    Examples:
        's01e05' -> (1, 5)
        's10e18' -> (10, 18)
        'S02E03' -> (2, 3)  # case-insensitive
    """
    match = EPISODE_PATTERN.match(episode_str.strip())
    if not match:
        raise ValueError(f"Invalid episode format: '{episode_str}' (expected 's01e01')")
    return int(match.group(1)), int(match.group(2))


def read_tsv_data(file_path: Path) -> list[dict]:
    """
    Read and parse the TSV file.

    Args:
        file_path: Path to the TSV file

    Returns:
        List of dicts with keys: season, episode_number, speaker_name, utterances

    Raises:
        FileNotFoundError: If TSV file doesn't exist
        ValueError: If TSV format is invalid
    """
    if not file_path.exists():
        raise FileNotFoundError(f"TSV file not found: {file_path}")

    records = []
    line_number = 0

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        # Validate header
        expected_columns = {"episode", "speaker", "utterances"}
        if not expected_columns.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                f"TSV missing required columns. "
                f"Expected: {expected_columns}, Got: {reader.fieldnames}"
            )

        for row in reader:
            line_number += 1
            try:
                season, episode_number = parse_episode(row["episode"])
                speaker_name = normalize_speaker_name(row["speaker"])
                utterances = int(row["utterances"])

                records.append(
                    {
                        "season": season,
                        "episode_number": episode_number,
                        "speaker_name": speaker_name,
                        "utterances": utterances,
                    }
                )
            except (ValueError, KeyError) as e:
                print(f"  Warning: Skipping line {line_number + 1}: {e}")
                continue

    return records


def import_speakers_postgres(db, records: list[dict]) -> tuple[int, int]:
    """
    Import speakers using PostgreSQL UPSERT (ON CONFLICT DO UPDATE).

    This is idempotent - running multiple times updates existing records
    and inserts new ones without creating duplicates.

    Args:
        db: Database session
        records: List of speaker records to import

    Returns:
        (inserted_count, updated_count) tuple
    """
    if not records:
        return 0, 0

    # Use PostgreSQL's INSERT ... ON CONFLICT DO UPDATE
    # This is atomic and handles race conditions
    stmt = pg_insert(EpisodeSpeaker).values(records)

    # On conflict with unique constraint, update utterances
    # (speaker_name normalization is idempotent, so no change expected there)
    stmt = stmt.on_conflict_do_update(
        constraint="uix_season_episode_speaker",
        set_={"utterances": stmt.excluded.utterances},
    )

    result = db.execute(stmt)
    db.commit()

    # PostgreSQL doesn't easily distinguish inserts vs updates in ON CONFLICT
    # Return total affected rows
    return result.rowcount, 0


def import_speakers_fallback(db, records: list[dict]) -> tuple[int, int]:
    """
    Fallback import method for non-PostgreSQL databases (e.g., SQLite).

    Uses query-then-insert/update pattern. Less efficient but compatible.

    Args:
        db: Database session
        records: List of speaker records to import

    Returns:
        (inserted_count, updated_count) tuple
    """
    inserted = 0
    updated = 0

    for record in records:
        # Check if record exists
        existing = (
            db.query(EpisodeSpeaker)
            .filter(
                EpisodeSpeaker.season == record["season"],
                EpisodeSpeaker.episode_number == record["episode_number"],
                EpisodeSpeaker.speaker_name == record["speaker_name"],
            )
            .first()
        )

        if existing:
            # Update utterances if changed
            if existing.utterances != record["utterances"]:
                existing.utterances = record["utterances"]
                updated += 1
        else:
            # Insert new record
            speaker = EpisodeSpeaker(**record)
            db.add(speaker)
            inserted += 1

    db.commit()
    return inserted, updated


def get_stats(db) -> dict:
    """
    Get statistics about the episode_speakers table.

    Args:
        db: Database session

    Returns:
        Dict with total_records, unique_episodes, unique_speakers
    """
    total = db.query(EpisodeSpeaker).count()

    # Count unique (season, episode) combinations
    unique_episodes = (
        db.query(EpisodeSpeaker.season, EpisodeSpeaker.episode_number)
        .distinct()
        .count()
    )

    # Count unique speaker names
    unique_speakers = db.query(EpisodeSpeaker.speaker_name).distinct().count()

    return {
        "total_records": total,
        "unique_episodes": unique_episodes,
        "unique_speakers": unique_speakers,
    }


def import_speakers():
    """
    Main import function.

    Reads TSV file, parses data, and imports into database.
    Idempotent - safe to run multiple times.
    """
    print("=" * 60)
    print("Friends Speaker Data Import")
    print("=" * 60)

    # Verify data file exists
    print(f"\nData file: {DATA_FILE}")
    if not DATA_FILE.exists():
        print(f"ERROR: Data file not found: {DATA_FILE}")
        print("Please ensure backend/data/friends_speakers.tsv exists.")
        sys.exit(1)

    # Read and parse TSV
    print("\nStep 1: Reading TSV file...")
    try:
        records = read_tsv_data(DATA_FILE)
        print(f"  Parsed {len(records)} speaker records")
    except Exception as e:
        print(f"ERROR: Failed to read TSV: {e}")
        sys.exit(1)

    if not records:
        print("WARNING: No valid records found in TSV file.")
        sys.exit(0)

    # Show sample data
    print("\nSample data (first 5 records):")
    for record in records[:5]:
        print(
            f"  S{record['season']:02d}E{record['episode_number']:02d} - "
            f"{record['speaker_name']} ({record['utterances']} utterances)"
        )

    # Connect to database and import
    print("\nStep 2: Importing to database...")
    db = SessionLocal()
    try:
        # Check database dialect
        dialect = db.bind.dialect.name if db.bind else "unknown"
        print(f"  Database dialect: {dialect}")

        # Get pre-import stats
        pre_stats = get_stats(db)
        print(f"  Existing records: {pre_stats['total_records']}")

        # Import using appropriate method
        if dialect == "postgresql":
            inserted, updated = import_speakers_postgres(db, records)
            print(f"  UPSERT completed: {inserted} rows affected")
        else:
            inserted, updated = import_speakers_fallback(db, records)
            print(f"  Inserted: {inserted}, Updated: {updated}")

        # Get post-import stats
        post_stats = get_stats(db)
        print(f"\nStep 3: Verifying import...")
        print(f"  Total records: {post_stats['total_records']}")
        print(f"  Unique episodes: {post_stats['unique_episodes']}")
        print(f"  Unique speakers: {post_stats['unique_speakers']}")

        # Verify expected data
        if post_stats["total_records"] < len(records):
            print(
                f"  WARNING: Fewer records in DB ({post_stats['total_records']}) "
                f"than in TSV ({len(records)}). Check for duplicates in source data."
            )

        print("\n" + "=" * 60)
        print("Import completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"ERROR: Import failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_speakers()
