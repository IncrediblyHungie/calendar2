"""
Server-side persistent storage system (temporary replacement for database)
Stores data in files on disk to survive deployments and restarts
"""
from flask import session, current_app
from datetime import datetime
import secrets
import pickle
import os
import gc
from pathlib import Path
import sys

# Storage directory (persistent volume on Fly.io, falls back to /tmp for local dev)
STORAGE_DIR = Path('/data/session_storage') if Path('/data').exists() else Path('/tmp/session_storage')
STORAGE_DIR.mkdir(exist_ok=True, parents=True)

# SERVER-SIDE storage (persisted to disk!)
# Key: session_id, Value: project data
_storage = {}
_loaded = False

def _log(msg):
    """Log message using Flask logger if available, otherwise print with flush"""
    try:
        current_app.logger.info(msg)
    except:
        print(msg, flush=True)
        sys.stdout.flush()

def _load_storage(force_reload=False):
    """Load storage from disk on first access"""
    global _storage, _loaded
    if _loaded and not force_reload:
        return

    # Load all session files from disk
    if force_reload:
        _storage.clear()  # Clear existing data when force reloading
    for session_file in STORAGE_DIR.glob('*.pkl'):
        try:
            with open(session_file, 'rb') as f:
                session_id = session_file.stem
                _storage[session_id] = pickle.load(f)
        except Exception as e:
            print(f"Warning: Failed to load session {session_file}: {e}")

    _loaded = True
    if force_reload:
        print(f"♻️  Force reloaded {len(_storage)} sessions from disk")
    else:
        print(f"✓ Loaded {len(_storage)} sessions from disk")

def _save_session(session_id):
    """Save a single session to disk"""
    if session_id not in _storage:
        return

    try:
        import os
        session_file = STORAGE_DIR / f'{session_id}.pkl'
        with open(session_file, 'wb') as f:
            pickle.dump(_storage[session_id], f)
            f.flush()  # Flush Python buffers to OS
            os.fsync(f.fileno())  # Force OS to write to disk immediately
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
            # MIGRATION: Add new fields to existing projects
            if 'generation_stage' not in project:
                project['preview_expiry'] = None
                project['payment_method_id'] = None
                project['setup_intent_id'] = None
                # Determine stage based on existing data
                months = project.get('months', [])
                if not months:
                    project['generation_stage'] = 'not_started'
                elif len(months) == 3 and all(m.get('generation_status') == 'completed' for m in months):
                    # 3 preview months complete → show payment gate
                    project['generation_stage'] = 'preview_only'
                elif len(months) == 13 and all(m.get('generation_status') == 'completed' for m in months):
                    # All 13 months complete → show product selection
                    project['generation_stage'] = 'fully_generated'
                else:
                    # Generation in progress
                    project['generation_stage'] = 'generating_full' if len(months) > 3 else 'preview_only'
                project['generation_progress'] = 0
                _save_session(_get_session_id())
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
        'preferences': None,
        # New fields for 3-month preview system
        'preview_expiry': None,
        'payment_method_id': None,
        'setup_intent_id': None,
        'generation_stage': 'not_started',
        'generation_progress': 0
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
    images = project.get('images', [])
    _log(f"📥 get_uploaded_images() called:")
    _log(f"   Project ID: {project['id']}")
    _log(f"   Found {len(images)} images")
    if images:
        _log(f"   Image IDs: {[img['id'] for img in images]}")
        _log(f"   Filenames: {[img['filename'] for img in images]}")
    return images

def get_uploaded_images_by_session_id(session_id, project_id=None):
    """Get uploaded images for a specific session (used by webhooks)"""
    _load_storage()
    if session_id not in _storage:
        return []

    storage = _storage[session_id]

    # If project_id specified, get that specific project
    if project_id:
        for project in storage.get('projects', []):
            if project['id'] == project_id:
                return project.get('images', [])
        return []

    # Otherwise, get active project's images
    active_id = storage.get('active_project_id')
    if not active_id:
        return []

    for project in storage.get('projects', []):
        if project['id'] == active_id:
            return project.get('images', [])

    return []

