"""
Signal two: the style signal. ← YOU BUILD THIS IN MILESTONE 4

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are stubbed below because the brief names those three. They are
stubs, not implementations: what they compute is yours, and so is how you
combine them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures ───────────────────────────────────────────────────────
# Direction convention: each raw measure is "higher = more human-looking".
# `style_signal` flips them onto the shared "higher = more likely AI" scale.

def sentence_length_spread(text: str) -> float:
    """
    Coefficient of variation of sentence length (stdev / mean, in words).

    Scale: 0 (every sentence the same length) up to ~1+ (very lumpy).
    Higher = more human-looking.

    Edge case: fewer than two sentences has no spread to measure. Returning 0.0
    would read as "machine-even" and accuse every one-liner, so it returns a
    neutral 0.5 instead (roughly what ordinary prose scores).
    """
    lengths = [len(words(s)) for s in sentences(text)]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 2:
        return 0.5
    mean = statistics.mean(lengths)
    return round(statistics.stdev(lengths) / mean, 4) if mean else 0.5


def type_token_ratio(text: str, window: int = 50) -> float:
    """
    Unique words over total words, length-corrected (moving-average TTR).

    A raw TTR falls as text gets longer, so this averages the ratio over
    sliding 50-word windows; text shorter than a window uses the whole text.
    Scale 0-1. Higher = more varied vocabulary = more human-looking.
    """
    toks = words(text)
    if not toks:
        return 0.0
    if len(toks) <= window:
        return round(len(set(toks)) / len(toks), 4)
    ratios = [
        len(set(toks[i:i + window])) / window
        for i in range(0, len(toks) - window + 1)
    ]
    return round(sum(ratios) / len(ratios), 4)


# Marks that vary between writers. Full stops are left out on purpose.
_PUNCT = re.compile(r"[,;:!?()\"\u201c\u201d\u2014\u2013]|--|\s-\s")


def punctuation_density(text: str) -> float:
    """
    Non-full-stop punctuation marks per word (commas, semicolons, colons,
    dashes, brackets, quotes, ! and ?). Typical prose is ~0.05-0.25.
    Higher = more human-looking.
    """
    n = len(words(text))
    if n == 0:
        return 0.0
    return round(len(_PUNCT.findall(text)) / n, 4)


# ── Combining them ───────────────────────────────────────────────────────────

def _ramp(value: float, ai_at: float, human_at: float) -> float:
    """Linear map: `ai_at` -> 1.0 (AI-ish), `human_at` -> 0.0, clamped."""
    t = (value - human_at) / (ai_at - human_at)
    return min(max(t, 0.0), 1.0)


def style_signal(text: str) -> float:
    """
    The style signal as a 0-1 score. **Higher means more likely AI.**

    Each raw measure is put on 0-1 with a linear ramp (so none wins by having
    bigger numbers), flipped so high = AI-ish, then weighted:

        sentence length spread (CV)   0.25 -> 1.0 (AI)   0.75 -> 0.0   weight 0.5
        moving-average TTR            0.60 -> 1.0 (AI)   0.85 -> 0.0   weight 0.25
        punctuation per word          0.04 -> 1.0 (AI)   0.20 -> 0.0   weight 0.25

    Sentence rhythm gets half the weight because it is the measure the
    "even, mid-length sentences" theory is most directly about.
    """
    spread = _ramp(sentence_length_spread(text), ai_at=0.25, human_at=0.75)
    vocab = _ramp(type_token_ratio(text), ai_at=0.60, human_at=0.85)
    punct = _ramp(punctuation_density(text), ai_at=0.04, human_at=0.20)
    score = 0.5 * spread + 0.25 * vocab + 0.25 * punct
    return round(min(max(score, 0.0), 1.0), 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
