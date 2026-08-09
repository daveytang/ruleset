# CN / GFW Ruleset

自动维护 **中国大陆 IP**、**国内直连域名**、**GFW 代理域名** 规则集，并输出多种代理工具格式。

每天由 GitHub Actions 自动拉取上游数据并更新 `dist/`。

## 列表说明

| 文件 | 含义 |
|------|------|
| `dist/cn_ip.txt` | 中国大陆 IPv4 CIDR |
| `dist/cn_ip6.txt` | 中国大陆 IPv6 CIDR |
| `dist/cn_domain.txt` | 国内直连域名 |
| `dist/gfw_domain.txt` | GFW / 需代理域名 |

同内容还提供 Clash、Surge、sing-box 格式，见下方。

## 原始数据源

- **CN IP (IPv4)**：[misakaio/chnroutes2](https://github.com/misakaio/chnroutes2)、[17mon/china_ip_list](https://github.com/17mon/china_ip_list)
- **CN IP (IPv6)**：[gaoyifan/china-operator-ip](https://github.com/gaoyifan/china-operator-ip)
- **CN 域名**：[felixonmars/dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list)
- **GFW 域名**：[Loyalsoldier/v2ray-rules-dat](https://github.com/Loyalsoldier/v2ray-rules-dat)、[Loyalsoldier/cn-blocked-domain](https://github.com/Loyalsoldier/cn-blocked-domain)

与 CN 域名冲突的条目会从 GFW 列表中剔除。可用 `custom/` 增减条目。

## 订阅地址

### 纯文本

```text
https://raw.githubusercontent.com/daveytang/ruleset/main/dist/cn_ip.txt
https://raw.githubusercontent.com/daveytang/ruleset/main/dist/cn_ip6.txt
https://raw.githubusercontent.com/daveytang/ruleset/main/dist/cn_domain.txt
https://raw.githubusercontent.com/daveytang/ruleset/main/dist/gfw_domain.txt
```

### Clash / Mihomo

```yaml
rule-providers:
  cn-ip:
    type: http
    behavior: ipcidr
    url: "https://raw.githubusercontent.com/daveytang/ruleset/main/dist/clash/cn_ip.yaml"
    path: ./ruleset/cn_ip.yaml
    interval: 86400
  cn-domain:
    type: http
    behavior: domain
    url: "https://raw.githubusercontent.com/daveytang/ruleset/main/dist/clash/cn_domain.yaml"
    path: ./ruleset/cn_domain.yaml
    interval: 86400
  gfw:
    type: http
    behavior: domain
    url: "https://raw.githubusercontent.com/daveytang/ruleset/main/dist/clash/gfw_domain.yaml"
    path: ./ruleset/gfw_domain.yaml
    interval: 86400

rules:
  - RULE-SET,cn-domain,DIRECT
  - RULE-SET,cn-ip,DIRECT
  - RULE-SET,gfw,PROXY
  - MATCH,PROXY
```

### Surge

```text
https://raw.githubusercontent.com/daveytang/ruleset/main/dist/surge/cn_ip.list
https://raw.githubusercontent.com/daveytang/ruleset/main/dist/surge/cn_ip6.list
https://raw.githubusercontent.com/daveytang/ruleset/main/dist/surge/cn_domain.list
https://raw.githubusercontent.com/daveytang/ruleset/main/dist/surge/gfw_domain.list
```

### sing-box

源格式 JSON（可用 `sing-box rule-set compile` 转成 `.srs`）：

```text
https://raw.githubusercontent.com/daveytang/ruleset/main/dist/sing-box/cn_ip.json
https://raw.githubusercontent.com/daveytang/ruleset/main/dist/sing-box/cn_ip6.json
https://raw.githubusercontent.com/daveytang/ruleset/main/dist/sing-box/cn_domain.json
https://raw.githubusercontent.com/daveytang/ruleset/main/dist/sing-box/gfw_domain.json
```

## 自定义

在 `custom/` 下按行添加：

| 文件 | 作用 |
|------|------|
| `cn_ip_extra.txt` / `cn_ip_exclude.txt` | 增/删 CN IPv4 |
| `cn_ip6_extra.txt` / `cn_ip6_exclude.txt` | 增/删 CN IPv6 |
| `cn_domain_extra.txt` / `cn_domain_exclude.txt` | 增/删国内域名 |
| `gfw_domain_extra.txt` / `gfw_domain_exclude.txt` | 增/删 GFW 域名 |

## 本地更新

```bash
python3 scripts/update.py
```

## 自动更新

`.github/workflows/update.yml` 每天 UTC 02:17 运行，也可在 Actions 里手动触发。

## License

MIT。上游数据版权归各自项目所有。
