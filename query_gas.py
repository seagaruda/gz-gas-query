#!/usr/bin/env python3
"""
广州燃气账户查询脚本

通过广州燃气微信小程序接口（wxxcx.gzgas.com）查询：
  - 当前燃气表余额、阶梯用量、欠费、抄表读数等
  - 用气账单列表（按抄表周期）
  - 账单详情（含单价、读数、缴费状态）
  - 抄表记录列表
  - 欠费信息
  - 缴费记录

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


def print_account(info: dict) -> None:
    print(f"\n{'=' * 60}")
    print("  广州燃气账户当前状态")
    print(f"{'=' * 60}")
    print(f"  用户编号: {_fmt(info.get('userNo'))}")
    print(f"  户名: {_fmt(info.get('userName'))}")
    print(f"  地址: {_fmt(info.get('userAddress'))}")
    print(f"  燃气公司: {_fmt(info.get('bmmc'))}")
    print(f"{'=' * 60}")

    rows = [
        ("表类型", info.get("blx")),
        ("表型号", info.get("rqb_ms")),
        ("表状态", info.get("rqbztdes")),
        ("账户余额(元)", info.get("dqye")),
        ("欠费状态", info.get("feeFlag")),
        ("欠费金额(元)", info.get("feeMoney")),
        ("阶梯周期用量(m³)", info.get("jieti_amount_benci")),
        ("阶梯周期", info.get("jieti_interval")),
        ("上次抄表读数", info.get("lastRecordWatchNum")),
        ("上次抄表日期", info.get("lastRecordWatchDate")),
        ("缴费方式", info.get("feeWay")),
        ("安检日期", info.get("safeInspectDate")),
        ("安检结果", info.get("safeInspectHas")),
    ]
    print(f"{'项目':<22}{'值':>36}")
    print("-" * 60)
    for name, val in rows:
        print(f"{name:<22}{_fmt(val):>36}")
    print(f"{'=' * 60}\n")


def print_bill_list(data: dict) -> None:
    bills = data.get("bill", [])
    year = data.get("year", "")
    print(f"\n{'=' * 60}")
    print(f"  用气账单列表 ({year}年)")
    print(f"{'=' * 60}")
    if not bills:
        print("  无账单记录")
        print(f"{'=' * 60}\n")
        return
    print(f"{'序号':<6}{'抄表周期':<28}{'用量(m³)':>10}{'金额(元)':>12}{'账单编号':>16}")
    print("-" * 72)
    for i, b in enumerate(bills, 1):
        print(f"{i:<6}{_fmt(b.get('desc')):<28}{_fmt(b.get('byyql')):>10}"
              f"{_fmt(b.get('total')):>12}{_fmt(b.get('fyjlid')):>16}")
    print(f"{'=' * 72}")
    print(f"  共 {len(bills)} 条记录（用 --detail <账单编号> 查看详情）\n")


def print_bill_detail(data: dict) -> None:
    print(f"\n{'=' * 60}")
    print("  用气账单详情")
    print(f"{'=' * 60}")
    print(f"  费用总额(元): {_fmt(data.get('amount'))}")
    print(f"  本期用量(m³): {_fmt(data.get('monthYql'))}")
    for group in data.get("billDetailList", []):
        print(f"\n  类型: {_fmt(group.get('type'))}  小计: {_fmt(group.get('total'))}元")
        for item in group.get("list", []):
            print(f"{'-' * 56}")
            rows = [
                ("费用项目", item.get("fyxmmc")),
                ("单价(元/m³)", item.get("fyjldj")),
                ("用量(m³)", item.get("fyjlsl")),
                ("上次读数", item.get("scbd")),
                ("本次读数", item.get("bcbd")),
                ("抄表日期", item.get("cbrq")),
                ("上次抄表", item.get("sccbrq")),
                ("缴费状态", item.get("jfstatus")),
                ("实缴金额(元)", item.get("sjjfe")),
                ("缴费日期", item.get("sjjfrq")),
                ("账单编号", item.get("fyjlid")),
            ]
            for name, val in rows:
                print(f"  {name:<16}{_fmt(val)}")
    print(f"{'=' * 60}\n")


def print_meter_readings(data: dict) -> None:
    meters = data.get("meter", [])
    year = data.get("year", "")
    print(f"\n{'=' * 60}")
    print(f"  抄表记录列表 ({year}年)")
    print(f"{'=' * 60}")
    if not meters:
        print("  无抄表记录")
        print(f"{'=' * 60}\n")
        return
    print(f"{'序号':<6}{'抄表日期':<22}{'上次读数':>8}{'本次读数':>8}"
          f"{'用量(m³)':>10}{'金额(元)':>10}")
    print("-" * 64)
    for i, m in enumerate(meters, 1):
        print(f"{i:<6}{_fmt(m.get('cbrq')):<22}{_fmt(m.get('scbds')):>8}"
              f"{_fmt(m.get('bdbds')):>8}{_fmt(m.get('bcyql')):>10}"
              f"{_fmt(m.get('yje')):>10}")
    print(f"{'=' * 64}")
    print(f"  共 {len(meters)} 条记录\n")


def print_arrearage(data: dict) -> None:
    print(f"\n{'=' * 60}")
    print("  欠费信息")
    print(f"{'=' * 60}")
    print(f"  欠费期数: {_fmt(data.get('dqsNum'))}")
    print(f"  待扣金额(元): {_fmt(data.get('dk'))}")
    print(f"  违约金(元): {_fmt(data.get('wyj'))}")
    fy_list = data.get("fyList")
    if fy_list:
        print(f"\n  费用明细:")
        for item in fy_list:
            print(f"    {item}")
    owe = data.get("oweInfo", {})
    if owe and owe.get("records"):
        print(f"\n  欠费记录:")
        for rec in owe["records"]:
            print(f"    {rec}")
    print(f"{'=' * 60}\n")


def print_pay_list(records: list, year: int) -> None:
    print(f"\n{'=' * 60}")
    print(f"  缴费记录 ({year}年)")
    print(f"{'=' * 60}")
    if not records:
        print("  无缴费记录")
        print(f"{'=' * 60}\n")
        return
    print(json.dumps(records, ensure_ascii=False, indent=2))
    print(f"\n  共 {len(records)} 条记录\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="广州燃气账户查询（微信小程序接口）")
    ap.add_argument("--config", type=Path, metavar="PATH",
                    help=f"凭证配置文件 JSON（默认 {DEFAULT_CONFIG.name}）")
    ap.add_argument("--json", action="store_true", help="输出原始 JSON 响应")
    ap.add_argument("--bill", action="store_true", help="查询用气账单列表")
    ap.add_argument("--detail", metavar="FYJLID", help="查询指定账单详情（账单编号）")
    ap.add_argument("--meter", action="store_true", help="查询抄表记录列表")
    ap.add_argument("--arrearage", action="store_true", help="查询欠费信息")
    ap.add_argument("--pay", action="store_true", help="查询缴费记录")
    ap.add_argument("--year", type=int, default=None, help="缴费记录年份（配合 --pay）")
    ap.add_argument("--page", type=int, default=1, help="分页页码（默认 1）")
    ap.add_argument("--rows", type=int, default=20, help="每页条数（默认 20）")
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
    except GuangzhouGasAuthError as e:
        sys.exit(f"认证失败: {e}（凭证可能已过期，请重新抓包获取）")
    except GuangzhouGasAPIError as e:
        sys.exit(f"接口错误: {e}")

    detail = {}
    try:
        detail = client.get_gas_detail(user_no)
    except GuangzhouGasAPIError as e:
        print(f"[提示] 燃气表详情接口不可用: {e}（使用基础用户信息展示）")

    info = {**user_info, **detail}

    if args.json and not any([args.bill, args.detail, args.meter, args.arrearage, args.pay]):
        print("\n--- user_info ---")
        print(json.dumps(user_info, ensure_ascii=False, indent=2))
        if detail:
            print("\n--- gas_detail ---")
            print(json.dumps(detail, ensure_ascii=False, indent=2))
        return

    if not any([args.bill, args.detail, args.meter, args.arrearage, args.pay]):
        print_account(info)

    if args.bill:
        try:
            data = client.get_bill_list(user_no, page=args.page, rows=args.rows)
            if args.json:
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                print_bill_list(data)
        except GuangzhouGasAPIError as e:
            print(f"[用气账单] {e}")

    if args.detail:
        try:
            data = client.get_bill_detail(user_no, args.detail)
            if args.json:
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                print_bill_detail(data)
        except GuangzhouGasAPIError as e:
            print(f"[账单详情] {e}")

    if args.meter:
        try:
            data = client.get_meter_reading_list(user_no, page=args.page, rows=args.rows)
            if args.json:
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                print_meter_readings(data)
        except GuangzhouGasAPIError as e:
            print(f"[抄表记录] {e}")

    if args.arrearage:
        try:
            data = client.get_arrearage(user_no)
            if args.json:
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                print_arrearage(data)
        except GuangzhouGasAPIError as e:
            print(f"[欠费信息] {e}")

    if args.pay:
        import datetime as dt
        year = args.year or dt.datetime.now().year
        try:
            records = client.get_pay_list(user_no, year)
            if args.json:
                print(json.dumps(records, ensure_ascii=False, indent=2))
            else:
                print_pay_list(records, year)
        except GuangzhouGasAPIError as e:
            print(f"[缴费记录] {e}")


if __name__ == "__main__":
    main()
