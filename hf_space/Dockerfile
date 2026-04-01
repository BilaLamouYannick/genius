FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn pydantic numpy scikit-learn xgboost

COPY api/ ./api/
COPY models/xgboost_pm25_genius.pkl ./models/xgboost_pm25_genius.pkl
COPY models/model_metadata.json ./models/model_metadata.json

EXPOSE 7860

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
