#!/bin/bash
pip install -r requirements.txt

# Create static directories
mkdir -p static/uploads

# Initialize database
python -c "from database import init_db; init_db()"