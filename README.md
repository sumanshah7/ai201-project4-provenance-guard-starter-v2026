# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

A submission travels through seven steps in `app.py::submit`:

1. **Arrives** as JSON `{text, creator_id}` at `POST /submit`.
2. **Validation.** A missing or empty `text` or `creator_id` gets a 400, text over 20,000 characters gets a 413, and text too short to score gets a 422. Each refusal is written to the audit log as a `rejected` entry.
3. **Signal one** (`detector.py::model_signal`): a local GPT-2 scores how predictable the text is and returns a 0-1 `model_score`.
4. **Signal two** (`stylometry.py::style_signal`): sentence-length spread, vocabulary variety and punctuation density give a 0-1 `style_score`.
5. **Combine** (`scoring.py::combine_signals`): the two scores become one `combined_score`.
6. **Label** (`scoring.py::score_to_label`): the combined score becomes a guess (`human`, `unsure` or `ai`) and a plain-language label.
7. **Log and answer** (`audit.py::log_decision`): one line goes to `logs/audit.jsonl` with all three scores, and the response carries `content_id`, `guess`, `confidence`, `label`, `model_score`, `style_score` and `combined_score`.

If the writer disagrees, `POST /appeal` takes the `content_id` and their reasoning, checks the id exists, appends an `appeal` entry with status `under_review`, and confirms. The log is append-only, so the original decision stays beside the appeal.



---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** perplexity under GPT-2 (run locally) on the first 400 tokens: how predictable the words are, squashed to 0-1 with a logistic (midpoint perplexity 45, steepness 1.6). Higher means more likely AI.

**Why that might differ between human and AI writing:** a language model writes by picking likely next words, so its output is easy for another model to predict. Human writing wanders more, with odd word choices and specific details.

**What it can't see:** authorship. It rewards common words in short, ordinary sentences, and plenty of real people write that way. My plain-English human paragraph ("I like my town. It is small and quiet...") scored 0.79, nearly as high as my clearly-AI paragraph's 0.81. It is also blind to everything past the first 400 tokens.

### Signal two — the style signal

**What it measures:** the shape of the text with no understanding of it, from three measures in `stylometry.py`. Each is ramped onto 0-1 and flipped so higher means more likely AI:

- Sentence-length spread (stdev / mean of words per sentence): 0.25 maps to 1.0, 0.75 to 0.0, weight 0.5.
- Moving-average type-token ratio over 50-word windows (so length doesn't distort it): 0.60 maps to 1.0, 0.85 to 0.0, weight 0.25.
- Non-full-stop punctuation per word: 0.04 maps to 1.0, 0.20 to 0.0, weight 0.25.

**Why that might differ between human and AI writing:** generated prose tends toward even, mid-length sentences and a narrower vocabulary. Human writing is lumpier, with a three-word sentence beside a forty-word one.

**What it can't see:** meaning. Anything that changes the shape without changing the substance moves it, such as adding typos, splitting sentences or pasting in a quotation, and all of these are cheap to do on purpose. It also reads a human who writes in short, even sentences as machine-like. A one-sentence submission has no spread, so that measure returns a neutral 0.5.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:** a weighted average that leans on the model signal, plus a disagreement rule. When the two signals differ by more than the gap, two methods splitting is itself uncertainty, and the costly error is accusing a human. So the result is pulled halfway from the average toward the lower (more human) of the two scores. One loud signal can't reach "AI" alone.

**The numbers:** `WEIGHT_MODEL_SIGNAL = 0.6`, `WEIGHT_STYLE_SIGNAL = 0.4`, `DISAGREEMENT_GAP = 0.4`, `HUMAN_THRESHOLD = 0.35`, `AI_THRESHOLD = 0.72` (all in `config.py`). I raised `AI_THRESHOLD` from the starter's 0.65 because my plain human paragraph combined to 0.668 and was labeled AI, and I would rather miss some AI text than accuse a writer.

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:** the plain human paragraph ("I like my town...") got `model_score` 0.791 but `style_score` 0.484. The gap is 0.31, under the 0.4 trigger, so the plain weighted average applies: 0.6 x 0.791 + 0.4 x 0.484 = 0.668. That is "unsure" under the 0.72 threshold but would have been "AI" under 0.65. The disagreement rule did not fire on any of my six calibration inputs, so it is untested on a real case.

Calibration table (all six inputs I tried):

| Input | model | style | combined | label |
|---|---|---|---|---|
| clearly AI | 0.809 | 0.701 | 0.766 | ai |
| clearly human | 0.403 | 0.185 | 0.316 | human |
| in between | 0.417 | 0.625 | 0.500 | unsure |
| formal human | 0.591 | 0.387 | 0.509 | unsure |
| plain human | 0.791 | 0.484 | 0.668 | unsure (was "ai" at 0.65) |
| lightly-edited AI | 0.555 | 0.503 | 0.534 | unsure |

The lightly-edited AI scores as unsure, so edited AI text slips through. That is the trade I chose.



---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 - 0.35 | We think this was probably written by a person. |
| unsure | 0.35 - 0.72 | We can't tell whether this was written by a person or by AI. Plenty of ordinary human writing lands here, so this is not a judgment about you. If you wrote it, nothing more is needed; you can ask for a person to look at it any time. |
| high-confidence AI | 0.72 - 1.00 | This reads a lot like AI-generated writing, but we can be wrong. If you wrote it yourself, tell us and a person will review it. |

**Why I worded the "unsure" one this way:** it opens by admitting we don't know, says outright that this isn't a judgment about the writer, and tells them nothing is required. The AI label says "we can be wrong" and offers a human review. These are first drafts that no one outside the project has read yet.



---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "Artificial intelligence is transforming the way businesses operate in todays rapidly evolving digital landscape. It is important to note that organizations must carefully consider several key factors when implementing new technologies. Furthermore, effective communication and collaboration are essential to ensuring successful outcomes. By leveraging innovative solutions, companies can improve efficiency, enhance productivity, and drive sustainable growth.", "creator_id": "demo-writer"}'
```

```json
{
  "combined_score": 0.7323,
  "confidence": 0.7323,
  "content_id": "d46e26764a77",
  "guess": "ai",
  "label": "This reads a lot like AI-generated writing, but we can be wrong. If you wrote it yourself, tell us and a person will review it.",
  "model_score": 0.7532,
  "status": "decided",
  "style_score": 0.7009
}
```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "d46e26764a77", "reasoning": "I wrote this myself for a marketing class and use formal phrasing on purpose."}'
```

