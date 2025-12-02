from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import os
import pymysql
from pymysql.cursors import DictCursor

app = FastAPI(title="菜单系统后端")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_connection():
    return pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="123456",
        database="menu_system",
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
    )


@app.get("/api/menu")
async def get_menu_items():
    return {
        "items": [
            {"id": "single-product", "name": "单个商品维护"},
            {"id": "batch-product", "name": "批量商品维护"},
            {"id": "customer", "name": "客户信息维护"},
            {"id": "supplier", "name": "供应信息维护"},
            {"id": "warehouse", "name": "仓库信息变更"},
            {"id": "purchase-code", "name": "采购编码变更"},
            {"id": "demand-report", "name": "问题需求提报"},
            {"id": "decision-report", "name": "决策报表维护"},
        ]
    }


@app.get("/api/status")
async def system_status():
    return {"status": "ok"}


@app.get("/api/items/{item_id}")
async def menu_item_detail(item_id: str):
    return {"id": item_id, "detail": "接口占位，后续实现具体功能"}


@app.get("/api/departments")
def list_departments():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM dept WHERE enabled = 1 ORDER BY id")
            rows = cursor.fetchall()
    finally:
        conn.close()
    return {"items": rows}


@app.post("/api/batch-upload")
async def batch_upload(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有接收到文件",
        )

    allowed_ext = {".xls", ".xlsx"}
    max_size_bytes = 10 * 1024 * 1024  # 10MB
    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    results: list[dict] = []
    for f in files:
        name = f.filename or ""
        _, ext = os.path.splitext(name)
        ext = ext.lower()
        status_value = "ok"
        reason_value = "校验通过，已保存"

        # 读取内容以便获取实际大小
        try:
            content = await f.read()
        except Exception as exc:  # noqa: BLE001
            status_value = "failed"
            reason_value = f"读取文件失败: {exc}"
            content = b""

        size_bytes = len(content)

        if ext not in allowed_ext:
            status_value = "failed"
            reason_value = "文件类型不正确，仅支持 .xls / .xlsx"
        elif size_bytes > max_size_bytes:
            status_value = "failed"
            reason_value = "文件过大，单个文件不能超过 10MB"
        else:
            save_path = os.path.join(upload_dir, name)
            try:
                with open(save_path, "wb") as out:
                    out.write(content)
            except Exception as exc:  # noqa: BLE001
                status_value = "failed"
                reason_value = f"保存失败: {exc}"

        results.append({
            "filename": name,
            "status": status_value,
            "reason": reason_value,
        })

        # 记录日志到数据库
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS upload_log (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        filename VARCHAR(255) NOT NULL,
                        size_bytes BIGINT NULL,
                        status VARCHAR(20) NOT NULL,
                        reason VARCHAR(255) NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
                cursor.execute(
                    "INSERT INTO upload_log (filename, size_bytes, status, reason) VALUES (%s, %s, %s, %s)",
                    (name, size_bytes, status_value, reason_value),
                )
        finally:
            try:
                conn.close()
            except Exception:  # noqa: BLE001
                pass

    return {"results": results}
