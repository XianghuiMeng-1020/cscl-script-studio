"""Student API: activity by share_code, join, chat, submit, progress. All @login_required; students read-only on script data."""
from flask import Blueprint, request, jsonify
from flask_login import current_user
from app.db import db
from app.models import (
    CSCLScript, CSCLScene, CSCLRole, CSCLScriptlet,
    StudentGroup, StudentGroupMember, GroupMessage, StudentTaskSubmission,
)
from app.auth import login_required
from datetime import datetime

student_api_bp = Blueprint('student_api', __name__, url_prefix='/api/student')


def _script_by_share_code(share_code):
    """Return published script for share_code or None. Lookup is case-insensitive (uppercase)."""
    key = (share_code or '').strip().upper()
    if not key:
        return None
    return CSCLScript.query.filter_by(share_code=key).filter(
        CSCLScript.published_at.isnot(None)
    ).first()


def _group_for_script(script_id):
    """Return the single StudentGroup for this script."""
    return StudentGroup.query.filter_by(script_id=script_id).first()


@student_api_bp.route('/activity/<share_code>', methods=['GET'])
@login_required
def get_activity(share_code):
    """Get published activity detail (scenes, roles, scriptlets). Read-only."""
    script = _script_by_share_code(share_code)
    if not script:
        return jsonify({'error': 'Activity not found or not published', 'code': 'NOT_FOUND'}), 404
    scenes = CSCLScene.query.filter_by(script_id=script.id).order_by(CSCLScene.order_index).all()
    roles = CSCLRole.query.filter_by(script_id=script.id).all()
    out = {
        'id': script.id,
        'title': script.title,
        'topic': script.topic,
        'task_type': script.task_type,
        'duration_minutes': script.duration_minutes,
        'learning_objectives': script.learning_objectives,
        'share_code': script.share_code,
        'scenes': [],
        'roles': [r.to_dict() for r in roles],
    }
    for scene in scenes:
        scene_dict = scene.to_dict()
        scriptlets = CSCLScriptlet.query.filter_by(scene_id=scene.id).all()
        scene_dict['scriptlets'] = [s.to_dict() for s in scriptlets]
        out['scenes'].append(scene_dict)
    return jsonify(out), 200


@student_api_bp.route('/activity/<share_code>/join', methods=['POST'])
@login_required
def join_activity(share_code):
    """Student joins the group; assign a role (round-robin from script roles)."""
    script = _script_by_share_code(share_code)
    if not script:
        return jsonify({'error': 'Activity not found or not published', 'code': 'NOT_FOUND'}), 404
    group = _group_for_script(script.id)
    if not group:
        return jsonify({'error': 'Group not found for activity', 'code': 'NOT_FOUND'}), 404
    member = StudentGroupMember.query.filter_by(group_id=group.id, user_id=current_user.id).first()
    if member:
        return jsonify({
            'joined': True,
            'group_id': group.id,
            'role_label': member.role_label,
            'member': member.to_dict(),
        }), 200
    roles = CSCLRole.query.filter_by(script_id=script.id).order_by(CSCLRole.id).all()
    existing = StudentGroupMember.query.filter_by(group_id=group.id).all()
    role_labels = [r.role_name for r in roles] if roles else []
    idx = len(existing) % len(role_labels) if role_labels else 0
    role_label = role_labels[idx] if role_labels else None
    member = StudentGroupMember(group_id=group.id, user_id=current_user.id, role_label=role_label)
    db.session.add(member)
    db.session.commit()
    return jsonify({
        'joined': True,
        'group_id': group.id,
        'role_label': role_label,
        'member': member.to_dict(),
    }), 200


@student_api_bp.route('/activity/<share_code>/messages', methods=['GET'])
@login_required
def get_messages(share_code):
    """Poll group chat messages: optional limit (default 50) or since (ISO timestamp)."""
    script = _script_by_share_code(share_code)
    if not script:
        return jsonify({'error': 'Activity not found or not published', 'code': 'NOT_FOUND'}), 404
    group = _group_for_script(script.id)
    if not group:
        return jsonify({'error': 'Group not found', 'code': 'NOT_FOUND'}), 404
    limit = min(int(request.args.get('limit', 50)), 100)
    since = request.args.get('since')
    q = GroupMessage.query.filter_by(group_id=group.id).order_by(GroupMessage.created_at.desc())
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
            q = q.filter(GroupMessage.created_at > since_dt)
        except Exception:
            pass
    messages = q.limit(limit).all()
    messages = list(reversed(messages))
    return jsonify({'messages': [m.to_dict() for m in messages]}), 200