def add_uploaded_image(filename, file_data, thumbnail_data):
    """Add an uploaded image to active project"""
    project = _get_active_project()
    session_id = _get_session_id()

    _log(f"💾 add_uploaded_image() called:")
    _log(f"   Session ID: {session_id}")
    _log(f"   Project ID: {project['id']}")
    _log(f"   Filename: {filename}")
    _log(f"   Current images in project: {len(project.get('images', []))}")

    # Check for duplicate filename to prevent double uploads
    for existing_image in project.get('images', []):
        if existing_image['filename'] == filename:
            _log(f"⚠️  Duplicate image detected: {filename} - skipping, returning existing ID {existing_image['id']}")
            return existing_image['id']  # Return existing ID

    # Store binary data directly in server memory (no base64 needed!)
    image_id = len(project['images']) + 1
    project['images'].append({
        'id': image_id,
        'filename': filename,
        'file_data': file_data,  # Raw binary data
        'thumbnail_data': thumbnail_data,  # Raw binary data
        'uploaded_at': datetime.utcnow().isoformat()
    })

    _log(f"   ✅ Added image ID {image_id}, total images now: {len(project['images'])}")
    _save_session(session_id)  # Persist to disk
    _log(f"   💾 Session saved to disk")
    return image_id

def get_image_by_id(image_id):
    """Get image by ID from active project"""
    project = _get_active_project()
    for img in project.get('images', []):
        if img['id'] == image_id:
            return img
    return None

def get_image_by_id_from_project(image_id, project_id):
    """Get image by ID from a SPECIFIC project (not active project)"""
    storage = _get_storage()

    # Find the specific project by ID
    for project in storage.get('projects', []):
        if project['id'] == project_id:
            # Search for image in this specific project
            for img in project.get('images', []):
                if img['id'] == image_id:
                    return img

    return None

def delete_image(image_id):
    """Delete an image from active project"""
    project = _get_active_project()
    project['images'] = [img for img in project.get('images', []) if img['id'] != image_id]
    _save_session(_get_session_id())  # Persist to disk

def clear_all_images():
    """Clear all images from active project (more efficient than deleting one by one)"""
    project = _get_active_project()
    session_id = _get_session_id()
    old_count = len(project.get('images', []))

    _log(f"🗑️  clear_all_images() called:")
    _log(f"   Session ID: {session_id}")
    _log(f"   Project ID: {project['id']}")
    _log(f"   Deleting {old_count} images")

    project['images'] = []
    _save_session(session_id)  # Persist to disk - single save instead of multiple

    _log(f"   ✅ All images cleared, session saved")

def get_all_months():
    """Get all calendar months for active project"""
    project = _get_active_project()
    return project.get('months', [])

def create_months_with_themes(themes):
    """
    Create months for active project
    NEW: Only creates 3 months initially (Jan, Feb, Mar) for preview - NO COVER
    Cover + remaining 9 months created after payment method authorization
    """
    project = _get_active_project()
    project['months'] = []

    # Phase 1: Only create first 3 months for FREE preview (Jan, Feb, Mar) - NO COVER
    preview_months = [1, 2, 3]  # January, February, March (cover comes later)

    for month_num in preview_months:
        theme = themes[month_num]
        project['months'].append({
            'id': month_num,
            'month_number': month_num,
            'prompt': theme['prompt'],
            'title': theme['title'],
            'description': theme['description'],
            'generation_status': 'pending',
            'master_image_data': None,  # Raw binary data (backwards compatibility)
            'image_variants': [],  # List of variant images [{data: bytes, generated_at: timestamp, variant_index: 0}, ...]
            'selected_variant_index': 0,  # Which variant is currently selected (0-2)
            'retry_count': 0,  # Number of retries used (max 2)
            'error_message': None,
            'generated_at': None
        })

    # Set generation stage and preview expiry
    project['generation_stage'] = 'preview_only'
    set_preview_expiry()  # 48 hours from now

    _save_session(_get_session_id())  # Persist to disk

