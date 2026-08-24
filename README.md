# speedtest-ustc

中科大网络测速 CLI 工具。基于中国科学技术大学 LibreSpeed 测速机制，提供原生终端测速体验。

## 安装

```bash
pip install speedtest-ustc
```

开发模式：

```bash
git clone https://github.com/yourname/speedtest-ustc
cd speedtest-ustc
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 使用

```bash
# 默认测速（完整 UI）
speedtest ustc

# 简单文本输出
speedtest ustc --simple

# JSON 输出（可配合 jq 使用）
speedtest ustc --json

# 指定测速时长（秒）
speedtest ustc --time 5

# IPv6
speedtest ustc --ipv6

# 调试模式
speedtest ustc --debug
```

也可以用 `python -m speedtest ustc` 运行。

## CLI 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--time N` | 下载/上传测速时长（秒） | 10 |
| `--ping-count N` | Ping 次数 | 10 |
| `--json` | JSON 格式输出 | - |
| `--simple` | 简单文本输出 | - |
| `--debug` | 显示完整错误栈 | - |
| `--ipv4` | 使用 IPv4 | ✓ |
| `--ipv6` | 使用 IPv6 | - |

## 输出示例

### 默认模式

```
╭────────────────────────── 网络测速 ──────────────────────────╮
│          下载速度                 上传速度                 网络延迟          │
│        532.13 Mbps               35.38 Mbps                37.58 ms          │
│         66.52 MB/s                4.42 MB/s                 2.54 ms          │
│                                                                              │
│ 下载   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   532 Mbps │
│                                                                              │
│ 上传   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    35 Mbps │
│                                                                              │
│  丢包率   0.00%                        耗时     28.03s                       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### JSON 模式

```json
{
  "server": "中科大",
  "server_name": "中国科学技术大学",
  "ip": "123.10.133.99",
  "download": 532.13,
  "upload": 35.38,
  "ping": 37.58,
  "jitter": 2.54,
  "duration": 28.03,
  "unit": "Mbps"
}
```

### Simple 模式

```
Ping: 37.58 ms
Jitter: 2.54 ms
Download: 532.13 Mbps
Upload: 35.38 Mbps
```

## 测速原理

本工具复现 USTC 网页版 LibreSpeed 的测速流程：

1. **初始化** — 访问主页获取 `ustc=1` cookie
2. **获取 IP** — 通过 `getIP.php` 获取客户端公网 IP
3. **PoW 验证** — SHA-256 Proof of Work 防滥用机制
4. **Ping 测试** — 10 次 HTTP GET，取最小 RTT
5. **Jitter** — 加权移动平均算法（与 LibreSpeed 一致）
6. **下载测试** — 6 路并发流持续下载，时间型测速
7. **上传测试** — 3 路并发流持续上传随机数据

速度计算：`Mbps = (bytes × 8 / elapsed / 1,000,000) × 1.06`

其中 1.06 为 LibreSpeed 的传输层开销补偿因子。

## 技术栈

- **Python 3.10+**
- **httpx** — 异步 HTTP 客户端，连接池，流式下载
- **rich** — 终端 UI，进度条，面板渲染

## 项目结构

```
speedtest-ustc/
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── speedtest/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py          # CLI 入口
│   ├── config.py       # 常量配置
│   ├── models.py       # 数据模型
│   ├── client.py       # HTTP 客户端
│   ├── engine.py       # 流程编排
│   ├── pow.py          # PoW 求解器
│   ├── ping.py         # Ping/Jitter
│   ├── download.py     # 下载测速
│   ├── upload.py       # 上传测速
│   └── ui.py           # Rich UI
└── tests/
    ├── test_pow.py
    ├── test_ping.py
    ├── test_speed.py
    └── test_format.py
```

## USTC 后端

测速服务器位于中国科学技术大学网络空间安全学院。

- IPv4: `https://test.ustc.edu.cn/`
- IPv6: `https://test6.ustc.edu.cn/`

## 开发

```bash
# 安装依赖
pip install -e .

# 运行测试
python -m pytest tests/ -v

# 运行测速
python -m speedtest ustc
```

## License

MIT
