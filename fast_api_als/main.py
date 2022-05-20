import time
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fast_api_als.routers import users, lead_conversion , submit_lead, reinforcement, oem, three_pl, quicksight

app = FastAPI()
app.include_router(users.router)
app.include_router(submit_lead.router)
app.include_router(lead_conversion.router)
app.include_router(reinforcement.router)
app.include_router(oem.router)
app.include_router(three_pl.router)
app.include_router(quicksight.router)

# only present during test development
# app.include_router(test_api.router)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s')



@app.get("/")
def root():
    logging.info("Welcome page loaded successfully.")
    return {"message": "Welcome to jTU"}


@app.get("/ping")
def ping():
    start = time.process_time()
    time_taken = (time.process_time() - start) * 1000
    logging.info("Ping took" + str(time_taken)+" ms")
    return {f"Pong with response time {time_taken} ms"}