def create_remaining_months(themes):
    """
    Create remaining 10 months (Cover + April-December) after payment authorization
    Called after setup_intent.succeeded webhook
    """
    project = _get_active_project()

    # Phase 2: Create cover + months 4-12 (Cover + April through December) = 10 months
    remaining_months = [0, 4, 5, 6, 7, 8, 9, 10, 11, 12]  # Cover comes AFTER payment

    for month_num in remaining_months:
        theme = themes[month_num]
        project['months'].append({
            'id': month_num,
            'month_number': month_num,
            'prompt': theme['prompt'],
            'title': theme['title'],
            'description': theme['description'],
            'generation_status': 'pending',
            'master_image_data': None,  # Raw binary data (backwards compatibility)
            'image_variants': [],  # List of variant images
            'selected_variant_index': 0,  # Which variant is currently selected (0-2)
            'retry_count': 0,  # Number of retries used (max 2)
            'error_message': None,
            'generated_at': None
        })

    # Update generation stage
    project['generation_stage'] = 'generating_full'
    project['generation_progress'] = 0

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

                # Initialize first variant if this is the first generation
                if 'image_variants' not in month or len(month['image_variants']) == 0:
                    month['image_variants'] = [{
                        'data': image_data,
                        'generated_at': month['generated_at'],
                        'variant_index': 0
                    }]
                    month['selected_variant_index'] = 0

            if error:
                month['error_message'] = str(error)

            _save_session(_get_session_id())  # Persist to disk
            return month

    return None

def get_month_image_data(month_num):
    """Get binary image data for a month (returns selected variant or master image)"""
    month = get_month_by_number(month_num)
    if not month:
        return None

    # Check if there are variants
    variants = month.get('image_variants', [])
    selected_index = month.get('selected_variant_index', 0)

    if variants and selected_index < len(variants):
        return variants[selected_index].get('data')

    # Fallback to master_image_data for backwards compatibility
    if month.get('master_image_data'):
        return month['master_image_data']

    return None

def get_month_by_id(month_id):
    """Get month by ID (month_number) from active project"""
    return get_month_by_number(month_id)

def get_month_variant_image(month_id, variant_index):
    """Get specific variant image data for a month"""
    month = get_month_by_id(month_id)
    if not month:
        return None

    variants = month.get('image_variants', [])
    if variant_index < len(variants):
        return variants[variant_index].get('data')

    return None

def select_month_variant(month_id, variant_index):
    """Update selected variant for a month"""
    project = _get_active_project()

    for month in project.get('months', []):
        if month['month_number'] == month_id:
            variants = month.get('image_variants', [])
            if variant_index < len(variants):
                month['selected_variant_index'] = variant_index
                _save_session(_get_session_id())
                return True

    return False

