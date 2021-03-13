python init_database.py &&
uvicorn example.app:init_app --port 5000 --host 0.0.0.0 --factory --workers 3