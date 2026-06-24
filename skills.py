# skills.py
"""
Termina Skills System — filesystem-based skill discovery and loading.

Skills are directories containing a SKILL.md file with YAML frontmatter.
They are discovered from two locations (in priority order):
  1. .termina/skills/  — project-local skills (commit to repo)
  2. ~/.termina/skills/ — global skills (personal library)

SKILL.md format:
---
name: skill-name
description: What this skill does and when to trigger it.
allowed-tools: read_file, grep_search  (optional, comma-separated)
---
# Skill content here...
"""

import re
from pathlib import Path
from typing import Optional


def _skill_directories() -> list[Path]:
    """Return skill search directories in priority order."""
    return [
        Path(".termina") / "skills",          # project-local (higher priority)
        Path.home() / ".termina" / "skills",  # global
    ]


def _parse_frontmatter(content: str) -> dict:
    """
    Parse YAML frontmatter from a SKILL.md file.
    Frontmatter is the block between the first two --- lines.
    """
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}
    meta = {}
    for line in match.group(1).splitlines():
        if ':' in line:
            k, _, v = line.partition(':')
            meta[k.strip()] = v.strip()
    return meta


def discover_skills() -> list[dict]:
    """
    Scan all skill directories and return a list of skill metadata dicts.
    Each dict has: name, description, allowed_tools, path, content.
    Deduplicates by name — project-local skills take priority over global.
    """
    seen_names = set()
    skills = []

    for skill_dir in _skill_directories():
        if not skill_dir.exists():
            continue

        for entry in sorted(skill_dir.iterdir()):
            if not entry.is_dir():
                continue
            skill_md = entry / "SKILL.md"
            if not skill_md.exists():
                continue

            try:
                content = skill_md.read_text(encoding="utf-8")
            except Exception:
                continue

            meta = _parse_frontmatter(content)
            name = meta.get("name", entry.name)

            if name in seen_names:
                continue  # project-local already registered this name
            seen_names.add(name)

            # Parse allowed-tools list
            raw_tools = meta.get("allowed-tools", "")
            allowed_tools = [t.strip() for t in raw_tools.split(",") if t.strip()]

            skills.append({
                "name":          name,
                "description":   meta.get("description", "No description."),
                "allowed_tools": allowed_tools,
                "path":          str(skill_md),
                "content":       content,
            })

    return skills


def build_skills_index(skills: list[dict]) -> str:
    """
    Build the compact metadata block injected into the system prompt.
    Only includes name + description — full content is loaded on demand.
    """
    if not skills:
        return ""
    lines = [
        "\n## AVAILABLE SKILLS",
        "The following skills are available. Trigger them automatically when relevant, "
        "or the user can invoke them with /skill <name>.",
        ""
    ]
    for s in skills:
        tools_note = f" (tools: {', '.join(s['allowed_tools'])})" if s['allowed_tools'] else ""
        lines.append(f"- **{s['name']}**: {s['description']}{tools_note}")
    return "\n".join(lines)


def load_skill(name: str, skills: list[dict]) -> Optional[str]:
    """Load the full content of a skill by name. Returns None if not found."""
    for s in skills:
        if s["name"] == name:
            return s["content"]
    return None


def create_skill(name: str, description: str = "", project_local: bool = True) -> Path:
    """
    Scaffold a new skill directory with a starter SKILL.md.
    Returns the path to the created SKILL.md.
    """
    if project_local:
        base = Path(".termina") / "skills"
    else:
        base = Path.home() / ".termina" / "skills"

    skill_dir = base / name
    skill_dir.mkdir(parents=True, exist_ok=True)

    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        return skill_md  # don't overwrite

    template = f"""\
---
name: {name}
description: {description or f'Describe what {name} does and when to trigger it.'}
allowed-tools: read_file, grep_search, run_command
---

# {name.replace('-', ' ').title()}

## Instructions

<!-- Write clear, step-by-step instructions for the AI to follow -->
<!-- Use concrete steps, not vague guidance -->

1. Step one
2. Step two
3. Step three

## Examples

<!-- Show example prompts that trigger this skill -->
<!-- Example: "Run this skill when the user asks to review code" -->

## Notes

<!-- Any additional context or caveats -->
"""
    skill_md.write_text(template, encoding="utf-8")
    return skill_md
