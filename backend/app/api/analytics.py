from fastapi import APIRouter, Depends, UploadFile

from app.api.deps import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/summary")
def summary():
    return {"cost": 0, "clicks": 0, "impressions": 0, "rsform_leads": 0, "virtuemart_orders": 0}


@router.get("/daily")
def daily():
    return []


@router.get("/sites")
def sites():
    return []


@router.post("/import-csv")
async def import_csv(file: UploadFile):
    content = await file.read()
    return {"filename": file.filename, "bytes": len(content), "status": "accepted"}
