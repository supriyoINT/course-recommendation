from flask import Flask,jsonify,request
from flask_cors import CORS
from config import Config
from db import get_db
from recommender import recommend_courses
from routes.user_routes import user_bp
from services.recommendation_service import get_all_questions, get_recommendation, get_recommendation_based_on_skill, get_required_step_by_user_goal, get_topics_based_on_user, goal_step_map
from services.user_service import create_user_goal, get_goal_steps, get_user_goals, run_generate_mcq

def create_app():
    app = Flask(__name__)
    CORS(app) 
    app.config.from_object(Config)

    app.register_blueprint(user_bp, url_prefix='/users')
    
    @app.route('/user-recommendation/<int:user_id>', methods=["GET"])
    def get_user_recommendation(user_id):
        result = get_recommendation(user_id)
        if result is None:
            return jsonify({"status": "failure", "message": "No recommendation found"}), 404
        
        return jsonify({"status": "success", "data": result}), 200
    
    @app.route('/user-topic-recommendation/<int:user_id>', methods=["GET"])
    def get_topics_for_user(user_id):
        result = get_topics_based_on_user(user_id)
        return jsonify({"status": "success", "data": result}), 200
    
    @app.route('/generate-questions', methods=["POST"])
    def generate_questions():
        data = request.json
        print(data["topics"])
        result = get_all_questions(data["topics"])
        return jsonify({"status": "success", "data": result}), 200

    @app.route('/')
    def home():
        print("home")
        return jsonify({"message": "Welcome to the Course Recommendation API"}), 200
    
    @app.route("/recommend", methods=["GET"])
    def recommend():
        print('recommend')
        query = request.args.get("query")
        
        if not query:
            return jsonify({"error": "Missing ?query= parameter"}), 400
        
        results = recommend_courses(query)
        return jsonify({"results": results})
    

    # this will generate steps based on user goal
    @app.route('/generate-steps', methods=["POST"])
    def generate_steps():
        data = request.json
        print(data["goal"])
        result = get_required_step_by_user_goal(data["goal"])
        return jsonify({"status": "success", "data": result}), 200
    
    @app.route('/user-goals', methods=["POST"])
    def create_goal():
        data = request.json
        print(data["goal"])
        
        goal_id = create_user_goal(data)
        result = get_required_step_by_user_goal(data["goal"])
        goal_step_map(goal_id, result)
        return jsonify({"status": "success", "data": {"goal_id": goal_id, "goal": data["goal"]}}), 200
    
    @app.route('/user-goals/<int:user_id>', methods=["GET"])
    def get_goals(user_id):
        result = get_user_goals(user_id)
        return jsonify({"status": "success", "data": result}), 200  
    
    @app.route('/user-goals-steps/<int:goal_id>', methods=["GET"])
    def goals_steps(goal_id):
        print(goal_id)
        result = get_goal_steps(goal_id)
        return jsonify({"status": "success", "data": result}), 200  
    
    @app.route('/generate-mcq', methods=["POST"])
    def generate_mcq():
        data = request.json
        print(data["topic"])
        result = run_generate_mcq(data["topic"])
        return jsonify({"status": "success", "data": result}), 200  
    
    @app.route('/recommended_course_based_on_skill', methods=["POST"])
    def generate_recommended_course():
        data = request.json
        result = get_recommendation_based_on_skill(data)
        return jsonify({"status": "success", "data": result}), 200  
    


    return app



if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)