#!/usr/bin/env python3
"""Generate a markdown authoring-reference doc for DEVELOP: the real 30-step/5-track
spec (from knowledge/schemas/develop.json) side by side with the current frontend
13-step placeholder (from studio.html BUILDING_TASKS['develop']), so Lee can write
creator_prompt/fy_rationale copy for the real steps with both in view.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

BACKEND = Path.home() / "Projects" / "studioyou-backend"
APP = Path.home() / "Downloads" / "studioyou-app"
STUDIO_HTML = APP / "studio.html"
DEVELOP_JSON = BACKEND / "knowledge" / "schemas" / "develop.json"
OUT = BACKEND / "knowledge" / "DEVELOP_REFERENCE_FOR_AUTHORING_2026-08-17.md"


def extract_building_tasks_js():
    text = STUDIO_HTML.read_text()
    marker = "const BUILDING_TASKS = "
    start = text.index(marker) + len(marker)
    i = start
    depth = 0
    in_str = False
    quote = None
    escaped = False
    while i < len(text):
        ch = text[i]
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                in_str = False
        else:
            if ch in ("'", '"', "`"):
                in_str = True
                quote = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
        i += 1
    literal = text[start:i]
    tmp_js = Path("/tmp/_extract_bt2.js")
    tmp_js.write_text(f"const BUILDING_TASKS = {literal};\nprocess.stdout.write(JSON.stringify(BUILDING_TASKS));\n")
    result = subprocess.run(["node", str(tmp_js)], capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def main():
    bt = extract_building_tasks_js()
    frontend_sections = bt["develop"]
    dev = json.loads(DEVELOP_JSON.read_text())

    lines = []
    lines.append("# DEVELOP — Authoring Reference (2026-08-17)")
    lines.append("")
    lines.append("Two things side by side so both can be authored together: the real agent-side spec "
                  "(30 steps, 5 archetype tracks, written Session Z) and the current frontend placeholder "
                  "(13 generic steps, zero title overlap with the real spec, currently live in studio.html). "
                  "Goal: write `creator_prompt` / `fy_rationale` for every real step below, then studio.html "
                  "gets wired to render whichever track applies instead of the placeholder.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## PART 1 — The real spec: 30 steps, 5 archetype tracks")
    lines.append("")
    lines.append("Selected by `idea_type` from IDEATE Step 8 (Give It a Skeleton): story/script → Narrative, "
                  "music → Music, visual → Visual Art, podcast/series → Podcast, brand/social → Brand.")
    lines.append("")

    for track in dev["tracks"]:
        lines.append(f"### TRACK: {track['track_name']}")
        lines.append("")
        for sec in track["sections"]:
            for step in sec["steps"]:
                lines.append(f"#### Step {step['step_id']}: {step['title']}")
                lines.append("")
                if step.get("purpose"):
                    lines.append(f"**Purpose:** {step['purpose']}")
                    lines.append("")
                if step.get("success_state"):
                    lines.append(f"**Success state:** {step['success_state']}")
                    lines.append("")
                if step.get("failure_state"):
                    lines.append(f"**Failure state:** {step['failure_state']}")
                    lines.append("")
                if step.get("fy_approach"):
                    lines.append(f"**FY approach (agent-side, not creator-facing):** {step['fy_approach']}")
                    lines.append("")
                lines.append("**creator_prompt:** _(to author — what the creator sees, today's `level1`)_")
                lines.append("")
                lines.append("**fy_rationale:** _(to author — why it matters, today's `level2`)_")
                lines.append("")
                lines.append("---")
                lines.append("")

    lines.append("## PART 2 — Current frontend placeholder (studio.html, live today)")
    lines.append("")
    lines.append("Flat, generic, one track — no archetype branching. Zero title overlap with Part 1. "
                  "This is what every creator sees in DEVELOP right now, regardless of idea_type.")
    lines.append("")
    for sec in frontend_sections:
        lines.append(f"### Section: {sec['section']}")
        lines.append("")
        for t in sec.get("tasks", []):
            lines.append(f"**{t['title']}**")
            lines.append("")
            lines.append(f"- creator_prompt (level1): {t.get('level1','')}")
            lines.append(f"- fy_rationale (level2): {t.get('level2','')}")
            lines.append("")
        lines.append("")

    OUT.write_text("\n".join(lines))
    print(f"Wrote {OUT} ({len(OUT.read_text())} chars)")


if __name__ == "__main__":
    main()
