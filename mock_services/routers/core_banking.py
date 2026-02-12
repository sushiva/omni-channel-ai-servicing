import json

from fastapi import APIRouter, Depends, HTTPException
from mock_services.models import AddressUpdate
from mock_services.db import get_db

router = APIRouter()

@router.post("/customers/{customer_id}/address")
async def update_address(customer_id: str, payload: AddressUpdate, db=Depends(get_db)):
    cursor = await db.execute("SELECT 1 FROM customers WHERE id = ?", (customer_id,))
    if not await cursor.fetchone():
        # Auto-create customer if not found (mock service behavior)
        await db.execute(
            "INSERT INTO customers (id, address) VALUES (?, ?)",
            (customer_id, json.dumps(payload.address))
        )
    else:
        await db.execute(
            "UPDATE customers SET address = ? WHERE id = ?",
            (json.dumps(payload.address), customer_id)
        )
    await db.commit()
    return {"status": "address updated"}

@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str, db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"customer": row}
