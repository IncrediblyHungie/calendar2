#!/bin/bash
# KevCal Project Cleanup Script
# Removes unused test scripts, templates, and old images
# Run from project root: bash cleanup_old_files.sh

echo "🗑️  KevCal Cleanup Script - Removing unused files..."
echo ""

# Change to project directory
cd /home/peteylinux/Projects/KevCal

# 1. Delete test/debug scripts (22 files, ~80 KB)
echo "1️⃣  Removing test scripts..."
rm -f test_*.py check_*.py generate_*.py debug_*.py fetch_*.py \
      edit_mockup_month.py printify_mockup_service.py quick_model_test.py \
      comprehensive_wall_calendar_check.py 2>/dev/null
echo "   ✅ Test scripts removed"

# 2. Delete unused templates (3 files, ~35 KB)
echo "2️⃣  Removing unused templates..."
rm -f app/templates/index_OLD.html \
      app/templates/prompts.html \
      app/templates/generating.html 2>/dev/null
echo "   ✅ Unused templates removed"

# 3. Delete unused service module
echo "3️⃣  Removing unused Celery service..."
rm -f app/services/celery_tasks.py 2>/dev/null
echo "   ✅ Celery tasks removed"

# 4. Delete duplicate/unused image folders (55+ MB!)
echo "4️⃣  Removing duplicate and old images..."

# Delete entire carousel folder (26 MB) - duplicates of examples folder
rm -rf app/static/assets/images/carousel/ 2>/dev/null
echo "   ✅ carousel/ folder removed (26 MB)"

# Delete entire examples folder (26 MB) - only used in deleted index_OLD.html
rm -rf app/static/assets/images/examples/ 2>/dev/null
echo "   ✅ examples/ folder removed (26 MB)"

# Delete archive folder (2.9 MB) - old back_cover.png
rm -rf app/static/assets/images/archive/ 2>/dev/null
echo "   ✅ archive/ folder removed (2.9 MB)"

# Delete old unused logo images
rm -f app/static/assets/images/logo/logo-cream-blue.png 2>/dev/null
rm -f app/static/assets/images/logo/logo-2.svg 2>/dev/null
echo "   ✅ Old logo files removed (~2 MB)"

# Delete old unused hero images
rm -f app/static/assets/images/hero/hero-image.svg 2>/dev/null
rm -f app/static/assets/images/hero/brand.svg 2>/dev/null
echo "   ✅ Old hero files removed"

# 5. Clean Python cache files
echo "5️⃣  Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
echo "   ✅ Python cache cleaned"

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Space saved: ~60-65 MB"
echo ""
echo "Removed:"
echo "  • 22 test/debug scripts"
echo "  • 3 unused templates"
echo "  • 1 unused service module"
echo "  • 55+ MB of duplicate/old images"
echo "  • Python cache files"
echo ""
echo "Next: Run 'git status' to review changes before committing"
