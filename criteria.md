# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1. Few real writers are called AI

Of 10 pieces of my own writing (varied length and tone), at most 1 is labeled high-confidence AI (combined score 0.72 or above). This must hold in each of 3 repeated runs.

**Why this target:** on a writing site a wrong accusation costs the writer far more than a missed detection costs the site. One in 10 is still a lot, but with only two weak local signals I can't honestly promise zero, and a stricter target I could never check with 10 samples is not a target.

---

## 2. Plain writers are not singled out

Of 5 plainly written human pieces (short sentences, common words, the style of a second-language or younger writer), at most 1 is labeled high-confidence AI, and at least 3 of the 5 are labeled "unsure" or "human".

**Why this target:** the model signal's known blind spot is plain, predictable human writing, and it scored my plain paragraph 0.79, close to my clearly-AI text. This group has the least room to argue back, so it gets its own number rather than hiding inside the average in criterion 1.

---

## 3. Clearly-AI and clearly-human text score far apart

Using 5 clearly-AI pieces and 5 clearly-human pieces, the average combined score of the AI group is at least 0.30 higher than the human group, and at least 4 of the 5 AI pieces score above 0.50.

**Why this target:** if the groups sit within 0.30 of each other, the thresholds are just noise. My first calibration gave 0.77 for AI and 0.32 for human (a gap of about 0.45), so 0.30 leaves room for variation without being trivial.

---

## 4. Every appeal changes status and is recorded

For 10 appeals sent with valid content ids, all 10 return `status: "under_review"` and each adds exactly one `appeal` entry to `logs/audit.jsonl` next to the original decision. For 5 appeals with unknown ids, all 5 return a 404 and add no entry.

**Why this target:** the appeal is the only thing standing between a wrong label and nothing at all, so it has to work every time, not most of the time. This is fully deterministic, so the target is 100%.

---

## 5. Bad input never crashes the service

For 6 bad inputs (missing `text`, empty `text`, whitespace-only `text`, missing `creator_id`, a body that is not a JSON object, and 50,000 characters of text), every one returns a 4xx with a JSON error, none returns a 500, and each leaves a `rejected` entry in the audit log.

**Why this target:** a crash on malformed input is one of the most common real failures, and a rejection that leaves no trace looks like a quiet afternoon. Six cases cover each way the route can be fed something it cannot score.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
