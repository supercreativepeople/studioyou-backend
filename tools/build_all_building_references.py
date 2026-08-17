#!/usr/bin/env python3
"""Generate one authoring-reference markdown doc per building (all 12), so Lee can
lay out the full internal product blueprint building by building and hand it back
in one batch.

For "full" spec_level buildings (ideate, develop today): mirrors the DEVELOP doc —
Part 1 walks every real step with its existing PURPOSE/SUCCESS STATE/FAILURE STATE/
FY APPROACH already written, creator_prompt/fy_rationale shown as "current (may
revise)" where they already exist (matched to frontend) or blank-to-author where
they don't. Part 2 shows the raw current frontend placeholder for comparison.

For "stub" spec_level buildings (the other 10): there is no agent-side spec yet, so
Part 1 is a blank authoring template following FY_LAYER2_SCHEMA.md's own governing
structure (Sections 1-10) — Section 6 (STEP SCHEMA) is pre-seeded with the existing
frontend section/step titles as a starting skeleton (freely renameable — buildings
don't have to keep today's structure), every other field blank-to-author. Part 2
shows the current frontend placeholder for reference.

Output: knowledge/schemas/authoring_reference/<building_id>.md, one per building.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

BACKEND = Path.home() / "Projects" / "studioyou-backend"
APP = Path.home() / "Downloads" / "studioyou-app"
STUDIO_HTML = APP / "studio.html"
SCHEMAS_DIR = BACKEND / "knowledge" / "schemas"
OUT_DIR = SCHEMAS_DIR / "authoring_reference"

BUILDING_NAMES = {
    "ideate": "IDEATE", "develop": "DEVELOP", "fund": "FUND", "cast": "CAST",
    "plan": "PLAN", "produce": "PRODUCE", "post": "POST", "licensing": "LICENSING",
    "distribute": "DISTRIBUTE", "brand": "BRAND", "market": "MARKET", "monetize": "MONETIZE",
}

TBD = "_(to author)_"


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
    tmp_js = Path("/tmp/_extract_bt3.js")
    tmp_js.write_text(f"const BUILDING_TASKS = {literal};\nprocess.stdout.write(JSON.stringify(BUILDING_TASKS));\n")
    result = subprocess.run(["node", str(tmp_js)], capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def render_full_building(building_id, building_name, schema, frontend_sections):
    lines = []
    lines.append(f"# {building_name} — Authoring Reference (2026-08-17)")
    lines.append("")
    lines.append("Full agent-side spec already exists for this building. Part 1 walks every real "
                  "step with its existing intelligence; `creator_prompt`/`fy_rationale` are shown as "
                  "**current (may revise)** where they already exist, or flagged to author where they "
                  "don't. Part 2 is the current frontend placeholder for direct comparison.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## PART 1 — Real spec")
    lines.append("")
    for track in schema["tracks"]:
        if track.get("track_name"):
            lines.append(f"### TRACK: {track['track_name']}")
            lines.append("")
        for sec in track["sections"]:
            if sec.get("section_name"):
                lines.append(f"### SECTION: {sec['section_name']}")
                lines.append("")
            for step in sec["steps"]:
                lines.append(f"#### Step {step['step_id']}: {step['title']}")
                lines.append("")
                for label, key in [("Purpose", "purpose"), ("Success state", "success_state"),
                                    ("Failure state", "failure_state")]:
                    if step.get(key):
                        lines.append(f"**{label}:** {step[key]}")
                        lines.append("")
                if step.get("fy_approach"):
                    lines.append(f"**FY approach (agent-side, not creator-facing):** {step['fy_approach']}")
                    lines.append("")
                if step.get("creator_prompt"):
                    lines.append(f"**creator_prompt (current, may revise):** {step['creator_prompt']}")
                else:
                    lines.append(f"**creator_prompt:** {TBD} — what the creator sees")
                lines.append("")
                if step.get("fy_rationale"):
                    lines.append(f"**fy_rationale (current, may revise):** {step['fy_rationale']}")
                else:
                    lines.append(f"**fy_rationale:** {TBD} — why it matters")
                lines.append("")
                lines.append("---")
                lines.append("")

    lines.append("## PART 2 — Current frontend placeholder (studio.html, live today)")
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
    return "\n".join(lines)


def render_stub_building(building_id, building_name, frontend_sections):
    lines = []
    lines.append(f"# {building_name} — Authoring Reference (2026-08-17)")
    lines.append("")
    lines.append("No agent-side spec exists yet for this building — this is a blank blueprint "
                  "template following the same governing structure as IDEATE/DEVELOP "
                  "(FY_LAYER2_SCHEMA.md Sections 1-10). Section 6 is pre-seeded with the current "
                  "frontend section/step titles as a starting skeleton only — rename, add, remove, "
                  "or restructure freely. Nothing here is locked.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## PART 1 — Blueprint template (nothing authored yet)")
    lines.append("")
    lines.append("### SECTION 1: ROLE DEFINITION")
    lines.append("")
    lines.append(f"BUILDING: {building_name}")
    lines.append(f"AGENT TYPE: {TBD} (Execution / Advisory — CAST and PRODUCE are advisory-only per "
                  "FY_LAYER2_SCHEMA.md Section 10, others are execution)")
    lines.append(f"CANVAS OUTPUT: {TBD}")
    lines.append(f"TIER: {TBD} (typically Tier 3 — dispatched by Tier 2 orchestrator)")
    lines.append(f"TONE: {TBD}")
    lines.append("")
    lines.append("### SECTION 2: BUILDING PHILOSOPHY")
    lines.append("")
    lines.append(TBD)
    lines.append("")
    lines.append("### SECTION 3: FY PRIME DIRECTIVE")
    lines.append("")
    lines.append(TBD)
    lines.append("")
    lines.append("### SECTION 4: PRIMARY FAILURE PATTERNS")
    lines.append("")
    lines.append("_(Format per pattern: WHAT IT LOOKS LIKE / WHY IT HAPPENS / FY RESPONSE — "
                  "see IDEATE Section 4 for the reference shape. Add as many as apply.)_")
    lines.append("")
    lines.append(f"FAILURE PATTERN 1: {TBD}")
    lines.append("")
    lines.append("### SECTION 5: IGNITION SEQUENCE")
    lines.append("")
    lines.append(f"{TBD} (optional — only if this building needs a distinct opening sequence "
                  "before Section 6's step-by-step begins, the way IDEATE does)")
    lines.append("")
    lines.append("### SECTION 6: STEP SCHEMA")
    lines.append("")
    lines.append("_Pre-seeded from the current frontend — freely rename/restructure._")
    lines.append("")
    for sec in frontend_sections:
        lines.append(f"#### SECTION — {sec['section']}")
        lines.append("")
        for i, t in enumerate(sec.get("tasks", []), start=1):
            lines.append(f"##### STEP {i}: {t['title']}")
            lines.append("")
            lines.append(f"**creator_prompt (current, may revise):** {t.get('level1','')}")
            lines.append("")
            lines.append(f"**fy_rationale (current, may revise):** {t.get('level2','')}")
            lines.append("")
            lines.append(f"**Purpose:** {TBD}")
            lines.append("")
            lines.append(f"**Success state:** {TBD} — checkable per Section 6.1, not aspirational")
            lines.append("")
            lines.append(f"**Failure state:** {TBD}")
            lines.append("")
            lines.append(f"**FY approach (agent-side):** {TBD}")
            lines.append("")
            lines.append(f"**Tool routing:** {TBD}")
            lines.append("")
            lines.append(f"**Left rail narration:** {TBD}")
            lines.append("")
            lines.append("---")
            lines.append("")
    lines.append("### SECTION 7: MODEL SUCCESS CONTEXT")
    lines.append("")
    lines.append(f"{TBD} — one entry per generative tool this building calls, format per "
                  "FY_LAYER2_SCHEMA.md Section 7 (RELIABLE AT / FAILS AT / FAILURE FREQUENCY / "
                  "BETTER MODEL / PROMPT FIX / VERIFICATION STEP)")
    lines.append("")
    lines.append("### SECTION 8: OUTPUT FORMAT")
    lines.append("")
    lines.append(f"CANVAS OUTPUT TYPE: {TBD}")
    lines.append(f"CARD STRUCTURE: {TBD}")
    lines.append(f"VAULT SCHEMA: {TBD}")
    lines.append("")
    lines.append("### SECTION 9: HANDOFF PROTOCOL")
    lines.append("")
    lines.append(f"HANDOFF TO: {TBD}")
    lines.append(f"HANDOFF PACKAGE: {TBD}")
    lines.append(f"FY HANDOFF LINE: {TBD}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## PART 2 — Current frontend placeholder (studio.html, live today)")
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
    return "\n".join(lines)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    building_tasks = extract_building_tasks_js()

    written = []
    for building_id, building_name in BUILDING_NAMES.items():
        frontend_sections = building_tasks.get(building_id, [])
        schema_path = SCHEMAS_DIR / f"{building_id}.json"
        schema = json.loads(schema_path.read_text()) if schema_path.exists() else None

        if schema and schema.get("spec_level") == "full":
            content = render_full_building(building_id, building_name, schema, frontend_sections)
        else:
            content = render_stub_building(building_id, building_name, frontend_sections)

        out_path = OUT_DIR / f"{building_id}.md"
        out_path.write_text(content)
        written.append(str(out_path))
        print(f"{building_id:12s} spec_level={schema.get('spec_level') if schema else 'none':5s} -> {out_path} ({len(content)} chars)")

    print(f"\nWrote {len(written)} files to {OUT_DIR}")


if __name__ == "__main__":
    main()
