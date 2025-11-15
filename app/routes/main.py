"""
Main routes - Landing page, about, etc.
"""
from flask import Blueprint, render_template, session, redirect, url_for, request, send_from_directory, current_app
from app import session_storage
from datetime import datetime, timedelta
import secrets
import os

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@bp.route('/.well-known/apple-developer-merchantid-domain-association')
def apple_pay_domain_verification():
    """
    Serve Apple Pay domain verification file for Stripe
    This file is required for Apple Pay to work on your domain
    Download from: Stripe Dashboard → Settings → Payment methods → Apple Pay
    """
    well_known_dir = os.path.join(current_app.root_path, 'static', '.well-known')
    return send_from_directory(well_known_dir, 'apple-developer-merchantid-domain-association')

@bp.route('/static/webfonts/<path:filename>')
def serve_font(filename):
    """
    Serve Font Awesome webfonts with proper MIME types and CORS headers
    This ensures fonts load correctly across all browsers
    """
    from flask import make_response

    webfonts_dir = os.path.join(current_app.root_path, 'static', 'webfonts')
    response = make_response(send_from_directory(webfonts_dir, filename))

    # Set proper MIME type based on extension
    if filename.endswith('.woff2'):
        response.headers['Content-Type'] = 'font/woff2'
    elif filename.endswith('.woff'):
        response.headers['Content-Type'] = 'font/woff'
    elif filename.endswith('.ttf'):
        response.headers['Content-Type'] = 'font/ttf'

    # Add CORS headers for cross-origin font loading
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'

    return response

@bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@bp.route('/start')
def start():
    """Start creating a calendar - initialize session storage"""
    # Generate session token
    session_token = secrets.token_urlsafe(32)
    session['guest_token'] = session_token
    session['created_at'] = datetime.utcnow().isoformat()

    # Initialize session storage (replaces database)
    session_storage.init_session()
    session_storage.update_project_status('uploading')

    return redirect(url_for('projects.upload'))

def get_current_project():
    """Get the current user's project from session"""
    guest_token = session.get('guest_token')
    if not guest_token:
        return None

    # Return project from session storage
    return session_storage.get_current_project()

@bp.route('/order/success')
def order_success():
    """Order confirmation page after successful Stripe payment"""
    session_id = request.args.get('session_id')

    # Calculate delivery date: 5-6 days from today
    delivery_date = (datetime.now() + timedelta(days=6)).strftime('%B %d, %Y')

    return render_template('order_success.html',
                         session_id=session_id,
                         delivery_date=delivery_date)
