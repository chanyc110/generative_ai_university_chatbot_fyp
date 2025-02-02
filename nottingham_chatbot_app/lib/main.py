from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess

app = FastAPI()

class BookingDetails(BaseModel):
    username: str
    password: str
    venue: str
    contact_no: str
    purpose: str
    date: str
    session: str

@app.post("/make_booking")
async def make_booking(details: BookingDetails):
    try:
        # Call the Selenium script with arguments
        process = subprocess.run([
            "python", "booking_page.py",
            details.username,
            details.password,
            details.venue,
            details.contact_no,
            details.purpose,
            details.date,
            details.session
        ], capture_output=True, text=True)

        # Return the script output
        return {"message": "Booking initiated", "output": process.stdout}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
