# 腾讯云函数部署指南

## 一、注册腾讯云账号（微信扫码即可）

https://cloud.tencent.com

新用户有免费额度（云函数每月免费 40 万次调用 + 40万GBs），个人用绰绰有余。

## 二、创建云函数

1. 打开 **https://console.cloud.tencent.com/scf**
2. 点 **新建 → 从头开始**
   - 函数名称: `qq-ship-bot`
   - 地域: 广州（或其他国内节点）
   - 运行环境: **Python 3.9**（或 3.6+）
   - 创建方式: 空函数（事件函数）
3. 把 `index.py` 的内容**全部粘贴**进编辑器，覆盖默认代码
4. 点 **部署**（保存）

## 三、配置环境变量

函数配置 → 环境变量，添加：

| 变量 | 值 |
|------|-----|
| GITHUB_PAT | 你的 GitHub Token |
| QQ_APPID | 1905322972 |
| QQ_SECRET | 你的 QQ 机器人密钥 |

## 四、创建 API 网关触发器

1. 函数 → **触发管理** → **创建触发器**
2. 触发方式: **API 网关触发**
3. 点 **提交**（保持默认即可：GET+POST 都允许）
4. 创建后会得到公网 URL，类似：
   `https://service-xxxx-xxxx.gz.apigw.tencentcs.com/release/qq-ship-bot`

## 五、测试回调

浏览器打开：`你的URL?ticket=test123`

应返回：`{"ticket": "test123"}`

## 六、QQ 开放平台配置

1. https://q.qq.com → 你的机器人 → 接入方式
2. 切换 **Webhook**
3. 回调地址填：`你的腾讯云函数URL`
4. 保存，应该通过验证

## 七、完成后

QQ 上给机器人发 `帮助` 测试。电脑关机也能用！
