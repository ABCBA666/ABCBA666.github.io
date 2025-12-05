# 企业微信审批接入说明

本文档说明如何在企业微信中完成一个“发起审批”的 H5 页面接入流程，包括：

- 创建审批模板  
- 配置自建应用 & JS-SDK  
- 搭建后端签名服务  
- 在前端调用 `thirdPartyOpenPage` 打开审批界面  
- （可选）接收审批相关消息/事件

---

## 一、前置准备

1. **企业微信管理员账号**  
   具有管理应用和审批的权限。

2. **一台服务器（建议公网）**  
   - 有固定公网 IP 和域名（方便配置 JS-SDK 安全域名和回调 URL）。  
   - 能部署后端服务（Node / Python / Java 等均可）。

3. **了解自己使用的技术栈**  
   - 前端：本示例使用简单 HTML + JS。  
   - 后端：本示例使用 Node.js + Express 提供签名接口。

---

## 二、创建审批模板并获取 `templateId`

1. 登录企业微信管理后台。  
2. 进入「应用管理」→ 找到审批相关入口（或直接进入“审批”模块）。  
3. 新建一个审批模板，配置你需要的字段和流程。  
4. 创建完成后，在模板详情页找到该模板对应的 **模板 ID（templateId）**。  
5. 记录下这个 `templateId`，后面前端会用到，例如：

   ```text
   d9cce789e72710b8a6dd12cb783897ab_1561702597
   ```

---

## 三、创建/配置自建应用

1. 在企业微信管理后台，进入「应用管理」。  
2. 创建一个**自建应用**（或使用已有应用）：  
   - 记下 **企业 ID（CorpID / corpid）**，形如：`wwxxxxxxxxxxxxxxxx`。  
   - 在应用详情中获取该应用的 **Secret**。  
3. 开启该应用的相关权限（如访问审批、JS-SDK 等，根据官方文档要求）。

后端签名服务中会使用：

- `CORP_ID` = 企业 ID（corpid）  
- `AGENT_SECRET` = 应用 Secret

---

## 四、配置服务器 IP 白名单（避免 60020）

后端调用企业微信接口时，若返回 `errcode: 60020, errmsg: not allow to access from your ip`，说明服务器 IP 不在白名单中。

1. 在企业微信管理后台，找到该自建应用的服务器 IP 白名单配置。  
2. 把后端服务器的**出口公网 IP** 加入白名单。  
3. 保存后稍等几分钟，再测试调用企业微信接口。

> 开发阶段如果是在本地机器上调试，可能 IP 变化较频繁，**建议尽快迁移到云服务器**，并将云服务器 IP 加白。

---

## 五、配置 JS-SDK 安全域名

要在 H5 中使用企业微信 JS-SDK（包括 `thirdPartyOpenPage`），必须配置安全域名。

1. 在企业微信管理后台的应用设置或“JS-SDK 安全域名”配置中：  
2. 将你的 H5 页面最终访问域名（例如 `h5.example.com`）添加为安全域名。  
3. 确保页面地址形如：

   ```text
   https://h5.example.com/approval/index.html
   ```

并且和后端签名时使用的 `url` 一致（注意不要带 `#` 后的部分）。

---

## 六、后端：JS-SDK 签名接口流程（Node 示例）

下面是一个典型的 Node.js + Express 实现思路（流程示意）：

1. **获取 `access_token`**：

   ```http
   GET https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=CORP_ID&corpsecret=AGENT_SECRET
   ```

2. **用 `access_token` 换取 `jsapi_ticket`**：

   ```http
   GET https://qyapi.weixin.qq.com/cgi-bin/get_jsapi_ticket?access_token=ACCESS_TOKEN
   ```

3. **生成签名**：用 `jsapi_ticket` + `noncestr` + `timestamp` + `url` 按照企业微信文档拼接字符串并做 `SHA1` 计算：

   ```text
   raw = "jsapi_ticket=...&noncestr=...&timestamp=...&url=..."
   signature = sha1(raw)
   ```

4. **返回给前端**：将 `appId/corpId`、`timestamp`、`nonceStr`、`signature` 返回给前端，例如：

   ```json
   {
     "appId": "wwxxxxxxxxxxxxxxxx",
     "timestamp": 1234567890,
     "nonceStr": "randomString",
     "signature": "sha1-result"
   }
   ```

> 实际代码已在 `wecom-server/server.js` 中实现（接口路径 `/api/wecom/jssdk-sign`），这里仅说明流程。

---

## 七、前端：H5 页面引入 JS-SDK 并调用 `thirdPartyOpenPage`

