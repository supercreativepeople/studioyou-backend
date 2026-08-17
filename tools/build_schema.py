#!/usr/bin/env python3
"""
Canonical building schema builder — StudioYou S2 schema refactor. v2.

Merges:
  - studioyou-app/studio.html:BUILDING_TASKS (frontend-facing creator_prompt/fy_rationale, all 12 buildings)
  - studioyou-backend/knowledge/buildings/*.md (agent-facing full spec, ideate + develop today)

v2 change: SECTION 6 (STEP SCHEMA) is not uniform across buildings. IDEATE organizes it as
flat sections ("### SECTION N — NAME") with sequential "STEP N:" numbering. DEVELOP organizes
it as archetype-conditional tracks ("### X TRACK", no SECTION prefix) with per-track lettered
step IDs ("STEP N-1:", "STEP M-1:", "STEP V-1:", "STEP P-1:", "STEP B-1:" for narrative/music/
visual/podcast/brand). Every building's canonical schema now uses a uniform outer "tracks" array
so consumers don't need to special-case shape: single-track buildings get one implicit track
(track_id "default"); DEVELOP gets one track per archetype, selected at runtime by the idea_type
captured in IDEATE Step 8 (Give It a Skeleton).

Writes one canonical JSON file per building to studioyou-backend/knowledge/schemas/<id>.json.
Writes a drift report to studioyou-backend/knowledge/schemas/_drift_report.json documenting
any step present in one source and not the other, for human review (not auto-resolved).

Safety design: every step keeps a `raw_spec` field with the full untouched .md block for that
step, so no content is ever lost even if the labeled-field extraction below misses something.
The orchestrator's step tier should treat `success_state` as authoritative for dispatch and
`raw_spec` as the full context to inject, per Section 6.1 of FY_LAYER2_SCHEMA.md.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

BACKEND = Path.home() / "Projects" / "studioyou-backend"
APP = Path.home() / "Downloads" / "studioyou-app"
KNOWLEDGE = BACKEND / "knowledge"
SCHEMAS_OUT = KNOWLEDGE / "schemas"
BUILDINGS_DIR = KNOWLEDGE / "buildings"
STUDIO_HTML = APP / "studio.html"

BUILDING_NAMES = {
    "ideate": "IDEATE", "develop": "DEVELOP", "fund": "FUND", "cast": "CAST",
    "plan": "PLAN", "produce": "PRODUCE", "post": "POST", "licensing": "LICENSING",
    "distribute": "DISTRIBUTE", "brand": "BRAND", "market": "MARKET", "monetize": "MONETIZE",
}

MD_SPEC_FILES = {
    "ideate": BUILDINGS_DIR / "FY_IDEATE_SUBAGENT_SPEC.md",
    "develop": BUILDINGS_DIR / "FY_DEVELOP_SUBAGENT_SPEC.md",
}

STEP_LABELS = [
    "PURPOSE", "SUCCESS STATE", "FAILURE STATE", "FY APPROACH",
    "TOOL ROUTING", "MODEL SUCCESS CONTEXT", "LEFT RAIL NARRATION", "CANVAS OUTPUT",
]

STEP_HEADER_RE = re.compile(r"^STEP ([A-Za-z0-9]+(?:-[A-Za-z0-9]+)?): (.+)$")
SECTION_HEADER_RE = re.compile(r"^### SECTION \d+ — (.+)$")
TRACK_HEADER_RE = re.compile(r"^### (.+)$")


def extract_building_tasks_js():
    text = STUDIO_HTML.read_text()
    marker = "const BUILDING_TASKS = "
    start = text.index(marker) + len(marker)
    assert text[start] == "{"
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

    tmp_js = Path("/tmp/_extract_building_tasks.js")
    tmp_js.write_text(f"const BUILDING_TASKS = {literal};\nprocess.stdout.write(JSON.stringify(BUILDING_TASKS));\n")
    result = subprocess.run(["node", str(tmp_js)], capture_output=True, text=True)
    if result.returncode != 0:
        print("NODE EVAL FAILED:", result.stderr, file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def extract_step_fields(block_lines):
    label_positions = []
    for idx, ln in enumerate(block_lines):
        for label in STEP_LABELS:
            if ln.strip() == f"{label}:" or ln.strip().startswith(f"{label}:"):
                label_positions.append((idx, label))
                break
    label_positions.append((len(block_lines), None))

    fields = {}
    for k in range(len(label_positions) - 1):
        idx, label = label_positions[k]
        next_idx = label_positions[k + 1][0]
        first_line = block_lines[idx].strip()
        first_line_content = first_line[len(label) + 1:].strip()
        rest = "\n".join(block_lines[idx + 1:next_idx]).strip()
        content = (first_line_content + ("\n" + rest if rest else "")).strip()
        fields[label] = content
    return fields


def parse_steps_in_range(lines):
    """Given a flat list of lines possibly containing multiple STEP blocks,
    return a list of step dicts."""
    step_bounds = []
    for idx, ln in enumerate(lines):
        m = STEP_HEADER_RE.match(ln)
        if m:
            step_bounds.append((idx, m.group(1), m.group(2).strip()))
    step_bounds.append((len(lines), None, None))

    steps = []
    for j in range(len(step_bounds) - 1):
        s_idx, step_id, step_title = step_bounds[j]
        e_idx = step_bounds[j + 1][0]
        if step_id is None:
            continue
        block_lines = lines[s_idx:e_idx]
        raw_spec = "\n".join(block_lines).strip()
        fields = extract_step_fields(block_lines)
        steps.append({
            "step_id": step_id,
            "title": step_title,
            "purpose": fields.get("PURPOSE"),
            "success_state": fields.get("SUCCESS STATE"),
            "failure_state": fields.get("FAILURE STATE"),
            "fy_approach": fields.get("FY APPROACH"),
            "tool_routing": fields.get("TOOL ROUTING"),
            "model_success_context": fields.get("MODEL SUCCESS CONTEXT"),
            "left_rail_narration": fields.get("LEFT RAIL NARRATION"),
            "canvas_output": fields.get("CANVAS OUTPUT"),
            "raw_spec": raw_spec,
        })
    return steps


def parse_md_spec(building_id, path):
    text = path.read_text()
    lines = text.split("\n")

    def slice_between(start_pat, end_pat):
        start_idx = end_idx = None
        for idx, ln in enumerate(lines):
            if start_idx is None and re.match(start_pat, ln):
                start_idx = idx
            elif start_idx is not None and re.match(end_pat, ln):
                end_idx = idx
                break
        if start_idx is None:
            return ""
        if end_idx is None:
            end_idx = len(lines)
        return "\n".join(lines[start_idx + 1:end_idx]).strip()

    philosophy = slice_between(r"^## SECTION 2:", r"^## SECTION 3:")
    prime_directive = slice_between(r"^## SECTION 3:", r"^## SECTION 4:")
    failure_patterns = slice_between(r"^## SECTION 4:", r"^## SECTION 5:")
    ignition_sequence = slice_between(r"^## SECTION 5:", r"^## SECTION 6:")
    model_success_context_notes = slice_between(r"^## SECTION 7:", r"^## SECTION 8:")
    output_format = slice_between(r"^## SECTION 8:", r"^## SECTION 9:")
    handoff_raw = slice_between(r"^## SECTION 9:", r"^## SECTION 10")

    handoff_to = None
    m = re.search(r"HANDOFF TO:\s*(.+)", handoff_raw)
    if m:
        handoff_to = m.group(1).strip()
    fy_handoff_line = None
    m = re.search(r"FY HANDOFF LINE:\s*\n\s*\"?(.+?)\"?\s*(\n\n|\Z)", handoff_raw, re.S)
    if m:
        fy_handoff_line = m.group(1).strip()

    sec6_start = sec6_end = None
    for idx, ln in enumerate(lines):
        if sec6_start is None and re.match(r"^## SECTION 6:", ln):
            sec6_start = idx
        elif sec6_start is not None and re.match(r"^## SECTION 7:", ln):
            sec6_end = idx
            break
    sec6_lines = lines[sec6_start:sec6_end] if sec6_start is not None else []

    # find all "###" headers in SECTION 6
    header_bounds = []
    for idx, ln in enumerate(sec6_lines):
        m = TRACK_HEADER_RE.match(ln)
        if m:
            header_bounds.append((idx, m.group(1).strip()))
    header_bounds.append((len(sec6_lines), None))

    is_section_style = any(SECTION_HEADER_RE.match(sec6_lines[idx]) for idx, _ in header_bounds[:-1])

    tracks = []
    if is_section_style:
        # ideate-style: one implicit track, headers are sections within it
        sections = []
        for hi in range(len(header_bounds) - 1):
            idx, name = header_bounds[hi]
            end_idx = header_bounds[hi + 1][0]
            if name is None:
                continue
            m = SECTION_HEADER_RE.match(sec6_lines[idx])
            section_name = m.group(1).strip() if m else name
            steps = parse_steps_in_range(sec6_lines[idx:end_idx])
            sections.append({"section_name": section_name, "steps": steps})
        tracks.append({"track_id": "default", "track_name": None, "sections": sections})
    else:
        # develop-style: each "###" header is an archetype track, flat steps inside, no sub-sections
        for hi in range(len(header_bounds) - 1):
            idx, name = header_bounds[hi]
            end_idx = header_bounds[hi + 1][0]
            if name is None:
                continue
            steps = parse_steps_in_range(sec6_lines[idx:end_idx])
            track_id = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
            tracks.append({"track_id": track_id, "track_name": name, "sections": [{"section_name": None, "steps": steps}]})

    return {
        "philosophy": philosophy or None,
        "prime_directive": prime_directive or None,
        "failure_patterns_raw": failure_patterns or None,
        "ignition_sequence_raw": ignition_sequence or None,
        "model_success_context_notes": model_success_context_notes or None,
        "output_format_raw": output_format or None,
        "handoff_to": handoff_to,
        "fy_handoff_line": fy_handoff_line,
        "handoff_raw": handoff_raw or None,
        "tracks": tracks,
    }


def norm_title(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())


def build_canonical(building_id, frontend_sections, md_data):
    spec_level = "full" if md_data else "stub"
    drift = {"building_id": building_id, "only_in_frontend": [], "only_in_md": []}

    fe_index = {}
    for sec in frontend_sections:
        for t in sec.get("tasks", []):
            fe_index[norm_title(t["title"])] = {
                "section_name": sec["section"],
                "title": t["title"],
                "creator_prompt": t.get("level1"),
                "fy_rationale": t.get("level2"),
            }

    if md_data:
        used_fe_keys = set()
        out_tracks = []
        for track in md_data["tracks"]:
            out_sections = []
            for sec in track["sections"]:
                out_steps = []
                for step in sec["steps"]:
                    key = norm_title(step["title"])
                    fe = fe_index.get(key)
                    if fe:
                        used_fe_keys.add(key)
                    out_steps.append({
                        "step_id": step["step_id"],
                        "title": step["title"],
                        "creator_prompt": fe["creator_prompt"] if fe else None,
                        "fy_rationale": fe["fy_rationale"] if fe else None,
                        "purpose": step["purpose"],
                        "success_state": step["success_state"],
                        "failure_state": step["failure_state"],
                        "fy_approach": step["fy_approach"],
                        "tool_routing": step["tool_routing"],
                        "model_success_context": step["model_success_context"],
                        "left_rail_narration": step["left_rail_narration"],
                        "canvas_output": step["canvas_output"],
                        "raw_spec": step["raw_spec"],
                    })
                    if not fe:
                        drift["only_in_md"].append({
                            "track": track["track_name"], "section": sec["section_name"], "title": step["title"]
                        })
                out_sections.append({"section_name": sec["section_name"], "steps": out_steps})
            out_tracks.append({"track_id": track["track_id"], "track_name": track["track_name"], "sections": out_sections})

        for key, fe in fe_index.items():
            if key not in used_fe_keys:
                drift["only_in_frontend"].append({"section": fe["section_name"], "title": fe["title"]})

        building = {
            "building_id": building_id,
            "building_name": BUILDING_NAMES[building_id],
            "spec_level": spec_level,
            "philosophy": md_data["philosophy"],
            "prime_directive": md_data["prime_directive"],
            "failure_patterns_raw": md_data["failure_patterns_raw"],
            "ignition_sequence_raw": md_data["ignition_sequence_raw"],
            "model_success_context_notes": md_data["model_success_context_notes"],
            "output_format_raw": md_data["output_format_raw"],
            "tracks": out_tracks,
            "handoff": {
                "handoff_to": md_data["handoff_to"],
                "fy_handoff_line": md_data["fy_handoff_line"],
                "raw": md_data["handoff_raw"],
            },
        }
    else:
        out_sections = []
        for sec in frontend_sections:
            out_steps = []
            for i, t in enumerate(sec.get("tasks", []), start=1):
                out_steps.append({
                    "step_id": str(i),
                    "title": t["title"],
                    "creator_prompt": t.get("level1"),
                    "fy_rationale": t.get("level2"),
                    "purpose": None, "success_state": None, "failure_state": None,
                    "fy_approach": None, "tool_routing": None, "model_success_context": None,
                    "left_rail_narration": None, "canvas_output": None, "raw_spec": None,
                })
            out_sections.append({"section_name": sec["section"], "steps": out_steps})
        building = {
            "building_id": building_id,
            "building_name": BUILDING_NAMES[building_id],
            "spec_level": spec_level,
            "philosophy": None, "prime_directive": None, "failure_patterns_raw": None,
            "ignition_sequence_raw": None, "model_success_context_notes": None, "output_format_raw": None,
            "tracks": [{"track_id": "default", "track_name": None, "sections": out_sections}],
            "handoff": {"handoff_to": None, "fy_handoff_line": None, "raw": None},
        }

    return building, drift


def main():
    SCHEMAS_OUT.mkdir(parents=True, exist_ok=True)
    building_tasks = extract_building_tasks_js()

    all_drift = []
    written = []
    for building_id in BUILDING_NAMES:
        if building_id not in building_tasks:
            print(f"WARNING: {building_id} not found in BUILDING_TASKS frontend object", file=sys.stderr)
        frontend_sections = building_tasks.get(building_id, [])
        md_path = MD_SPEC_FILES.get(building_id)
        md_data = parse_md_spec(building_id, md_path) if md_path and md_path.exists() else None
        building, drift = build_canonical(building_id, frontend_sections, md_data)
        out_path = SCHEMAS_OUT / f"{building_id}.json"
        out_path.write_text(json.dumps(building, indent=2))
        written.append(str(out_path))
        if drift["only_in_frontend"] or drift["only_in_md"]:
            all_drift.append(drift)

    report_path = SCHEMAS_OUT / "_drift_report.json"
    report_path.write_text(json.dumps({"generated_from": "build_schema.py", "findings": all_drift}, indent=2))

    print(f"Wrote {len(written)} building schema files to {SCHEMAS_OUT}")
    summary = []
    for building_id in BUILDING_NAMES:
        p = SCHEMAS_OUT / f"{building_id}.json"
        d = json.loads(p.read_text())
        n_tracks = len(d["tracks"])
        n_steps = sum(len(sec["steps"]) for tr in d["tracks"] for sec in tr["sections"])
        summary.append(f"  {building_id:12s} spec_level={d['spec_level']:5s} tracks={n_tracks} steps={n_steps}")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
