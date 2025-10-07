from app import app, db
from app.models import Text, AnalysisResult, ACMTopic
from app.ai_generator import initialize_acm_topics


def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

        # Initialize ACM topics
        initialize_acm_topics()
        print("ACM topics initialized!")


if __name__ == '__main__':
    init_db()