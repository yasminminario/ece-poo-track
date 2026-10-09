import json
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path


with (Path(__file__).parent / "data" / "festival.json").open(encoding="utf-8") as file:
    festival = json.load(file)

# Step 03
def venues():
    total_seats = 0
    for venue in festival["venues"]:
        venue_slug = (
            venue["name"].lower()
            .replace("é", "e")
            .replace("â", "a")
            .replace(" ", "-")
        )
        print(f"{venue_slug}: {venue['name']}, {venue['capacity']} seats")
        total_seats += venue["capacity"]
    print(f"Total: {total_seats} seats")

def artist(artist_slug):
    selected_artist = next(
        (
            artist for artist in festival["artists"]
            if "".join(
                character for character in unicodedata.normalize(
                    "NFKD", artist["name"]
                )
                if not unicodedata.combining(character)
            ).lower().replace(" ", "-") == artist_slug
        ),
        None,
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
                if venue["name"].lower()
                .replace("é", "e")
                .replace("â", "a")
                .replace(" ", "-") == performance["venue"]
            )
            start = datetime.fromisoformat(performance["start"])
            end = start + timedelta(minutes=performance["duration_minutes"])
            print(
                f"{start:%a %d %H:%M}-{end:%H:%M} | "
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
        print(f"No performance on '{day}'. Days: {', '.join(days)}")
        return

    venue_names = {
        venue["name"].lower()
        .replace("é", "e")
        .replace("â", "a")
        .replace(" ", "-"): venue["name"]
        for venue in festival["venues"]
    }
    programme_day = datetime.fromisoformat(day)
    print(f"Programme for {programme_day.strftime('%A')} {programme_day.day} "
          f"{programme_day.strftime('%B')}:")
    for performance in festival["performances"]:
        start = datetime.fromisoformat(performance["start"])
        festival_day = (start - timedelta(hours=6)).date()
        if festival_day.isoformat() == day:
            end = start + timedelta(minutes=performance["duration_minutes"])
            venue_name = venue_names[performance["venue"]]
            print(
                f"{start:%H:%M}-{end:%H:%M} | {venue_name} | "
                f"{performance['title']} ({performance['kind']})"
            )

def now(now_time):
    venue_names = {
        venue["name"].lower()
        .replace("é", "e")
        .replace("â", "a")
        .replace(" ", "-"): venue["name"]
        for venue in festival["venues"]
    }

    print(f"On stage at {now_time:%Y-%m-%d %H:%M}:")
    upcoming = []
    for performance in festival["performances"]:
        start = datetime.fromisoformat(performance["start"])
        end = start + timedelta(minutes=performance["duration_minutes"])
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
        if (
            item[0].date()
            - timedelta(days=1 if item[0].hour < 6 else 0)
        ) >= current_festival_day
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
        print("Please provide a day (YYYY-MM-DD).")
        raise SystemExit
    day = sys.argv[2]
    programme(day)
    raise SystemExit

if len(sys.argv) > 1 and sys.argv[1] == "now":
    if len(sys.argv) < 3:
        print("Please provide a date and time (YYYY-MM-DDTHH:MM).")
        raise SystemExit
    now(datetime.fromisoformat(sys.argv[2]))
    raise SystemExit


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

artists_on_stage_4_times = [
    artist_id for artist_id in artist_order if artist_appearances[artist_id] == 4
]
print("On stage 4 times: " + ", ".join(artists_on_stage_4_times))


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
