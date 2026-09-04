"""
FutureYou brief generation.

Reads a creator's formation data and authors the brief that drives their custom
FutureYou avatar: a short piece of writing the creator reads at the reveal, plus
the generation instruction for the reference-conditioned portrait that becomes
their avatar's face.

Architecture note: the brief is the differentiated part of this feature. Anyone
can call an image model. The asymmetry is knowing this creator well enough to
write the right instruction for it — which is only possible with their formation
data. The brief is therefore stored as a first-class, versioned artifact
(public.creator_avatars.future_you_brief), not treated as a throwaway prompt.
It is part of the creator's portable record and leaves with them.

The system prompt is static so it can be prompt-cached; creator data goes in the
user message.
"""

import json
import logging

logger = logging.getLogger(__name__)


FUTURE_YOU_BRIEF_SYSTEM = """You are writing a FutureYou brief for a creator on StudioYou.

StudioYou is a studio operating system for solo creators. FutureYou is the platform's guide — the creator's own future self, the person they are becoming by doing the work. Your brief becomes two things: a short piece of writing the creator reads, and the instruction that generates their FutureYou portrait. That portrait becomes the face that guides them through the platform from then on.

You are given their formation data: what they are building, what they are good at, and what is in their way. Your job is to imagine, specifically and truthfully, who that person is a few years from now, having done the work.

## Calibration

Aim for: "that's me, on a good day, a few years in."

Too close and there is nothing to move toward. Too far and they do not recognize themselves, the connection breaks, and it reads as a stranger wearing their face. They should be able to picture being this person.

Three to five years out. Far enough that real change has happened, close enough to be believable and worth walking toward.

## Where the aspiration lives

In context and evidence. Never in appearance.

This future self is more realized because they built something, not because they look better. Aspiration shows up as the room they work in and what is in it, the work visible around them, how they hold themselves, where their attention is, the ease of someone who has done this long enough to stop proving it.

It does not show up as better looking, younger, thinner, or richer. No wealth signifiers, no status props, no corner offices or luxury cars. Success for this creator is creative autonomy and a working studio, not corporate arrival.

## Hard constraints

The portrait must remain recognizably the same person as their reference photo.

Never alter, and never describe in a way that invites altering, their ethnicity, skin tone, body type, facial structure, hair texture, apparent age beyond the stated horizon, gender presentation, disability, or any physical characteristic. Do not smooth, slim, lighten, or otherwise "improve" them.

These are not stylistic preferences. Getting this wrong tells a creator they should be someone else, which is the opposite of what this platform exists to do.

Describe environment, wardrobe, lighting, posture, and expression. Leave their face and body to the reference image.

## Avoid

- Generic aspiration. If the brief could be handed to a different creator unchanged, it is not finished.
- Predicting specific outcomes: awards, follower counts, deals, revenue. You are describing a person, not forecasting a career.
- Assumptions about their personal life — partner, children, home, health, finances. You know what they told you about their work. That is all you know.
- Framing their present as a problem. This is continuity, not correction. They are not broken now and fixed later.
- Hustle language: grind, empire, crushing it, 10x, next level.

## Output

Return JSON only. No preamble, no code fence, no commentary.

{
  "brief": "...",
  "image_prompt": "..."
}

"brief" — 120 to 180 words, second person, addressed to them. This is what they read at the reveal, so it has to land. Warm, specific, plain-spoken. Name what they moved through and what it took. No headers, no bullet points.

"image_prompt" — one paragraph for a reference-conditioned image generator that receives their photo alongside it. It must produce a front-facing upper-body portrait, 16:9, clear even lighting, eyes to camera, relaxed neutral-to-warm expression, mouth closed. Describe the setting, wardrobe, light, and posture. Describe nothing about their face or body beyond expression and bearing.

Two rules specific to this paragraph. Describe light functionally — even, clear, soft, warm, daylight — never evaluatively. "Flattering", "glamorous", "cinematic beauty lighting" and the like are appearance judgments wearing technical clothes; leave them out. And keep the face optically sharp: no shallow depth of field, soft focus, bloom, or heavy grain. This image is the reference a face renderer will animate, so anything that softens their features degrades the avatar built from it.

The roadblock in their formation data matters most. This future self is specifically the person who moved through *that* obstacle. That is what makes the brief theirs and nobody else's."""


def _clean_json(text: str) -> str:
    """Strip a code fence if the model wrapped its JSON in one."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def build_brief_user_message(formation: dict) -> str:
    """Assemble the creator-specific half of the prompt from formation data.

    Accepts either a raw formations row or the flattened formation_context the
    agent uses — pulls whichever shape the fields arrive in.
    """
    data = formation.get("data") or formation.get("formation_data") or {}
    briefing = data.get("briefing") or formation.get("briefing") or {}

    def pick(*keys, default=""):
        for src in (formation, briefing, data):
            for k in keys:
                v = src.get(k)
                if v:
                    return v
        return default

    archetype = pick("archetype", "creator_type")
    if isinstance(archetype, list):
        archetype = archetype[0] if archetype else ""

    answers = formation.get("formation_answers") or data.get("answers") or []
    try:
        answers_text = json.dumps(answers, indent=2)[:6000]
    except Exception:
        answers_text = str(answers)[:6000]

    return f"""Here is the creator's formation data.

First name: {pick("first_name", default="(not given)")}
Studio: {pick("studio_name", default="(not given)")}
Creator type: {archetype or "(not given)"}
Strengths: {pick("arsenal", "strengths", default="(not given)")}
Roadblock: {pick("roadblock", default="(not given)")}

Formation answers:
{answers_text}

Write their FutureYou brief."""


def generate_future_you_brief(formation: dict, anthropic_client, model: str) -> dict:
    """Return {"brief": str, "image_prompt": str}.

    Raises ValueError if the model returns something unusable — the caller should
    mark the creator_avatars row 'failed' rather than provisioning from garbage.
    """
    resp = anthropic_client.messages.create(
        model=model,
        max_tokens=2000,
        system=FUTURE_YOU_BRIEF_SYSTEM,
        messages=[{"role": "user", "content": build_brief_user_message(formation)}],
    )
    raw = "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")

    try:
        parsed = json.loads(_clean_json(raw))
    except json.JSONDecodeError as e:
        logger.error("FutureYou brief returned non-JSON: %s", raw[:400])
        raise ValueError(f"brief generation returned non-JSON: {e}") from e

    brief = (parsed.get("brief") or "").strip()
    image_prompt = (parsed.get("image_prompt") or "").strip()
    if not brief or not image_prompt:
        raise ValueError("brief generation missing 'brief' or 'image_prompt'")

    return {"brief": brief, "image_prompt": image_prompt}
