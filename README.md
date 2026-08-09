# Ruleset Mirror

每日自动镜像 [Loyalsoldier/v2ray-rules-dat](https://github.com/Loyalsoldier/v2ray-rules-dat) 的常用规则文件，保持本仓库 `release/` 为最新。

上游更新由 GitHub Actions 每天拉取（也可在 Actions 里手动触发），无需本地维护。

## 文件

| 文件 | 说明 |
|------|------|
| `release/geoip.dat` | GeoIP 数据库 |
| `release/geosite.dat` | GeoSite 域名数据库 |
| `release/direct-list.txt` | 直连域名 |
| `release/proxy-list.txt` | 代理域名 |
| `release/reject-list.txt` | 广告 / 拒绝域名 |
| `release/apple-cn.txt` | Apple 大陆直连域名 |
| `release/google-cn.txt` | Google 大陆直连域名 |
| `release/gfw.txt` | GFWList 域名 |
| `release/win-update.txt` | Windows 更新域名 |

## 订阅地址

```text
https://raw.githubusercontent.com/daveytang/ruleset/main/release/geoip.dat
https://raw.githubusercontent.com/daveytang/ruleset/main/release/geosite.dat
https://raw.githubusercontent.com/daveytang/ruleset/main/release/direct-list.txt
https://raw.githubusercontent.com/daveytang/ruleset/main/release/proxy-list.txt
https://raw.githubusercontent.com/daveytang/ruleset/main/release/reject-list.txt
https://raw.githubusercontent.com/daveytang/ruleset/main/release/apple-cn.txt
https://raw.githubusercontent.com/daveytang/ruleset/main/release/google-cn.txt
https://raw.githubusercontent.com/daveytang/ruleset/main/release/gfw.txt
https://raw.githubusercontent.com/daveytang/ruleset/main/release/win-update.txt
```

## 来源

优先从 GitHub Release / raw 下载，失败时回退 jsDelivr（见 `scripts/sync.sh`）。

数据版权归 [Loyalsoldier/v2ray-rules-dat](https://github.com/Loyalsoldier/v2ray-rules-dat) 及其上游项目。

## License

MIT（本仓库脚本与工作流）；规则数据遵循各自上游许可。
