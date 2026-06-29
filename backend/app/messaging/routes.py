from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import emit, join_room, leave_room

from backend.app import db, socketio
from backend.app.models import Message, Channel, ChannelMember, User

messaging_bp = Blueprint('messaging', __name__)


@messaging_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    current_user_id = int(get_jwt_identity())

    sent = Message.query.filter_by(sender_id=current_user_id, message_type='direct').all()
    received = Message.query.filter_by(recipient_id=current_user_id, message_type='direct').all()

    user_ids = set()
    for msg in sent:
        if msg.recipient_id:
            user_ids.add(msg.recipient_id)
    for msg in received:
        user_ids.add(msg.sender_id)

    conversations = []
    for uid in user_ids:
        user = User.query.get(uid)
        last_msg = Message.query.filter(
            db.or_(
                db.and_(Message.sender_id == current_user_id, Message.recipient_id == uid),
                db.and_(Message.sender_id == uid, Message.recipient_id == current_user_id)
            )
        ).order_by(Message.created_at.desc()).first()

        unread = Message.query.filter_by(
            sender_id=uid, recipient_id=current_user_id, is_read=False
        ).count()

        if user and last_msg:
            conversations.append({
                'user': user.to_dict(),
                'last_message': last_msg.to_dict(),
                'unread_count': unread
            })

    conversations.sort(key=lambda x: x['last_message']['created_at'], reverse=True)

    return jsonify({'conversations': conversations}), 200


@messaging_bp.route('/messages/<int:user_id>', methods=['GET'])
@jwt_required()
def get_messages(user_id):
    current_user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user_id, Message.recipient_id == user_id),
            db.and_(Message.sender_id == user_id, Message.recipient_id == current_user_id)
        )
    ).order_by(Message.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    Message.query.filter_by(
        sender_id=user_id, recipient_id=current_user_id, is_read=False
    ).update({'is_read': True})
    db.session.commit()

    return jsonify({
        'messages': [m.to_dict() for m in messages.items],
        'total': messages.total,
        'pages': messages.pages
    }), 200


@messaging_bp.route('/messages', methods=['POST'])
@jwt_required()
def send_message():
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    message = Message(
        sender_id=current_user_id,
        recipient_id=data.get('recipient_id'),
        channel_id=data.get('channel_id'),
        subject=data.get('subject'),
        body=data['body'],
        message_type=data.get('message_type', 'direct')
    )
    db.session.add(message)
    db.session.commit()

    if message.recipient_id:
        socketio.emit('new_message', message.to_dict(), room=f'user_{message.recipient_id}')

    return jsonify({'message': message.to_dict()}), 201


@messaging_bp.route('/channels', methods=['GET'])
@jwt_required()
def get_channels():
    current_user_id = int(get_jwt_identity())

    memberships = ChannelMember.query.filter_by(user_id=current_user_id).all()
    channel_ids = [m.channel_id for m in memberships]

    channels = Channel.query.filter(Channel.id.in_(channel_ids)).all()

    return jsonify({
        'channels': [{
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'channel_type': c.channel_type
        } for c in channels]
    }), 200


@socketio.on('join')
def on_join(data):
    room = data.get('room')
    if room:
        join_room(room)


@socketio.on('leave')
def on_leave(data):
    room = data.get('room')
    if room:
        leave_room(room)


@socketio.on('send_message')
def handle_message(data):
    message = Message(
        sender_id=data['sender_id'],
        recipient_id=data.get('recipient_id'),
        channel_id=data.get('channel_id'),
        body=data['body'],
        message_type=data.get('message_type', 'direct')
    )
    db.session.add(message)
    db.session.commit()

    if message.recipient_id:
        emit('new_message', message.to_dict(), room=f'user_{message.recipient_id}')
    elif message.channel_id:
        emit('new_message', message.to_dict(), room=f'channel_{message.channel_id}')