@student_api_bp.route('/activity/<share_code>/messages', methods=['POST'])
@login_required
def post_message(share_code):
    """Send a chat message to the group."""
    script = _script_by_share_code(share_code)
    if not script:
        return jsonify({'error': 'Activity not found or not published', 'code': 'NOT_FOUND'}), 404
    group = _group_for_script(script.id)
    if not group:
        return jsonify({'error': 'Group not found', 'code': 'NOT_FOUND'}), 404
    member = StudentGroupMember.query.filter_by(group_id=group.id, user_id=current_user.id).first()
    if not member:
        return jsonify({'error': 'Join the activity first', 'code': 'NOT_JOINED'}), 403
    data = request.get_json() or {}
    content = (data.get('content') or '').strip()
    if not content:
        return jsonify({'error': 'content is required', 'code': 'VALIDATION'}), 400
    msg = GroupMessage(group_id=group.id, user_id=current_user.id, content=content[:5000])
    db.session.add(msg)
    db.session.commit()
    return jsonify(msg.to_dict()), 201


@student_api_bp.route('/activity/<share_code>/scenes/<scene_id>/submit', methods=['POST'])
@login_required
def submit_scene(share_code, scene_id):
    """Submit work for a scene task. Body: { content?, status? }. status: pending | submitted | reviewed."""
    script = _script_by_share_code(share_code)
    if not script:
        return jsonify({'error': 'Activity not found or not published', 'code': 'NOT_FOUND'}), 404
    scene = CSCLScene.query.filter_by(id=scene_id, script_id=script.id).first()
    if not scene:
        return jsonify({'error': 'Scene not found', 'code': 'NOT_FOUND'}), 404
    group = _group_for_script(script.id)
    if not group:
        return jsonify({'error': 'Group not found', 'code': 'NOT_FOUND'}), 404
    member = StudentGroupMember.query.filter_by(group_id=group.id, user_id=current_user.id).first()
    if not member:
        return jsonify({'error': 'Join the activity first', 'code': 'NOT_JOINED'}), 403
    data = request.get_json() or {}
    content = data.get('content')
    status = (data.get('status') or 'submitted').strip().lower()
    if status not in ('pending', 'submitted', 'reviewed'):
        status = 'submitted'
    sub = StudentTaskSubmission.query.filter_by(
        script_id=script.id, scene_id=scene_id, user_id=current_user.id
    ).first()
    if sub:
        if content is not None:
            sub.content = content
        sub.status = status
        if status == 'submitted':
            sub.submitted_at = datetime.utcnow()
        db.session.commit()
        return jsonify(sub.to_dict()), 200
    sub = StudentTaskSubmission(
        script_id=script.id,
        scene_id=scene_id,
        user_id=current_user.id,
        content=content,
        status=status,
        submitted_at=datetime.utcnow() if status == 'submitted' else None,
    )
    db.session.add(sub)
    db.session.commit()
    return jsonify(sub.to_dict()), 201


@student_api_bp.route('/activity/<share_code>/progress', methods=['GET'])
@login_required
def get_progress(share_code):
    """Get current user's submission progress for this activity."""
    script = _script_by_share_code(share_code)
    if not script:
        return jsonify({'error': 'Activity not found or not published', 'code': 'NOT_FOUND'}), 404
    subs = StudentTaskSubmission.query.filter_by(
        script_id=script.id, user_id=current_user.id
    ).all()
    return jsonify({'submissions': [s.to_dict() for s in subs]}), 200


@student_api_bp.route('/my-activities', methods=['GET'])
@login_required
def my_activities():
    """List all activities this student has joined (groups they are member of)."""
    members = StudentGroupMember.query.filter_by(user_id=current_user.id).all()
    group_ids = [m.group_id for m in members]
    groups = StudentGroup.query.filter(StudentGroup.id.in_(group_ids)).all() if group_ids else []
    script_ids = list({g.script_id for g in groups})
    scripts = CSCLScript.query.filter(
        CSCLScript.id.in_(script_ids),
        CSCLScript.published_at.isnot(None),
    ).all() if script_ids else []
    group_by_script = {g.script_id: g for g in groups}
    member_by_group = {m.group_id: m for m in members}
    out = []
    for script in scripts:
        g = group_by_script.get(script.id)
        m = member_by_group.get(g.id) if g else None
        out.append({
            'script': script.to_dict(),
            'share_code': script.share_code,
            'group_id': g.id if g else None,
            'role_label': m.role_label if m else None,
            'joined_at': m.joined_at.isoformat() if m and m.joined_at else None,
        })
    return jsonify({'activities': out}), 200
