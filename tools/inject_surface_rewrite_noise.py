#!/usr/bin/env python3
"""
Second perturbation family: surface_rewrite_rule_based.

A rule-based, fully local perturbation family that is deliberately distinct
from the discourse-noise family in tools/inject_discourse_noise.py /
exp_perturbation_sweep.py. Discourse noise removes or replaces message
CONTENT (truncation, benign-swap, drop) and jitters order. This family
preserves content and meaning while rewriting SURFACE FORM and message
SEGMENTATION:

  - chat-register substitutions: swap words with common chat variants from a
    fixed, neutral, non-sensitive lookup table (e.g. "you" <-> "u",
    "okay" <-> "ok", "because" -> "cuz"), applied in both directions;
  - casing/punctuation jitter: lowercase the message or strip terminal
    punctuation;
  - message split: break one message into two at a word boundary
    (same author, adjacent positions);
  - message merge: join two adjacent messages from the same author.

No word is ever invented, no content is generated, and the table contains
only register/orthography variants of function words and common chat tokens.
The family attacks exactly the character n-gram surface features the
per-message baseline uses, while leaving conversational structure (who says
what, in what order) almost intact — the natural complement to discourse
noise. No raw conversation text is printed by this module.

Used by experiments/exp_perturbation_second_family.py.
"""

import re

import numpy as np

# Bidirectional chat-register variants. Neutral function words and chat
# tokens only — nothing sensitive, nothing content-bearing.
_PAIRS = [
    ("you", "u"), ("your", "ur"), ("are", "r"), ("why", "y"),
    ("okay", "ok"), ("please", "plz"), ("thanks", "thx"), ("people", "ppl"),
    ("because", "cuz"), ("about", "bout"), ("what", "wat"), ("later", "l8r"),
    ("tonight", "2nite"), ("tomorrow", "tmrw"), ("really", "rly"),
    ("probably", "prolly"), ("going to", "gonna"), ("want to", "wanna"),
    ("got to", "gotta"), ("kind of", "kinda"), ("see you", "cya"),
    ("i don't know", "idk"), ("be right back", "brb"), ("oh my god", "omg"),
    ("laughing out loud", "lol"), ("right now", "rn"), ("for real", "fr"),
    ("no problem", "np"), ("never mind", "nvm"), ("message", "msg"),
    ("picture", "pic"), ("school", "skool"), ("something", "sumthin"),
    ("nothing", "nuthin"), ("though", "tho"), ("through", "thru"),
]
SUBSTITUTIONS = {}
for a, b in _PAIRS:
    SUBSTITUTIONS[a] = b
    SUBSTITUTIONS[b] = a
_SUB_PATTERNS = {k: re.compile(r"\b" + re.escape(k) + r"\b", re.IGNORECASE)
                 for k in SUBSTITUTIONS}

OP_PROBS = {"substitute": 0.5, "case_punct": 0.2, "split": 0.15, "merge": 0.15}
FAMILY_NAME = "surface_rewrite_rule_based"


def _substitute(text: str, rng: np.random.Generator, max_subs: int = 4) -> str:
    keys = [k for k in SUBSTITUTIONS if _SUB_PATTERNS[k].search(text)]
    if not keys:
        return text
    rng.shuffle(keys)
    for k in keys[:max_subs]:
        text = _SUB_PATTERNS[k].sub(SUBSTITUTIONS[k], text, count=1)
    return text


def _case_punct(text: str, rng: np.random.Generator) -> str:
    if rng.random() < 0.5:
        text = text.lower()
    else:
        text = text.rstrip(".!?,;: ")
    return text if text else " "


def perturb_conversation_surface(msgs: list, strength: float,
                                 rng: np.random.Generator) -> tuple:
    """
    Apply surface-rewrite/segmentation perturbation to one conversation.
    Returns (perturbed_messages, op_counts). Message count may grow (split)
    or shrink (merge) but content tokens are preserved up to the register
    substitutions above. Author IDs are always preserved.
    """
    ops = {"kept": 0, "substituted": 0, "case_punct": 0,
           "split": 0, "merged": 0}
    if not msgs or strength <= 0.0:
        ops["kept"] = len(msgs)
        return list(msgs), ops

    op_names = list(OP_PROBS.keys())
    op_p = np.array([OP_PROBS[k] for k in op_names])

    out = []
    for author, text in msgs:
        if rng.random() >= strength:
            out.append((author, text))
            ops["kept"] += 1
            continue
        op = op_names[rng.choice(len(op_names), p=op_p)]
        if op == "merge" and out and out[-1][0] == author:
            prev_author, prev_text = out.pop()
            out.append((author, (prev_text + " " + text).strip() or " "))
            ops["merged"] += 1
        elif op == "split":
            words = text.split()
            if len(words) >= 4:
                cut = int(rng.integers(1, len(words)))
                out.append((author, " ".join(words[:cut])))
                out.append((author, " ".join(words[cut:])))
                ops["split"] += 1
            else:
                out.append((author, _substitute(text, rng)))
                ops["substituted"] += 1
        elif op == "case_punct":
            out.append((author, _case_punct(text, rng)))
            ops["case_punct"] += 1
        else:  # substitute
            out.append((author, _substitute(text, rng)))
            ops["substituted"] += 1
    return out, ops
