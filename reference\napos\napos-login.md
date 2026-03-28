# 登录信息获取流程

## 一、对用户可见（硬约束）

**允许**：一句极简操作提示、极短进度、**门店 Markdown 表**或一句人话错误。  
**禁止**：任何可复用鉴权串（含片段）、带 query 的完整 URL、请求头/body、SSE/`data:`、JSON-RPC 原文、脚本输出、工具名与参数、轮询/snapshot/读存储等过程叙事、Skill 章节引用；手机号须脱敏。用户索要「完整 JSON/凭证」仍不提供。

**发送前自检（任一不满足则不发当前稿）**：无鉴权字段值；无 URL/头/SSE 原文；无技术过程自述；无工具细节；隐私已脱敏。

**静默**：浏览器轮询、关浏览器、读写 `auth_storage.json`、调接口与解析默认不对用户逐步播报；仅失败需配合时给**一句**现象说明（仍不带 URL/token/工具名）。

---

## 二、对内流程（勿复述给用户）

授权页URL:`https://open-api.shop.ele.me/authorize?response_type=code&client_id=OT8tFbck5X&redirect_uri=https%3A%2F%2Fwww.dingtalk.com%2F&scope=all&state=wukong&WDID=替换为<钉钉ID>`

| 顺序 | 动作 |
|------|------|
| 1 | 取钉钉 `userId`，与 `auth_storage.json` 的 `wdid` 对齐（缺则 `dws contact user get-self` 后写入） |
| 2 | `read_file` 读 `auth_storage.json`：有可用 `auth_code` → 直接第 4 步；接口报过期则清空 `auth_code`（可清空门店字段）保留 `wdid` 再授权 |
| 3 | 无可用 `auth_code`：拼授权页URL （**重要**替换参数`WDID=` <钉钉ID>）→ `open_tab` → **立即开启检测（重要且必须）**循环 `snapshot` 取 **`url`**（约 2s，默认 300s 超时） |
| 3a | `url` 含 `napos-auth.faas.ele.me/success` → 成功；含 `/failed` → 失败；含 `/wukong` 中间页 → 继续轮询 |
| 3b | 成功：**先**读 LocalStorage `WNTK` → 写 `auth_code`、`obtained_at` → **再**关浏览器；失败/超时默认关浏览器 |
| 4 | `NaposCodeToShop`：请求头 `sk` = JSON `code` = 本轮 `WNTK`；请求头 `WDID` = `wdid`。`python3 "${SKILL_DIR}/script/napos/login.py" NaposCodeToShop "<授权码>" "<wdid>"` |
| 5 | 多门店则表格让用户选，选定后写回 `shop_id` / `shop_name` |

- **`auth_storage.json`（工作区根）字段**：`wdid`、`auth_code`（即 WNTK）、`shop_id`、`shop_name`、`obtained_at`。
- 用户主动要求重新登陆则清空`auth_code`，及门店列表、门店信息等业务信息本地缓存和记忆，`wdid`可保留，重新走登录步骤

---

## 三、门禁与顺序铁律（防遗漏）

未完成前**禁止**用「登录完告诉我」结束本轮（可说一句「已打开授权页」后**马上**继续工具调用）：

- [ ] 已读 `auth_storage.json` 并判断是否要浏览器授权  
- [ ] 若要授权：已 `open_tab`，且**紧接着**至少 1 次 `snapshot` 并开始/继续按 `url` 轮询  
- [ ] 未用 `wait_for(text=...)` 充当 URL 检测  
- [ ] 关闭浏览器前确保WNTK已经保存
- [ ] 重新获取门店列表信息后要覆盖旧数据

**铁律**：`open_tab` → **立刻** `snapshot` 循环并检测（只认返回里的 `url`）→ 成功则读存储并落盘 → 关浏览器。

---

## 四、脚本

**路径约定**：`${SKILL_DIR}` = 本 Skill 根目录（与 `SKILL.md` 同级）。执行前将环境变量 `SKILL_DIR` 设为该目录，或在命令里写绝对路径替换 `${SKILL_DIR}`。

- `${SKILL_DIR}/script/napos/login.py`：对内调 `NaposCodeToShop` 等。  
