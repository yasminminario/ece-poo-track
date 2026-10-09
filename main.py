import json
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path


DATA_PATH = Path(__file__).parent / "data" / "festival.json"
try:
    with DATA_PATH.open(encoding="utf-8") as file:
        festival = json.load(file)
except (FileNotFoundError, json.JSONDecodeError) as error:
    print(f"Error: {error}")
    raise SystemExit(1)

# Step 03
def slug(text):
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode().lower()
    text = "".join(character if character.isalnum() else " " for character in text)
    return "-".join(text.split())

def venues():
    total_seats = 0
    for venue in festival["venues"]:
        venue_slug = slug(venue["name"])
        print(f"{venue_slug}: {venue['name']}, {venue['capacity']} seats")
        total_seats += venue["capacity"]
    print(f"Total: {total_seats} seats")

def performance_start(performance):
    return datetime.fromisoformat(performance["start"])

def performance_end(performance):
    return performance_start(performance) + timedelta(
        minutes=performance["duration_minutes"]
    )

def festival_day(performance):
    return (performance_start(performance) - timedelta(hours=6)).date()


def artist(artist_slug):
    selected_artist = next(
        (artist for artist in festival["artists"] if slug(artist["name"]) == artist_slug),
        None
    )
    if selected_artist is None:
        print(f"No artist '{artist_slug}'.")
        return

    print(selected_artist["name"])
    for performance in festival["performances"]:
        role = None
        if performance.get("artist") == artist_slug:
            role = "solo"
        elif performance.get("teacher") == artist_slug:
            role = "teacher"
        elif performance.get("host") == artist_slug:
            role = "host"
        elif artist_slug in performance.get("acts", []):
            role = "act"

        if role is not None:
            venue_name = next(
                venue["name"]
                for venue in festival["venues"]
                if slug(venue["name"]) == performance["venue"]
            )
            start = performance_start(performance)
            end = performance_end(performance)
            day = festival_day(performance)

            print(
                f"{day:%a %d} {start:%H:%M}-{end:%H:%M} | "
                f"{venue_name} | {performance['title']} ({role})"
            )
if len(sys.argv) > 1 and sys.argv[1] == "venues":
    venues()
    raise SystemExit

if len(sys.argv) > 1 and sys.argv[1] == "artist":
    if len(sys.argv) < 3:
        print("Please provide an artist name.")
        raise SystemExit
    artist_slug = sys.argv[2]
    artist(artist_slug)
    raise SystemExit

# Step 04
def programme(day):
    days = sorted({performance["start"][:10] for performance in festival["performances"]})
    if day not in days:
        raise ValueError(f"'{day}' is not a day, use YYYY-MM-DD.")

    venue_names = {
        slug(venue["name"]): venue["name"]
        for venue in festival["venues"]
    }
    programme_day = datetime.fromisoformat(day)
    print(f"Programme for {programme_day.strftime('%A')} {programme_day.day} "
          f"{programme_day.strftime('%B')}:")
    for performance in festival["performances"]:
        start = performance_start(performance)
        if festival_day(performance).isoformat() == day:
            end = performance_end(performance)
            venue_name = venue_names[performance["venue"]]
            print(
                f"{start:%H:%M}-{end:%H:%M} | {venue_name} | "
                f"{performance['title']} ({performance['kind']})"
            )

def now(now_time):
    venue_names = {
        slug(venue["name"]): venue["name"]
        for venue in festival["venues"]
    }

    print(f"On stage at {now_time:%Y-%m-%d %H:%M}:")
    upcoming = []
    for performance in festival["performances"]:
        start = performance_start(performance)
        end = performance_end(performance)
        if start <= now_time < end:
            print(
                f"- {performance['title']} at "
                f"{venue_names[performance['venue']]}, until {end:%H:%M}"
            )
        elif start > now_time:
            upcoming.append((start, end, performance))

    current_festival_day = now_time.date()
    if now_time.hour < 6:
        current_festival_day -= timedelta(days=1)
    upcoming = [
        item for item in upcoming
        if festival_day(item[2]) >= current_festival_day
    ]
    if upcoming:
        print("Up next:")
        for start, end, performance in sorted(upcoming)[:3]:
            print(
                f"- {start:%H:%M}-{end:%H:%M} | "
                f"{venue_names[performance['venue']]} | "
                f"{performance['title']} ({performance['kind']})"
            )
            
