/**
 * QQ 机器人 → GitHub Actions 中转 Worker
 * 接收 QQ 平台回调事件，解析命令，触发 GitHub Actions 执行
 *
 * 环境变量 (Secrets):
 *   GITHUB_PAT  - GitHub Personal Access Token (带 workflow 权限)
 *   QQ_APPID    - QQ 机器人 AppID
 *   QQ_SECRET   - QQ 机器人密钥
 *   GITHUB_REPO - 仓库名 (默认 a1642425527-ship-it/ship-tracker)
 */

const GITHUB_REPO = "a1642425527-ship-it/ship-tracker";

/** QQ 命令 → ship_tracker.py 参数 */
function parseCommand(content) {
  content = content.replace(/<@!?\d+>/g, "").trim();

  // 帮助：直接返回菜单，不触发 GitHub
  if (["帮助", "help", "菜单", "?"].includes(content)) {
    return {
      help: true,
      text:
        "📖 船舶跟踪机器人可用命令：\n\n" +
        "📤 推送 —— 手动推送船期到钉钉\n" +
        "➕ 添加 船名 航次 [备注] —— 添加船舶\n" +
        "  例：添加 YM TOPMOST 025W 周超群\n" +
        "➖ 删除 船名 —— 删除船舶\n" +
        "📝 备注 船名 内容 —— 设置备注\n" +
        "📋 列表 —— 查看所有船舶\n" +
        "📊 状态 —— 查看系统状态\n" +
        "❓ 帮助 —— 显示本菜单"
    };
  }

  if (["推送", "push", "强制推送"].includes(content)) return { args: ["--push"] };
  if (["列表", "船列表", "list", "船"].includes(content)) return { args: ["--list"] };
  if (["状态", "status", "系统状态"].includes(content)) return { args: ["--status"] };

  let m = content.match(/^(?:添加|新增|add)\s+(.+?)\s+(\S+)(?:\s+(.+))?$/i);
  if (m) {
    const args = ["--add", m[1].trim(), m[2].trim()];
    if (m[3] && m[3].trim()) args.push(m[3].trim());
    return { args };
  }

  m = content.match(/^(?:删除|移除|删掉|remove|del)\s+(.+)$/i);
  if (m) return { args: ["--remove", m[1].trim()] };

  m = content.match(/^(?:备注|remark)\s+(.+?)\s+(.+)$/i);
  if (m) return { args: ["--remark", m[1].trim(), m[2].trim()] };

  return { args: ["--help"], unknown: true };
}

/** 发送 QQ 消息 */
async function sendQQMsg(env, openid, msgType, groupOpenid, text) {
  try {
    // 获取 access_token
    const tokenResp = await fetch("https://bots.qq.com/app/getAppAccessToken", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ appId: env.QQ_APPID, clientSecret: env.QQ_SECRET })
    });
    const tokenData = await tokenResp.json();
    const token = tokenData.access_token;
    if (!token) return;

    const payload = {
      content: [{ type: "text", data: text.slice(0, 1500) }],
      msg_type: 0,
      msg_seq: Math.floor(Math.random() * 100000)
    };
    const headers = {
      "Authorization": `QQBot ${token}`,
      "Content-Type": "application/json"
    };

    let url;
    if (msgType === "group" && groupOpenid) {
      url = `https://api.sgroup.qq.com/v2/groups/${groupOpenid}/messages`;
    } else {
      url = `https://api.sgroup.qq.com/v2/users/${openid}/messages`;
    }
    await fetch(url, { method: "POST", headers, body: JSON.stringify(payload) });
  } catch (e) {
    console.log("sendQQMsg error:", e.message);
  }
}

/** 验证 QQ 回调签名 (HMAC-SHA256, key=secret, msg=body) */
async function verifySignature(secret, body, signature) {
  if (!signature) return false;
  try {
    const key = await crypto.subtle.importKey(
      "raw", new TextEncoder().encode(secret),
      { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
    );
    const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(body));
    const hex = [...new Uint8Array(sig)].map(b => b.toString(16).padStart(2, "0")).join("");
    return hex === signature;
  } catch (e) {
    return false;
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // ========== 回调地址验证 (GET) ==========
    if (request.method === "GET") {
      const ticket = url.searchParams.get("ticket") || "";
      const msg = url.searchParams.get("msg") || "";
      const signature = url.searchParams.get("signature") || "";
      const timestamp = url.searchParams.get("timestamp") || "";
      const nonce = url.searchParams.get("nonce") || "";
      const echostr = url.searchParams.get("echostr") || "";

      // 兼容多种验证协议：
      // 1. QQ 官方: 返回 {"ticket": "ticket值"}
      if (ticket) {
        return new Response(JSON.stringify({ ticket }), {
          headers: { "Content-Type": "application/json" }
        });
      }
      // 2. 微信/企业微信风格: 返回 echostr
      if (echostr) {
        return new Response(echostr, {
          headers: { "Content-Type": "text/plain" }
        });
      }
      // 3. 默认返回 OK
      return new Response("OK", { headers: { "Content-Type": "text/plain" } });
    }

    // ========== 事件推送 (POST) ==========
    if (request.method === "POST") {
      const rawBody = await request.text();

      // 签名验证（可选，失败则拒绝）
      const signature = request.headers.get("X-QQ-Signature") || "";
      const valid = await verifySignature(env.QQ_SECRET, rawBody, signature);
      if (signature && !valid) {
        return new Response(JSON.stringify({ code: 0 }), { status: 200 });
      }

      try {
        const event = JSON.parse(rawBody);
        const d = event.d || {};
        const content = (d.content || "").replace(/<@!?\d+>/g, "").trim();
        const openid = (d.author && d.author.id) || "";
        const msgType = d.msg_type || (d.group_openid ? "group" : "c2c");
        const groupOpenid = d.group_openid || "";

        console.log("收到QQ消息:", content, "类型:", msgType);

        if (!content) {
          return new Response(JSON.stringify({ code: 0 }), { status: 200 });
        }

        const parsed = parseCommand(content);

        // 帮助菜单直接回复
        if (parsed.help) {
          await sendQQMsg(env, openid, msgType, groupOpenid, parsed.text);
          return new Response(JSON.stringify({ code: 0 }), { status: 200 });
        }

        // 无法识别
        if (parsed.unknown) {
          await sendQQMsg(env, openid, msgType, groupOpenid,
            "🤔 看不懂这条指令，发送 帮助 查看可用命令");
          return new Response(JSON.stringify({ code: 0 }), { status: 200 });
        }

        // 触发 GitHub Actions
        const resp = await fetch(
          `https://api.github.com/repos/${env.GITHUB_REPO || GITHUB_REPO}/actions/workflows/ship-track.yml/dispatches`,
          {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${env.GITHUB_PAT}`,
              "Accept": "application/vnd.github.v3+json",
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              ref: "main",
              inputs: {
                qq_command: JSON.stringify(parsed.args),
                qq_openid: openid,
                qq_msg_type: msgType,
                qq_group_openid: groupOpenid
              }
            })
          }
        );

        // 立即回复"收到"
        await sendQQMsg(env, openid, msgType, groupOpenid,
          "⏳ 收到指令，正在执行，请稍候...");

        console.log("GitHub dispatch status:", resp.status);
        return new Response(JSON.stringify({ code: 0, status: resp.status }), { status: 200 });
      } catch (e) {
        console.log("handle event error:", e.message);
        return new Response(JSON.stringify({ code: 0 }), { status: 200 });
      }
    }

    return new Response("OK");
  }
};
