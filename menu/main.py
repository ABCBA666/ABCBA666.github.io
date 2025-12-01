from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="菜单系统后端")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
