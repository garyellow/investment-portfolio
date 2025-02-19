from typing import Optional

import requests

"""
網路工具模組：提供 fetch_json 函式以設定 timeout 並返回解析後的 JSON 數據。
"""


def fetch_json(
    url: str, params: Optional[dict] = None, headers: Optional[dict] = None
) -> dict | list | None:
    """
    發送 GET 請求並返回 JSON 資料；如發生錯誤則返回 None。
    """
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None
