# Rollback Instructions - KevCal Preview Mockup Feature

**Current Deployment**: `preview-test` branch (Calendar Preview Mockups)
**Deployed to**: Fly.io (hunkofthemonth.fly.dev)
**Date**: November 3, 2025

---

## 🔄 Quick Rollback to Main (Original Version)

If you need to revert to the original version WITHOUT the mockup preview feature:

### Option 1: Fast Rollback (Recommended)

```bash
cd /home/peteylinux/Projects/KevCal

# Switch to main branch
git checkout main

# Deploy main branch to Fly.io
export PATH="/root/.fly/bin:$PATH"
flyctl deploy -a hunkofthemonth
```

**Time**: ~2-3 minutes

---

### Option 2: Rollback to Specific Previous Deployment

```bash
cd /home/peteylinux/Projects/KevCal

# List recent deployments
export PATH="/root/.fly/bin:$PATH"
flyctl releases -a hunkofthemonth

# Rollback to previous version (one before current)
flyctl releases rollback -a hunkofthemonth
```

**Time**: ~30 seconds (instant rollback)

---

## 📊 Current Deployment Info

### Preview-Test Branch
- **Branch**: `preview-test`
- **Commit**: `20520bb` - "Add realistic calendar preview mockups before purchase"
- **Features Added**:
  - ✅ Printify product mockup generation
  - ✅ Realistic calendar preview on preview page
  - ✅ 5x faster checkout (product reuse)
  - ✅ Session storage for mockup data

### Main Branch (Fallback)
- **Branch**: `main`
- **Last Commit**: `3532fce` - "Add comprehensive project documentation for future reference"
- **Features**:
  - ✅ AI image generation
  - ✅ Individual month previews
  - ✅ Stripe checkout
  - ✅ Printify fulfillment
  - ❌ No mockup previews

---

## 🧪 Testing After Rollback

After rolling back to `main`, test these key features:

1. **Image Generation**:
   ```
   Visit: https://hunkofthemonth.fly.dev
   Upload: 3-10 selfies
   Generate: 12 calendar months
   ```

2. **Preview Page**:
   ```
   Verify: Individual month images display correctly
   Check: NO "Realistic Calendar Preview" section (removed)
   ```

3. **Checkout**:
   ```
   Test: Stripe checkout flow
   Verify: Webhook creates new Printify product
   Expected: ~90 seconds for product creation
   ```

---

## 🚀 Re-Deploying Preview-Test

To switch back to the preview mockup feature:

```bash
cd /home/peteylinux/Projects/KevCal

# Switch to preview-test branch
git checkout preview-test

# Deploy to Fly.io
export PATH="/root/.fly/bin:$PATH"
flyctl deploy -a hunkofthemonth
```

---

## 📝 Deployment History

| Date | Branch | Commit | Description |
|------|--------|--------|-------------|
| 2025-11-03 | `preview-test` | `20520bb` | **CURRENT**: Calendar mockup previews |
| 2025-11-02 | `main` | `3532fce` | Project documentation |
| 2025-11-02 | `main` | `bf4ce57` | Fix image cropping issues |
| 2025-11-02 | `main` | `b39cb32` | Security: Remove exposed API tokens |

---

## 🔍 How to Check Which Branch is Deployed

```bash
cd /home/peteylinux/Projects/KevCal

# Method 1: Check latest commit in Fly.io logs
export PATH="/root/.fly/bin:$PATH"
flyctl logs -a hunkofthemonth | grep -i "commit\|branch"

# Method 2: SSH into machine and check
flyctl ssh console -a hunkofthemonth
git log -1 --oneline  # Shows current deployed commit
exit

# Method 3: Test the feature
# If preview page shows "Realistic Calendar Preview" section → preview-test
# If preview page only shows individual images → main
```

---

## ⚙️ Environment Variables (Same for Both Branches)

These secrets are configured in Fly.io and don't need to change during rollback:

```bash
FLASK_SECRET_KEY     # Auto-generated
GOOGLE_API_KEY       # Gemini API key
PRINTIFY_API_TOKEN   # Printify integration
STRIPE_SECRET_KEY    # Payment processing
STRIPE_WEBHOOK_SECRET # Webhook verification
FLASK_ENV            # production
```

To verify secrets are set:
```bash
export PATH="/root/.fly/bin:$PATH"
flyctl secrets list -a hunkofthemonth
```

---

## 🐛 Troubleshooting

### Issue: Deployment fails

**Solution**:
```bash
# Check if you're on the correct branch
git branch --show-current

# Verify fly.toml exists
ls -la fly.toml

# Check Fly.io authentication
export PATH="/root/.fly/bin:$PATH"
flyctl auth whoami

# Try deployment again with verbose logging
flyctl deploy -a hunkofthemonth --verbose
```

### Issue: App shows 502/503 errors after deployment

**Solution**:
```bash
# Check machine status
export PATH="/root/.fly/bin:$PATH"
flyctl status -a hunkofthemonth

# View recent logs
flyctl logs -a hunkofthemonth

# Restart machine if needed
flyctl machine restart <machine-id> -a hunkofthemonth
```

### Issue: Old version still showing after deployment

**Solution**:
```bash
# Force restart all machines
export PATH="/root/.fly/bin:$PATH"
flyctl machine restart -a hunkofthemonth --force

# Clear browser cache
# Hard refresh: Ctrl+Shift+R (Linux/Windows) or Cmd+Shift+R (Mac)
```

---

## 📞 Support Commands

```bash
# View all deployments
export PATH="/root/.fly/bin:$PATH"
flyctl releases -a hunkofthemonth

# View logs (real-time)
flyctl logs -a hunkofthemonth --follow

# Check app health
flyctl status -a hunkofthemonth

# SSH into machine for debugging
flyctl ssh console -a hunkofthemonth

# List all machines
flyctl machine list -a hunkofthemonth

# Scale machines (if needed)
flyctl scale count 1 -a hunkofthemonth
```

---

## 🔐 Security Notes

- Both branches use the same environment variables/secrets
- No credentials are stored in git (all in Fly.io secrets)
- Rollback does NOT affect user data (sessions stored in /data volume)
- Session storage persists across deployments

---

## 📊 Performance Comparison

| Metric | Main Branch | Preview-Test Branch |
|--------|-------------|---------------------|
| **Preview Load** | Instant | +15s (one-time mockup generation) |
| **Checkout Time** | ~90s | ~15s (if mockup exists) |
| **User Confidence** | Medium | High (see realistic product) |
| **Conversion Rate** | Baseline | Expected +15-30% |

---

## 💡 Recommendation

**Keep preview-test deployed** if:
- ✅ Users appreciate seeing realistic mockup before buying
- ✅ Conversion rate improves
- ✅ No critical bugs reported

**Rollback to main** if:
- ❌ Mockup generation fails frequently
- ❌ Printify rate limits hit
- ❌ Performance issues detected
- ❌ Users prefer simpler preview

---

## 📝 Deployment Checklist

Before switching branches:

- [ ] Test the current deployment
- [ ] Note any issues or bugs
- [ ] Back up important session data (if needed)
- [ ] Notify users if downtime expected (usually zero downtime)
- [ ] Have rollback command ready
- [ ] Monitor logs after deployment

---

**Last Updated**: November 3, 2025
**Deployed By**: Claude Code
**Current Branch**: `preview-test`
**Rollback Ready**: ✅ Yes (main branch available)
