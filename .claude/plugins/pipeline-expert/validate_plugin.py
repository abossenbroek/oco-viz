"""Validate the pipeline-expert plugin structure.

Checks:
- All expected agent files exist under agents/
- All expected command files exist under commands/
- Every agent's skills: frontmatter list resolves to a SKILL.md
- Every command's agent references resolve to existing agents
- No orphan SKILL.md files (every skill referenced by at least one agent or command)

Exit code 0 if no errors, 1 if errors found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent

EXPECTED_AGENTS = [
    "auteur",
    "spectralist",
    "sculptor",
    "tonalist",
    "choreographer",
    "alchemist",
    "installer",
]

EXPECTED_COMMANDS = [
    "review-stage",
    "consult",
    "ideate",
    "audit",
]


def parse_frontmatter(filepath: Path) -> dict[str, str | list[str]]:
    """Extract YAML frontmatter between --- delimiters."""
    text = filepath.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    fm: dict[str, str | list[str]] = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value:
                fm[key] = value
            else:
                fm[key] = []
        elif isinstance(fm.get(list(fm.keys())[-1] if fm else ""), list):
            last_key = list(fm.keys())[-1]
            item = line.lstrip("- ").strip()
            if item:
                fm[last_key].append(item)  # type: ignore[union-attr]
    return fm


def find_all_skills() -> dict[str, Path]:
    """Find all SKILL.md files and return {skill_name: path}.

    Skill names are the relative path from skills/ to the SKILL.md parent dir.
    E.g. skills/reference/output-schemas/SKILL.md -> 'reference/output-schemas'
    and  skills/density-to-dread/SKILL.md        -> 'density-to-dread'
    """
    skills: dict[str, Path] = {}
    skills_dir = PLUGIN_ROOT / "skills"
    if not skills_dir.exists():
        return skills
    for skill_file in skills_dir.rglob("SKILL.md"):
        rel = skill_file.parent.relative_to(skills_dir)
        skill_name = str(rel).replace("\\", "/")
        skills[skill_name] = skill_file
    return skills


def validate() -> tuple[list[str], list[str]]:
    """Run all validation checks. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []
    referenced_skills: set[str] = set()

    # Check agent files
    agents_dir = PLUGIN_ROOT / "agents"
    existing_agents: set[str] = set()
    for agent_name in EXPECTED_AGENTS:
        agent_file = agents_dir / f"{agent_name}.md"
        if agent_file.exists():
            existing_agents.add(agent_name)
        else:
            errors.append(f"Missing agent file: agents/{agent_name}.md")

    # Check command files
    commands_dir = PLUGIN_ROOT / "commands"
    for cmd_name in EXPECTED_COMMANDS:
        cmd_file = commands_dir / f"{cmd_name}.md"
        if not cmd_file.exists():
            errors.append(f"Missing command file: commands/{cmd_name}.md")

    # Discover all skills
    all_skills = find_all_skills()

    # Validate agent skill references
    if agents_dir.exists():
        for agent_file in sorted(agents_dir.glob("*.md")):
            fm = parse_frontmatter(agent_file)
            agent_skills = fm.get("skills", [])
            if isinstance(agent_skills, str):
                agent_skills = [agent_skills]
            for skill_name in agent_skills:
                referenced_skills.add(skill_name)
                if skill_name not in all_skills:
                    errors.append(
                        f"Agent {agent_file.name}: skill '{skill_name}' "
                        f"has no SKILL.md under skills/"
                    )

    # Validate command agent references
    if commands_dir.exists():
        for cmd_file in sorted(commands_dir.glob("*.md")):
            fm = parse_frontmatter(cmd_file)
            # Commands may reference agents via 'agent' or 'agents' field
            agent_refs: list[str] = []
            for key in ("agent", "agents"):
                val = fm.get(key, [])
                if isinstance(val, str):
                    agent_refs.append(val)
                else:
                    agent_refs.extend(val)
            for agent_ref in agent_refs:
                if agent_ref not in existing_agents:
                    errors.append(
                        f"Command {cmd_file.name}: references agent "
                        f"'{agent_ref}' which does not exist"
                    )
            # Commands may also reference skills
            cmd_skills = fm.get("skills", [])
            if isinstance(cmd_skills, str):
                cmd_skills = [cmd_skills]
            for skill_name in cmd_skills:
                referenced_skills.add(skill_name)

    # Check for orphan skills
    for skill_name, skill_path in sorted(all_skills.items()):
        if skill_name not in referenced_skills:
            rel = skill_path.relative_to(PLUGIN_ROOT)
            warnings.append(f"Orphan skill (unreferenced): {rel}")

    return errors, warnings


def main() -> int:
    """Run validation and print report."""
    print("pipeline-expert plugin validation")
    print("=" * 40)

    errors, warnings = validate()

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  x {e}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  ! {w}")

    all_skills = find_all_skills()
    agents_found = len(list((PLUGIN_ROOT / "agents").glob("*.md"))) if (PLUGIN_ROOT / "agents").exists() else 0
    commands_found = len(list((PLUGIN_ROOT / "commands").glob("*.md"))) if (PLUGIN_ROOT / "commands").exists() else 0

    print(f"\nSUMMARY:")
    print(f"  Agents:   {agents_found}/{len(EXPECTED_AGENTS)} found")
    print(f"  Commands: {commands_found}/{len(EXPECTED_COMMANDS)} found")
    print(f"  Skills:   {len(all_skills)} discovered")
    print(f"  Errors:   {len(errors)}")
    print(f"  Warnings: {len(warnings)}")

    if errors:
        print("\nRESULT: FAIL")
        return 1
    if warnings:
        print("\nRESULT: PASS (with warnings)")
    else:
        print("\nRESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