```json
{
  "content_id": "d46e26764a77",
  "message": "Thank you. Your appeal has been recorded and a person will review it. Until then, this result is marked as under review.",
  "status": "under_review"
}
```

An unknown id fails loudly with a 404:

```json
{
  "error": "unknown_content_id",
  "message": "No submission with content_id 'nope'. Check the id and try again."
}
```

**What the log shows afterwards**

```bash
$ curl "http://127.0.0.1:5000/log?limit=4"
```

```json
{
  "count": 4,
  "entries": [
    {
      "combined_score": 0.7323,
      "content_id": "d46e26764a77",
      "creator_id": "demo-writer",
      "guess": "ai",
      "label": "This reads a lot like AI-generated writing, but we can be wrong. If you wrote it yourself, tell us and a person will review it.",
      "model_score": 0.7532,
      "status": "decided",
      "style_score": 0.7009,
      "text_length": 459,
      "timestamp": "2026-11-14T22:28:35+00:00"
    },
    {
      "content_id": "d46e26764a77",
      "creator_id": "demo-writer",
      "event": "appeal",
      "reasoning": "I wrote this myself for a marketing class and use formal phrasing on purpose.",
      "status": "under_review",
      "timestamp": "2026-11-14T22:28:35+00:00"
    },
    {
      "combined_score": 0.316,
      "content_id": "f0e61148ca6c",
      "creator_id": "demo-writer",
      "guess": "human",
      "label": "We think this was probably written by a person.",
      "model_score": 0.4034,
      "status": "decided",
      "style_score": 0.185,
      "text_length": 255,
      "timestamp": "2026-11-14T22:28:40+00:00"
    },
    {
      "combined_score": 0.4941,
      "content_id": "d5515797cf4e",
      "creator_id": "demo-writer",
      "guess": "unsure",
      "label": "We can't tell whether this was written by a person or by AI. Plenty of ordinary human writing lands here, so this is not a judgment about you. If you wrote it, nothing more is needed; you can ask for a person to look at it any time.",
      "model_score": 0.398,
      "status": "decided",
      "style_score": 0.6383,
      "text_length": 265,
      "timestamp": "2026-11-14T22:28:40+00:00"
    }
  ]
}
```

---

## How I Used AI

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
