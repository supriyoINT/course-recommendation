from flask import Blueprint, jsonify, request
from services.user_service import (get_users)

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/', methods=['GET'])
def fetch_users():
    users = get_users()
    return jsonify(users), 200