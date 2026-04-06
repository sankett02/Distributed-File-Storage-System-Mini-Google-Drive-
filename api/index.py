import sys
import os

# Add master to the python path so it can import its modules
master_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'master')
sys.path.append(master_dir)

from app import app
from metadata import init_database

# Initialize database on startup (for Vercel serverless environment)
init_database()

# This is required for Vercel
if __name__ == "__main__":
    app.run()
