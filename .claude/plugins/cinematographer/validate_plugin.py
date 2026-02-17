"""Plugin structure validator."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent

EXPECTED_AGENTS = [
    "dp",
    "production-designer",
    "colorist",
    "groundtruth",
    "storyboarder",
]

EXPECTED_COMMANDS = [
    "storyboard",
    "lookdev",
    "shoot",
    "grade",
    "dailies",
    "wrap",
]

# Cross-plugin references that skills may declare.
CROSS_PLUGIN_ROOTS = {
    "critical-eye": PLUGIN_ROOT.parent / "critical-eye",
    "pipeline-expert": PLUGIN_ROOT.parent / "pipeline-expert",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
        elif fm and isinstance(fm.get(list(fm.keys())[-1]), list):
            last_key = list(fm.keys())[-1]
            item = line.lstrip("- ").strip()
            if item:
                fm[last_key].append(item)  # type: ignore[union-attr]
    return fm


def find_all_skills() -> dict[str, Path]:
    """Return {skill_name: SKILL.md path} for every skill in the plugin."""
    skills: dict[str, Path] = {}
    skills_dir = PLUGIN_ROOT / "skills"
    if not skills_dir.exists():
        return skills
    for skill_file in skills_dir.rglob("SKILL.md"):
        rel = skill_file.parent.relative_to(skills_dir)
        skill_name = str(rel).replace("\\", "/")
        skills[skill_name] = skill_file
    return skills


def extract_python_snippets(text: str) -> list[str]:
    """Return all ```python ... ``` fenced code blocks from *text*."""
    return re.findall(r"```python\s*\n(.*?)```", text, re.DOTALL)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_agent_skills_resolve(
    all_skills: dict[str, Path],
    referenced: set[str],
) -> list[str]:
    """1. Every agent's skills: list resolves to a SKILL.md."""
    errors: list[str] = []
    agents_dir = PLUGIN_ROOT / "agents"
    if not agents_dir.exists():
        return errors
    for agent_file in sorted(agents_dir.glob("*.md")):
        fm = parse_frontmatter(agent_file)
        agent_skills = fm.get("skills", [])
        if isinstance(agent_skills, str):
            agent_skills = [agent_skills]
        for skill_name in agent_skills:
            referenced.add(skill_name)
            if skill_name not in all_skills:
                errors.append(
                    f"Agent {agent_file.name}: skill '{skill_name}' "
                    f"has no SKILL.md under skills/"
                )
    return errors


def check_command_agents_resolve() -> list[str]:
    """2. Every command's agents: list resolves to an agent .md."""
    errors: list[str] = []
    commands_dir = PLUGIN_ROOT / "commands"
    agents_dir = PLUGIN_ROOT / "agents"
    if not commands_dir.exists():
        return errors
    existing_agents = {
        p.stem for p in agents_dir.glob("*.md")
    } if agents_dir.exists() else set()
    for cmd_file in sorted(commands_dir.glob("*.md")):
        fm = parse_frontmatter(cmd_file)
        agent_refs: list[str] = []
        for key in ("agent", "agents"):
            val = fm.get(key, [])
            if isinstance(val, str):
                agent_refs.append(val)
            else:
                agent_refs.extend(val)
        for ref in agent_refs:
            if ref not in existing_agents:
                errors.append(
                    f"Command {cmd_file.name}: references agent "
                    f"'{ref}' which does not exist"
                )
    return errors


def check_no_orphan_skills(
    all_skills: dict[str, Path],
    referenced: set[str],
) -> list[str]:
    """3. No orphan SKILL.md files."""
    warnings: list[str] = []
    for skill_name, skill_path in sorted(all_skills.items()):
        if skill_name not in referenced:
            rel = skill_path.relative_to(PLUGIN_ROOT)
            warnings.append(f"Orphan skill (unreferenced): {rel}")
    return warnings


