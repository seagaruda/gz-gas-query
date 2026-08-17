# GZ Gas Account Query | 广州燃气账户查询

[English](#english) | [中文](#中文)

---

## 中文

查询**广州燃气**个人账户的当前状态：燃气表余额、阶梯周期用气量、欠费、上次抄表读数、充值记录等。月度历史账单为预留扩展点（见下）。

> ⚠️ **免责声明**：本项目通过广州燃气微信小程序后端接口（`wxxcx.gzgas.com`）获取数据，**非官方公开 API**，与广州燃气集团有限公司无关。仅供个人查询本人绑定账户，请勿用于商业用途或大规模抓取。使用风险自负。

### 与南方电网项目的差异

| | 南方电网 | 本项目（广州燃气） |
|---|---|---|
| 接口端 | 网页端 95598.csg.cn | 微信小程序 wxxcx.gzgas.com |
| 登录 | 手机号+短信 | 微信抓包凭证 unionid/acceptKey/nickname |
| 月度账单 | ✅ 有 | ❌ 现接口无，预留扩展点 |

### 功能

- 当前燃气表余额、欠费状态/金额
- 阶梯周期用气量、阶梯周期
- 上次抄表读数/日期
- 最近充值金额/时间、表具状态、表号
- 原始 JSON 输出（便于发现字段）
- 月度账单接口预留（`get_monthly_bill`，待抓包补全）

### 依赖

- Python ≥ 3.10
- `requests`

```bash
pip install -r requirements.txt
```

### 凭证获取（一次性，抓包）

广州燃气接口是微信小程序，登录需三个微信侧凭证。用 Charles / Fiddler / mitmproxy 抓包「广州燃气」微信小程序的登录请求：

```text
POST https://wxxcx.gzgas.com/ydeq/min/login/getToken.action
```

从请求中取出 `nickName`、`acceptKey`（表单字段）和 `unionid`（请求头）。这三个凭证长期有效，保存好即可反复用。

### 快速开始

```bash
git clone https://github.com/seagaruda/gz-gas-query.git
cd gz-gas-query
pip install -r requirements.txt

# 方式 A：环境变量
export GZ_GAS_UNIONID=你的unionid
export GZ_GAS_NICKNAME=你的nickName
export GZ_GAS_ACCEPT_KEY=你的acceptKey
python3 query_gas.py

# 方式 B：配置文件（默认 credentials.json，已被 .gitignore 排除）
cat > credentials.json <<'EOF'
{"unionid": "...", "nickname": "...", "accept_key": "..."}
EOF
python3 query_gas.py
```

### 用法

```bash
python3 query_gas.py                 # 查询当前账户状态
python3 query_gas.py --json          # 输出原始 JSON（查看全部字段）
python3 query_gas.py --config my.json  # 指定凭证文件
python3 query_gas.py --month 7       # 月度账单（预留，目前会提示未实现）
```

### 月度账单扩展点

现有广州燃气小程序接口仅返回**当前**余额/用量，无按月历史账单。若你抓包找到了月度账单接口，实现步骤：

1. 在 `gz_gas_client/const.py` 添加接口 URL
2. 在 `gz_gas_client/__init__.py` 的 `get_monthly_bill` 方法内实现请求与解析
3. `python3 query_gas.py --year 2026 --month 7` 即可调用

欢迎以 PR 形式贡献。

### 隐私与安全

- 凭证 `unionid`/`acceptKey`/`nickname` 为微信侧长期凭证，**仅在本地**通过环境变量或配置文件传入，不经过任何第三方或 AI
- `credentials.json` 已被 `.gitignore` 排除，切勿提交或分享
- 凭证失效时重新抓包即可
- 若通过 AI agent 使用：让 AI 克隆/运行查询，但**凭证请自己在本地配置**，不要发给 AI

### 致谢

- [zoechancn/ha-component-guangzhou-gas](https://github.com/zoechancn/ha-component-guangzhou-gas) — 核心接口封装（MIT，本项目基于其改写为同步命令行版）

### 许可证

MIT

---

## English

Query **Guangzhou Gas** residential account current status: meter balance, tiered-period usage, arrears, last meter reading, recharge records, etc. Monthly historical bills are a reserved extension point (see below).

> ⚠️ **Disclaimer**: This project uses the Guangzhou Gas WeChat mini-program backend (`wxxcx.gzgas.com`), which is **NOT an official public API** and is not affiliated with Guangzhou Gas Group. Use only to query your own bound account. Do not use for commercial purposes or large-scale scraping. Use at your own risk.

### Differences from the CSG project

| | CSG (sibling project) | This project (GZ Gas) |
|---|---|---|
| Endpoint | web 95598.csg.cn | WeChat mini-program wxxcx.gzgas.com |
| Login | phone + SMS | WeChat-captured unionid/acceptKey/nickname |
| Monthly bill | ✅ available | ❌ not in current API, reserved extension |

### Features

- Current meter balance, arrears status/amount
- Tiered-period usage, billing cycle
- Last meter reading value/date
- Last recharge amount/time, meter status, meter number
- Raw JSON output (to discover fields)
- Monthly bill interface reserved (`get_monthly_bill`, pending capture)

### Requirements

- Python ≥ 3.10
- `requests`

```bash
pip install -r requirements.txt
```

### Obtaining credentials (one-time, via packet capture)

The Guangzhou Gas API is a WeChat mini-program. Login requires three WeChat-side credentials. Use Charles / Fiddler / mitmproxy to capture the login request of the「广州燃气」WeChat mini-program:

```text
POST https://wxxcx.gzgas.com/ydeq/min/login/getToken.action
```

Extract `nickName`, `acceptKey` (form fields) and `unionid` (request header). These are long-lived; save them for reuse.

### Quick Start

```bash
git clone https://github.com/seagaruda/gz-gas-query.git
cd gz-gas-query
pip install -r requirements.txt

# Option A: env vars
export GZ_GAS_UNIONID=...
export GZ_GAS_NICKNAME=...
export GZ_GAS_ACCEPT_KEY=...
python3 query_gas.py

# Option B: config file (default credentials.json, gitignored)
cat > credentials.json <<'EOF'
{"unionid": "...", "nickname": "...", "accept_key": "..."}
EOF
python3 query_gas.py
```

### Usage

```bash
python3 query_gas.py                 # query current account status
python3 query_gas.py --json          # raw JSON output (inspect all fields)
python3 query_gas.py --config my.json  # specify credential file
python3 query_gas.py --month 7       # monthly bill (reserved, currently NotImplemented)
```

### Monthly bill extension point

The current Guangzhou Gas mini-program API returns only **current** balance/usage, no monthly history. If you capture a monthly-bill endpoint:

1. Add the URL to `gz_gas_client/const.py`
2. Implement the request/parsing in `get_monthly_bill` in `gz_gas_client/__init__.py`
3. Run `python3 query_gas.py --year 2026 --month 7`

PRs welcome.

### Privacy & security

- Credentials `unionid`/`acceptKey`/`nickname` are long-lived WeChat-side secrets, passed **locally only** via env vars or config file, never through any third party or AI
- `credentials.json` is excluded by `.gitignore` — never commit or share
- Re-capture when credentials expire
- If using an AI agent: let it clone/run queries, but **configure credentials yourself locally**; don't send them to the AI

### Credits

- [zoechancn/ha-component-guangzhou-gas](https://github.com/zoechancn/ha-component-guangzhou-gas) — core API client (MIT; this project rewrites it as a synchronous CLI)

### License

MIT