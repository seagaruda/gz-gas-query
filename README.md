# GZ Gas Account Query | 广州燃气账户查询

[English](#english) | [中文](#中文)

---

## 中文

查询**广州燃气**个人账户的当前状态与历史记录：燃气表余额、阶梯周期用气量、欠费、上次抄表读数，以及**用气账单列表**、**账单详情**、**抄表记录**、**欠费信息**、**缴费记录**。

> ⚠️ **免责声明**：本项目通过广州燃气微信小程序后端接口（`wxxcx.gzgas.com`）获取数据，**非官方公开 API**，与广州燃气集团有限公司无关。仅供个人查询本人绑定账户，请勿用于商业用途或大规模抓取。使用风险自负。

### 与南方电网项目的差异

| | 南方电网 | 本项目（广州燃气） |
|---|---|---|
| 接口端 | 网页端 95598.csg.cn | 微信小程序 wxxcx.gzgas.com |
| 登录 | 手机号+短信 | 微信抓包凭证 unionid/acceptKey/nickname |
| 月度账单 | ✅ 有 | ✅ 用气账单列表+详情 |

### 功能

- 当前燃气表余额、欠费状态/金额
- 阶梯周期用气量、阶梯周期
- 上次抄表读数/日期
- 最近充值金额/时间、表具状态、表号
- **用气账单列表**（按抄表周期，含用量/金额/账单编号）
- **账单详情**（含单价、上下次读数、缴费状态/日期）
- **抄表记录列表**（含抄表日期、上次/本次读数、用量、金额）
- **欠费信息**（欠费期数、待扣金额、违约金）
- **缴费记录**（按年查询）
- 原始 JSON 输出（便于发现字段）

### 依赖

- Python ≥ 3.10
- `requests`

```bash
pip install -r requirements.txt
```

### 凭证获取（一次性，PC 抓包）

广州燃气接口是**微信小程序**，登录需三个微信侧凭证：`unionid`（请求头）、`nickName` 和 `acceptKey`（表单字段）。这三个凭证长期有效，抓一次即可反复用。

**能在电脑上抓吗？** 能。Windows / Mac 版 PC 微信都支持打开小程序，配合抓包工具即可，比手机抓包简单得多。

#### 步骤（以 mitmproxy 为例，免费跨平台）

1. **装抓包工具**（任选其一）：
   - `mitmproxy`（推荐，免费命令行）：`pip install mitmproxy` 或 `brew install mitmproxy`
   - `Charles`（Mac/Win，付费有 30 天试用，界面友好）
   - `Fiddler Classic`（Win，免费，界面友好）

2. **启动并配置 SSL 证书**（首次需要，否则 HTTPS 只能看到密文）：
   ```bash
   mitmweb --listen-port 8888          # 启动，会自动打开浏览器面板
   ```
   - mitmproxy：访问 `http://mitm.it` 下载证书并安装到系统，设为始终信任
   - Charles：菜单 Help → SSL Proxying → Install Charles Root Certificate
   - Fiddler：Tools → Options → HTTPS → Decrypt HTTPS → 信任证书

3. **设置系统代理**指向抓包工具（端口 8888）：
   - Mac：系统设置 → 网络 → 代理 → Web/安全代理 `127.0.0.1:8888`
   - Win：设置 → 网络 → 代理 → `127.0.0.1:8888`
   - Charles/Fiddler 会自动帮你设系统代理

4. **打开 PC 微信，进入「广州燃气」小程序**：
   - 微信左侧栏 → 小程序面板 → 搜索「广州燃气」→ 打开
   - 小程序加载时会自动发起登录请求

5. **在抓包工具里找到登录请求**：
   ```
   POST https://wxxcx.gzgas.com/ydeq/min/login/getToken.action
   ```
   - mitmproxy：在面板按 `f` 过滤 `~u gzgas.com`，找到该 POST
   - 查看请求头 `unionid`，查看表单 `nickName`、`acceptKey`

6. **取出三个凭证**，配置到本脚本（见快速开始）。抓完可关闭代理和工具。

#### 常见问题

- **抓不到 HTTPS 明文**：证书没装好/没信任，重做第 2 步
- **PC 微信打不开小程序**：确保微信版本足够新；部分企业版微信禁用小程序，换个人版
- **证书 pinning**：微信核心接口有 pinning，但**小程序业务接口（gzgas.com）一般可抓**；若被拒换用 Fiddler 或手机抓包
- **凭证失效**：`acceptKey` 可能数天到数周过期，重新抓一次登录请求即可

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
python3 query_gas.py                          # 查询当前账户状态
python3 query_gas.py --bill                   # 用气账单列表
python3 query_gas.py --detail <账单编号>       # 账单详情（编号从 --bill 获取）
python3 query_gas.py --meter                  # 抄表记录列表
python3 query_gas.py --arrearage              # 欠费信息
python3 query_gas.py --pay --year 2026        # 缴费记录
python3 query_gas.py --bill --meter           # 可组合多个查询
python3 query_gas.py --json                   # 输出原始 JSON
python3 query_gas.py --config my.json         # 指定凭证文件
```


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

Query **Guangzhou Gas** residential account status and history: meter balance, tiered-period usage, arrears, last meter reading, plus **bill list**, **bill detail**, **meter reading records**, **arrearage info**, and **payment records**.

> ⚠️ **Disclaimer**: This project uses the Guangzhou Gas WeChat mini-program backend (`wxxcx.gzgas.com`), which is **NOT an official public API** and is not affiliated with Guangzhou Gas Group. Use only to query your own bound account. Do not use for commercial purposes or large-scale scraping. Use at your own risk.

### Differences from the CSG project

| | CSG (sibling project) | This project (GZ Gas) |
|---|---|---|
| Endpoint | web 95598.csg.cn | WeChat mini-program wxxcx.gzgas.com |
| Login | phone + SMS | WeChat-captured unionid/acceptKey/nickname |
| Monthly bill | ✅ available | ✅ bill list + detail |

### Features

- Current meter balance, arrears status/amount
- Tiered-period usage, billing cycle
- Last meter reading value/date
- Last recharge amount/time, meter status, meter number
- **Bill list** (by meter-reading cycle, with usage/amount/bill ID)
- **Bill detail** (unit price, prev/next reading, payment status/date)
- **Meter reading records** (date, prev/next reading, usage, amount)
- **Arrearage info** (arrears periods, pending deduction, penalty)
- **Payment records** (by year)
- Raw JSON output (to discover fields)

### Requirements

- Python ≥ 3.10
- `requests`

```bash
pip install -r requirements.txt
```

### Obtaining credentials (one-time, PC packet capture)

The Guangzhou Gas API is a **WeChat mini-program**. Login needs three WeChat-side credentials: `unionid` (request header), `nickName` and `acceptKey` (form fields). They are long-lived; capture once and reuse.

**Can I capture on a PC?** Yes. Windows / Mac WeChat desktop clients can open mini-programs, which makes PC capture far easier than phone capture.

#### Steps (mitmproxy example, free & cross-platform)

1. **Install a capture tool** (any one):
   - `mitmproxy` (recommended, free CLI): `pip install mitmproxy` or `brew install mitmproxy`
   - `Charles` (Mac/Win, paid 30-day trial, friendly UI)
   - `Fiddler Classic` (Win, free, friendly UI)

2. **Start and trust the SSL cert** (first time only, otherwise HTTPS stays encrypted):
   ```bash
   mitmweb --listen-port 8888          # starts and opens a web panel
   ```
   - mitmproxy: visit `http://mitm.it`, download & install the cert, mark as always-trusted
   - Charles: Help → SSL Proxying → Install Charles Root Certificate
   - Fiddler: Tools → Options → HTTPS → Decrypt HTTPS → trust cert

3. **Set system proxy** to the tool (port 8888):
   - Mac: System Settings → Network → Proxy → Web/Secure `127.0.0.1:8888`
   - Win: Settings → Network → Proxy → `127.0.0.1:8888`
   - Charles/Fiddler auto-configure the system proxy for you

4. **Open PC WeChat → enter the「广州燃气」mini-program**:
   - WeChat sidebar → mini-program panel → search「广州燃气」→ open
   - Loading the mini-program triggers the login request automatically

5. **Find the login request in the capture tool**:
   ```
   POST https://wxxcx.gzgas.com/ydeq/min/login/getToken.action
   ```
   - mitmproxy: press `f` in the panel, filter `~u gzgas.com`, locate the POST
   - Read request header `unionid`, form fields `nickName` and `acceptKey`

6. **Save the three credentials** into the script (see Quick Start). Close the proxy/tool when done.

#### Troubleshooting

- **HTTPS still encrypted**: cert not installed/trusted — redo step 2
- **PC WeChat can't open mini-programs**: update WeChat; some enterprise builds disable them, use personal WeChat
- **Cert pinning**: WeChat core endpoints use pinning, but **mini-program business endpoints (gzgas.com) are usually capturable**; if blocked, try Fiddler or phone capture
- **Credentials expired**: `acceptKey` may expire in days/weeks — re-capture the login request

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
python3 query_gas.py                          # query current account status
python3 query_gas.py --bill                   # bill list
python3 query_gas.py --detail <bill_id>       # bill detail (ID from --bill)
python3 query_gas.py --meter                  # meter reading records
python3 query_gas.py --arrearage              # arrearage info
python3 query_gas.py --pay --year 2026        # payment records
python3 query_gas.py --bill --meter           # combine multiple queries
python3 query_gas.py --json                   # raw JSON output
python3 query_gas.py --config my.json         # specify credential file
```

### Privacy & security

- Credentials `unionid`/`acceptKey`/`nickname` are long-lived WeChat-side secrets, passed **locally only** via env vars or config file, never through any third party or AI
- `credentials.json` is excluded by `.gitignore` — never commit or share
- Re-capture when credentials expire
- If using an AI agent: let it clone/run queries, but **configure credentials yourself locally**; don't send them to the AI

### Credits

- [zoechancn/ha-component-guangzhou-gas](https://github.com/zoechancn/ha-component-guangzhou-gas) — core API client (MIT; this project rewrites it as a synchronous CLI)

### License

MIT