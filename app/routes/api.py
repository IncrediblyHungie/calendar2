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

@bp.route('/delete/all-images', methods=['POST'])
def delete_all_images():
    """Delete all uploaded images for the current project"""
    project = get_current_project()
    if not project:
        return jsonify({'error': 'Unauthorized'}), 401

    # Get all images for this project and delete them
    images = project.uploaded_images
    for image in images:
        session_storage.delete_image(image.id)

    return jsonify({'success': True, 'deleted_count': len(images)})

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

        # Check if all months are now complete
        all_months = session_storage.get_all_months()
        completed_count = sum(1 for m in all_months if m['generation_status'] == 'completed')

        # Only set to fully_generated when ALL 13 months are complete
        if len(all_months) == 13 and completed_count == 13:
            print(f"🎉 All 13 months complete! Updating stage to fully_generated")
            session_storage.set_generation_stage('fully_generated')
        elif len(all_months) == 3 and completed_count == 3:
            print(f"✅ Preview complete (3/3 months) - keeping stage as preview_only to show payment gate")
            # Don't change stage - stay at preview_only to show payment gate
        else:
            print(f"📊 Progress: {completed_count}/{len(all_months)} months complete")

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

        # Create Printify products for all calendar types
        from app.services import printify_service

        product_types = ['wall_calendar', 'desktop']
        total_mockups = 0

        print(f"\n🎨 Generating mockups for {len(product_types)} product types...")

        for product_type in product_types:
            try:
                print(f"\n{'─'*50}")
                print(f"📸 Creating mockup for: {product_type}")

                mockup_result = printify_service.create_product_for_preview(
                    month_image_data=month_image_data,
                    product_type=product_type
                )

                # Save mockup data to session (one per product type)
                session_storage.save_preview_mockup_data(mockup_result, product_type)
                mockup_count = len(mockup_result.get('mockup_images', []))
                total_mockups += mockup_count
                print(f"✅ {product_type}: {mockup_count} mockup images created")

            except Exception as product_error:
                print(f"⚠️ Failed to create mockup for {product_type}: {product_error}")
                # Continue with other products - don't fail completely if one fails

        print(f"\n{'='*70}")
        print(f"✅ Mockup generation complete: {total_mockups} total images")
        print(f"{'='*70}\n")

        return jsonify({
            'success': True,
            'mockup_count': total_mockups,
            'product_types': product_types,
            'message': f'Mockups generated for {len(product_types)} calendar types'
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

    if product_type not in ['wall_calendar', 'desktop']:
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

# ============================================================================
# CART API ENDPOINTS
# ============================================================================

@bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    """Add current project to cart with specified product type"""
    project = get_current_project()
    if not project:
        return jsonify({'error': 'No active project'}), 401

    data = request.json
    product_type = data.get('product_type')

    if product_type not in ['wall_calendar', 'desktop']:
        return jsonify({'error': 'Invalid product type'}), 400

    try:
        # Verify all months are completed
        months = session_storage.get_all_months()
        if not all(m['generation_status'] == 'completed' for m in months):
            return jsonify({'error': 'Calendar not fully generated yet'}), 400

        # Add to cart
        cart_item_id = session_storage.add_to_cart(project['id'], product_type)

        return jsonify({
            'success': True,
            'cart_item_id': cart_item_id,
            'cart_count': session_storage.get_cart_count(),
            'message': f'Added to cart! You now have {session_storage.get_cart_count()} item(s).'
        })

    except Exception as e:
        print(f"❌ Add to cart error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/cart', methods=['GET'])
def get_cart():
    """Get all cart items"""
    try:
        cart_items = session_storage.get_cart_items()
        cart_total = session_storage.get_cart_total()

        return jsonify({
            'success': True,
            'items': cart_items,
            'count': len(cart_items),
            'total': cart_total
        })

    except Exception as e:
        print(f"❌ Get cart error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/cart/remove/<cart_item_id>', methods=['DELETE'])
def remove_from_cart(cart_item_id):
    """Remove item from cart"""
    try:
        session_storage.remove_from_cart(cart_item_id)

        return jsonify({
            'success': True,
            'cart_count': session_storage.get_cart_count(),
            'message': 'Item removed from cart'
        })

    except Exception as e:
        print(f"❌ Remove from cart error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/cart/clear', methods=['POST'])
def clear_cart():
    """Clear all items from cart"""
    try:
        session_storage.clear_cart()

        return jsonify({
            'success': True,
            'message': 'Cart cleared'
        })

    except Exception as e:
        print(f"❌ Clear cart error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/cart/checkout', methods=['POST'])
def checkout_cart():
    """Create Stripe checkout session for all items in cart"""
    try:
        cart_items = session_storage.get_cart_items()

        if not cart_items:
            return jsonify({'error': 'Cart is empty'}), 400

        # Get internal session ID for webhook lookup
        internal_session_id = session_storage._get_session_id()

        # Build line items for Stripe
        line_items = []
        for item in cart_items:
            # Get product info
            product_info = stripe_service.PRODUCT_INFO.get(item['product_type'])
            if not product_info:
                return jsonify({'error': f'Invalid product type: {item["product_type"]}'}), 400

            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(item['price'] * 100),  # Convert to cents
                    'product_data': {
                        'name': product_info['name'],
                        'description': product_info['description']
                    }
                },
                'quantity': 1
            })

        # Create Stripe checkout session (API key already configured globally in app/__init__.py)
        import stripe

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card', 'link'],
            line_items=line_items,
            mode='payment',
            success_url=url_for('main.order_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('projects.cart_page', _external=True),
            customer_email=None,  # Stripe will collect
            billing_address_collection='auto',  # Collect billing address (shows "same as shipping" checkbox)
            shipping_address_collection={
                'allowed_countries': ['US', 'CA', 'GB', 'AU', 'DE', 'FR', 'ES', 'IT', 'NL', 'BE']
            },
            phone_number_collection={
                'enabled': True
            },
            metadata={
                'internal_session_id': internal_session_id,
                'is_cart_checkout': 'true',
                'cart_item_count': str(len(cart_items))
            },
            allow_promotion_codes=True  # Enable discount codes
        )

        return jsonify({
            'success': True,
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        })

    except Exception as e:
        print(f"❌ Cart checkout error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@bp.route('/cart/project-image/<project_id>')
def get_cart_project_cover(project_id):
    """Get cover image for a project in cart"""
    try:
        project = session_storage.get_project_by_id(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404

        # Get cover image (month 0)
        for month in project.get('months', []):
            if month['month_number'] == 0 and month.get('master_image_data'):
                return send_file(
                    io.BytesIO(month['master_image_data']),
                    mimetype='image/jpeg'
                )

        return jsonify({'error': 'Cover image not found'}), 404

    except Exception as e:
        print(f"❌ Get project cover error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# 3-MONTH PREVIEW SYSTEM ENDPOINTS
# ============================================================================

@bp.route('/authorize-payment', methods=['POST'])
def authorize_payment():
    """
    Create Stripe Setup Intent for card authorization (NO CHARGE)
    Called when user clicks "Unlock All 12 Months" button
    """
    project = get_current_project()
    if not project:
        return jsonify({'error': 'No active project'}), 401

    print(f"\n{'='*70}")
    print(f"🔓 PAYMENT AUTHORIZATION REQUEST")
    print(f"{'='*70}")

    try:
        # Check if preview expired
        if session_storage.is_preview_expired():
            print(f"❌ Preview expired")
            return jsonify({'error': 'Preview expired. Please start over.'}), 400

        # Check if already authorized
        if session_storage.get_payment_method_id():
            print(f"✓ Payment method already authorized")
            return jsonify({'error': 'Payment method already authorized'}), 400

        # Get internal session ID for webhook metadata
        internal_session_id = session_storage._get_session_id()

        print(f"✓ Creating Setup Intent for session: {internal_session_id}")

        # Create Setup Intent
        setup_intent = stripe_service.create_setup_intent(
            metadata={
                'internal_session_id': internal_session_id,
                'project_id': project['id'],
                'purpose': '3_month_preview_unlock'
            }
        )

        # Save setup intent ID
        session_storage.save_setup_intent(setup_intent['setup_intent_id'])

        print(f"✅ Setup Intent created: {setup_intent['setup_intent_id']}")
        print(f"{'='*70}\n")

        return jsonify({
            'success': True,
            'client_secret': setup_intent['client_secret'],
            'setup_intent_id': setup_intent['setup_intent_id']
        })

    except Exception as e:
        print(f"❌ Payment authorization error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@bp.route('/save-payment-method', methods=['POST'])
def save_payment_method():
    """
    Save payment method ID immediately after Stripe card confirmation
    Called by frontend after stripe.confirmCardSetup() succeeds
    """
    project = get_current_project()
    if not project:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        payment_method_id = data.get('payment_method_id')

        if not payment_method_id:
            return jsonify({'error': 'Missing payment_method_id'}), 400

        print(f"\n{'='*70}")
        print(f"💳 SAVING PAYMENT METHOD (Direct from frontend)")
        print(f"   Payment Method ID: {payment_method_id}")
        print(f"{'='*70}\n")

        # Save payment method to session
        session_storage.save_payment_method(payment_method_id)

        print(f"✅ Payment method saved successfully!")

        return jsonify({
            'success': True,
            'message': 'Payment method saved'
        })

    except Exception as e:
        print(f"❌ Save payment method error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/generation-progress', methods=['GET'])
def generation_progress():
    """
    Get real-time generation progress for months 4-12
    Polled by frontend every 2 seconds during generation
    """
    project = get_current_project()
    if not project:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        status = session_storage.get_generation_status()

        return jsonify({
            'success': True,
            'stage': status['stage'],
            'progress': status['progress'],
            'completed_months': status['completed_months'],
            'total_months': status['total_months'],
            'is_complete': status['stage'] == 'fully_generated',
            'has_payment_method': status['has_payment_method']
        })

    except Exception as e:
        print(f"❌ Generation progress error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/generate-remaining-months', methods=['POST'])
def generate_remaining_months():
    """
    Prepare remaining 10 months (Cover + Apr-Dec) for generation after payment authorization
    Returns immediately - actual generation happens via AJAX in generating_local.html
    """
    from app.services.monthly_themes import get_all_themes

    print(f"\n{'='*70}")
    print(f"🎨 PREPARING REMAINING 10 MONTHS (Cover + Apr-Dec)")
    print(f"{'='*70}\n")

    project = get_current_project()
    if not project:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Verify payment method is saved
        if not session_storage.get_payment_method_id():
            return jsonify({'error': 'Payment method not authorized'}), 400

        # Set status to generating
        session_storage.set_generation_stage('generating_full')
        session_storage.update_generation_progress(0)

        # Get all themes
        all_themes = get_all_themes()

        # Create remaining month records (Cover + Apr-Dec) with status 'pending'
        # Actual generation will happen via /api/generate/month/{month_num} calls from frontend
        session_storage.create_remaining_months(all_themes)

        print("✅ Created 10 month records with status 'pending'")
        print("📋 Frontend will generate these via individual AJAX calls")
        print(f"{'='*70}\n")

        return jsonify({
            'success': True,
            'months_created': 10,
            'message': 'Remaining months prepared for generation'
        })

    except Exception as e:
        print(f"\n❌ REMAINING MONTHS PREPARATION FAILED")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*70}\n")

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
