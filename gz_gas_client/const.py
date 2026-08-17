"""广州燃气微信小程序接口常量（取自 zoechancn/ha-component-guangzhou-gas, MIT）"""

API_BASE_URL = "https://wxxcx.gzgas.com/ydeq/min"
API_LOGIN_URL = f"{API_BASE_URL}/login/getToken.action"
API_USER_INFO_URL = f"{API_BASE_URL}/bind/getUserByShowIndex.action"
API_GAS_DETAIL_URL = f"{API_BASE_URL}/order/getBiaoDetail.action"
API_BILL_LIST_URL = f"{API_BASE_URL}/ebill/getBillList.action"
API_BILL_DETAIL_URL = f"{API_BASE_URL}/ebill/getBillDetail.action"
API_METER_READING_LIST_URL = f"{API_BASE_URL}/ebill/getCbList.action"
API_ARREARAGE_URL = f"{API_BASE_URL}/order/getArrearage.action"
API_PAY_LIST_URL = f"{API_BASE_URL}/order/getPayList.action"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 "
        "Safari/537.36 MicroMessenger/7.0.20.1781 MiniProgramEnv/Windows"
    ),
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://servicewechat.com/wx6a4fd0ebb4a12c11/366/page-frame.html",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "xweb_xhr": "1",
}