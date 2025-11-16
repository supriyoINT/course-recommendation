from flask import Flask,jsonify,request
from config import Config
from db import get_db
from routes.user_routes import user_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(user_bp, url_prefix='/users')

    @app.route('/')
    def home():
        return jsonify({"message": "Welcome to the Course Recommendation API"}), 200

    return app



if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)