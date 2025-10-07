from app import app, db
from app.routes import initialize_app
import os

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database and app
with app.app_context():
    db.create_all()
    initialize_app()
    print("Database initialized and app configured")

if __name__ == '__main__':
    app.run(debug=True)