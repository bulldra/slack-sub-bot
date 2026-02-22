import re
from pathlib import Path
from string import Template
from typing import Optional

_SKILLS_DIR = Path(__file__).resolve().parent
_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)


def load_skill(skill_name: str, variables: Optional[dict[str, str]] = None) -> str:
    skill_path = _SKILLS_DIR / skill_name / "SKILL.md"
    with open(skill_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = _FRONTMATTER_RE.sub("", content)
    if variables:
        content = Template(content).substitute(variables)
    return content
