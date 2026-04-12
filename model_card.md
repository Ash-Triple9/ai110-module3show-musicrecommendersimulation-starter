# Model Card: Music Recommender Simulation

---

## 1. Model Name

**VibeFinder 1.0**

A rule-based music recommender that matches songs to a listener's stated preferences using a weighted point system.

---

## 2. Goal / Task

VibeFinder tries to answer one question: given what a user tells you they like, which songs from the catalog should they hear first?

It does this by scoring every song in the library against the user's preferences and returning the top five. The higher the score, the better the match. It is not predicting what the user will click on — it is surfacing songs that look like a good fit based on explicit feature labels.

This system is designed for classroom exploration. It is not a production recommender. There are no real users, no listening history, and no feedback loop.

---

## 3. Algorithm Summary

Each song gets a score out of 5.5 points. Here is how those points are handed out:

- **Genre match (+1.5 pts):** If a song's genre exactly matches what the user asked for, it gets 1.5 points. This is an all-or-nothing check — "indie pop" and "pop" count as completely different.
- **Mood match (+1.0 pts):** Same idea. If the song's mood tag matches the user's target mood exactly, it gets 1 point.
- **Energy proximity (+2.0 pts):** The closer a song's energy level is to what the user wants (on a 0–1 scale), the more points it earns. A perfect match gives 2.0; a song at the opposite end of the scale gives 0.
- **Danceability proximity (+0.5 pts):** Same math, lower stakes. How close is the song's danceability to the user's target?
- **Acousticness proximity (+0.5 pts):** Same again for acousticness.

The five scores are added together and the songs are ranked highest to lowest. The top five are shown.

**What changed from the original design:** The original version weighted genre at 2.0 and energy at 1.5. After testing, it became clear that genre was too powerful — a rock song could rank first for a user who wanted maximum stillness just because the genre label matched. The weights were flipped: energy now carries 2.0 and genre carries 1.5. This means a song with a near-perfect energy fit can now outrank a song with only a genre match.

---

## 4. Data Used

The catalog has **18 songs** stored in a CSV file. Each song has the following fields: title, artist, genre, mood, energy (0–1), tempo in BPM, valence (0–1), danceability (0–1), and acousticness (0–1).

**Genres represented:** lofi (4 songs), pop (2), rock (2), ambient (2), jazz (2), synthwave (2), indie pop (2), hip-hop (1), classical (1).

**Moods represented:** happy (3), chill (3), intense (3), relaxed (2), moody (2), focused (2), confident (1), peaceful (1), melancholic (1).

**Important limits:**
- No songs exist for many real-world genres — country, R&B, metal, folk, electronic, reggae, and others are completely absent.
- The energy distribution has a significant gap: no songs fall between 0.55 and 0.75. Medium-energy listeners are underserved.
- Two fields that are loaded — `tempo_bpm` and `valence` — are never actually used in scoring. They exist in the data but have no effect on results.
- Lofi is the only genre with more than two songs, giving lofi listeners more variety than anyone else.

No songs were added or removed from the original dataset.

---

## 5. Strengths

VibeFinder works best when the user's preferences line up with what is actually in the catalog.

**Strong cases:**
- A Chill Lofi listener got a near-perfect top result (*Late Night Pages*, 5.42/5.5) because genre, mood, and energy all matched real songs in the catalog.
- Deep Intense Rock hit 5.35/5.5 on *Storm Runner* for the same reason — genre, mood, and energy converged on one song.
- When the genre preference is absent or useless, mood still steers results in a meaningful direction. The Genre Void profile (an intentionally fake genre) and the Witch House profile both returned distinct, different playlists entirely because of their different mood targets.

**What the scoring captures well:**
- Energy is the most reliable differentiator. Low-energy and high-energy profiles consistently get songs that sound different from each other, which is the most intuitive thing a listener actually notices.
- The explained output (showing how many points each feature contributed) makes it easy to understand exactly why a song ranked where it did.