1. **通过 CDN 引入 JS-SDK**：

   ```html
   <script src="https://wwcdn.weixin.qq.com/node/open/js/wecom-jssdk-2.3.3.js"></script>
   ```

2. **在页面 JS 中调用后端签名接口并执行 `ww.config`**：

   ```js
   async function initWecomSDK() {
     const url = location.href.split('#')[0];
     const res = await fetch('/api/wecom/jssdk-sign?url=' + encodeURIComponent(url));
     const data = await res.json();

     ww.config({
       beta: true,
       debug: true,                 // 开发阶段可开启
       appId: data.appId,           // 企业 ID（corpid）
       timestamp: data.timestamp,
       nonceStr: data.nonceStr,
       signature: data.signature,
       jsApiList: ['thirdPartyOpenPage']
     });

     ww.ready(function () {
       console.log('wecom jssdk ready, version:', ww.SDK_VERSION);
       // 后面绑定按钮事件
     });

     ww.error(function (err) {
       console.error('wecom jssdk config 失败', err);
     });
   }

   initWecomSDK();
   ```

3. **在 `ww.ready` 中调用审批接口**：

   ```js
   document.getElementById('btn-approval').onclick = function () {
     ww.invoke('thirdPartyOpenPage', {
         oaType: '10001',                  // 10001 表示审批
         templateId: '你的审批模板ID',       // 上文记录的 templateId
         thirdNo: 'R0000000001',           // 业务系统中的唯一单号
         extData: {
           fieldList: [
             {
               title: '规则审批',
               type: 'text',
               value: '初审',
             },
             {
               title: '跳转链接',
               type: 'link',
               value: 'https://work.weixin.qq.com',
             }
           ]
         }
       },
       function (res) {
         console.log('thirdPartyOpenPage result:', res);
       }
     );
   };
   ```

> 说明：真实的审批界面一般只会在 **企业微信内置浏览器 / 客户端内嵌 WebView** 中拉起，普通浏览器主要用于调试，查看 `config:ok` / `config:fail` 等日志。

---

## 八、部署到服务器与访问方式

1. **后端部署**  
   - 将签名服务部署到云服务器上，例如：`https://api.example.com`。  
   - 确保对外访问时，能正确返回 `/api/wecom/jssdk-sign` 的 JSON。

2. **前端部署**  
   - 将 H5 页面部署到 Nginx/静态服务器，例如 `https://h5.example.com/approval/index.html`。  
   - 确保页面中的 `fetch('/api/wecom/jssdk-sign?url=...')` 能访问到真实后端（如必要用反向代理）。

3. **在企业微信中访问**  
   - 可将 H5 地址配置到应用的“自定义菜单”或发送链接给用户。  
   - 用户在企业微信中点击链接，打开 H5 页面。  
   - 页面完成 JS-SDK 初始化后，点击“发起审批”，拉起企业微信审批界面。

---

## 九、（可选）接收审批回调 / 消息事件概述

若需要在你自己的系统里同步审批状态（通过、驳回等），需要：

1. 在企业微信后台为该应用配置「接收消息」 / 回调 URL：  
   - URL：`https://api.example.com/wecom/callback`  
   - Token：自定义字符串（如 `myToken123`）  
   - EncodingAESKey：后台生成的一串 43 位密钥。

2. 在后端实现 `/wecom/callback`：  
   - GET：用于 URL 验证（解密 `echostr` 并原样返回）。  
   - POST：接收消息/事件（解密 `<Encrypt>` 获得明文 XML，再按业务逻辑处理）。

3. 使用官方文档提供的加解密算法或示例代码（各语言均有）实现签名校验与 AES 解密。

> 详细的加解密实现和审批事件字段，请参考企业微信官方文档中的“消息加解密方案”和“审批回调事件说明”。

---

## 十、常见错误与排查

- **`invalid corpid (40013)`**  
  - 检查后端 `corpid` 是否与“我的企业”中的企业 ID 完全一致。  
- **`invalid secret (40001)`**  
  - 检查 `secret` 是否为当前应用的 Secret，是否已重置过。  
- **`not allow to access from your ip (60020)`**  
  - 在应用的服务器 IP 白名单中添加后端服务器的出口 IP。  
- **前端 `ww.config is not a function` 或 `config:fail`**  
  - 确认 JS-SDK 脚本是否正确加载。  
  - 确认 `/api/wecom/jssdk-sign` 返回 200 且 `signature` 等字段正确。  
  - 确认当前访问 URL 与签名时使用的 `url` 完全一致（不含 `#` 部分）。