def check_command_mirrors() -> list[str]:
    """4. Command mirror files exist in .claude/commands/."""
    errors: list[str] = []
    claude_commands = PLUGIN_ROOT.parent.parent / "commands"
    for cmd_name in EXPECTED_COMMANDS:
        mirror = claude_commands / f"cinematographer:{cmd_name}.md"
        if not mirror.exists():
            errors.append(
                f"Missing command mirror: .claude/commands/cinematographer:{cmd_name}.md"
            )
    return errors


def check_skill_frontmatter(all_skills: dict[str, Path]) -> list[str]:
    """5. Every skill has type: and primary_owner: in frontmatter."""
    errors: list[str] = []
    for skill_name, skill_path in sorted(all_skills.items()):
        fm = parse_frontmatter(skill_path)
        for required_key in ("type", "primary_owner"):
            if required_key not in fm:
                errors.append(
                    f"Skill '{skill_name}': missing '{required_key}' in frontmatter"
                )
    return errors


def check_mece_ownership(all_skills: dict[str, Path]) -> list[str]:
    """6. MECE check: no skill has primary_owner matching two different agents."""
    errors: list[str] = []
    owner_map: dict[str, list[str]] = {}
    for skill_name, skill_path in sorted(all_skills.items()):
        fm = parse_frontmatter(skill_path)
        owner = fm.get("primary_owner", "")
        if isinstance(owner, str) and owner:
            owner_map.setdefault(skill_name, []).append(owner)
    for skill_name, owners in owner_map.items():
        if len(owners) > 1:
            errors.append(
                f"Skill '{skill_name}' has multiple primary_owner values: "
                f"{', '.join(owners)}"
            )
    return errors


