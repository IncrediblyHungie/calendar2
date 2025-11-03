"""
API routes for AJAX calls and image serving
"""
from flask import Blueprint, jsonify, send_file, Response, request, url_for
from app import session_storage
from app.routes.main import get_current_project
from app.services import stripe_service
import io

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/image/thumbnail/<int:image_id>')
def get_thumbnail(image_id):
    """Serve thumbnail image"""
    project = get_current_project()
    if not project:
        return jsonify({'error': 'Unauthorized'}), 401

    image = session_storage.get_image_by_id(image_id)

    if not image or not image.get('thumbnail_data'):
        return jsonify({'error': 'Image not found'}), 404

    return send_file(
        io.BytesIO(image['thumbnail_data']),
        mimetype='image/jpeg'
    )

@bp.route('/image/month/<int:month_id>')
def get_month_image(month_id):
    """Serve generated month image"""
    project = get_current_project()
    if not project:
        return jsonify({'error': 'Unauthorized'}), 401

    image_data = session_storage.get_month_image_data(month_id)

    if not image_data:
        return jsonify({'error': 'Image not found'}), 404

    return send_file(
        io.BytesIO(image_data),
        mimetype='image/jpeg'
    )

@bp.route('/project/status')
def project_status():
    """Get current project status"""
    project = get_current_project()
    if not project:
        return jsonify({'error': 'No active project'}), 404

    # Get generation status from session
    months = session_storage.get_all_months()

    return jsonify({
        'project_id': project['id'],
        'status': project['status'],
        'months': months
    })

