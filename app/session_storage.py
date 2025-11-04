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
        # New multi-project + cart structure
        project_id = secrets.token_urlsafe(16)
        _storage[session_id] = {
            'projects': [
                {
                    'id': project_id,
                    'status': 'new',
                    'created_at': datetime.utcnow().isoformat(),
                    'images': [],
                    'months': [],
                    'preferences': None
                }
            ],
            'active_project_id': project_id,
            'cart': []
        }
        _save_session(session_id)  # Save new session to disk
    else:
        # MIGRATION: Convert old single-project format to new multi-project format
        storage = _storage[session_id]
        if 'project' in storage and 'projects' not in storage:
            # Old format detected - migrate to new format
            old_project = storage['project']
            project_id = secrets.token_urlsafe(16)

            _storage[session_id] = {
                'projects': [
                    {
                        'id': project_id,
                        'status': old_project.get('status', 'new'),
                        'created_at': old_project.get('created_at', datetime.utcnow().isoformat()),
                        'images': storage.get('images', []),
                        'months': storage.get('months', []),
                        'preferences': storage.get('preferences')
                    }
                ],
                'active_project_id': project_id,
                'cart': [],
                # Preserve order info and mockups if they exist
                'order': storage.get('order'),
                'preview_mockups': storage.get('preview_mockups', {}),
                'preview_mockup': storage.get('preview_mockup')
            }
            _save_session(session_id)

    return _storage[session_id]

def init_session():
    """Initialize session storage if needed"""
    _get_storage()  # Creates storage if doesn't exist

def _get_active_project():
    """Internal: Get active project object"""
    storage = _get_storage()
    active_id = storage['active_project_id']
    for project in storage['projects']:
        if project['id'] == active_id:
            return project
    # Fallback: return first project if active not found
    if storage['projects']:
        storage['active_project_id'] = storage['projects'][0]['id']
        _save_session(_get_session_id())
        return storage['projects'][0]
    # No projects exist - create one
    project_id = secrets.token_urlsafe(16)
    new_project = {
        'id': project_id,
        'status': 'new',
        'created_at': datetime.utcnow().isoformat(),
        'images': [],
        'months': [],
        'preferences': None
    }
    storage['projects'].append(new_project)
    storage['active_project_id'] = project_id
    _save_session(_get_session_id())
    return new_project

def get_current_project():
    """Get or create current project (backward compatible)"""
    project = _get_active_project()
    # Return in old format for backward compatibility
    return {
        'id': project['id'],
        'status': project['status'],
        'created_at': project['created_at']
    }

def get_uploaded_images():
    """Get list of uploaded images for active project"""
    project = _get_active_project()
    return project.get('images', [])

def add_uploaded_image(filename, file_data, thumbnail_data):
    """Add an uploaded image to active project"""
    project = _get_active_project()

    # Store binary data directly in server memory (no base64 needed!)
    image_id = len(project['images']) + 1
    project['images'].append({
        'id': image_id,
        'filename': filename,
        'file_data': file_data,  # Raw binary data
        'thumbnail_data': thumbnail_data,  # Raw binary data
        'uploaded_at': datetime.utcnow().isoformat()
    })
    _save_session(_get_session_id())  # Persist to disk
    return image_id

def get_image_by_id(image_id):
    """Get image by ID from active project"""
    project = _get_active_project()
    for img in project.get('images', []):
        if img['id'] == image_id:
            return img
    return None

def delete_image(image_id):
    """Delete an image from active project"""
    project = _get_active_project()
    project['images'] = [img for img in project.get('images', []) if img['id'] != image_id]
    _save_session(_get_session_id())  # Persist to disk

def get_all_months():
    """Get all calendar months for active project"""
    project = _get_active_project()
    return project.get('months', [])

