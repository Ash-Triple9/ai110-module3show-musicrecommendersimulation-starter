import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Point-weighting recipe
# ---------------------------------------------------------------------------
# +2.0  Genre match      (categorical, binary)
# +1.0  Mood match       (categorical, binary)
# +1.5  Energy proximity (continuous: 1.5 × (1 − |song − target|))
# +0.5  Danceability proximity (continuous: 0.5 × (1 − |song − target|))
# +0.5  Acousticness proximity (continuous: 0.5 × (1 − |song − target|))
#
# Maximum possible score = 5.5
#
# Rationale:
#   Genre is the strongest signal (2.0) because listeners strongly identify
#   with a genre.  Mood is meaningful but softer (1.0) — a "chill" song can
#   still land in many moods.  Energy (1.5) is the most important continuous
#   feature; it determines workout vs study feel.  Danceability and
#   acousticness are tie-breakers at 0.5 each.
# ---------------------------------------------------------------------------

WEIGHT_GENRE       = 2.0
WEIGHT_MOOD        = 1.0
WEIGHT_ENERGY      = 1.5
WEIGHT_DANCEABILITY = 0.5
WEIGHT_ACOUSTICNESS = 0.5


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py

    Only favorite_genre, favorite_mood, and target_energy are required.
    All other fields have sensible defaults so the test suite and example
    profiles can each supply only the fields they care about.
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    name: str = "User"
    target_danceability: float = 0.65
    target_acousticness: float = 0.50
    target_tempo_bpm: float = 100.0
    likes_acoustic: bool = True


# --- Example Taste Profiles ---

PROFILE_CHILL_STUDY = UserProfile(
    name="Chill Studier",
    favorite_genre="lofi",
    favorite_mood="focused",
    target_energy=0.40,
    target_danceability=0.60,
    target_acousticness=0.80,
)

PROFILE_WORKOUT = UserProfile(
    name="Workout Mode",
    favorite_genre="pop",
    favorite_mood="intense",
    target_energy=0.90,
    target_danceability=0.85,
    target_acousticness=0.05,
    likes_acoustic=False,
)

PROFILE_LATE_NIGHT = UserProfile(
    name="Late Night Drive",
    favorite_genre="synthwave",
    favorite_mood="moody",
    target_energy=0.75,
    target_danceability=0.70,
    target_acousticness=0.20,
    likes_acoustic=False,
)

PROFILE_JAZZ_CAFE = UserProfile(
    name="Jazz Cafe",
    favorite_genre="jazz",
    favorite_mood="relaxed",
    target_energy=0.38,
    target_danceability=0.55,
    target_acousticness=0.85,
)


def _proximity(song_val: float, target_val: float, weight: float) -> float:
    """Return weighted proximity points for a continuous feature (0 → weight)."""
    return weight * (1.0 - abs(song_val - target_val))


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _score(self, user: UserProfile, song: Song) -> float:
        score = 0.0
        if song.genre == user.favorite_genre:
            score += WEIGHT_GENRE
        if song.mood == user.favorite_mood:
            score += WEIGHT_MOOD
        score += _proximity(song.energy, user.target_energy, WEIGHT_ENERGY)
        score += _proximity(song.danceability, user.target_danceability, WEIGHT_DANCEABILITY)
        score += _proximity(song.acousticness, user.target_acousticness, WEIGHT_ACOUSTICNESS)
        return score

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        scored = sorted(self.songs, key=lambda s: self._score(user, s), reverse=True)
        return scored[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        parts = []

        if song.genre == user.favorite_genre:
            parts.append(f"genre matches '{song.genre}' (+{WEIGHT_GENRE:.1f} pts)")
        if song.mood == user.favorite_mood:
            parts.append(f"mood matches '{song.mood}' (+{WEIGHT_MOOD:.1f} pts)")

        energy_pts = _proximity(song.energy, user.target_energy, WEIGHT_ENERGY)
        parts.append(
            f"energy {song.energy:.2f} is {'close to' if energy_pts >= 1.0 else 'somewhat near'} "
            f"your target {user.target_energy:.2f} (+{energy_pts:.2f} pts)"
        )

        dance_pts = _proximity(song.danceability, user.target_danceability, WEIGHT_DANCEABILITY)
        parts.append(f"danceability proximity (+{dance_pts:.2f} pts)")

        acoustic_pts = _proximity(song.acousticness, user.target_acousticness, WEIGHT_ACOUSTICNESS)
        parts.append(f"acousticness proximity (+{acoustic_pts:.2f} pts)")

        total = self._score(user, song)
        return f"Score {total:.2f}/5.5 — " + "; ".join(parts)


# ---------------------------------------------------------------------------
# Functional API (used by src/main.py)
# ---------------------------------------------------------------------------

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file into a list of dicts.
    Required by src/main.py
    """
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id":           int(row["id"]),
                "title":        row["title"],
                "artist":       row["artist"],
                "genre":        row["genre"],
                "mood":         row["mood"],
                "energy":       float(row["energy"]),
                "tempo_bpm":    float(row["tempo_bpm"]),
                "valence":      float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            })
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences using the point-weighting recipe.
    Required by recommend_songs() and src/main.py

    user_prefs keys: "genre", "mood", "energy",
                     optionally "danceability", "acousticness"
    Returns: (total_score, list_of_reason_strings)
    """
    score = 0.0
    reasons: List[str] = []

    # --- Categorical matches ---
    if song["genre"] == user_prefs.get("genre", ""):
        score += WEIGHT_GENRE
        reasons.append(f"Genre match '{song['genre']}': +{WEIGHT_GENRE:.1f}")

    if song["mood"] == user_prefs.get("mood", ""):
        score += WEIGHT_MOOD
        reasons.append(f"Mood match '{song['mood']}': +{WEIGHT_MOOD:.1f}")

    # --- Continuous proximity ---
    target_energy = user_prefs.get("energy", 0.5)
    energy_pts = _proximity(song["energy"], target_energy, WEIGHT_ENERGY)
    score += energy_pts
    reasons.append(
        f"Energy {song['energy']:.2f} vs target {target_energy:.2f}: +{energy_pts:.2f}"
    )

    target_dance = user_prefs.get("danceability", 0.65)
    dance_pts = _proximity(song["danceability"], target_dance, WEIGHT_DANCEABILITY)
    score += dance_pts
    reasons.append(f"Danceability {song['danceability']:.2f} vs target {target_dance:.2f}: +{dance_pts:.2f}")

    target_acoustic = user_prefs.get("acousticness", 0.50)
    acoustic_pts = _proximity(song["acousticness"], target_acoustic, WEIGHT_ACOUSTICNESS)
    score += acoustic_pts
    reasons.append(f"Acousticness {song['acousticness']:.2f} vs target {target_acoustic:.2f}: +{acoustic_pts:.2f}")

    return score, reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Scores every song, ranks by score descending, returns the top-k.
    Required by src/main.py

    Returns a list of (song_dict, score, explanation_string) tuples.
    """
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = " | ".join(reasons)
        scored.append((song, score, explanation))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]
