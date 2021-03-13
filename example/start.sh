python init_database.py &&
uvicorn app:init_app --port 5000 --host 0.0.0.0 --factory --workers 3