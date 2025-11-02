"""
Server-side persistent storage system (temporary replacement for database)
Stores data in files on disk to survive deployments and restarts
"""
from flask import session
from datetime import datetime
import secrets
import pickle
import os
import gc
from pathlib import Path

# Storage directory (persistent volume on Fly.io, falls back to /tmp for local dev)
STORAGE_DIR = Path('/data/session_storage') if Path('/data').exists() else Path('/tmp/session_storage')
STORAGE_DIR.mkdir(exist_ok=True, parents=True)

# SERVER-SIDE storage (persisted to disk!)
# Key: session_id, Value: project data
_storage = {}
_loaded = False

def _load_storage():
    """Load storage from disk on first access"""
    global _storage, _loaded
    if _loaded:
        return

    # Load all session files from disk
    for session_file in STORAGE_DIR.glob('*.pkl'):
        try:
            with open(session_file, 'rb') as f:
                session_id = session_file.stem
                _storage[session_id] = pickle.load(f)
        except Exception as e:
            print(f"Warning: Failed to load session {session_file}: {e}")

    _loaded = True
    print(f"✓ Loaded {len(_storage)} sessions from disk")

def _save_session(session_id):
    """Save a single session to disk"""
    if session_id not in _storage:
        return

    try:
        session_file = STORAGE_DIR / f'{session_id}.pkl'
        with open(session_file, 'wb') as f:
            pickle.dump(_storage[session_id], f)
        # Force garbage collection after saving large image data
        gc.collect()
    except Exception as e:
        print(f"Warning: Failed to save session {session_id}: {e}")

def _get_session_id():
    """Get or create session ID (only ID stored in cookie, not data)"""
    if 'storage_id' not in session:
        session['storage_id'] = secrets.token_urlsafe(32)
    return session['storage_id']

def _get_storage():
    """Get storage for current session"""
    _load_storage()  # Load from disk if not already loaded

    session_id = _get_session_id()
    if session_id not in _storage:
        _storage[session_id] = {
            'project': {
                'id': 1,
                'status': 'new',
                'created_at': datetime.utcnow().isoformat()
            },
            'images': [],
            'months': [],
            'preferences': None
        }
        _save_session(session_id)  # Save new session to disk
    return _storage[session_id]

def init_session():
    """Initialize session storage if needed"""
    _get_storage()  # Creates storage if doesn't exist

def get_current_project():
    """Get or create current project"""
    storage = _get_storage()
    return storage['project']

def get_uploaded_images():
    """Get list of uploaded images"""
    storage = _get_storage()
    return storage['images']

def add_uploaded_image(filename, file_data, thumbnail_data):
    """Add an uploaded image"""
    storage = _get_storage()

    # Store binary data directly in server memory (no base64 needed!)
    image_id = len(storage['images']) + 1
    storage['images'].append({
        'id': image_id,
        'filename': filename,
        'file_data': file_data,  # Raw binary data
        'thumbnail_data': thumbnail_data,  # Raw binary data
        'uploaded_at': datetime.utcnow().isoformat()
    })
    _save_session(_get_session_id())  # Persist to disk
    return image_id

def get_image_by_id(image_id):
    """Get image by ID"""
    storage = _get_storage()
    for img in storage['images']:
        if img['id'] == image_id:
            return img
    return None

def delete_image(image_id):
    """Delete an image"""
    storage = _get_storage()
    storage['images'] = [img for img in storage['images'] if img['id'] != image_id]
    _save_session(_get_session_id())  # Persist to disk

def get_all_months():
    """Get all calendar months"""
    storage = _get_storage()
    return storage['months']

def create_months_with_themes(themes):
    """Create 13 images with themes (cover + 12 months)"""
    storage = _get_storage()
    storage['months'] = []

    for month_num in range(0, 13):
        theme = themes[month_num]
        storage['months'].append({
            'id': month_num,
            'month_number': month_num,
            'prompt': theme['title'],
            'generation_status': 'pending',
            'master_image_data': None,  # Raw binary data
            'error_message': None,
            'generated_at': None
        })
    _save_session(_get_session_id())  # Persist to disk

def get_month_by_number(month_num):
    """Get month by number"""
    storage = _get_storage()
    for month in storage['months']:
        if month['month_number'] == month_num:
            return month
    return None

def update_month_status(month_num, status, image_data=None, error=None):
    """Update month generation status"""
    storage = _get_storage()

    for month in storage['months']:
        if month['month_number'] == month_num:
            month['generation_status'] = status

            if image_data:
                # Store as raw binary (no base64 needed in server memory!)
                month['master_image_data'] = image_data
                month['generated_at'] = datetime.utcnow().isoformat()

            if error:
                month['error_message'] = str(error)

            _save_session(_get_session_id())  # Persist to disk
            return month

    return None

def get_month_image_data(month_num):
    """Get binary image data for a month"""
    month = get_month_by_number(month_num)
    if month and month.get('master_image_data'):
        return month['master_image_data']
    return None

def update_project_status(status):
    """Update project status"""
    storage = _get_storage()
    storage['project']['status'] = status
    _save_session(_get_session_id())  # Persist to disk

def get_completion_count():
    """Get number of completed months"""
    storage = _get_storage()
    return sum(1 for m in storage['months'] if m['generation_status'] == 'completed')

def get_preferences():
    """Get user customization preferences"""
    storage = _get_storage()
    return storage.get('preferences')

def set_preferences(preferences):
    """Set user customization preferences"""
    storage = _get_storage()
    storage['preferences'] = preferences
    _save_session(_get_session_id())  # Persist to disk
    return preferences

def clear_session():
    """Clear all session data (for testing)"""
    session_id = _get_session_id()
    if session_id in _storage:
        del _storage[session_id]

    # Delete session file from disk
    session_file = STORAGE_DIR / f'{session_id}.pkl'
    if session_file.exists():
        session_file.unlink()

    session.clear()

def get_months_by_session_id(session_id):
    """Get all months for a specific session ID (used by webhooks)"""
    _load_storage()
    if session_id in _storage:
        return _storage[session_id].get('months', [])
    return []

def save_order_info(session_id, order_data):
    """Save order information to a specific session (used by webhooks)"""
    _load_storage()
    if session_id in _storage:
        _storage[session_id]['order'] = order_data
        _save_session(session_id)
        return True
    return False

def get_order_info_by_session_id(session_id):
    """Get order information for a specific session"""
    _load_storage()
    if session_id in _storage:
        return _storage[session_id].get('order')
    return None