if len(sys.argv) > 1 and sys.argv[1] == "programme":
    if len(sys.argv) < 3:
        print("Error: Please provide a day (YYYY-MM-DD).")
        raise SystemExit(1)
    day = sys.argv[2]
    try:
        programme(day)
    except ValueError as error:
        print(f"Error: {error}")
        raise SystemExit(1)
    raise SystemExit

if len(sys.argv) > 1 and sys.argv[1] == "now":
    if len(sys.argv) < 3:
        print("Error: Please provide a date and time (YYYY-MM-DDTHH:MM).")
        raise SystemExit(1)

    try:
        now_time = datetime.fromisoformat(sys.argv[2])
    except ValueError:
        print(f"Error: '{sys.argv[2]}' is not a valid date and time.")
        raise SystemExit(1)

    now(now_time)
    raise SystemExit

# Step 05

def validate_new_performance(
    artist_slug,
    venue_slug,
    start,
    duration,
    venue_slugs,
    artist_names,
):
    if venue_slug not in venue_slugs:
        raise ValueError(f"Unknown venue '{venue_slug}'.")

    if artist_slug not in artist_names:
        raise ValueError(f"Unknown artist '{artist_slug}'.")

    if not 1 <= duration <= 360:
        raise ValueError("Duration must be between 1 and 360 minutes.")

    new_festival_day = (start - timedelta(hours=6)).date()
    first_day = datetime.fromisoformat(festival["first_day"]).date()
    last_day = datetime.fromisoformat(festival["last_day"]).date()

    if not first_day <= new_festival_day <= last_day:
        raise ValueError(
            f"{new_festival_day} is not a day of the festival."
        )

    new_end = start + timedelta(minutes=duration)

    for performance in festival["performances"]:
        existing_start = performance_start(performance)
        existing_end = performance_end(performance)

        too_close = (
            start < existing_end + timedelta(minutes=30)
            and existing_start < new_end + timedelta(minutes=30)
        )

        if not too_close:
            continue

        if performance["venue"] == venue_slug:
            raise ValueError(
                f"{venue_slugs[venue_slug]} is busy with "
                f"{performance['title']}."
            )

        performance_artists = [performance.get("artist")]
        performance_artists += [
            performance.get("teacher"),
            performance.get("host"),
        ]
        performance_artists += performance.get("acts", [])

        if artist_slug in performance_artists:
            raise ValueError(
                f"{artist_names[artist_slug]} is on stage in "
                f"{performance['title']}."
            )
            
def add():
    title = input("Title: ").strip()
    artist_slug = input("Artist (slug): ").strip()
    venue_slug = input("Venue (slug): ").strip()
    start_text = input("Start (YYYY-MM-DDTHH:MM): ").strip()
    duration_text = input("Duration (minutes): ").strip()
    try:
        start = datetime.fromisoformat(start_text)
    except ValueError:
        raise ValueError(f"'{start_text}' is not a valid date and time.") from None
    try:
        duration = int(duration_text)
    except ValueError:
        raise ValueError(
            f"'{duration_text}' is not a number of minutes."
        ) from None

    venue_slugs = {
        slug(venue["name"]): venue["name"]
        for venue in festival["venues"]
    }

    artist_names = {
        slug(artist["name"]): artist["name"]
        for artist in festival["artists"]
    }

    validate_new_performance(
        artist_slug,
        venue_slug,
        start,
        duration,
        venue_slugs,
        artist_names,
    )

    performance_id = f"{venue_slug}-{start:%Y-%m-%d-%H%M}"
    festival["performances"].append({
        "kind": "solo",
        "title": title,
        "venue": venue_slug,
        "start": start_text,
        "duration_minutes": duration,
        "description": "",
        "artist": artist_slug,
        "min_age": 0,
    })
    with DATA_PATH.open("w", encoding="utf-8") as file:
        json.dump(festival, file, ensure_ascii=False, indent=2)
    print(f"Added: {performance_id}")


def cancel(performance_id):
    for index, performance in enumerate(festival["performances"]):
        candidate_id = (
            f"{performance['venue']}-{performance['start'].replace('T', '-')}"
            .replace(":", "")
        )
        if candidate_id == performance_id:
            cancelled = festival["performances"].pop(index)
            with DATA_PATH.open("w", encoding="utf-8") as file:
                json.dump(festival, file, ensure_ascii=False, indent=2)
            print(f"Cancelled: {cancelled['title']}")
            return
    raise ValueError(f"No performance '{performance_id}'.")


