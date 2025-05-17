import json

import requests

import utils.stored_gcs


class Weather:
    URL_ENDPOINT = "https://www.jma.go.jp/bosai/forecast/data/overview_forecast"

    def __init__(self):
        from pathlib import Path

        conf_path = Path(__file__).resolve().parent.parent / "conf" / "gcs_bucket.json"
        with open(conf_path, "r", encoding="utf-8") as json_file:
            config: dict = json.load(json_file)
            self._gcs_bucket_name: str = config["gcs_bucket_name"]
            self._gcs_weathr_dir: str = config["gcs_weather_dir"]

    def get(self, area_no: int = 130000):
        file_name = f"{area_no}.json"
        blob = f"{self._gcs_weathr_dir}/{file_name}"
        gcs = utils.stored_gcs.StoredGcs(self._gcs_bucket_name, blob)
        from typing import Optional

        content: Optional[str] = None
        if gcs.is_exists() and not gcs.is_expired():
            content = gcs.download_as_string()
        else:
            response = requests.get(
                f"{self.URL_ENDPOINT}/{area_no}.json", timeout=(3, 8)
            )
            if response.status_code == 200:
                content = response.text
                gcs.parsist(content)
            elif gcs.is_exists():
                content = gcs.download_as_string()

        if not content:
            return None
        json_data = json.loads(content)
        return json_data
