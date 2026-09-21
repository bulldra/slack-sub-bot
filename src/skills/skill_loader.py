import re
from pathlib import Path
from string import Template
from typing import Any, Optional

import yaml

_SKILLS_DIR = Path(__file__).resolve().parent
_FRONTMATTER_EXTRACT_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def load_skill_frontmatter(skill_name: str) -> dict[str, Any]:
    """指定されたスキルのYAMLフロントマターのみをパースして辞書で返す。"""
    skill_path = _SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_path.exists():
        return {}
    with open(skill_path, "r", encoding="utf-8") as f:
        content = f.read()
    match = _FRONTMATTER_EXTRACT_RE.match(content)
    if not match:
        return {}
    try:
        data = yaml.safe_load(match.group(1))
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def load_all_skill_frontmatters() -> dict[str, dict[str, Any]]:
    """すべてのスキルのフロントマターを読み込む。"""
    skills: dict[str, dict[str, Any]] = {}
    if not _SKILLS_DIR.exists():
        return skills
    for skill_dir in sorted(_SKILLS_DIR.iterdir()):
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            meta = load_skill_frontmatter(skill_dir.name)
            if meta:
                name = meta.get("name", skill_dir.name)
                skills[name] = meta
    return skills


def get_routable_skills() -> list[dict[str, Any]]:
    """
    ルーティング対象のスキルをフロントマターのみを参照して取得し、
    Gemini Function Calling (tools) 形式のリストにして返す。
    フロントマターの name, description, parameters を参照する。
    """
    all_skills = load_all_skill_frontmatters()
    routable = [meta for meta in all_skills.values() if meta.get("routable", False)]
    routable.sort(key=lambda x: int(x.get("priority", 100)))
    tools: list[dict[str, Any]] = []
    for meta in routable:
        tools.append(
            {
                "name": meta["name"],
                "description": meta.get("description", ""),
                "parameters": meta.get(
                    "parameters", {"type": "object", "properties": {}}
                ),
            }
        )
    return tools


def load_skill(skill_name: str, variables: Optional[dict[str, str]] = None) -> str:
    """スキルの本文（Markdown）のみを読み込み、変数を適用して返す。"""
    skill_path = _SKILLS_DIR / skill_name / "SKILL.md"
    with open(skill_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = _FRONTMATTER_EXTRACT_RE.sub("", content)
    if variables:
        for k in variables.keys():
            content = re.sub(rf"\{{\{{\s*{re.escape(k)}\s*\}}\}}", f"${{{k}}}", content)
        content = Template(content).safe_substitute(variables)
    return content.strip()
