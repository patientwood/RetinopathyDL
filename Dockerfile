
FROM node:18-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /code

COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt

COPY ./app /code/app
COPY ./MODELS /code/MODELS

COPY --from=frontend-build /frontend/build /code/frontend/build

EXPOSE 8000

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]