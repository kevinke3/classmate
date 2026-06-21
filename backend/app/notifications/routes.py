from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.app import db
from backend.app.models import Notification, Announcement

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    current_user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    unread_only = request.args.get('unread_only', 'false') == 'true'

    query = Notification.query.filter_by(user_id=current_user_id)

    if unread_only:
        query = query.filter_by(is_read=False)

    pagination = query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    unread_count = Notification.query.filter_by(
        user_id=current_user_id, is_read=False
    ).count()

    return jsonify({
        'notifications': [n.to_dict() for n in pagination.items],
        'total': pagination.total,
        'unread_count': unread_count
    }), 200


@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(notification_id):
    current_user_id = int(get_jwt_identity())
    notification = Notification.query.filter_by(
        id=notification_id, user_id=current_user_id
    ).first_or_404()

    notification.is_read = True
    db.session.commit()

    return jsonify({'message': 'Notification marked as read'}), 200


@notifications_bp.route('/mark-all-read', methods=['PUT'])
@jwt_required()
def mark_all_read():
    current_user_id = int(get_jwt_identity())
    Notification.query.filter_by(
        user_id=current_user_id, is_read=False
    ).update({'is_read': True})
    db.session.commit()

    return jsonify({'message': 'All notifications marked as read'}), 200


@notifications_bp.route('/announcements', methods=['GET'])
@jwt_required()
def get_announcements():
    announcements = Announcement.query.order_by(
        Announcement.created_at.desc()
    ).limit(20).all()

    return jsonify({'announcements': [a.to_dict() for a in announcements]}), 200


@notifications_bp.route('/announcements', methods=['POST'])
@jwt_required()
def create_announcement():
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    announcement = Announcement(
        title=data['title'],
        body=data['body'],
        target_role=data.get('target_role'),
        priority=data.get('priority', 'normal'),
        created_by=current_user_id
    )
    db.session.add(announcement)
    db.session.commit()

    return jsonify({'announcement': announcement.to_dict()}), 201
