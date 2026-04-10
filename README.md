# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

### Song Features

Each `Song` in `data/songs.csv` carries ten attributes used during scoring:

| Feature | Type | Role |
|---|---|---|
| `genre` | categorical | matched against the user's preferred genre |
| `mood` | categorical | matched against the user's preferred mood |
| `energy` | 0.0 – 1.0 | proximity compared to the user's target energy |
| `danceability` | 0.0 – 1.0 | proximity compared to the user's target danceability |
| `acousticness` | 0.0 – 1.0 | proximity compared to the user's target acousticness |
| `tempo_bpm` | integer | stored for future use / display |
| `valence` | 0.0 – 1.0 | stored for future use / display |

### User Profile

A `UserProfile` stores what the listener cares about most:

- `favorite_genre` — the genre they most identify with
- `favorite_mood` — the emotional feel they are looking for
- `target_energy` — how high-energy the music should feel (0 = very calm, 1 = very intense)
- `target_danceability` — how beat-driven the music should be
- `target_acousticness` — preference for organic/live sound vs. electronic production

### Algorithm Recipe

Every song is scored by `score_song()` using the following point-weighting system:

```
+2.0 pts   Genre match          (binary — song.genre == user.favorite_genre)
+1.0 pts   Mood match           (binary — song.mood  == user.favorite_mood)
+1.5 pts   Energy proximity     (continuous — 1.5 × (1 − |song.energy − target|))
+0.5 pts   Danceability proximity (continuous — 0.5 × (1 − |song.danceability − target|))
+0.5 pts   Acousticness proximity (continuous — 0.5 × (1 − |song.acousticness − target|))
────────────────────────────────────────────────────────────────
Max score  5.5 pts
```

**Why these weights?**
Genre (2.0) is the heaviest signal because listeners strongly self-identify with a genre.
Mood (1.0) matters but is softer — a "chill" lofi track can serve a "focused" listener too.
Energy (1.5) is the dominant continuous feature; it separates a workout playlist from a study playlist.
Danceability and acousticness (0.5 each) act as tie-breakers that add texture without overriding the primary signals.

### Ranking Rule

`recommend_songs()` collects `(song, score, explanation)` for every song in the catalog, sorts the list by score in descending order, and returns the top-k results (default k = 5). Each result includes a plain-language explanation string so the reason for every recommendation is transparent.

### Data Flow

```
Input (User prefs)
        │
        ▼
load_songs() ── songs.csv ──► list of song dicts
        │
        ▼
Loop: for each song ──► score_song() ──► (score, reasons)
        │                                      │
        └──────────── accumulate ──────────────┘
                            │
                            ▼
                    sort descending by score
                            │
                            ▼
                    slice top-k results
                            │
                            ▼
              Output (ranked recommendations)
```

### Potential Biases to Watch For

- **Genre over-dominance.** A genre match alone adds 2.0 points — the same as a near-perfect energy + danceability + acousticness trio. A song in the "wrong" genre that fits the user's vibe in every other way can easily be outranked by a genre match with mismatched energy. This means great cross-genre discoveries get buried.
- **Mood is binary and coarse.** Two songs labeled "chill" are treated identically even if one is dreamy ambient and the other is laid-back hip-hop. The system cannot distinguish within a mood category.
- **Continuous features assume a neutral default.** When a user does not specify `target_danceability` or `target_acousticness`, they default to 0.65 and 0.50 respectively. This quietly biases recommendations toward mid-range songs for those dimensions, which may not match every listener.
- **Small catalog amplifies accidents.** With only 17 songs, a single genre (e.g., lofi or pop) having more entries than others means those genres appear more often in recommendations regardless of real fit — a popularity bias in miniature.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this


---

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance. :contentReference[oaicite:2]{index=2}  

```markdown
# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

Give your recommender a name, for example:

> VibeFinder 1.0

---

## 2. Intended Use

- What is this system trying to do
- Who is it for

Example:

> This model suggests 3 to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is for classroom exploration only, not for real users.

---

## 3. How It Works (Short Explanation)

Describe your scoring logic in plain language.

- What features of each song does it consider
- What information about the user does it use
- How does it turn those into a number

Try to avoid code in this section, treat it like an explanation to a non programmer.

---

## 4. Data

Describe your dataset.

- How many songs are in `data/songs.csv`
- Did you add or remove any songs
- What kinds of genres or moods are represented
- Whose taste does this data mostly reflect

---

## 5. Strengths

Where does your recommender work well

You can think about:
- Situations where the top results "felt right"
- Particular user profiles it served well
- Simplicity or transparency benefits

---

## 6. Limitations and Bias

Where does your recommender struggle

Some prompts:
- Does it ignore some genres or moods
- Does it treat all users as if they have the same taste shape
- Is it biased toward high energy or one genre by default
- How could this be unfair if used in a real product

---

## 7. Evaluation

How did you check your system

Examples:
- You tried multiple user profiles and wrote down whether the results matched your expectations
- You compared your simulation to what a real app like Spotify or YouTube tends to recommend
- You wrote tests for your scoring logic

You do not need a numeric metric, but if you used one, explain what it measures.

---

## 8. Future Work

If you had more time, how would you improve this recommender

Examples:

- Add support for multiple users and "group vibe" recommendations
- Balance diversity of songs instead of always picking the closest match
- Use more features, like tempo ranges or lyric themes

---

## 9. Personal Reflection

A few sentences about what you learned:

- What surprised you about how your system behaved
- How did building this change how you think about real music recommenders
- Where do you think human judgment still matters, even if the model seems "smart"

