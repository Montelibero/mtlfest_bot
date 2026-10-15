"""Archive a past ticket season: mark tickets instead of moving them.

Usage (from project root, with .env pointing at the target Mongo):
    python archive_season.py 2025            # dry-run: preview only, no writes
    python archive_season.py 2025 --apply    # actually write the flags

For every user with ``tickets.<season>`` without an ``archived`` flag, sets:
    tickets.<season>.archived = true
    tickets.<season>.archived_at = <utcnow>

Idempotent: users already archived are skipped on re-run.
Reads MONGO_URI from .env / environment.
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv

load_dotenv()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Archive a ticket season (dry-run by default)")
    parser.add_argument("season", help="season key, e.g. 2025")
    parser.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    args = parser.parse_args()

    from database.database import users_collection

    season = args.season
    field = f"tickets.{season}"

    to_archive: list[dict] = []
    already: list[dict] = []
    async for user in users_collection.find({field: {"$exists": True}}):
        info = (user.get("tickets") or {}).get(season) or {}
        if info.get("archived"):
            already.append(user)
        else:
            to_archive.append(user)

    print(f"Season '{season}': {len(to_archive)} to archive, {len(already)} already archived")
    if to_archive:
        print("Preview (first 5):")
        for user in to_archive[:5]:
            info = (user.get("tickets") or {}).get(season) or {}
            print(f"  UserID={user.get('UserID')} key={info.get('key')} created={info.get('created_at')}")

    if not args.apply:
        print("\nDRY-RUN: nothing written. Re-run with --apply to archive.")
        return

    if not to_archive:
        print("Nothing to do.")
        return

    now = datetime.utcnow()
    result = await users_collection.update_many(
        {f"{field}": {"$exists": True}, f"{field}.archived": {"$ne": True}},
        {"$set": {f"{field}.archived": True, f"{field}.archived_at": now}},
    )
    print(f"Archived: {result.modified_count} users")


if __name__ == "__main__":
    asyncio.run(main())
