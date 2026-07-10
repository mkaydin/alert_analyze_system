import httpx


class ApiError(Exception):
    pass


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _request(self, method: str, path: str, *, json=None, timeout=180.0) -> dict:
        try:
            resp = httpx.request(method, self._url(path), json=json, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            detail = e.response.text
            try:
                detail = e.response.json().get("detail", detail)
            except Exception:
                pass
            raise ApiError(f"{e.response.status_code}: {detail}") from e
        except httpx.HTTPError as e:
            raise ApiError(f"Cannot reach server at {self.base_url} ({e})") from e

    def health(self) -> dict:
        return self._request("GET", "/api/v1/health", timeout=5.0)

    def analyze_input(self, content: str, content_type: str = "auto") -> dict:
        return self._request(
            "POST",
            "/api/v1/analyze-input",
            json={"content": content, "content_type": content_type},
        )

    def feedback(
        self, alert_id: str, analysis: str, decision: str, reason: str = ""
    ) -> dict:
        return self._request(
            "POST",
            "/api/v1/feedback",
            json={
                "alert_id": alert_id,
                "analysis": analysis,
                "decision": decision,
                "reason": reason,
            },
        )
