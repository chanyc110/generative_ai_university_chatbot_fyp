from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import sys


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
        
        script_path = "C:/Users/PC 5/Desktop/fyp_new_version/nottingham_chatbot_app/lib/booking_page.py"
        
        # Debug: Log details before execution
        print(f"Executing script: {script_path}")
        print(f"Arguments: {details.username}, {details.password}, {details.venue}, "
            f"{details.contact_no}, {details.purpose}, {details.date}, {details.session}")
        
        # Call the Selenium script with arguments
        process = subprocess.run([
            "C:/Users/PC 5/Desktop/fyp_new_version/venv/Scripts/python.exe", script_path,
            details.username,
            details.password,
            details.venue,
            details.contact_no,
            details.purpose,
            details.date,
            details.session
        ], capture_output=True, text=True)

        # Debug: Print stdout and stderr
        print("STDOUT:", process.stdout)
        print("STDERR:", process.stderr)

        if process.returncode != 0:
            return {"message": "Booking failed", "error": process.stderr}

        return {"message": "Booking initiated", "output": process.stdout}

    except Exception as e:
        print(f"Error running script: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
