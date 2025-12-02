from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import pymysql
from pymysql.cursors import DictCursor


db_connection = None


def _create_connection():
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_connection
    if db_connection is None:
        db_connection = _create_connection()
    try:
        yield
    finally:
        if db_connection is not None:
            try:
                db_connection.close()
            except Exception:  # noqa: BLE001
                pass
            finally:
                db_connection = None


app = FastAPI(title="菜单系统后端", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_connection():
    global db_connection
    if db_connection is None or not getattr(db_connection, "open", False):
        db_connection = _create_connection()
    return db_connection


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
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name FROM dept WHERE enabled = 1 ORDER BY id")
        rows = cursor.fetchall()
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

        # 根据文件名简单判断所属功能模块
        module_code = "UNKNOWN"
        if "规则" in name:
            module_code = "RULE_TEMPLATE"
        elif "批量新增" in name or "新增" in name:
            module_code = "BATCH_PRODUCT_ADD"
        elif "批量变更" in name or "变更" in name:
            module_code = "BATCH_PRODUCT_UPDATE"

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

        # 记录文件级日志和上传任务到数据库
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                # 文件级日志表（增加 module_code 字段，用于区分功能模块）
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS upload_log (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        filename VARCHAR(255) NOT NULL,
                        size_bytes BIGINT NULL,
                        status VARCHAR(20) NOT NULL,
                        reason VARCHAR(255) NULL,
                        module_code VARCHAR(50) NOT NULL DEFAULT 'UNKNOWN',
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_upload_log_module (module_code)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )

                # 上传任务主表，用于按模块区分任务和统计信息
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS upload_task (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        filename VARCHAR(255) NOT NULL,
                        size_bytes BIGINT NULL,
                        module_code VARCHAR(50) NOT NULL,
                        template_code VARCHAR(50) NULL,
                        status VARCHAR(20) NOT NULL,
                        total_rows INT NULL,
                        success_rows INT NULL,
                        fail_rows INT NULL,
                        message VARCHAR(500) NULL,
                        created_by VARCHAR(50) NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_upload_task_module_status (module_code, status),
                        INDEX idx_upload_task_created_at (created_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )

                # 写入文件级日志（包含模块编码 module_code）
                cursor.execute(
                    "INSERT INTO upload_log (filename, size_bytes, status, reason, module_code) VALUES (%s, %s, %s, %s, %s)",
                    (name, size_bytes, status_value, reason_value, module_code),
                )

                # 写入上传任务日志：此阶段仅记录文件级结果，不解析业务数据
                task_status = "COMPLETED" if status_value == "ok" else "FAILED"
                task_message = reason_value or ""
                cursor.execute(
                    """
                    INSERT INTO upload_task (
                        filename, size_bytes, module_code, template_code,
                        status, total_rows, success_rows, fail_rows, message, created_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        name,
                        size_bytes,
                        module_code,
                        None,
                        task_status,
                        None,
                        None,
                        None,
                        task_message,
                        None,
                    ),
                )
        finally:
            pass

    return {"results": results}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