def add_month_variant(month_id, image_data):
    """Add new variant to month and increment retry count"""
    from datetime import datetime

    project = _get_active_project()

    for month in project.get('months', []):
        if month['month_number'] == month_id:
            # Initialize variants array if not exists
            if 'image_variants' not in month:
                month['image_variants'] = []

            # Initialize retry count if not exists
            if 'retry_count' not in month:
                month['retry_count'] = 0

            # If this is the first variant, migrate master_image_data
            if len(month['image_variants']) == 0 and month.get('master_image_data'):
                month['image_variants'].append({
                    'data': month['master_image_data'],
                    'generated_at': month.get('generated_at', datetime.utcnow().isoformat()),
                    'variant_index': 0
                })

            # Add new variant
            new_variant_index = len(month['image_variants'])
            month['image_variants'].append({
                'data': image_data,
                'generated_at': datetime.utcnow().isoformat(),
                'variant_index': new_variant_index
            })

            # Increment retry count
            month['retry_count'] += 1

            # Select the new variant automatically
            month['selected_variant_index'] = new_variant_index

            # Update master_image_data for backwards compatibility
            month['master_image_data'] = image_data

            _save_session(_get_session_id())
            return new_variant_index

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
    'desktop': 22.50,
    'wall_calendar': 26.50
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
        'preferences': None,
        # New fields for 3-month preview system
        'preview_expiry': None,
        'payment_method_id': None,
        'setup_intent_id': None,
        'generation_stage': 'not_started',  # 'not_started' | 'preview_only' | 'generating_full' | 'fully_generated'
        'generation_progress': 0  # 0-100 percentage for remaining months generation
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
            # Already in cart - increment quantity instead of adding duplicate
            item['quantity'] = item.get('quantity', 1) + 1
            if item['quantity'] > 99:
                item['quantity'] = 99  # Cap at 99
            _save_session(_get_session_id())
            print(f"📦 Incremented quantity to {item['quantity']} for existing cart item")
            return item['id']

    # Get Printify mockup URL for this product type
    mockup_url = None
    preview_mockups = storage.get('preview_mockups', {})

    print(f"🔍 Debug add_to_cart mockup lookup:")
    print(f"   Product type: {product_type}")
    print(f"   Available mockup types: {list(preview_mockups.keys())}")

    if preview_mockups and product_type in preview_mockups:
        mockup_data = preview_mockups[product_type]
        mockup_images = mockup_data.get('mockup_images', [])
        print(f"   Found {len(mockup_images)} mockup images for {product_type}")

        # Get specific mockup image for cart preview
        # Wall Calendar: mockup #8 (index 7)
        # Desktop Calendar: mockup #9 (index 8)
        if mockup_images:
            mockup_index = 7 if product_type == 'wall_calendar' else 8  # Default to index 8 for desktop

            # Ensure the requested index exists, fallback to first image
            if mockup_index < len(mockup_images):
                selected_mockup = mockup_images[mockup_index]
                print(f"   📸 Using mockup #{mockup_index + 1} (index {mockup_index}) for cart")
            else:
                selected_mockup = mockup_images[0]
                print(f"   ⚠️ Mockup index {mockup_index} not available, using first mockup")

            mockup_url = selected_mockup.get('src')
            print(f"   ✅ Mockup URL: {mockup_url[:80]}..." if mockup_url else "   ❌ No mockup URL found")
    else:
        print(f"   ❌ No mockups found for {product_type}")

    # Create cart item with quantity
    cart_item_id = secrets.token_urlsafe(16)
    cart_item = {
        'id': cart_item_id,
        'project_id': project_id,
        'product_type': product_type,
        'price': PRODUCT_PRICES[product_type],
        'quantity': 1,  # Default quantity
        'mockup_url': mockup_url,  # Printify mockup image URL
        'added_at': datetime.utcnow().isoformat()
    }

    storage['cart'].append(cart_item)
    _save_session(_get_session_id())

    return cart_item_id

def get_cart_items():
    """Get all cart items with project details"""
    # Force reload from disk to ensure we have latest cart data (fixes race condition)
    _load_storage(force_reload=True)
    storage = _get_storage()
    cart_items_with_details = []

    for cart_item in storage['cart']:
        project = get_project_by_id(cart_item['project_id'])
        if project:
            # Get cover image (month 0) for preview - fallback if no Printify mockup
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
                'quantity': cart_item.get('quantity', 1),  # Include quantity (default 1 for legacy items)
                'added_at': cart_item['added_at'],
                'project_created_at': project['created_at'],
                'has_cover_image': cover_month is not None and cover_month.get('generation_status') == 'completed',
                'mockup_url': cart_item.get('mockup_url')  # Printify mockup URL (preferred)
            })

    return cart_items_with_details

def get_cart_count():
    """Get number of items in cart"""
    storage = _get_storage()
    return len(storage['cart'])

def get_cart_total():
    """Get total price of all cart items (price × quantity for each item)"""
    storage = _get_storage()
    return sum(item['price'] * item.get('quantity', 1) for item in storage['cart'])

def update_cart_quantity(cart_item_id, quantity):
    """Update the quantity of a cart item"""
    storage = _get_storage()

    # Validate quantity (1-99)
    if not isinstance(quantity, int) or quantity < 1 or quantity > 99:
        raise ValueError("Quantity must be between 1 and 99")

    # Find cart item and update quantity
    for item in storage['cart']:
        if item['id'] == cart_item_id:
            item['quantity'] = quantity
            _save_session(_get_session_id())
            print(f"📦 Updated cart item {cart_item_id} quantity to {quantity}")
            return True

    raise ValueError(f"Cart item not found: {cart_item_id}")

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
    # Force reload from disk to ensure we have latest cart data (fixes race condition)
    _load_storage(force_reload=True)
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

