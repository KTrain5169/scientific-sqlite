from fastapi import APIRouter, HTTPException
from utils.db import get_db_connection
from schema.sample import SampleRecord

router = APIRouter()

@router.get("/sample")
async def read_sample():
    conn = get_db_connection()
    data = conn.execute("SELECT * FROM sample_table").fetchall()
    conn.close()
    # Transform the sqlite rows to a serializable form
    result = [dict(row) for row in data]
    if not result:
        raise HTTPException(status_code=404, detail="No data found")
    return {"data": result}

@router.post("/sample")
async def create_sample(record: SampleRecord):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sample_table (name, description) VALUES (?, ?)", 
                   (record.name, record.description))
    conn.commit()
    conn.close()
    return {"message": "Sample record created"}