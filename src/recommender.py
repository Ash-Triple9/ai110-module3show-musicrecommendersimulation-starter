import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Point-weighting recipe
# ---------------------------------------------------------------------------
# +1.5  Genre match      (categorical, binary)
# +1.0  Mood match       (categorical, binary)
# +2.0  Energy proximity (continuous: 2.0 × (1 − |song − target|))
# +0.5  Danceability proximity (continuous: 0.5 × (1 − |song − target|))
# +0.5  Acousticness proximity (continuous: 0.5 × (1 − |song − target|))
#
# Maximum possible score = 5.5
#
# Rationale (revised):
#   Genre is still a strong signal (1.5) but no longer dominant enough to
#   override a poor continuous match.  Energy is now the top weight (2.0)
#   because it most directly determines the listening feel (workout vs study).
#   A song with near-perfect energy/danceability/acousticness alignment can
#   now overturn a weak genre match — previously impossible when genre alone
#   was worth 36 % of the max score.  Mood and tie-breaker weights unchanged.
#
# Previous weights: GENRE=2.0, ENERGY=1.5  →  genre share was 36 % of 5.5
# Revised weights:  GENRE=1.5, ENERGY=2.0  →  genre share is  27 % of 5.5
#                                              continuous share is 55 % of 5.5
# ---------------------------------------------------------------------------

WEIGHT_GENRE       = 1.5
WEIGHT_MOOD        = 1.0
WEIGHT_ENERGY      = 2.0
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
    target_danceability: float = 0.65   # default silently biases toward danceable songs (bias #8)
    target_acousticness: float = 0.50
    target_tempo_bpm: float = 100.0     # loaded but never used in scoring (dead field — bias #6)
    likes_acoustic: bool = True         # defined but never read in _score() (dead field — bias #5)


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


# ---------------------------------------------------------------------------
# KNOWN BIASES & FILTER BUBBLE ANALYSIS
# ---------------------------------------------------------------------------
#
# 1. ENERGY DESERT (dataset gap 0.55 → 0.75)
#    The catalog has NO songs between energy 0.55 and 0.75 — a gap of 0.20.
#    A user targeting energy=0.65 can score at most:
#      2.0 × (1 − 0.10) = 1.80 pts  (best available: Afternoon Daydream at 0.55)
#    vs a user targeting energy=0.38:
#      2.0 × (1 − 0.00) = 2.00 pts  (exact match: Late Night Pages)
#    Medium-energy users are structurally disadvantaged — their best possible
#    energy score is capped ~10 % below maximum through no fault of their prefs.
#
# 2. LOFI OVER-REPRESENTATION
#    Genre counts: lofi=4, all others ≤2, hip-hop=1, classical=1.
#    A lofi user has twice the variety and twice the chance of a genre+mood
#    double-hit compared to a hip-hop or classical user, who are limited to
#    a single song each and can never earn the genre bonus on anything else.
#
# 3. ARTIST ECHO CHAMBER (no diversity penalty)
#    Neon Echo (3 songs) and Slow Stereo (3 songs) can occupy multiple slots
#    in a user's top-5 simultaneously. The scorer has no artist-repeat penalty,
#    so the same artist can sweep all 5 recommendations for some profiles.
#
# 4. SINGLE-OCCURRENCE MOODS ("confident", "peaceful", "melancholic")
#    These moods each appear exactly once in the catalog. A user whose target
#    mood is "confident" can earn the +1.0 mood bonus on at most one song,
#    and that song (Gold Chain Manifesto, hip-hop) must also compete on all
#    continuous dimensions. Effectively these users have mood scoring disabled.
#
# 5. DEAD FIELD — `likes_acoustic` (UserProfile)
#    `likes_acoustic: bool` is defined on UserProfile but is NEVER read in
#    `_score()` or `score_song()`. A user who sets `likes_acoustic=False` gets
#    no benefit; highly acoustic songs are not penalised for them.
#
# 6. DEAD COLUMNS — `valence` and `tempo_bpm` (songs.csv)
#    Both columns are loaded by `load_songs()` and stored in every song dict,
#    but neither is passed to `_proximity()` in the scoring path. A user who
#    prefers high-valence (uplifting) or specific-tempo (e.g., 180 BPM for
#    running) music cannot express those preferences at all.
#
# 7. BINARY CATEGORICAL MATCHING (no semantic distance)
#    Genre and mood are matched with exact string equality. "indie pop" and
#    "pop" are treated as completely unrelated (0 pts) even though listeners
#    routinely cross between them. "moody" and "melancholic" are equally
#    distant. A genre taxonomy or mood adjacency matrix would fix this.
#
# 8. SILENT DEFAULT BIAS (danceability=0.65, energy=0.5)
#    `score_song()` uses `user_prefs.get("danceability", 0.65)` — any profile
#    that omits danceability is silently scored as if it prefers medium-high
#    danceability. The dataset mean is ~0.62, so this subtly biases omitted
#    profiles toward danceable songs. Same pattern for energy default of 0.5.
#
# 9. SYMMETRIC PROXIMITY (no directional preferences)
#    `_proximity` treats energy=0.70 and energy=0.90 as equally close to a
#    target of 0.80. There is no way to express "at least 0.8 energy" or
#    "no more than 0.4 energy" — overshooting and undershooting are penalised
#    identically regardless of listening context.
# ---------------------------------------------------------------------------


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
        """Apply the point-weighting recipe and return the total score for one song."""
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
        """Score all songs for the given user and return the top-k sorted by score."""
        scored = sorted(self.songs, key=lambda s: self._score(user, s), reverse=True)
        return scored[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable breakdown of why a song was recommended."""
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
    """Read songs.csv and return a list of dicts with numeric fields cast to float/int."""
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
                "tempo_bpm":    float(row["tempo_bpm"]),    # loaded, never scored (dead column — bias #6)
                "valence":      float(row["valence"]),      # loaded, never scored (dead column — bias #6)
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            })
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score one song against user preferences; return (total_score, reasons_list)."""
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
    """Score every song in the catalog and return the top-k as (song, score, explanation) tuples."""
    scored = [
        (song, score, " | ".join(reasons))
        for song in songs
        for score, reasons in [score_song(user_prefs, song)]
    ]
    return sorted(scored, key=lambda x: x[1], reverse=True)[:k]