---

## 6. Limitations and Bias

**Weakness 1 — The medium-energy user penalty (most impactful):**
The catalog has no songs between energy 0.55 and 0.75. A listener targeting energy 0.65 can earn at most 1.80 out of 2.00 possible energy points — a 10% structural ceiling that cannot be fixed by changing preferences. A listener targeting energy 0.38 routinely earned a perfect 2.00. This is not a flaw in the formula; it is a dataset coverage gap that silently treats medium-energy listeners as second-class users.

**Weakness 2 — Genre orphaning with no warning:**
If a user asks for a genre that does not exist in the catalog (like math rock, nintendocore, or witch house), the system quietly recommends songs from other genres with no indication that a substitution happened. A math rock fan received lofi songs as their top results. The system never said "we don't have math rock."

**Weakness 3 — Same-artist flooding:**
There is no penalty for recommending the same artist multiple times. Neon Echo has three songs and Slow Stereo has three songs. Both artists can fill multiple slots in a user's top-five list, making the recommendations feel narrow even when different genres appear.

**Weakness 4 — Binary matching ignores related genres and moods:**
"Indie pop" and "pop" score zero genre similarity. "Moody" and "melancholic" are treated as completely unrelated. In reality, listeners who enjoy one often enjoy the other. The system has no concept of genre or mood proximity.

**Weakness 5 — Three fields are defined but never used:**
`tempo_bpm` and `valence` are loaded from the CSV but ignored in scoring. `likes_acoustic` is a flag on the user profile that is also never read. A runner who wants 170+ BPM tracks cannot express that preference, and a user who sets `likes_acoustic=False` receives no benefit.

---

## 7. Evaluation Process

Eleven user profiles were run and their top-five recommendations were examined manually.

**Normal profiles tested:** High-Energy Pop, Chill Lofi, Deep Intense Rock, Math Rock, Nintendocore, Witch House.

**Adversarial / edge-case profiles tested:** Manic Sad (high energy + sad mood), Acoustic Rave (ambient genre + near-zero energy + maximum danceability), Genre Void (a genre invented to match nothing), All Zeros (every continuous target at 0.0), All Ones (every continuous target at 1.0).

**What I looked for:** Whether the top result made intuitive sense, whether scores were high enough to represent a real signal rather than noise, and whether the same songs reappeared across very different profiles.

**What the results showed:** Well-matched profiles (Chill Lofi, Deep Intense Rock) scored in the 5.2–5.4 range and returned genre-appropriate songs. Orphaned genres (Math Rock, Nintendocore) peaked below 3.0 and quietly drifted toward whichever real genre shared their energy range.

**What surprised me:** *Storm Runner* — a loud rock track with energy 0.91 — ranked first for the "All Zeros" profile that requested the lowest possible energy. Genre and mood together awarded 2.5 points before any continuous features were checked, which was enough to overcome terrible energy alignment. This showed that even the rebalanced weights leave categorical bonuses too strong in extreme cases. The second surprise was *Gym Hero* showing up in the top two for both the Happy Pop and Manic Sad profiles — two profiles with opposite moods — because only two pop songs exist, so the second one is always a default fallback regardless of fit.

---

## 8. Ideas for Improvement

**1. Fill the energy gap and expand the catalog.**
The single highest-impact fix is adding songs in the 0.55–0.75 energy range. Beyond that, adding at least 2–3 songs per genre for every represented genre would immediately reduce genre orphaning and same-artist flooding. More data does more for this system than any algorithm change.

**2. Activate the unused fields — tempo and valence.**
`tempo_bpm` and `valence` are already loaded for every song. Adding proximity scoring for both (similar to how energy is scored now) would let users express preferences like "uplifting music" (high valence) or "fast-paced for running" (high tempo) that are currently invisible to the system.

