"""
GoLogin API Client
Wrapper for GoLogin REST API
"""

import requests


GOLOGIN_API_BASE = "https://api.gologin.com"
CLOUD_BROWSER_BASE = "https://cloudbrowser.gologin.com"


class GoLoginAPIError(Exception):
    """Lỗi khi gọi API GoLogin"""
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{status_code}] {message}")


class GoLoginClient:
    """Client bọc REST API của GoLogin"""
    
    def __init__(self, token, timeout=30):
        self.token = (token or "").strip()
        self.timeout = timeout
    
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
    
    def _request(self, method, path, **kwargs):
        url = f"{GOLOGIN_API_BASE}{path}"
        kwargs.setdefault("timeout", self.timeout)
        r = requests.request(method, url, headers=self._headers(), **kwargs)
        if r.status_code >= 400:
            raise GoLoginAPIError(r.status_code, r.text)
        if not r.text:
            return {}
        try:
            return r.json()
        except ValueError:
            return {"raw": r.text}
    
    def _get(self, path, params=None):
        return self._request("GET", path, params=params)
    
    def _post(self, path, json=None, params=None):
        return self._request("POST", path, json=json, params=params)
    
    def _put(self, path, json=None):
        return self._request("PUT", path, json=json)
    
    def _delete(self, path, json=None, params=None):
        return self._request("DELETE", path, json=json, params=params)
    
    # Profile Management
    def list_profiles(self, page=1):
        """GET /browser/v2 -> danh sách profile"""
        data = self._get("/browser/v2", params={"page": page})
        if isinstance(data, dict):
            return data.get("profiles", data.get("browsers", []))
        return data if isinstance(data, list) else []
    
    def get_profile(self, profile_id):
        """GET /browser/{id}"""
        return self._get(f"/browser/{profile_id}")
    
    def create_quick_profile(self, name, os_type="win"):
        """POST /browser/quick -> tạo profile nhanh"""
        return self._post("/browser/quick", json={"name": name, "os": os_type})
    
    def create_custom_profile(self, params):
        """POST /browser/custom -> tạo profile tùy chỉnh"""
        return self._post("/browser/custom", json=params)
    
    def update_profile_custom(self, profile_id, params):
        """PUT /browser/{id}/custom -> cập nhật profile"""
        return self._put(f"/browser/{profile_id}/custom", json=params)
    
    def delete_profiles(self, profile_ids):
        """DELETE /browser -> xóa profile"""
        return self._delete("/browser", json={"ids": profile_ids})
    
    # Cloud Browser
    def run_profile_cloud(self, profile_id):
        """POST /browser/{id}/web -> chạy profile trên cloud, trả về URL kết nối"""
        return self._post(f"/browser/{profile_id}/web")
    
    def stop_profile_cloud(self, profile_id):
        """DELETE /browser/{id}/web -> dừng phiên cloud"""
        return self._delete(f"/browser/{profile_id}/web")
    
    def get_cloud_connect_url(self, profile_id=None):
        """URL để Puppeteer/Playwright connect_over_cdp()"""
        url = f"{CLOUD_BROWSER_BASE}/connect?token={self.token}"
        if profile_id:
            url += f"&profile={profile_id}"
        return url
