import time
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fast_api_als.routers import users, submit_lead, lead_conversion, reinforcement, oem, three_pl, quicksight

app = FastAPI()
app.include_router(users.router)
app.include_router(submit_lead.router)
app.include_router(lead_conversion.router)
app.include_router(reinforcement.router)
app.include_router(oem.router)
app.include_router(three_pl.router)
app.include_router(quicksight.router)

logging.basicConfig(level=logging.DEBUG , format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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


@app.get("/")
def root():
    logging.info("The welcome page is loaded")
    return {"message": "Welcome to jTU"}


@app.get("/ping")
def ping():
    logging.debug("The ping function has been entered ")
    start = time.process_time()
    time_taken = (time.process_time() - start) * 1000
    logging.info("The time taken by the ping function is " + str(time_taken) + " ms")
    return {f"Pong with response time {time_taken} ms"}
