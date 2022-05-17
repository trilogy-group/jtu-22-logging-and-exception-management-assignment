FROM python:3.9
WORKDIR /app
EXPOSE 8000
COPY ./fast_api_als/requirements.txt .
RUN pip3 install -r requirements.txt
COPY . .
ENTRYPOINT ["uvicorn", "fast_api_als.main:app"]