@bp.route('/delete/image/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    """Delete an uploaded image"""
    project = get_current_project()
    if not project:
        return jsonify({'error': 'Unauthorized'}), 401

    session_storage.delete_image(image_id)

    return jsonify({'success': True})

@bp.route('/generate/month/<int:month_num>', methods=['POST'])
def generate_month(month_num):
    """Generate a single month's image with AI face-swapping (0=Cover, 1-12=Months)"""
    from app.services.gemini_service import generate_calendar_image
    from app.services.monthly_themes import get_enhanced_prompt
    from PIL import Image as PILImage
    import io
    import traceback

    print(f"\n{'='*70}")
    print(f"🚀 GENERATE MONTH {month_num} - START {'(COVER)' if month_num == 0 else ''}")
    print(f"{'='*70}")

    project = get_current_project()
    if not project:
        print(f"❌ Month {month_num}: No project found (Unauthorized)")
        return jsonify({'error': 'Unauthorized'}), 401

    if month_num < 0 or month_num > 12:
        print(f"❌ Month {month_num}: Invalid month number (must be 0-12)")
        return jsonify({'error': 'Invalid month number'}), 400

    try:
        # Get the month record from session
        print(f"📋 Month {month_num}: Getting month record from session...")
        month = session_storage.get_month_by_number(month_num)

        if not month:
            print(f"❌ Month {month_num}: Month not found in session storage")
            return jsonify({'error': 'Month not found'}), 404

        print(f"✓ Month {month_num}: Found month record, status={month.get('generation_status')}")

        # Check if already completed
        if month['generation_status'] == 'completed':
            print(f"✓ Month {month_num}: Already completed, skipping")
            return jsonify({
                'success': True,
                'status': 'completed',
                'message': f'Month {month_num} already generated'
            })

        # Mark as processing
        print(f"📝 Month {month_num}: Marking as processing...")
        session_storage.update_month_status(month_num, 'processing')

        # Get reference images for face-swapping (already raw binary data!)
        print(f"🖼️  Month {month_num}: Getting reference images...")
        uploaded_images = session_storage.get_uploaded_images()
        print(f"✓ Month {month_num}: Found {len(uploaded_images)} uploaded images")

        reference_image_data = [img['file_data'] for img in uploaded_images]

        if not reference_image_data:
            error_msg = 'No reference images found'
            print(f"❌ Month {month_num}: {error_msg}")
            session_storage.update_month_status(month_num, 'failed', error=error_msg)
            return jsonify({'error': error_msg}), 400

        print(f"✓ Month {month_num}: Prepared {len(reference_image_data)} reference images")

        # Generate image with simple working prompts
        print(f"📸 Month {month_num}: Getting enhanced prompt...")
        enhanced_prompt = get_enhanced_prompt(month_num)
        print(f"✓ Month {month_num}: Prompt length: {len(enhanced_prompt)} chars")

        print(f"🎨 Month {month_num}: Starting Gemini API call...")
        image_data = generate_calendar_image(enhanced_prompt, reference_image_data)
        print(f"✅ Month {month_num}: Generation succeeded! Size: {len(image_data)} bytes")

        # Convert PNG to JPEG for smaller file size
        # Quality 80 optimized for memory: good quality, smaller files, less RAM
        img = PILImage.open(io.BytesIO(image_data))
        img_io = io.BytesIO()
        img.convert('RGB').save(img_io, format='JPEG', quality=80, optimize=True)
        jpeg_data = img_io.getvalue()

        # Clear image data from memory immediately
        del image_data
        del img
        del img_io
        import gc
        gc.collect()

        # Save to session storage
        session_storage.update_month_status(month_num, 'completed', image_data=jpeg_data)

        print(f"💾 Month {month_num}: Saved {len(jpeg_data)} bytes")

        return jsonify({
            'success': True,
            'status': 'completed',
            'month': month_num,
            'message': f'Month {month_num} generated successfully',
            'image_size': len(jpeg_data)
        })

    except Exception as e:
        # Mark as failed
        error_msg = str(e)
        print(f"\n❌ Month {month_num}: EXCEPTION CAUGHT")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {error_msg}")
        print(f"   Traceback:")
        traceback.print_exc()
        print(f"{'='*70}\n")

        session_storage.update_month_status(month_num, 'failed', error=error_msg)

        return jsonify({
            'success': False,
            'status': 'failed',
            'month': month_num,
            'error': error_msg,
            'error_type': type(e).__name__
        }), 500

@bp.route('/test/gemini', methods=['GET'])
def test_gemini():
    """Test Gemini API connection and generation"""
    import os
    from app.services.gemini_service import GOOGLE_API_KEY, generate_calendar_image
    from app.services.monthly_themes import get_enhanced_prompt

    result = {
        'api_key_set': bool(GOOGLE_API_KEY),
        'api_key_prefix': GOOGLE_API_KEY[:20] if GOOGLE_API_KEY else None,
    }

    try:
        # Test simple generation
        simple_prompt = "A muscular shirtless firefighter with a helmet"
        image_data = generate_calendar_image(simple_prompt, reference_image_data_list=None)

        result['test_passed'] = True
        result['image_size'] = len(image_data) if image_data else 0
        result['message'] = 'Gemini API working correctly'

    except Exception as e:
        result['test_passed'] = False
        result['error'] = str(e)
        result['error_type'] = type(e).__name__

    return jsonify(result)

@bp.route('/debug/session', methods=['GET'])
def debug_session():
    """Debug endpoint to check session storage state"""
    project = get_current_project()

    debug_info = {
        'has_project': bool(project),
        'project_id': project['id'] if project else None,
        'project_status': project.get('status') if project else None,
    }

    if project:
        uploaded_images = session_storage.get_uploaded_images()
        months = session_storage.get_all_months()

        debug_info.update({
            'uploaded_images_count': len(uploaded_images),
            'uploaded_images_sizes': [len(img.get('file_data', b'')) for img in uploaded_images],
            'months_count': len(months),
            'months_status': {
                m['month_number']: m.get('generation_status')
                for m in months
            }
        })

    return jsonify(debug_info)

@bp.route('/calendar-grid-image')
def calendar_grid_image():
    """Generate and serve 3×4 grid preview of all 12 calendar months"""
    from PIL import Image as PILImage

    project = get_current_project()
    if not project:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get all months from session storage
        months = session_storage.get_all_months()

        # Check if all months are generated
        if not all(m['generation_status'] == 'completed' for m in months):
            return jsonify({'error': 'Not all months are generated yet'}), 400

        # Grid configuration
        COLUMNS = 4
        ROWS = 3
        THUMB_WIDTH = 400
        THUMB_HEIGHT = 533  # 3:4 aspect ratio
        GRID_WIDTH = THUMB_WIDTH * COLUMNS  # 1600px
        GRID_HEIGHT = THUMB_HEIGHT * ROWS    # 1599px

        # Create blank canvas
        grid_image = PILImage.new('RGB', (GRID_WIDTH, GRID_HEIGHT), color='white')

        # Paste each month image into the grid
        for month in months:
            month_num = month['month_number']
            image_data = session_storage.get_month_image_data(month_num)

            if not image_data:
                print(f"⚠ Warning: Month {month_num} has no image data")
                continue

            # Load and resize month image
            month_img = PILImage.open(io.BytesIO(image_data))
            month_img = month_img.resize((THUMB_WIDTH, THUMB_HEIGHT), PILImage.Resampling.LANCZOS)

            # Calculate position in grid (0-indexed, left to right, top to bottom)
            index = month_num - 1
            col = index % COLUMNS
            row = index // COLUMNS
            x = col * THUMB_WIDTH
            y = row * THUMB_HEIGHT

            # Paste into grid
            grid_image.paste(month_img, (x, y))

        # Save grid to bytes
        grid_io = io.BytesIO()
        grid_image.save(grid_io, format='JPEG', quality=85, optimize=True)
        grid_io.seek(0)

        return send_file(
            grid_io,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name='calendar_preview.jpg'
        )

    except Exception as e:
        print(f"❌ Grid generation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@bp.route('/generate/mockup', methods=['POST'])
def generate_mockup():
    """
    Generate Printify product mockup preview after all months complete
    This creates a draft Printify product and returns mockup image URLs
    """
    import traceback

    project = get_current_project()
    if not project:
        return jsonify({'error': 'Unauthorized'}), 401

    print(f"\n{'='*70}")
    print(f"🎨 MOCKUP GENERATION REQUEST RECEIVED")
    print(f"{'='*70}\n")

    try:
        # Get all completed month images
        months = session_storage.get_all_months()

        # Verify all 12 months (1-12) are completed
        completed_months = [m for m in months if m['month_number'] in range(1, 13) and m['generation_status'] == 'completed']

        if len(completed_months) < 12:
            error_msg = f"Not all months completed: {len(completed_months)}/12"
            print(f"❌ {error_msg}")
            return jsonify({'error': error_msg}), 400

        print(f"✓ All 12 months confirmed completed")

        # Collect month image data
        month_image_data = {}
        for month_num in range(1, 13):
            image_data = session_storage.get_month_image_data(month_num)
            if not image_data:
                raise Exception(f"Missing image data for month {month_num}")
            month_image_data[month_num] = image_data

        print(f"✓ Collected {len(month_image_data)} month images")

        # Create Printify product and get mockup images
        from app.services import printify_service

        mockup_result = printify_service.create_product_for_preview(
            month_image_data=month_image_data,
            product_type='calendar_2026'  # Default to main calendar product
        )

        # Save mockup data to session
        session_storage.save_preview_mockup_data(mockup_result)
        print(f"✅ Mockup data saved to session")

        return jsonify({
            'success': True,
            'mockup_count': len(mockup_result.get('mockup_images', [])),
            'product_id': mockup_result.get('product_id'),
            'message': 'Mockup preview generated successfully'
        })

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ MOCKUP GENERATION FAILED")
        print(f"   Error: {error_msg}")
        print(f"   Traceback:")
        traceback.print_exc()
        print(f"{'='*70}\n")

        return jsonify({
            'success': False,
            'error': error_msg,
            'error_type': type(e).__name__
        }), 500

@bp.route('/checkout/create', methods=['POST'])
def create_checkout():
    """Create Stripe checkout session for calendar purchase"""
    project = get_current_project()
    if not project:
        return jsonify({'error': 'No active project'}), 401

    data = request.json
    product_type = data.get('product_type')

    if product_type not in ['calendar_2026', 'desktop', 'standard_wall']:
        return jsonify({'error': 'Invalid product type'}), 400

    try:
        # Get internal session ID for webhook lookup
        internal_session_id = session_storage._get_session_id()

        # Create Stripe checkout session with metadata
        session_data = stripe_service.create_checkout_session(
            product_type=product_type,
            success_url=url_for('main.order_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('projects.preview', _external=True),
            metadata={
                'internal_session_id': internal_session_id,
                'product_type': product_type
            }
        )

        return jsonify({
            'success': True,
            'checkout_url': session_data['url'],
            'session_id': session_data['session_id']
        })

    except Exception as e:
        print(f"❌ Checkout creation error: {e}")
        return jsonify({'error': str(e)}), 500
