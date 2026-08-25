# speedtest-ustc

中科大网络测速 CLI 工具。基于中国科学技术大学 LibreSpeed 测速机制，提供原生终端测速体验。

## 安装

### Homebrew（macOS 推荐）

```bash
brew tap Nanako718/tap
brew install speedtest-ustc
```

### pip 安装（需要 Python 3.10+）

```bash
pip install speedtest-ustc
```

## 使用

```bash
# 直接测速
speedtest-ustc

# 简单文本输出
speedtest-ustc --simple

# JSON 输出
speedtest-ustc --json

# 指定测速时长（秒）
speedtest-ustc --time 5

# IPv6
speedtest-ustc --ipv6

# 查看版本
speedtest-ustc --version
```

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
| `--version` | 显示版本号 | - |

## 输出示例

### 默认模式

```
╭────────────────────────────── ✓ TEST COMPLETE ───────────────────────────────╮
│          下载速度                 上传速度                 网络延迟          │
│        511.66 Mbps               53.10 Mbps                35.79 ms          │
│         63.96 MB/s                6.64 MB/s                 1.22 ms          │
│                                                                              │
│ 下载   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   512 Mbps │
│                                                                              │
│ 上传   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    53 Mbps │
│                                                                              │
│  丢包率   0.00%                        耗时     27.07s                       │
│                                                                              │
│  服务器   中科大                       IP       202.38.64.43                 │
│  位置     中国 · 安徽 · 合肥           ISP      USTC                         │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### JSON 模式

```json
{
  "server": "中科大",
  "server_name": "中国科学技术大学",
  "ip": "123.10.133.99",
  "server_ip": "202.38.64.43",
  "server_location": "中国 · 安徽 · 合肥",
  "server_isp": "USTC",
  "download": 511.66,
  "upload": 53.10,
  "ping": 35.79,
  "jitter": 1.22,
  "duration": 27.07,
  "unit": "Mbps"
}
```

### Simple 模式

```
Ping: 35.79 ms
Jitter: 1.22 ms
Download: 511.66 Mbps
Upload: 53.10 Mbps
```

## 测速原理

1. **初始化** — 访问主页获取 `ustc=1` cookie
2. **获取 IP** — 通过 `getIP.php` 获取客户端公网 IP
3. **服务器定位** — 通过 IP 查询获取服务器地理位置和 ISP
4. **PoW 验证** — SHA-256 Proof of Work 防滥用机制
5. **Ping 测试** — 10 次 HTTP GET，取最小 RTT
6. **下载测试** — 6 路并发流持续下载，时间型测速
7. **上传测试** — 3 路并发流持续上传随机数据

速度计算：`Mbps = (bytes × 8 / elapsed / 1,000,000) × 1.06`

## 技术栈

- **Python 3.10+**
- **httpx** — 异步 HTTP 客户端
- **rich** — 终端 UI

## License

MIT
