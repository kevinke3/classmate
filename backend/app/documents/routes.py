import os
import uuid
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from backend.app import db
from backend.app.models import Document

documents_bp = Blueprint('documents', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@documents_bp.route('/', methods=['GET'])
@jwt_required()
def get_documents():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category')
    student_id = request.args.get('student_id', type=int)

    query = Document.query

    if category:
        query = query.filter_by(category=category)
    if student_id:
        query = query.filter_by(student_id=student_id)

    pagination = query.order_by(Document.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'documents': [d.to_dict() for d in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages
    }), 200


@documents_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_document():
    current_user_id = int(get_jwt_identity())

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{extension}"

    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    document = Document(
        student_id=request.form.get('student_id', type=int),
        uploaded_by=current_user_id,
        filename=filename,
        original_filename=original_filename,
        file_type=extension,
        file_size=os.path.getsize(file_path),
        category=request.form.get('category', 'general'),
        description=request.form.get('description')
    )
    db.session.add(document)
    db.session.commit()

    return jsonify({'document': document.to_dict()}), 201


@documents_bp.route('/<int:document_id>/download', methods=['GET'])
@jwt_required()
def download_document(document_id):
    document = Document.query.get_or_404(document_id)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], document.filename)

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name=document.original_filename
    )


@documents_bp.route('/<int:document_id>', methods=['DELETE'])
@jwt_required()
def delete_document(document_id):
    document = Document.query.get_or_404(document_id)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], document.filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(document)
    db.session.commit()

    return jsonify({'message': 'Document deleted'}), 200
