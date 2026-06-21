from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from backend.app import db
from backend.app.models import User

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    return jsonify({'profile': user.to_dict()}), 200


@settings_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    data = request.get_json()

    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'phone' in data:
        user.phone = data['phone']
    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']

    db.session.commit()

    return jsonify({'profile': user.to_dict()}), 200


@settings_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    data = request.get_json()

    if not user.check_password(data.get('current_password', '')):
        return jsonify({'error': 'Current password is incorrect'}), 400

    user.set_password(data['new_password'])
    db.session.commit()

    return jsonify({'message': 'Password changed successfully'}), 200


@settings_bp.route('/school', methods=['GET'])
@jwt_required()
def get_school_settings():
    return jsonify({
        'school': {
            'name': 'ClassMate Academy',
            'motto': 'Excellence in Education',
            'address': 'Nairobi, Kenya',
            'phone': '+254 700 000 000',
            'email': 'info@classmate.io',
            'academic_year': '2025',
            'current_term': 'Term 1'
        }
    }), 200
