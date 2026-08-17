"""广州燃气微信小程序接口同步客户端

改写自 zoechancn/ha-component-guangzhou-gas 的异步 api.py（MIT），
改为同步 requests 实现，供命令行脚本使用。
"""
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import requests

from .const import (
    API_ARREARAGE_URL,
    API_BILL_DETAIL_URL,
    API_BILL_LIST_URL,
    API_GAS_DETAIL_URL,
    API_LOGIN_URL,
    API_METER_READING_LIST_URL,
    API_PAY_LIST_URL,
    API_USER_INFO_URL,
    DEFAULT_HEADERS,
)

_LOGGER = logging.getLogger(__name__)
REQUEST_TIMEOUT = 15


class GuangzhouGasAPIError(Exception):
    """API 错误基类"""


class GuangzhouGasAuthError(GuangzhouGasAPIError):
    """认证失败（token 无效/被拒）"""


class GuangzhouGasDataError(GuangzhouGasAPIError):
    """数据解析失败"""


class GuangzhouGasClient:
    """广州燃气微信小程序接口同步客户端"""

    def __init__(
        self,
        unionid: str,
        nickname: str,
        accept_key: str,
        session: requests.Session | None = None,
    ) -> None:
        self._unionid = unionid
        self._nickname = nickname
        self._accept_key = accept_key
        self._session = session or requests.Session()
        self._token: str | None = None

    def _headers(self, token: str | None = None) -> dict[str, str]:
        headers = {**DEFAULT_HEADERS, "unionid": self._unionid}
        if token:
            headers["accessToken"] = token
        return headers

    def _request(self, url: str, data: Mapping[str, str], token: str | None = None) -> dict[str, Any]:
        try:
            resp = self._session.post(
                url, data=dict(data), headers=self._headers(token), timeout=REQUEST_TIMEOUT
            )
        except requests.RequestException as err:
            raise GuangzhouGasAPIError(f"请求失败: {err}") from err
        if resp.status_code in {401, 403}:
            raise GuangzhouGasAuthError(f"认证被拒 (HTTP {resp.status_code})")
        if resp.status_code != 200:
            raise GuangzhouGasAPIError(f"HTTP {resp.status_code}")
        try:
            payload = resp.json()
        except ValueError as err:
            raise GuangzhouGasDataError(f"响应非 JSON: {resp.text[:200]!r}") from err
        if not isinstance(payload, dict):
            raise GuangzhouGasDataError("响应不是 JSON 对象")
        self._validate_response(payload)
        return payload

    @staticmethod
    def _validate_response(payload: Mapping[str, Any]) -> None:
        code = payload.get("code")
        errcode = payload.get("errcode")
        is_error = payload.get("error") is True
        successful = code in {None, 0, 200, "0", "200"} and errcode in {None, 0, "0"}
        if successful and not is_error:
            return
        message = str(
            payload.get("errmsg") or payload.get("msg") or payload.get("message") or "未知错误"
        )
        if any(w in message.lower() for w in ("认证", "登录", "token", "auth")):
            raise GuangzhouGasAuthError(message)
        raise GuangzhouGasAPIError(message)

    @staticmethod
    def _extract_record(value: Any, field: str) -> dict[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)
        if isinstance(value, list) and value and isinstance(value[0], Mapping):
            return dict(value[0])
        raise GuangzhouGasDataError(f"{field} 无可用记录")

    def login(self) -> str:
        """登录并保存 token"""
        resp = self._request(
            API_LOGIN_URL,
            {"nickName": self._nickname, "acceptKey": self._accept_key},
        )
        token = resp.get("data")
        if not isinstance(token, str) or not token:
            raise GuangzhouGasDataError("登录响应未包含 token")
        self._token = token
        return token

    def get_user_info(self) -> dict[str, Any]:
        """获取绑定的燃气账户信息"""
        if not self._token:
            self.login()
        resp = self._request(API_USER_INFO_URL, {}, token=self._token)
        data = resp.get("data")
        if not isinstance(data, Mapping):
            raise GuangzhouGasDataError("用户响应无 data 对象")
        return self._extract_record(data.get("wtVo"), "wtVo")

    def get_gas_detail(self, user_no: str) -> dict[str, Any]:
        """获取燃气表余额/用量/欠费/充值等详情"""
        if not self._token:
            self.login()
        resp = self._request(API_GAS_DETAIL_URL, {"userno": user_no}, token=self._token)
        data = resp.get("data")
        if not isinstance(data, Mapping):
            raise GuangzhouGasDataError("详情响应无 data 对象")
        meter = self._extract_record(data.get("rqbList"), "rqbList")
        return {**{k: v for k, v in data.items() if k != "rqbList"}, **meter}

    def get_bill_list(self, user_no: str, page: int = 1, rows: int = 20) -> dict[str, Any]:
        """获取用气账单列表"""
        if not self._token:
            self.login()
        resp = self._request(
            API_BILL_LIST_URL,
            {"userno": user_no, "page": str(page), "rows": str(rows)},
            token=self._token,
        )
        data = resp.get("data")
        if not isinstance(data, Mapping):
            raise GuangzhouGasDataError("账单列表响应无 data 对象")
        return dict(data)

    def get_bill_detail(self, user_no: str, fyjlid: str) -> dict[str, Any]:
        """获取用气账单详情"""
        if not self._token:
            self.login()
        resp = self._request(
            API_BILL_DETAIL_URL,
            {"userno": user_no, "fyjlid": fyjlid},
            token=self._token,
        )
        data = resp.get("data")
        if not isinstance(data, Mapping):
            raise GuangzhouGasDataError("账单详情响应无 data 对象")
        return dict(data)

    def get_meter_reading_list(self, user_no: str, page: int = 1, rows: int = 20) -> dict[str, Any]:
        """获取抄表记录列表"""
        if not self._token:
            self.login()
        resp = self._request(
            API_METER_READING_LIST_URL,
            {"userno": user_no, "page": str(page), "rows": str(rows)},
            token=self._token,
        )
        data = resp.get("data")
        if not isinstance(data, Mapping):
            raise GuangzhouGasDataError("抄表记录响应无 data 对象")
        return dict(data)

    def get_arrearage(self, user_no: str) -> dict[str, Any]:
        """获取欠费信息"""
        if not self._token:
            self.login()
        resp = self._request(
            API_ARREARAGE_URL,
            {"userno": user_no},
            token=self._token,
        )
        data = resp.get("data")
        if not isinstance(data, Mapping):
            raise GuangzhouGasDataError("欠费响应无 data 对象")
        return dict(data)

    def get_pay_list(self, user_no: str, year: int) -> list[dict[str, Any]]:
        """获取缴费记录列表"""
        if not self._token:
            self.login()
        resp = self._request(
            API_PAY_LIST_URL,
            {"userNo": user_no, "year": str(year)},
            token=self._token,
        )
        data = resp.get("data")
        if data is None:
            return []
        if isinstance(data, list):
            return [dict(item) for item in data if isinstance(item, Mapping)]
        raise GuangzhouGasDataError("缴费记录响应格式异常")

    def dump(self) -> dict[str, Any]:
        return {
            "unionid": self._unionid,
            "nickname": self._nickname,
            "accept_key": self._accept_key,
            "token": self._token,
        }

    @classmethod
    def load(cls, data: Mapping[str, Any]) -> "GuangzhouGasClient":
        c = cls(data["unionid"], data["nickname"], data["accept_key"])
        c._token = data.get("token")
        return c