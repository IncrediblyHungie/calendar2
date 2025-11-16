"""
Project routes - Upload, prompts, preview, checkout
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
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

    current_app.logger.info("=" * 70)
    current_app.logger.info(f"📤 UPLOAD ROUTE - Method: {request.method}")
    current_app.logger.info(f"   Project ID: {project['id']}")
    current_app.logger.info("=" * 70)

    if request.method == 'POST':
        # Handle file uploads
        current_app.logger.info(f"   request.files keys: {list(request.files.keys())}")
        current_app.logger.info(f"   request.form keys: {list(request.form.keys())}")
        current_app.logger.info(f"   'photos' in request.files: {'photos' in request.files}")

        if 'photos' in request.files:
            files = request.files.getlist('photos')

            # Check current uploaded images count
            current_images = session_storage.get_uploaded_images()
            current_count = len(current_images)

            # Enforce maximum of 5 photos total
            if current_count + len(files) > 5:
                flash(f'Maximum 5 photos allowed. You currently have {current_count} photo(s). Please remove some before uploading more.', 'warning')
                return redirect(url_for('projects.upload'))

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
                        image_id = session_storage.add_uploaded_image(
                            secure_filename(file.filename),
                            img_data,
                            thumb_data
                        )
                        current_app.logger.info(f"   ✅ Saved image {image_id}: {secure_filename(file.filename)} to project {project['id']}")
                        processed_count += 1

                    except Exception as e:
                        flash(f'Error processing {file.filename}: {str(e)}', 'warning')
                        current_app.logger.error(f"   ❌ Error processing {file.filename}: {str(e)}")
                        continue

            current_app.logger.info(f"✅ Upload complete: {processed_count} images saved to project {project['id']}")
            current_app.logger.info(f"   Redirecting to GET /project/upload...")
            flash(f'{len(files)} photos uploaded successfully!', 'success')
        else:
            current_app.logger.warning(f"⚠️  NO 'photos' in request.files - upload skipped!")

        # Redirect to GET request (Post/Redirect/Get pattern)
        # This prevents "Are you sure you want to resubmit?" warnings
        return redirect(url_for('projects.upload'))

    # GET request - retrieve and display images
    images = session_storage.get_uploaded_images()
    current_app.logger.info(f"   Retrieved {len(images)} images from project {project['id']}")
    if images:
        current_app.logger.info(f"   Image IDs: {[img['id'] for img in images]}")
        current_app.logger.info(f"   Filenames: {[img['filename'] for img in images]}")

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

            # No flash message - redirect directly to generation
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

    # Check if themes are confirmed (now only creates 3 months for preview)
    months = session_storage.get_all_months()
    if len(months) < 3:  # Only 3 months preview (Jan, Feb, Mar - no cover)
        # No flash message - just redirect
        return redirect(url_for('projects.themes'))

    # Check if we have reference images
    images = session_storage.get_uploaded_images()
    if len(images) < 3:
        flash('Please upload at least 3 photos first!', 'warning')
        return redirect(url_for('projects.upload'))

    try:
        # Mark project as processing
        session_storage.update_project_status('processing')

        # Redirect immediately to preview page (AJAX will handle actual generation)
        return redirect(url_for('projects.preview'))

    except Exception as e:
        flash(f'Error starting generation: {str(e)}', 'danger')
        return redirect(url_for('projects.themes'))

@bp.route('/preview')
def preview():
    """Preview generated calendar"""
    try:
        project = get_current_project()
        if not project:
            return redirect(url_for('main.start'))

        # Get all months from session storage
        months = session_storage.get_all_months()

        # Check if generation is complete
        if not all(m['generation_status'] == 'completed' for m in months):
            flash('Calendar generation in progress...', 'info')
            generation_stage = session_storage.get_generation_status().get('stage', 'preview_only')

            # Create JSON-serializable version of months (without binary image_data)
            months_json = [
                {
                    'id': m['id'],
                    'month_number': m['month_number'],
                    'generation_status': m.get('generation_status', 'pending')
                }
                for m in months
            ]

            return render_template('generating_local.html',
                                 project=project,
                                 months=months_json,  # Pass JSON-safe version
                                 generation_stage=generation_stage)

        # Month names: Index 0 = Cover, Index 1-12 = January-December
        month_names = [
            'Cover',  # Month 0 = Cover photo
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]

        # Get mockup data if available
        mockup_data = session_storage.get_preview_mockup_data()

        # Get generation status for 3-month preview system
        gen_status = session_storage.get_generation_status()

        # Create JSON-serializable version of months (without binary image_data)
        months_json = [
            {
                'id': m['id'],
                'month_number': m['month_number'],
                'generation_status': m.get('generation_status', 'pending')
            }
            for m in months
        ]

        # Import monthly themes for current titles/descriptions
        from app.services.monthly_themes import MONTHLY_THEMES

        return render_template('preview.html',
                              project=project,
                              months=months,
                              months_json=months_json,
                              month_names=month_names,
                              mockup_data=mockup_data,
                              generation_status=gen_status,
                              monthly_themes=MONTHLY_THEMES)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n{'='*70}")
        print(f"❌ PREVIEW PAGE ERROR")
        print(f"{'='*70}")
        print(f"Error: {str(e)}")
        print(f"Traceback:\n{error_details}")
        print(f"{'='*70}\n")
        flash(f'An error occurred loading the preview. Please try again or start over.', 'danger')
        return redirect(url_for('main.start'))

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

@bp.route('/cart')
def cart_page():
    """Shopping cart page"""
    project = get_current_project()
    if not project:
        return redirect(url_for('main.start'))

    # Get cart items
    cart_items = session_storage.get_cart_items()
    cart_total = session_storage.get_cart_total()

    # Get preview mockups for dynamic mockup selection
    preview_mockups = session_storage.get_preview_mockup_data()

    return render_template('cart.html',
                          project=project,
                          cart_items=cart_items,
                          cart_total=cart_total,
                          preview_mockups=preview_mockups)

@bp.route('/create-another')
def create_another():
    """Create a new calendar project"""
    # Create new project and make it active
    new_project_id = session_storage.create_new_project()

    flash('New calendar started! Upload photos to begin.', 'success')
    return redirect(url_for('projects.upload'))

@bp.route('/success')
def success():
    """Success page"""
    project = get_current_project()
    return render_template('success.html', project=project)
