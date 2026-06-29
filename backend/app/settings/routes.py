from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from backend.app import db
from backend.app.models import User, SchoolSettings

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
    school = SchoolSettings.query.first()
    if not school:
        school = SchoolSettings()
        db.session.add(school)
        db.session.commit()

    return jsonify({'school': school.to_dict()}), 200


@settings_bp.route('/school', methods=['PUT'])
@jwt_required()
def update_school_settings():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    school = SchoolSettings.query.first()
    if not school:
        school = SchoolSettings()
        db.session.add(school)

    data = request.get_json()

    if 'school_name' in data:
        school.school_name = data['school_name']
    if 'motto' in data:
        school.motto = data['motto']
    if 'email' in data:
        school.email = data['email']
    if 'phone' in data:
        school.phone = data['phone']
    if 'address' in data:
        school.address = data['address']
    if 'logo_url' in data:
        school.logo_url = data['logo_url']
    if 'website' in data:
        school.website = data['website']
    if 'academic_year' in data:
        school.academic_year = data['academic_year']
    if 'current_term' in data:
        school.current_term = data['current_term']

    db.session.commit()

    return jsonify({'school': school.to_dict()}), 200
