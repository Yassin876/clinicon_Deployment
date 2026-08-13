from fastapi import APIRouter

router = APIRouter(prefix="/records", tags=["records"])

@router.get("/")
async def get_records():
    return {"message": "Get records endpoint stub"}

@router.get("/{id}")
async def get_record_by_id(id: str):
    return {"message": f"Get record {id} endpoint stub"}
