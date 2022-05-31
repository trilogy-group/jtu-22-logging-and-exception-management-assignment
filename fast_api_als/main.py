import logging
import time

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
    return {"message": "Welcome to jTU"}


@app.get("/ping")
def ping():
    start = time.process_time()
    time_taken = (time.process_time() - start) * 1000
    return {f"Pong with response time {time_taken} ms"}

def main():
    # setting up global logging configuration with threshold level = INFO and truncate on restart
    FORMAT = '%(name)s %(asctime)s %(levelname)s:%(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO, filename='fast_api_als.log', filemode='w')


if __name__ == '__main__':
    main()