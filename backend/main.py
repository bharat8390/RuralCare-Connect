from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware

from database import init_schema
from facilities import FACILITY_TYPES, get_facility, list_districts, list_facilities
from follow_ups import (
    ALLOWED_FOLLOW_UP_STATUSES,
    create_follow_up,
    list_follow_ups,
    update_follow_up_status,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create missing tables on startup. Existing rows are left untouched.
    init_schema()
    yield


app = FastAPI(title="RuralCare Connect", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Allow the local Vite development server (port 5173) to call this API
# while the backend is running on http://127.0.0.1:8001.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "app": "RuralCare Connect"}


@app.get("/api/v1/facilities")
def read_facilities(
    q: str | None = Query(default=None, max_length=100),
    district: str | None = Query(default=None, max_length=100),
    facility_type: str | None = Query(default=None, max_length=50),
    service: str | None = Query(default=None, max_length=100),
):
    if facility_type and facility_type.strip() and facility_type.strip() not in FACILITY_TYPES:
        raise HTTPException(status_code=422, detail="Unknown facility type.")

    return {
        "facilities": list_facilities(
            q=q,
            district=district,
            facility_type=facility_type,
            service=service,
        ),
        "districts": list_districts(),
    }


@app.get("/api/v1/facilities/{facility_id}")


def read_facility(facility_id: int = Path(..., ge=1)):
    facility = get_facility(facility_id)
    if facility is None:
        raise HTTPException(status_code=404, detail="Facility not found.")
    return facility

from pydantic import BaseModel, Field

from referrals import (
    ALLOWED_STATUSES,
    create_referral,
    list_referrals,
    update_referral_status,
)
from resources import (
    ALLOWED_RESOURCE_STATUSES,
    get_resource_summary,
    list_resources,
    upsert_resource,
)



class ReferralCreate(BaseModel):
    patient_name: str = Field(min_length=1, max_length=100)
    patient_age: int | None = Field(default=None, ge=0, le=120)
    from_facility_id: int = Field(ge=1)
    to_facility_id: int = Field(ge=1)
    service_id: int | None = Field(default=None, ge=1)
    referred_by_user_id: int | None = Field(default=None, ge=1)
    notes: str | None = Field(default=None, max_length=1000)


class ReferralStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=20)
    
class FollowUpCreate(BaseModel):
    referral_id: int = Field(ge=1)
    due_at: str = Field(min_length=1, max_length=50)
    notes: str | None = Field(default=None, max_length=1000)
    assigned_to_user_id: int | None = Field(default=None, ge=1)



class FollowUpStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=20)   

class ResourceUpdate(BaseModel):
    facility_id: int = Field(ge=1)
    resource_name: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=0)
    status: str = Field(min_length=1, max_length=20)
    
    
@app.get("/api/v1/follow-ups")
def read_follow_ups(
    status: str | None = Query(default=None, max_length=20),
):
    if status and status not in ALLOWED_FOLLOW_UP_STATUSES:
        raise HTTPException(
            status_code=422,
            detail="Unknown follow-up status.",
        )

    try:
        return {"follow_ups": list_follow_ups(status=status)}
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@app.post("/api/v1/follow-ups", status_code=201)
def add_follow_up(payload: FollowUpCreate):
    try:
        follow_up = create_follow_up(**payload.model_dump())
        return {"follow_up": dict(follow_up)}
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@app.patch("/api/v1/follow-ups/{follow_up_id}/status")
def change_follow_up_status(
    payload: FollowUpStatusUpdate,
    follow_up_id: int = Path(..., ge=1),
):
    try:
        follow_up = update_follow_up_status(
            follow_up_id,
            payload.status,
        )
        return {"follow_up": follow_up}
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if message == "Follow-up not found." else 422
        raise HTTPException(
            status_code=status_code,
            detail=message,
        ) from exc



@app.get("/api/v1/referrals")
def read_referrals(
    status: str | None = Query(default=None, max_length=20),
):
    if status and status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=422, detail="Unknown referral status.")

    return {"referrals": list_referrals(status=status)}


@app.post("/api/v1/referrals", status_code=201)
def add_referral(payload: ReferralCreate):
    try:
        referral = create_referral(**payload.model_dump())
        return {"referral": referral}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.patch("/api/v1/referrals/{referral_id}/status")
def change_referral_status(
    payload: ReferralStatusUpdate,
    referral_id: int = Path(..., ge=1),
):
    try:
        referral = update_referral_status(referral_id, payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if referral is None:
        raise HTTPException(status_code=404, detail="Referral not found.")

    return {"referral": referral}

@app.get("/api/v1/resources")
def read_resources(
    facility_id: int | None = Query(default=None, ge=1),
):
    return {"resources": list_resources(facility_id)}


@app.get("/api/v1/resources/summary")
def read_resource_summary():
    return get_resource_summary()


@app.post("/api/v1/resources")
def save_resource(payload: ResourceUpdate):
    if payload.status not in ALLOWED_RESOURCE_STATUSES:
        raise HTTPException(
            status_code=422,
            detail="Unknown resource status.",
        )

    try:
        resource = upsert_resource(**payload.model_dump())
        return {"resource": resource}
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if message == "Facility not found." else 422
        raise HTTPException(
            status_code=status_code,
            detail=message,
        ) from exc