from flask import Blueprint, jsonify, request
from services.user_service import (get_profile, get_user_by_email, get_users,create_user,create_profile)

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/', methods=['GET'])
def fetch_users():
    users = get_users()
    return jsonify(users), 200

@user_bp.route('/login', methods=['POST'])
def fetch_user_by_email():
    data = request.get_json()  # extract JSON body
    users = get_user_by_email(data["email"])
    return jsonify(users), 200

@user_bp.route('/', methods=['POST'])
def create_user_data():
    data = request.get_json()  # extract JSON body
    print(data)
    if data is None:
        return jsonify({"error": "JSON body required"}), 400
    user =  create_user(data)
    if user:
        return jsonify({"message":"User created successfully", "success":True}), 201
    else:
        return jsonify({"success":False}), 400
    
@user_bp.route('/profile', methods=['POST'])
def create_user_profile():
    data = request.get_json()  # extract JSON body
    # print(data)
    if data is None:
        return jsonify({"error": "JSON body required"}), 400
    # data["user_id"] = 1
    profile =  create_profile(data)
    print("profile",profile)
    if profile:
        return jsonify({"message":"User profile created successfully", "success":True}), 201
    else:
        return jsonify({"success":False}), 400
    
@user_bp.route('/profile/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    print(user_id)
    profile =  get_profile(user_id)
    if profile:
        return jsonify({"data":profile, "success":True}), 200
    else:
        return jsonify({"success":False}), 400