"""
Project routes - Upload, prompts, preview, checkout
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from app import session_storage
from app.routes.main import get_current_project
from app.services.monthly_themes import get_all_themes, get_theme, get_enhanced_prompt
from PIL import Image, ImageOps
import io

# Register HEIC support for iPhone photos
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass  # HEIC support not available

bp = Blueprint('projects', __name__, url_prefix='/project')

@bp.route('/upload', methods=['GET', 'POST'])
def upload():
    """Upload selfies page"""
    project = get_current_project()
    if not project:
        return redirect(url_for('main.start'))

    if request.method == 'POST':
        # Handle file uploads
        if 'photos' in request.files:
            files = request.files.getlist('photos')

            processed_count = 0
            for file in files:
                if file and file.filename:
                    try:
                        # Read image data
                        original_data = file.read()

                        # Open image (supports JPEG, PNG, HEIC, etc.)
                        img = Image.open(io.BytesIO(original_data))

                        # Auto-rotate based on EXIF orientation (iPhone photos)
                        img = ImageOps.exif_transpose(img)

                        # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')

                        # Optimize: Resize if too large while preserving quality for AI
                        # Target max dimension: 2560px (high quality for AI face analysis)
                        # Gemini limit: 20MB total, ~6MB per image with 3 references
                        max_dimension = 2560
                        if max(img.size) > max_dimension:
                            # Resize maintaining aspect ratio
                            ratio = max_dimension / max(img.size)
                            new_size = tuple(int(dim * ratio) for dim in img.size)
                            img = img.resize(new_size, Image.Resampling.LANCZOS)

                        # Save with maximum quality (strips EXIF for privacy)
                        # Quality 95: Near-lossless, optimal for AI reference images
                        optimized_io = io.BytesIO()
                        img.save(optimized_io, format='JPEG', quality=95, optimize=True)
                        img_data = optimized_io.getvalue()

                        # Create thumbnail for preview
                        img.thumbnail((200, 200))
                        thumb_io = io.BytesIO()
                        img.save(thumb_io, format='JPEG', quality=85)
                        thumb_data = thumb_io.getvalue()

                        # Save to session storage
                        session_storage.add_uploaded_image(
                            secure_filename(file.filename),
                            img_data,
                            thumb_data
                        )
                        processed_count += 1

                    except Exception as e:
                        flash(f'Error processing {file.filename}: {str(e)}', 'warning')
                        continue

            flash(f'{len(files)} photos uploaded successfully!', 'success')

        # Check if enough photos
        images = session_storage.get_uploaded_images()
        if len(images) >= 3:  # Minimum 3 photos
            return redirect(url_for('projects.themes'))

    # Get uploaded images
    images = session_storage.get_uploaded_images()

    return render_template('upload.html', project=project, images=images)

# REMOVED: Customization feature - using simple stock prompts instead
# Users now go directly from upload → themes → generate
# @bp.route('/customize', methods=['GET', 'POST'])
# def customize():
#     """Customize calendar preferences (gender, body type, style, tone)"""
#     # ... (removed to simplify flow and use proven working prompts)

@bp.route('/themes', methods=['GET', 'POST'])
def themes():
    """Review pre-defined monthly hunk themes"""
    project = get_current_project()
    if not project:
        return redirect(url_for('main.start'))

    # Check if user uploaded photos
    images = session_storage.get_uploaded_images()
    if len(images) < 3:
        flash('Please upload at least 3 photos first!', 'warning')
        return redirect(url_for('projects.upload'))

    if request.method == 'POST':
        try:
            # Auto-create months with pre-defined themes
            all_themes = get_all_themes()
            session_storage.create_months_with_themes(all_themes)

            session_storage.update_project_status('prompts')

            flash('Themes confirmed! Ready to make you a hunk!', 'success')
            return redirect(url_for('projects.generate'))

        except Exception as e:
            flash(f'Error setting up themes: {str(e)}', 'danger')
            return redirect(url_for('projects.themes'))

    # Get all pre-defined themes
    all_themes = get_all_themes()

    return render_template('themes.html', project=project, themes=all_themes)

@bp.route('/generate')
def generate():
    """Start AI generation - redirect immediately to avoid timeout"""
    project = get_current_project()
    if not project:
        return redirect(url_for('main.start'))

    # Check if themes are confirmed
    months = session_storage.get_all_months()
    if len(months) < 13:
        flash('Please review the monthly themes first!', 'warning')
        return redirect(url_for('projects.themes'))

    # Check if we have reference images
    images = session_storage.get_uploaded_images()
    if len(images) < 3:
        flash('Please upload at least 3 photos first!', 'warning')
        return redirect(url_for('projects.upload'))

    try:
        # Mark project as processing
        session_storage.update_project_status('processing')

        flash('Starting AI generation with face-swapping... This will take 5-10 minutes.', 'info')

        # Redirect immediately to preview page (AJAX will handle actual generation)
        return redirect(url_for('projects.preview'))

    except Exception as e:
        flash(f'Error starting generation: {str(e)}', 'danger')
        return redirect(url_for('projects.themes'))

@bp.route('/preview')
def preview():
    """Preview generated calendar"""
    project = get_current_project()
    if not project:
        return redirect(url_for('main.start'))

    # Get all months from session storage
    months = session_storage.get_all_months()

    # Check if generation is complete
    if not all(m['generation_status'] == 'completed' for m in months):
        flash('Calendar generation in progress...', 'info')
        return render_template('generating_local.html', project=project, months=months)

    # Month names: Index 0 = Cover, Index 1-12 = January-December
    month_names = [
        'Cover',  # Month 0 = Cover photo
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]

    # Get mockup data if available
    mockup_data = session_storage.get_preview_mockup_data()

    # Create JSON-serializable version of months (without binary image_data)
    months_json = [
        {
            'id': m['id'],
            'month_number': m['month_number'],
            'generation_status': m.get('generation_status', 'pending')
        }
        for m in months
    ]

    return render_template('preview.html',
                          project=project,
                          months=months,
                          months_json=months_json,
                          month_names=month_names,
                          mockup_data=mockup_data)

@bp.route('/calendar-preview')
def calendar_preview():
    """Show 3×4 grid preview of all 12 calendar months"""
    project = get_current_project()
    if not project:
        return redirect(url_for('main.start'))

    # Get all months from session storage
    months = session_storage.get_all_months()

    # Check if all months are generated
    if not all(m['generation_status'] == 'completed' for m in months):
        flash('Please wait for all months to be generated before viewing the calendar preview.', 'warning')
        return redirect(url_for('projects.preview'))

    return render_template('calendar_preview.html', project=project)

@bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Checkout page (mock)"""
    project = get_current_project()
    if not project:
        return redirect(url_for('main.start'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if email:
            # Store email in session (mock order)
            session['order_email'] = email
            session_storage.update_project_status('checkout')

            flash('Thanks for your interest! Payment integration coming soon.', 'info')
            return redirect(url_for('projects.success'))

    return render_template('checkout.html', project=project)

@bp.route('/success')
def success():
    """Success page"""
    project = get_current_project()
    return render_template('success.html', project=project)
