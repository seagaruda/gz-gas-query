#!/usr/bin/env python3
"""
广州燃气账户查询脚本

通过广州燃气微信小程序接口（wxxcx.gzgas.com）查询当前燃气表
余额、阶梯用量、欠费、上次抄表读数、充值记录等。

登录凭证为微信小程序抓包所得的 unionid / nickname / acceptKey
（长期有效，非一次性验证码），通过环境变量或配置文件传入，
无需交互输入。

依赖: requests
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gz_gas_client import (  # noqa: E402
    GuangzhouGasAPIError,
    GuangzhouGasAuthError,
    GuangzhouGasClient,
)

DEFAULT_CONFIG = Path(__file__).resolve().parent / "credentials.json"


def load_credentials(config_path: Path | None) -> tuple[str, str, str]:
    unionid = os.getenv("GZ_GAS_UNIONID")
    nickname = os.getenv("GZ_GAS_NICKNAME")
    accept_key = os.getenv("GZ_GAS_ACCEPT_KEY")
    if unionid and nickname and accept_key:
        return unionid, nickname, accept_key
    path = config_path or DEFAULT_CONFIG
    if not path.is_file():
        sys.exit(
            f"未找到凭证。请通过环境变量 GZ_GAS_UNIONID / GZ_GAS_NICKNAME / "
            f"GZ_GAS_ACCEPT_KEY 提供，或写入配置文件 {path}（格式见 README）。"
        )
    cfg = json.loads(path.read_text(encoding="utf-8"))
    unionid = unionid or cfg.get("unionid")
    nickname = nickname or cfg.get("nickname")
    accept_key = accept_key or cfg.get("accept_key")
    if not (unionid and nickname and accept_key):
        sys.exit(f"配置文件 {path} 缺少 unionid/nickname/accept_key 字段")
    return unionid, nickname, accept_key


def _fmt(v) -> str:
    if v is None:
        return "N/A"
    if isinstance(v, str) and v.strip() in ("", "null", "None", "--"):
        return "N/A"
    return str(v)


def print_account(user_info: dict, detail: dict) -> None:
    print(f"\n{'=' * 60}")
    print("  广州燃气账户当前状态")
    print(f"{'=' * 60}")
    user_no = user_info.get("userNo") or user_info.get("userno") or detail.get("userno")
    print(f"  用户编号: {_fmt(user_no)}")
    print(f"  户名: {_fmt(user_info.get('userName') or user_info.get('username'))}")
    print(f"  地址: {_fmt(user_info.get('address') or user_info.get('userAddr'))}")
    print(f"{'=' * 60}")

    rows = [
        ("账户余额(元)", detail.get("dqye")),
        ("欠费状态", detail.get("feeFlag")),
        ("欠费金额(元)", detail.get("qfje")),
        ("阶梯周期用气量(m³)", detail.get("jtzqyl") or detail.get("ladderUsed")),
        ("阶梯周期", detail.get("jtzq") or detail.get("billingCycle")),
        ("上次抄表读数", detail.get("lastRecordWatchNum")),
        ("上次抄表日期", detail.get("lastRecordWatchDate")),
        ("最近充值金额(元)", detail.get("czje") or detail.get("lastChargeAmount")),
        ("最近充值时间", detail.get("czsj") or detail.get("lastChargeTime")),
        ("表具状态", detail.get("bjzt") or detail.get("meterStatus")),
        ("表号", detail.get("bh") or detail.get("meterNo")),
    ]
    print(f"{'项目':<22}{'值':>36}")
    print("-" * 60)
    for name, val in rows:
        print(f"{name:<22}{_fmt(val):>36}")
    print(f"{'=' * 60}\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="广州燃气账户查询（微信小程序接口）")
    ap.add_argument("--config", type=Path, metavar="PATH",
                    help=f"凭证配置文件 JSON（默认 {DEFAULT_CONFIG.name}）")
    ap.add_argument("--json", action="store_true", help="输出原始 JSON 响应")
    ap.add_argument("--month", type=int, metavar="MM",
                    help="查询月度账单（预留，需补全接口后可用）")
    ap.add_argument("--year", type=int, default=None, help="月度账单年份（配合 --month）")
    args = ap.parse_args()

    unionid, nickname, accept_key = load_credentials(args.config)
    client = GuangzhouGasClient(unionid, nickname, accept_key)

    try:
        token = client.login()
        print(f"登录成功，token 前12位: {token[:12]}...")
        user_info = client.get_user_info()
        user_no = user_info.get("userNo") or user_info.get("userno")
        if not user_no:
            if args.json:
                print("user_info 原始:", json.dumps(user_info, ensure_ascii=False, indent=2))
            sys.exit("未能从用户信息中提取 userNo，请用 --json 查看原始响应")
        detail = client.get_gas_detail(user_no)
    except GuangzhouGasAuthError as e:
        sys.exit(f"认证失败: {e}（凭证可能已过期，请重新抓包获取）")
    except GuangzhouGasAPIError as e:
        sys.exit(f"接口错误: {e}")

    if args.json:
        print("\n--- user_info ---")
        print(json.dumps(user_info, ensure_ascii=False, indent=2))
        print("\n--- gas_detail ---")
        print(json.dumps(detail, ensure_ascii=False, indent=2))
        return

    print_account(user_info, detail)

    if args.month:
        import datetime as dt
        year = args.year or dt.datetime.now().year
        try:
            bill = client.get_monthly_bill(user_no, year, args.month)
            print(f"\n{year}-{args.month:02d} 月度账单:")
            print(json.dumps(bill, ensure_ascii=False, indent=2))
        except NotImplementedError as e:
            print(f"[月度账单] {e}")


if __name__ == "__main__":
    main()