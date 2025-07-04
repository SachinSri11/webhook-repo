from flask import Flask
from app.extensions import init_mongo
from dotenv import load_dotenv
import os

def create_app():
    app = Flask(__name__)

    # ✅ Load .env file from root directory
    load_dotenv()

    # ✅ Set config from environment variables
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")

    init_mongo(app)

    from app.webhook.routes import webhook_bp
    app.register_blueprint(webhook_bp)

    return app
