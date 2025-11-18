from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import json
import os

print("✅ planner_server on Koyeb loaded")

app = FastAPI()

# ---- CORS設定 ----
# file:// で開いたHTML や 他のOrigin からも受け取れるようにゆるく設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # 必要なら後で自分のドメインだけに絞る
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 入力データの型定義 ----
class Availability(BaseModel):
    date: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None

class Survey(BaseModel):
    name: str
    availability: List[Availability] = []
    area: Optional[str] = ""
    moveTime: Optional[str] = ""
    hateFood: Optional[str] = ""
    cantFood: Optional[str] = ""
    weakFood: Optional[str] = ""
    wantFood: Optional[str] = ""

# Koyebのコンテナ内の保存先（永続化したければ、後でVolumeを付ける）
DATA_FILE = Path("/app/responses.jsonl")


@app.get("/")
async def root():
    return {"status": "ok", "service": "planner_server"}


@app.get("/health")
async def health():
    return {"status": "ok"}


# CORSプリフライト対策
@app.options("/submit")
async def options_submit():
    """CORSプリフライト用"""
    return JSONResponse(status_code=200, content={})


@app.post("/submit")
async def submit(survey: Survey, request: Request):
    """予定情報を1行1件で保存"""
    entry = {
        "received_at": datetime.utcnow().isoformat() + "Z",
        "client_ip": request.client.host if request.client else None,
        **survey.model_dump(),
    }

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return {"ok": True}
