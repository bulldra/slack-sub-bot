from datetime import datetime, timedelta, timezone

import utils.weather
from skills.skill_loader import load_skill


def build_system_prompt(use_character: bool) -> str:
    now_iso: str = datetime.now(timezone(timedelta(hours=9))).isoformat()
    if use_character:
        weather: dict = utils.weather.Weather().get()
        return load_skill(
            "system",
            {
                "WEATHER_REPORT_DATETIME": str(weather.get("reportDatetime", "")),
                "WEATHER_REPORT_TEXT": str(weather.get("text", "")),
                "DATE_TIME": now_iso,
            },
        )
    return load_skill(
        "system_base",
        {"DATE_TIME": now_iso},
    )