def create_months_with_themes(themes):
    """Create 13 images with themes (cover + 12 months) for active project"""
    project = _get_active_project()
    project['months'] = []

    for month_num in range(0, 13):
        theme = themes[month_num]
        project['months'].append({
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
    """Get month by number from active project"""
    project = _get_active_project()
    for month in project.get('months', []):
        if month['month_number'] == month_num:
            return month
    return None

def update_month_status(month_num, status, image_data=None, error=None):
    """Update month generation status for active project"""
    project = _get_active_project()

    for month in project.get('months', []):
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
    """Update active project status"""
    project = _get_active_project()
    project['status'] = status
    _save_session(_get_session_id())  # Persist to disk

def get_completion_count():
    """Get number of completed months for active project"""
    project = _get_active_project()
    return sum(1 for m in project.get('months', []) if m['generation_status'] == 'completed')

def get_preferences():
    """Get user customization preferences for active project"""
    project = _get_active_project()
    return project.get('preferences')

def set_preferences(preferences):
    """Set user customization preferences for active project"""
    project = _get_active_project()
    project['preferences'] = preferences
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

# ============================================================================
# MULTI-PROJECT CART FUNCTIONS
# ============================================================================

# Product pricing (must match checkout.html)
PRODUCT_PRICES = {
    'desktop': 19.99,
    'wall_calendar': 29.99
}

def create_new_project():
    """Create a new project and make it active"""
    storage = _get_storage()
    project_id = secrets.token_urlsafe(16)

    new_project = {
        'id': project_id,
        'status': 'new',
        'created_at': datetime.utcnow().isoformat(),
        'images': [],
        'months': [],
        'preferences': None
    }

    storage['projects'].append(new_project)
    storage['active_project_id'] = project_id
    _save_session(_get_session_id())

    return project_id

def get_project_by_id(project_id):
    """Get a specific project by ID"""
    storage = _get_storage()
    for project in storage['projects']:
        if project['id'] == project_id:
            return project
    return None

def add_to_cart(project_id, product_type):
    """Add a project to the cart with specified product type"""
    storage = _get_storage()

    # Validate product type
    if product_type not in PRODUCT_PRICES:
        raise ValueError(f"Invalid product type: {product_type}")

    # Verify project exists
    project = get_project_by_id(project_id)
    if not project:
        raise ValueError(f"Project not found: {project_id}")

    # Check if this project+product combo already in cart
    for item in storage['cart']:
        if item['project_id'] == project_id and item['product_type'] == product_type:
            # Already in cart - don't add duplicate
            return item['id']

    # Create cart item
    cart_item_id = secrets.token_urlsafe(16)
    cart_item = {
        'id': cart_item_id,
        'project_id': project_id,
        'product_type': product_type,
        'price': PRODUCT_PRICES[product_type],
        'added_at': datetime.utcnow().isoformat()
    }

    storage['cart'].append(cart_item)
    _save_session(_get_session_id())

    return cart_item_id

def get_cart_items():
    """Get all cart items with project details"""
    storage = _get_storage()
    cart_items_with_details = []

    for cart_item in storage['cart']:
        project = get_project_by_id(cart_item['project_id'])
        if project:
            # Get cover image (month 0) for preview
            cover_month = None
            for month in project.get('months', []):
                if month['month_number'] == 0:
                    cover_month = month
                    break

            cart_items_with_details.append({
                'id': cart_item['id'],
                'project_id': cart_item['project_id'],
                'product_type': cart_item['product_type'],
                'price': cart_item['price'],
                'added_at': cart_item['added_at'],
                'project_created_at': project['created_at'],
                'has_cover_image': cover_month is not None and cover_month.get('generation_status') == 'completed'
            })

    return cart_items_with_details

def get_cart_count():
    """Get number of items in cart"""
    storage = _get_storage()
    return len(storage['cart'])

def get_cart_total():
    """Get total price of all cart items"""
    storage = _get_storage()
    return sum(item['price'] for item in storage['cart'])

def remove_from_cart(cart_item_id):
    """Remove an item from the cart"""
    storage = _get_storage()
    storage['cart'] = [item for item in storage['cart'] if item['id'] != cart_item_id]
    _save_session(_get_session_id())

def clear_cart():
    """Remove all items from cart"""
    storage = _get_storage()
    storage['cart'] = []
    _save_session(_get_session_id())

def clear_cart_by_session_id(session_id):
    """Clear cart for a specific session ID (used by webhooks)"""
    _load_storage()
    if session_id in _storage:
        _storage[session_id]['cart'] = []
        _save_session(session_id)
        return True
    return False

# ============================================================================
# WEBHOOK FUNCTIONS (Multi-Session Access)
# ============================================================================

def get_months_by_session_id(session_id, project_id=None):
    """Get all months for a specific session ID (used by webhooks)

    Args:
        session_id: The session ID
        project_id: Optional project ID. If None, returns active project's months.
    """
    _load_storage()
    if session_id not in _storage:
        return []

    storage = _storage[session_id]

    # Handle old format (backward compatibility)
    if 'months' in storage and 'projects' not in storage:
        return storage['months']

    # New multi-project format
    if project_id:
        # Get specific project
        for project in storage.get('projects', []):
            if project['id'] == project_id:
                return project.get('months', [])
        return []
    else:
        # Get active project
        active_id = storage.get('active_project_id')
        if active_id:
            for project in storage.get('projects', []):
                if project['id'] == active_id:
                    return project.get('months', [])
        # Fallback: first project
        if storage.get('projects'):
            return storage['projects'][0].get('months', [])
        return []

def get_cart_by_session_id(session_id):
    """Get cart items for a specific session ID (used by webhooks)"""
    _load_storage()
    if session_id in _storage:
        return _storage[session_id].get('cart', [])
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

def save_preview_mockup_data(mockup_data, product_type='calendar_2026'):
    """
    Save Printify preview mockup data to session

    Args:
        mockup_data: Dict with product_id, variant_id, mockup_images, etc.
        product_type: 'calendar_2026', 'desktop', or 'standard_wall'
    """
    storage = _get_storage()

    # Store mockups as dict by product type
    if 'preview_mockups' not in storage:
        storage['preview_mockups'] = {}

    storage['preview_mockups'][product_type] = mockup_data
    _save_session(_get_session_id())

def get_preview_mockup_data(product_type=None):
    """
    Get preview mockup data from session

    Args:
        product_type: Optional specific product type. If None, returns all mockups.

    Returns:
        dict: Single mockup data if product_type specified, or dict of all mockups
    """
    storage = _get_storage()
    mockups = storage.get('preview_mockups', {})

    if product_type:
        return mockups.get(product_type)

    # Legacy support: check for old single mockup format
    if not mockups and 'preview_mockup' in storage:
        return {'calendar_2026': storage.get('preview_mockup')}

    return mockups

def get_preview_mockup_by_session_id(session_id):
    """Get preview mockup data for a specific session (used by webhooks)"""
    _load_storage()
    if session_id in _storage:
        # Return all mockups (new format) or single mockup (legacy)
        mockups = _storage[session_id].get('preview_mockups', {})
        if not mockups:
            # Legacy support
            single_mockup = _storage[session_id].get('preview_mockup')
            if single_mockup:
                return {'calendar_2026': single_mockup}
        return mockups
    return None