if len(sys.argv) > 1 and sys.argv[1] == "add":
    try:
        add()
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"Error: {error}")
        raise SystemExit(1)
    raise SystemExit

if len(sys.argv) > 1 and sys.argv[1] == "cancel":
    if len(sys.argv) < 3:
        print("Error: Please provide a performance id.")
        raise SystemExit(1)
    try:
        cancel(sys.argv[2])
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"Error: {error}")
        raise SystemExit(1)
    raise SystemExit

known_commands = {"venues", "artist", "programme", "now", "add", "cancel"}

if len(sys.argv) > 1 and sys.argv[1] not in known_commands:
    print("Usage: uv run main.py [venues|artist|programme|now|add|cancel]")
    raise SystemExit(1)

# Step 00
print(festival["name"])
print(f'From {festival["first_day"]} to {festival["last_day"]}')
print(
    f'{len(festival["venues"])} venues, '
    f'{len(festival["artists"])} artists, '
    f'{len(festival["performances"])} performances'
)

# Step 01
print("\nVenues:")
for venue in festival["venues"]:
    print(f" - {venue['name']}: {venue['capacity']} seats ({venue['address']})")
print (f"Total: {sum(venue['capacity'] for venue in festival['venues'])} seats")
print ("\n")
print(f"lineup: {sum(1 for performance in festival['performances'] if performance['kind'] == 'lineup')}")
print(f"solo: {sum(1 for performance in festival['performances'] if performance['kind'] == 'solo')}")
print(f"workshop: {sum(1 for performance in festival['performances'] if performance['kind'] == 'workshop')}")
print ("\n")
venue_slug = "le-kiosque"
venue_name = next(
    venue["name"] for venue in festival["venues"] if venue["name"] == "Le Kiosque"
)
print(f"At {venue_name}:")
for performance in festival["performances"]:
    if performance["venue"] == venue_slug:
        date = performance["start"].split("T")[0]
        print(f" - {date} {performance['title']}")
print("\n")
print(f"Longest: {max(festival['performances'], key=lambda p: p['duration_minutes'])['title']} ({max(festival['performances'], key=lambda p: p['duration_minutes'])['duration_minutes']} minutes)")
print("\n")
for performance in festival["performances"]:
    if "participants" in performance and "max_participants" in performance:
        date = performance["start"].split("T")[0]
        print(f"{performance['title']} on {date}: "
              f"{len(performance['participants'])}/"
              f"{performance['max_participants']} registered")
print("\n")
artist_appearances = Counter()
artist_order = []
for performance in festival["performances"]:
    if performance["kind"] == "solo":
        performance_artists = [performance["artist"]]
    elif performance["kind"] == "workshop":
        performance_artists = [performance["teacher"]]
    elif performance["kind"] == "lineup":
        performance_artists = [performance["host"]] + performance["acts"]

    for artist_id in performance_artists:
        artist_appearances[artist_id] += 1
        if artist_id not in artist_order:
            artist_order.append(artist_id)

most_appearances = max(artist_appearances.values())

artists_on_stage_most = [
    artist_id
    for artist_id in artist_order
    if artist_appearances[artist_id] == most_appearances
]

print(
    f"On stage {most_appearances} times: "
    + ", ".join(artists_on_stage_most)
)

# Step 02
days = sorted({performance["start"][:10] for performance in festival["performances"]})
venue_names = {}
for venue in festival["venues"]:
    venue_slug = (
        venue["name"].lower()
        .replace("é", "e")
        .replace("â", "a")
        .replace(" ", "-")
    )
    venue_names[venue_slug] = venue["name"]

day = input("Day (YYYY-MM-DD): ").strip()
while day not in days:
    print(f"No performance on '{day}'. Days: {', '.join(days)}")
    day = input("Day (YYYY-MM-DD): ").strip()

print(f"Programme for {day}:")
for performance in festival["performances"]:
    if performance["start"][:10] == day:
        time = performance["start"][11:]
        venue_name = venue_names[performance["venue"]]
        print(
            f"{time} | {venue_name} | "
            f"{performance['title']} ({performance['kind']})"
        )