def save_delivery_image(session_id, image_data):
    """Save delivery worker image to a specific session (used after order)"""
    _load_storage()
    if session_id in _storage:
        _storage[session_id]['delivery_image'] = image_data
        _save_session(session_id)
        return True
    return False

def get_delivery_image():
    """Get delivery worker image for current session"""
    storage = _get_storage()
    return storage.get('delivery_image')

def get_delivery_image_by_session_id(session_id):
    """Get delivery worker image for a specific session"""
    _load_storage()
    if session_id in _storage:
        return _storage[session_id].get('delivery_image')
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

# ============================================================================
# 3-MONTH PREVIEW SYSTEM FUNCTIONS
# ============================================================================

def set_preview_expiry():
    """Set preview expiry to 48 hours from now"""
    from datetime import timedelta
    project = _get_active_project()
    expiry = datetime.utcnow() + timedelta(hours=48)
    project['preview_expiry'] = expiry.isoformat()
    _save_session(_get_session_id())

def get_preview_expiry():
    """Get preview expiry datetime"""
    project = _get_active_project()
    expiry_str = project.get('preview_expiry')
    if expiry_str:
        return datetime.fromisoformat(expiry_str)
    return None

def is_preview_expired():
    """Check if preview has expired"""
    expiry = get_preview_expiry()
    if not expiry:
        return False
    return datetime.utcnow() > expiry

def save_setup_intent(setup_intent_id):
    """Save Stripe Setup Intent ID"""
    project = _get_active_project()
    project['setup_intent_id'] = setup_intent_id
    _save_session(_get_session_id())

def save_payment_method(payment_method_id):
    """Save Stripe payment method ID"""
    project = _get_active_project()
    project['payment_method_id'] = payment_method_id
    _save_session(_get_session_id())

def get_payment_method_id():
    """Get saved payment method ID"""
    project = _get_active_project()
    return project.get('payment_method_id')

def save_payment_method_by_session_id(session_id, payment_method_id):
    """Save payment method for a specific session (used by webhooks)"""
    _load_storage()
    if session_id in _storage:
        active_id = _storage[session_id].get('active_project_id')
        if active_id:
            for project in _storage[session_id].get('projects', []):
                if project['id'] == active_id:
                    project['payment_method_id'] = payment_method_id
                    _save_session(session_id)
                    return True
    return False

def set_generation_stage(stage):
    """
    Set generation stage
    Stages: 'not_started' | 'preview_only' | 'generating_full' | 'fully_generated'
    """
    project = _get_active_project()
    project['generation_stage'] = stage
    _save_session(_get_session_id())

def get_generation_stage():
    """Get current generation stage"""
    project = _get_active_project()
    return project.get('generation_stage', 'not_started')

def update_generation_progress(progress):
    """Update generation progress (0-100)"""
    project = _get_active_project()
    project['generation_progress'] = progress
    _save_session(_get_session_id())

def get_generation_progress():
    """Get generation progress (0-100)"""
    project = _get_active_project()
    return project.get('generation_progress', 0)

def get_generation_status():
    """
    Get detailed generation status for frontend
    Returns dict with stage, progress, and counts
    """
    project = _get_active_project()
    months = project.get('months', [])

    completed_count = sum(1 for m in months if m.get('generation_status') == 'completed')

    # Smart stage detection (safety check in case stage wasn't set correctly)
    current_stage = project.get('generation_stage', 'not_started')
    if len(months) == 3 and completed_count == 3:
        # 3 preview months done → should show payment gate
        current_stage = 'preview_only'
    elif len(months) == 13 and completed_count == 13:
        # All 13 months done → show product selection
        current_stage = 'fully_generated'
    elif len(months) > 3 and completed_count < len(months):
        # Generating remaining months
        current_stage = 'generating_full'

    return {
        'stage': current_stage,
        'progress': project.get('generation_progress', 0),
        'completed_months': completed_count,
        'total_months': len(months),
        'preview_expiry': project.get('preview_expiry'),
        'is_expired': is_preview_expired(),
        'has_payment_method': bool(project.get('payment_method_id')),
        'is_complete': (len(months) == 13 and completed_count == 13)
    }
