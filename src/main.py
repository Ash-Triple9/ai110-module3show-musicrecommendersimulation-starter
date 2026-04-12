"""
Command line runner for the Music Recommender Simulation.
"""

try:
    from src.recommender import load_songs, recommend_songs
except ModuleNotFoundError:
    from recommender import load_songs, recommend_songs

BAR  = "═" * 52
THIN = "─" * 52


def print_recommendation(rank: int, song: dict, score: float, explanation: str) -> None:
    reasons = explanation.split(" | ")
    max_score = 5.5

    filled = round((score / max_score) * 20)
    bar = "█" * filled + "░" * (20 - filled)

    print(f"  {BAR}")
    print(f"  #{rank}  {song['title']}  —  {song['artist']}")
    print(f"  {THIN}")
    print(f"  Score  {score:.2f} / {max_score:.1f}   [{bar}]")
    print(f"  {THIN}")
    for reason in reasons:
        print(f"    •  {reason}")


# Adversarial / edge-case profiles deliberately combine contradictory signals
# to stress-test the scorer: the winning songs will satisfy whichever features
# carry the most weight (genre/energy) while revealing how the recommender
# handles irreconcilable trade-offs.
EDGE_CASE_PROFILES = {
    # High energy + sad mood: scorer cannot satisfy both (energy drives hype,
    # mood drives sadness). Songs that match genre and energy will win,
    # even though their mood rarely aligns.
    "Manic Sad [high energy + sad mood]": {
        "genre": "pop",
        "mood": "sad",
        "energy": 0.90,
        "danceability": 0.85,
        "acousticness": 0.10,
    },
    # Acoustic/ambient genre but wants near-silence energy (0.05) and
    # maximum danceability — three features that rarely coexist.
    "Acoustic Rave [ambient + max dance + near-zero energy]": {
        "genre": "ambient",
        "mood": "relaxed",
        "energy": 0.05,
        "danceability": 0.99,
        "acousticness": 0.95,
    },
    # Completely unknown genre forces genre score to 0 for every song,
    # so the ranker must rely entirely on the continuous features.
    "Genre Void [unknown genre, all continuous mid-range]": {
        "genre": "xyzzy",
        "mood": "happy",
        "energy": 0.50,
        "danceability": 0.50,
        "acousticness": 0.50,
    },
    # Exact boundary values test numeric edge behaviour in _proximity().
    "All Zeros [boundary: energy=0, dance=0, acoustic=0]": {
        "genre": "rock",
        "mood": "intense",
        "energy": 0.00,
        "danceability": 0.00,
        "acousticness": 0.00,
    },
    # Ceiling values for every continuous feature.
    "All Ones [boundary: energy=1, dance=1, acoustic=1]": {
        "genre": "lofi",
        "mood": "focused",
        "energy": 1.00,
        "danceability": 1.00,
        "acousticness": 1.00,
    },
}

PROFILES = {
    "High-Energy Pop": {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.90,
        "danceability": 0.85,
        "acousticness": 0.10,
    },
    "Chill Lofi": {
        "genre": "lofi",
        "mood": "focused",
        "energy": 0.35,
        "danceability": 0.55,
        "acousticness": 0.80,
    },
    "Deep Intense Rock": {
        "genre": "rock",
        "mood": "intense",
        "energy": 0.88,
        "danceability": 0.50,
        "acousticness": 0.08,
    },
    "Math Rock": {
        "genre": "math rock",
        "mood": "focused",
        "energy": 0.72,
        "danceability": 0.40,
        "acousticness": 0.20,
    },
    "Nintendocore": {
        "genre": "nintendocore",
        "mood": "energetic",
        "energy": 0.95,
        "danceability": 0.65,
        "acousticness": 0.05,
    },
    "Witch House": {
        "genre": "witch house",
        "mood": "moody",
        "energy": 0.45,
        "danceability": 0.55,
        "acousticness": 0.35,
    },
}


def main() -> None:
    songs = load_songs("data/songs.csv")

    print(f"\n  {BAR}")
    print(f"  MUSIC RECOMMENDER  —  {len(songs)} songs loaded")
    print(f"  {BAR}")

    for profile_name, user_prefs in PROFILES.items():
        print(f"\n  {BAR}")
        print(f"  PROFILE: {profile_name}")
        print(f"  Genre: {user_prefs['genre']}   Mood: {user_prefs['mood']}   Energy: {user_prefs['energy']}")
        print(f"  {BAR}")

        recommendations = recommend_songs(user_prefs, songs, k=5)

        print(f"\n  Top {len(recommendations)} Recommendations\n")
        for rank, (song, score, explanation) in enumerate(recommendations, start=1):
            print_recommendation(rank, song, score, explanation)

        print(f"  {BAR}\n")

    print(f"\n  {'▓' * 52}")
    print(f"  ADVERSARIAL / EDGE-CASE PROFILES")
    print(f"  {'▓' * 52}")

    for profile_name, user_prefs in EDGE_CASE_PROFILES.items():
        print(f"\n  {BAR}")
        print(f"  EDGE CASE: {profile_name}")
        print(f"  Genre: {user_prefs['genre']}   Mood: {user_prefs['mood']}   Energy: {user_prefs['energy']}")
        print(f"  {BAR}")

        recommendations = recommend_songs(user_prefs, songs, k=5)

        print(f"\n  Top {len(recommendations)} Recommendations\n")
        for rank, (song, score, explanation) in enumerate(recommendations, start=1):
            print_recommendation(rank, song, score, explanation)

        print(f"  {BAR}\n")


if __name__ == "__main__":
    main()
