import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import submit_lead, lead_conversion, three_pl

app = FastAPI()
app.include_router(submit_lead.router)
app.include_router(lead_conversion.router)
app.include_router(three_pl.router)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Welcome to jTU"}


@app.get("/ping")
def ping():
    start = time.process_time()
    time_taken = (time.process_time() - start) * 1000
    return {f"Pong with response time {time_taken} ms"}