def check_antipatterns(all_skills: dict[str, Path]) -> list[str]:
    """7. Every skill has Anti-Patterns section (non-empty)."""
    errors: list[str] = []
    for skill_name, skill_path in sorted(all_skills.items()):
        text = skill_path.read_text(encoding="utf-8")
        match = re.search(
            r"#+\s*Anti[- ]?Patterns\s*\n(.*?)(?=\n#+\s|\Z)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if not match or not match.group(1).strip():
            errors.append(
                f"Skill '{skill_name}': missing or empty Anti-Patterns section"
            )
    return errors


def check_collaboration_protocol() -> list[str]:
    """8. Every agent loads reference/collaboration-protocol in its skills list."""
    errors: list[str] = []
    agents_dir = PLUGIN_ROOT / "agents"
    if not agents_dir.exists():
        return errors
    for agent_file in sorted(agents_dir.glob("*.md")):
        fm = parse_frontmatter(agent_file)
        agent_skills = fm.get("skills", [])
        if isinstance(agent_skills, str):
            agent_skills = [agent_skills]
        if "reference/collaboration-protocol" not in agent_skills:
            errors.append(
                f"Agent {agent_file.name}: does not list "
                f"'reference/collaboration-protocol' in skills"
            )
    return errors


def check_cross_plugin_references(all_skills: dict[str, Path]) -> list[str]:
    """9. Cross-plugin references (to critical-eye, pipeline-expert) are valid paths."""
    errors: list[str] = []
    cross_ref_pattern = re.compile(
        r"\.\./(?:critical-eye|pipeline-expert)/[^\s\)\"']+"
    )
    for skill_name, skill_path in sorted(all_skills.items()):
        text = skill_path.read_text(encoding="utf-8")
        for match in cross_ref_pattern.finditer(text):
            ref_path = match.group(0)
            resolved = (skill_path.parent / ref_path).resolve()
            if not resolved.exists():
                errors.append(
                    f"Skill '{skill_name}': cross-plugin reference "
                    f"'{ref_path}' does not resolve"
                )
    # Also check agent files for cross-plugin references.
    agents_dir = PLUGIN_ROOT / "agents"
    if agents_dir.exists():
        for agent_file in sorted(agents_dir.glob("*.md")):
            text = agent_file.read_text(encoding="utf-8")
            for match in cross_ref_pattern.finditer(text):
                ref_path = match.group(0)
                resolved = (agent_file.parent / ref_path).resolve()
                if not resolved.exists():
                    errors.append(
                        f"Agent {agent_file.name}: cross-plugin reference "
                        f"'{ref_path}' does not resolve"
                    )
    return errors


def check_python_snippets(all_skills: dict[str, Path]) -> list[str]:
    """10. Skills with code snippets: snippets are syntactically valid Python."""
    errors: list[str] = []
    for skill_name, skill_path in sorted(all_skills.items()):
        text = skill_path.read_text(encoding="utf-8")
        snippets = extract_python_snippets(text)
        for i, snippet in enumerate(snippets, 1):
            try:
                ast.parse(snippet)
            except SyntaxError as exc:
                errors.append(
                    f"Skill '{skill_name}': Python snippet #{i} "
                    f"has syntax error: {exc.msg} (line {exc.lineno})"
                )
    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def validate() -> tuple[list[str], list[str]]:
    """Run all 10 validation checks. Returns (errors, warnings)."""
    all_skills = find_all_skills()
    referenced_skills: set[str] = set()
    errors: list[str] = []
    warnings: list[str] = []

    checks = [
        ("1. Agent skill references",
         lambda: check_agent_skills_resolve(all_skills, referenced_skills)),
        ("2. Command agent references",
         lambda: check_command_agents_resolve()),
        ("3. Orphan skills",
         None),  # handled after referenced_skills is populated
        ("4. Command mirror files",
         lambda: check_command_mirrors()),
        ("5. Skill frontmatter (type + primary_owner)",
         lambda: check_skill_frontmatter(all_skills)),
        ("6. MECE ownership",
         lambda: check_mece_ownership(all_skills)),
        ("7. Anti-Patterns sections",
         lambda: check_antipatterns(all_skills)),
        ("8. Collaboration protocol in agents",
         lambda: check_collaboration_protocol()),
        ("9. Cross-plugin references",
         lambda: check_cross_plugin_references(all_skills)),
        ("10. Python snippet validity",
         lambda: check_python_snippets(all_skills)),
    ]

    for label, check_fn in checks:
        if check_fn is None:
            # Orphan check deferred until after agent skill scan.
            continue
        print(f"  Checking: {label}")
        result = check_fn()
        if label.startswith("3."):
            warnings.extend(result)
        else:
            errors.extend(result)

    # Now run deferred orphan check.
    print("  Checking: 3. Orphan skills")
    orphan_warnings = check_no_orphan_skills(all_skills, referenced_skills)
    warnings.extend(orphan_warnings)

    return errors, warnings


def main() -> int:
    """Run validation and print report."""
    print("cinematographer plugin validation")
    print("=" * 40)

    # Basic structure checks.
    agents_dir = PLUGIN_ROOT / "agents"
    commands_dir = PLUGIN_ROOT / "commands"
    all_skills = find_all_skills()

    missing_agents = [
        name for name in EXPECTED_AGENTS
        if not (agents_dir / f"{name}.md").exists()
    ]
    missing_commands = [
        name for name in EXPECTED_COMMANDS
        if not (commands_dir / f"{name}.md").exists()
    ]

    for name in missing_agents:
        print(f"  FAIL  Missing agent file: agents/{name}.md")
    for name in missing_commands:
        print(f"  FAIL  Missing command file: commands/{name}.md")

    errors, warnings = validate()

    agents_found = len(list(agents_dir.glob("*.md"))) if agents_dir.exists() else 0
    commands_found = len(list(commands_dir.glob("*.md"))) if commands_dir.exists() else 0
    total_errors = len(errors) + len(missing_agents) + len(missing_commands)

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  FAIL  {e}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  WARN  {w}")

    print(f"\nSUMMARY:")
    print(f"  Agents:   {agents_found}/{len(EXPECTED_AGENTS)} found")
    print(f"  Commands: {commands_found}/{len(EXPECTED_COMMANDS)} found")
    print(f"  Skills:   {len(all_skills)} discovered")
    print(f"  Errors:   {total_errors}")
    print(f"  Warnings: {len(warnings)}")

    if total_errors:
        print("\nRESULT: FAIL")
        return 1
    if warnings:
        print("\nRESULT: PASS (with warnings)")
    else:
        print("\nRESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
