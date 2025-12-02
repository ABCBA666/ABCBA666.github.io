# 菜单系统（前后端分离示例）

- 当前版本：**1.0**

## 一、访问入口

### 本地开发环境

- **前端入口（菜单页面）**  
  直接用浏览器打开本地文件：  
  `c:/Users/mc/Desktop/menu/index.html`

- **后端接口文档（Swagger UI）**  
  `http://127.0.0.1:8000/docs`

> 如后续部署到服务器或内网环境，只需要在这里补充线上地址即可。

---

## 二、当前已实现功能（仅页面与接口占位，不含业务逻辑）

### 1. 前端页面

- 顶部标题：**菜单系统**
- 中间菜单区（左右两列、始终左右对称排列）：
  - 左侧：单个商品维护、客户信息维护、仓库信息变更、问题需求提报、银行账户维护、陆续开放（灰色，表示未开放，位于“银行账户维护”后面）
  - 右侧：批量商品维护、供应信息维护、采购编码变更、决策报表维护、规则模版维护
- 提示文字：
  - `未开放内容请暂时通过（问题需求提报）进行提报，后续将陆续开放`
- 底部操作区：
  - 我的处理
  - 我的提报
  - 我的审核

- 独立页面：**商品批量维护**（`batch.html`）
  - 从首页菜单“批量商品维护”跳转进入
  - 功能：
    - 提报事业部选择（从 `/api/departments` 动态加载 MySQL `dept` 表中的数据）。
    - 下载模板链接：商品批量新增模板.xls / 商品批量变更模板.xls。
    - “点击上传”：在本地/手机上选择多个文件，并在表格中展示文件名、大小和状态，可逐行删除。
    - “校验文件”：将当前列表中的文件上传到后端 `/api/batch-upload`，后端只校验文件类型（.xls/.xlsx）并保存到 `uploads/` 目录，返回每个文件的校验结果，在表格“状态”列中展示。

> 目前页面只做静态展示和简单点击日志，未接入具体业务接口，方便后续扩展。

### 2. 后端接口（FastAPI，占位实现）

启动命令（在项目根目录 `c:/Users/mc/Desktop/menu` 下）：

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

主要接口：

- `GET /api/menu`
  - 返回当前菜单项列表（id + 名称），供前端渲染菜单使用。
- `GET /api/status`
  - 返回 `{ "status": "ok" }`，用于健康检查。
- `GET /api/items/{item_id}`（如后续添加）
  - 返回指定菜单项的占位详情：`{"id": item_id, "detail": "接口占位，后续实现具体功能"}`。
 - `GET /api/departments`
   - 从 MySQL 数据库 `menu_system.dept` 中读取事业部列表，返回形如：`{"items": [{"id": 1, "name": "集团总部"}, ...]}`。
 - `POST /api/batch-upload`
   - 接收表单字段 `files` 中上传的一个或多个文件，校验规则：
     - 只允许扩展名为 `.xls` 或 `.xlsx`；
     - 单个文件大小不超过 10MB；
   - 校验通过的保存到后端 `uploads/` 目录；每个文件的处理结果会以 `{"results": [{"filename": "...", "status": "ok|failed", "reason": "..."}]}` 形式返回，`reason` 中包含类型或大小错误的具体提示。

> 后续可以在 FastAPI 中为每个菜单项增加独立的路由和业务实现，并在此 README 中补充对应说明。

---

## 三、依赖与环境

- Python 版本：建议 3.10+（当前测试环境为 Windows）
- 主要依赖：
  - fastapi
  - uvicorn[standard]
  - pymysql（连接 MySQL）

> 本地开发环境默认使用 MySQL 账号：`root`，密码：`123456`，数据库：`menu_system`。

示例表结构（由后端在首次上传时自动创建）：

```sql
CREATE TABLE IF NOT EXISTS upload_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  filename VARCHAR(255) NOT NULL,
  size_bytes BIGINT NULL,
  status VARCHAR(20) NOT NULL,
  reason VARCHAR(255) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

安装依赖：

```bash
pip install -r requirements.txt
```

---

## 四、后续维护建议

- 每新增一个菜单项或接口：
  - 在 `index.html` / `styles.css` 中更新对应前端展示；
  - 在 `main.py` 中新增对应的 API 路由；
  - 在本 `README.md` 中同步补充：
    - 新增的菜单名称、入口说明；
    - 新增 API 的路径、方法和简要功能说明。

这样可以保持文档与实际系统**实时同步、方便交接与维护**。
