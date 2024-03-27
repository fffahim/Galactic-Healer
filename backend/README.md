# rqmo_backend

## RUN BACKEND
```bash
$ cd backend
$ pip install -r requirements.txt
$ export MILVUS_KEY=your_milvus_key
$ export MILVUS_HOST=your_milvus_host
$ export MONGO_URI=your_mongo_uri
$ export OPENAI_API_KEY=your_openai_api_key
$ export SQL_PASS=your_sql_password
$ export SQL_USER=your_sql_user
$ export SQL_URI=your_sql_uri
$ uvicorn app.main:app --reload
```

## DEPLOY BACKEND
Follow link to deploy on Azure Web Apps [Deploy to Azure](https://docs.microsoft.com/en-us/azure/app-service/quickstart-python?tabs=bash&pivots=python-framework-fastapi)
```bash
$ gunicon app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```