**3. Add a genre/mood adjacency fallback.**
Instead of awarding zero points for a near-miss genre, build a small lookup table of related genres (e.g., pop → indie pop → synthwave) and partial-credit moods (e.g., moody → melancholic → chill). When the exact genre is absent, the system could award half points for a related genre and tell the user "we recommended indie pop because we don't have witch house." This would make genre orphaning visible and less jarring.

---

## 9. Personal Reflection — Engineering Process

### Biggest learning moment

The biggest learning moment came when I ran the "All Zeros" edge-case profile — a user who asked for rock and intense mood but set every continuous feature (energy, danceability, acousticness) to zero. I expected the system to fail gracefully or at least rank that song near the bottom. Instead, *Storm Runner* — a loud, aggressive 0.91-energy rock track — ranked first with a respectable 3.30 out of 5.5. It won because genre and mood together awarded 2.5 points before a single continuous feature was even looked at.

That result forced me to confront something I had not fully appreciated before: in a weighted scoring system, the weights are not just parameters — they are policy decisions. Choosing how much genre matters relative to energy is not a technical choice, it is a values choice about what "a good recommendation" means. I had been treating the weights as if there were a mathematically correct answer. There is not. Every weight is an opinion.

### How AI tools helped — and when I needed to double-check them

AI tools were most useful for the parts of engineering that are tedious but well-defined: generating test profiles, formatting output, writing the bias analysis comments systematically, and running the "what would happen if" experiments quickly. What would have taken several manual iterations — designing five adversarial profiles, running them, reading the output, and identifying patterns — happened in one session.

The moments that required the most double-checking were anywhere the AI tool was making a *judgment call* dressed up as a *fact*. For example, when the initial weight rationale said "genre is the strongest signal because listeners strongly identify with genre," that is a plausible opinion, not an established finding. It sounded authoritative in the comments but had no experimental backing until I actually ran the adversarial profiles and confirmed that genre dominance was causing real problems. The tool was right for a plausible reason, but I only knew it was right after verifying it with evidence. That habit — treating AI-generated reasoning as a hypothesis to test, not a conclusion to accept — turned out to be the most important engineering discipline in this project.

### What surprised me about how simple algorithms can still "feel" like recommendations

The most surprising thing was how little logic it actually takes to produce output that feels personalized. The entire scoring function is five arithmetic operations. There are no neural networks, no embeddings, no training data. And yet when a Chill Lofi profile returns *Late Night Pages* as its top result, the reaction is "yes, that makes sense" — because the song genuinely sounds like what a tired student at midnight would put on. The algorithm did not understand that. It just added up five numbers and picked the biggest one.

This revealed something important: the feeling of being understood by a recommendation system comes mostly from the *catalog labels* agreeing with human intuition, not from the algorithm being smart. The song was already tagged "lofi, focused, low energy." The system just found it. If the tags had been wrong — if *Late Night Pages* had been mislabeled as "rock, intense" — the algorithm would have confidently recommended it to the wrong person with no way to know. The intelligence is in the metadata, not the math.

### What I would try next

If I extended this project, the first thing I would do is activate the two dead fields — `tempo_bpm` and `valence` — as scoring dimensions. Tempo in particular is a feature that listeners feel physically; the difference between 70 BPM and 140 BPM is immediately obvious in a way that a 0.1 shift in danceability is not. Adding tempo proximity would make the recommender useful for context-specific listening like running or sleeping.

Second, I would replace binary genre matching with a small genre graph — a lookup table where "indie pop" is one step from "pop," which is one step from "synthwave," so a partial match earns partial credit. This would eliminate genre orphaning for the Math Rock and Nintendocore profiles without needing a larger dataset.

Third, and most ambitiously, I would add a diversity re-ranking step after scoring. Right now the top five results are just the five highest-scoring songs. A simple post-processing pass that penalises the same artist appearing twice would immediately make the output feel broader without changing the underlying scoring logic at all. It would be ten lines of code with a noticeable effect on recommendation quality — the kind of small change that disproportionately improves user experience.
