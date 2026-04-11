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


def main() -> None:
    songs = load_songs("data/songs.csv")

    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}

    print(f"\n  {BAR}")
    print(f"  MUSIC RECOMMENDER")
    print(f"  Genre: {user_prefs['genre']}   Mood: {user_prefs['mood']}   Energy: {user_prefs['energy']}")
    print(f"  Catalog: {len(songs)} songs loaded")
    print(f"  {BAR}")

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print(f"\n  Top {len(recommendations)} Recommendations\n")
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print_recommendation(rank, song, score, explanation)

    print(f"  {BAR}\n")


if __name__ == "__main__":
    main()
