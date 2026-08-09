# MosDNS 自定义规则

这个目录由 DNS 服务器上的 `/etc/mosdns/bin/sync-custom` 每 5 分钟拉取一次，
内容有变化时自动重启 MosDNS。**直接在 GitHub 网页或手机 App 上编辑这里的文件即可，
最迟 5 分钟后线上生效**，不需要登录服务器。

## 我该改哪个文件

| 我想做的事 | 改这个文件 |
|---|---|
| 让某个域名走**国内 DNS**（直连） | `custom-cn-domain.txt` |
| 让某个域名走**国外 DNS**（代理） | `custom-remote-domain.txt` |
| 屏蔽某个域名 | `custom-block-domain.txt` |
| 新发现的 TikTok 推流域名（走国外且不缓存） | `tiktok-live-domain.txt` |
| 指定域名固定解析到某个 IP | `hosts.txt` |
| 未知域名解析到这些 IP 时算「国内」 | `custom-cn-ip.txt` |
| 未知域名解析到这些 IP 时强制改问国外 | `custom-remote-ip.txt` |

绝大多数情况下你只会用到前两个。

## 写法

一行一个域名，**会自动匹配所有子域名**，所以写 `example.com` 就够了，
不用再单独写 `www.example.com`。

行尾**不能**写注释。整行以 `#` 开头的注释是可以的。

```
example.com          ← 正确
example.com # 备注    ← 错误，同步会被拒绝
www.example.com      ← 多余，写 example.com 已经包含它
```

IP 文件一行一个 IP 或 CIDR，例如 `203.0.113.0/24`。

`hosts.txt` 是唯一需要空格的文件，格式是 `域名 IP`。

## 优先级

从高到低，命中即停：

1. `hosts.txt`
2. `custom-block-domain.txt`（屏蔽）
3. `tiktok-live-domain.txt`（国外，且跳过缓存）
4. `custom-remote-domain.txt`（国外）
5. `custom-cn-domain.txt`（国内）
6. GeoSite 自动判定

所以同一个域名如果同时写进了国外表和国内表，**国外表生效**。

## 写错了会怎样

不会影响线上服务。同步脚本有三层保护：先逐行检查格式并指出出错行号，
再用新规则试启动一个实例，加载失败就回滚，重启失败也回滚。
任何一层不过，正在运行的 MosDNS 都不受影响。

在服务器上查看同步结果：

```bash
journalctl -u mosdns-sync -n 30 --no-pager
```

## 不要动的东西

不要在 `tiktok-live-domain.txt` 里添加 `douyin.com` 或 `bytedance.com`，
会把国内抖音业务送去国外 DNS。

本目录之外的 `release/` 是 Loyalsoldier 规则镜像，由 CI 自动更新，不要手改。
