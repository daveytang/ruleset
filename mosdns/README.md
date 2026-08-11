# MosDNS 自定义规则与配置

仓库路径：https://github.com/daveytang/ruleset/tree/main/mosdns

## 两类文件，别搞混

| 类型 | 文件 | 怎么更新到服务器 |
|---|---|---|
| **配置** | `config.yaml` | **手动**拉取（不会被 `sync-custom` 自动覆盖） |
| **自定义规则** | `custom-*.txt`、`tiktok-live-domain.txt`、`hosts.txt` | `sync-custom` 每 5 分钟自动拉；也可手动跑一次 |

改规则（加直连/代理域名）→ 编辑对应 txt，等 timer 或跑 `sync-custom`。  
改分流逻辑 / 上游 → 改仓库里的 `config.yaml`，再到**每台** DNS 上执行下面的拉取命令。

---

## 每台机器：更新 config.yaml

在服务器上执行（需要已安装到 `/etc/mosdns`）：

```bash
cd /etc/mosdns
cp -a config.yaml "config.yaml.bak.$(date +%Y%m%d%H%M%S)"
curl -fsSL -o config.yaml \
  https://raw.githubusercontent.com/daveytang/ruleset/main/mosdns/config.yaml
# 若习惯 wget，可用：
# wget -q -O config.yaml https://raw.githubusercontent.com/daveytang/ruleset/main/mosdns/config.yaml
systemctl restart mosdns
systemctl is-active mosdns
dig @127.0.0.1 www.baidu.com A +short
dig @127.0.0.1 www.google.com A +short
```

验证期望：百度为国内 IP，谷歌为国外 IP。

raw 有时有短缓存。若刚推完 GitHub 却拉到旧文件，可改用带 commit 的地址，例如：

```bash
# 把 COMMIT 换成本次提交的完整或短 SHA
curl -fsSL -o config.yaml \
  "https://raw.githubusercontent.com/daveytang/ruleset/COMMIT/mosdns/config.yaml"
systemctl restart mosdns
```

---

## 每台机器：立刻同步自定义规则（可选）

```bash
/etc/mosdns/bin/sync-custom
journalctl -u mosdns-sync -n 20 --no-pager
```

---

## 我该改哪个规则文件

| 我想做的事 | 改这个文件 |
|---|---|
| 让某个域名走**国内 DNS**（直连） | `custom-cn-domain.txt` |
| 让某个域名走**国外 DNS**（代理） | `custom-remote-domain.txt` |
| 屏蔽某个域名 | `custom-block-domain.txt` |
| 新发现的 TikTok 推流域名（走国外且不缓存） | `tiktok-live-domain.txt` |
| 指定域名固定解析到某个 IP | `hosts.txt` |

一行一个域名，自动匹配子域名。行尾**不能**写 `# 备注`。

**优先级（高→低）：** hosts → 屏蔽 → TikTok 免缓存 → `custom-remote` → `custom-cn` → 仓库规则 → GeoSite → **其余未知域名走国外 DNS**。

人工规则整体高于自动规则。同一域名同时写在国外表和国内表时，**国外表生效**。

---

## 写错了会怎样

`sync-custom` 有格式检查和试启动；不过则回滚，不影响正在跑的实例。  
`config.yaml` 是你手动覆盖的，拉取前务必 `cp` 备份；重启失败可把 `.bak` 拷回去再 `systemctl restart mosdns`。
