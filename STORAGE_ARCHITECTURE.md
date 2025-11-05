# KevCal Storage Architecture

## Overview
KevCal uses a file-based persistent storage system on Fly.io to store user sessions, uploaded images, generated calendars, and shopping cart data.

## Storage Configuration

### Production (Fly.io)
- **Storage Type**: Fly.io Persistent Volume (block storage)
- **Mount Point**: `/data`
- **Volume Name**: `session_storage`
- **Volume ID**: `vol_4y5ey7jjg1dmnyer`
- **Size**: 5GB
- **Created**: November 2, 2025
- **Region**: sjc (San Jose, California)

### Local Development
- **Storage Type**: Temporary filesystem
- **Location**: `/tmp/session_storage`
- **Behavior**: Data is lost on system restart

## How It Works

### Automatic Environment Detection
The application automatically detects whether it's running in production or locally:

```python
# app/session_storage.py line 14
STORAGE_DIR = Path('/data/session_storage') if Path('/data').exists() else Path('/tmp/session_storage')
```

**Logic**:
- If `/data` directory exists → Use persistent volume (production)
- If `/data` doesn't exist → Use `/tmp` (local development)

### Data Persistence
All data is stored as pickle files (`.pkl`) in `/data/session_storage/`:
- Session state and metadata
- Uploaded user images (binary data)
- Generated calendar months and themes
- Shopping cart items with project references
- Product type and pricing information

### Current Storage Usage (as of Nov 5, 2025)
- **Total Size**: ~65MB
- **Session Files**: 70+ active session files
- **File Sizes**: Range from 137 bytes (empty sessions) to 11MB (sessions with images)
- **Retention**: Data persists across all deployments

## Fly.io Volume Configuration

### fly.toml Configuration
```toml
[mounts]
  source = "session_storage"
  destination = "/data"
```

This configuration:
- Mounts the `session_storage` volume at `/data` in the container
- Volume survives deployments, restarts, and machine updates
- Data is preserved even when the app is stopped or scaled

### Volume Management Commands
```bash
# List volumes
flyctl volumes list -a hunkofthemonth

# Check volume status
flyctl volumes show vol_4y5ey7jjg1dmnyer -a hunkofthemonth

# SSH into machine to inspect storage
flyctl ssh console -a hunkofthemonth -C "ls -lah /data/session_storage/"
```

## Storage Architecture Decisions

### Why File-Based Storage?
1. **Simplicity**: No database setup or management required
2. **Cost**: Free (included with Fly.io free tier)
3. **Performance**: Fast local disk I/O for session operations
4. **Adequate for Scale**: Current usage (~65MB) is well within limits
5. **Pickle Efficiency**: Binary serialization is fast and space-efficient

### When to Consider Database Migration
Consider migrating to Postgres/Redis when:
- Storage exceeds 3-4GB (approaching 5GB limit)
- Need to query/search across sessions
- Multiple app instances need shared state
- Need atomic transactions across sessions
- Webhook processing requires complex queries

### Current Storage Breakdown
```
/data/
├── lost+found/          # Volume filesystem metadata
└── session_storage/     # Application session data (65MB)
    ├── session1.pkl     # User session with uploaded images
    ├── session2.pkl     # User session with generated calendar
    ├── session3.pkl     # User session with cart items
    └── ...
```

## Pricing Information Storage

Product prices are defined in multiple locations for different purposes:

### 1. Stripe Checkout (`app/services/stripe_service.py`)
```python
CALENDAR_PRICES = {
    'wall_calendar': 3500,  # $35.00 (cents)
    'desktop': 3000         # $30.00 (cents)
}
```
**Purpose**: Actual amount charged to customer via Stripe

### 2. Printify Order Creation (`app/services/printify_service.py`)
```python
CALENDAR_PRODUCTS = {
    'wall_calendar': {
        'price': 3500,  # $35.00 (cents)
        ...
    },
    'desktop': {
        'price': 3000,  # $30.00 (cents)
        ...
    }
}
```
**Purpose**: Product configuration for print fulfillment

### 3. Session Storage Reference (`app/session_storage.py`)
```python
PRODUCT_PRICES = {
    'desktop': 30.00,      # $30.00 (dollars)
    'wall_calendar': 35.00  # $35.00 (dollars)
}
```
**Purpose**: Reference prices for cart items and session data (dollars, not cents)

**Note**: All three price definitions must stay synchronized when updating pricing.

## Data Flow

### User Session Lifecycle
1. **User visits site** → Session created in `/data/session_storage/`
2. **Upload images** → Binary data stored in session pickle file
3. **Generate calendar** → AI-generated months saved to session
4. **Add to cart** → Cart items with project references stored
5. **Checkout** → Stripe session created, order placed with Printify
6. **Webhook received** → Cart items cleared from session
7. **Session persists** → Data available across visits until expiry

### Deployment Behavior
- **Before deployment**: All session data in `/data/session_storage/`
- **During deployment**: Volume remains attached, data untouched
- **After deployment**: New app version reads existing session data
- **Result**: Zero data loss, seamless user experience

## Backup Strategy

### Current Backup
- Fly.io volumes have snapshot capability (manual)
- No automated backups configured yet

### Recommended Future Backups
```bash
# Manual volume snapshot
flyctl volumes snapshots create vol_4y5ey7jjg1dmnyer -a hunkofthemonth

# Automated daily backups (future enhancement)
# Add to .github/workflows or cron job
```

## Monitoring & Maintenance

### Storage Health Checks
```bash
# Check available space
flyctl ssh console -a hunkofthemonth -C "df -h /data"

# Check session file count
flyctl ssh console -a hunkofthemonth -C "ls /data/session_storage/ | wc -l"

# Check total storage usage
flyctl ssh console -a hunkofthemonth -C "du -sh /data/session_storage/"

# Find largest sessions (potential cleanup candidates)
flyctl ssh console -a hunkofthemonth -C "du -h /data/session_storage/* | sort -rh | head -10"
```

### Session Cleanup
Currently, no automatic session expiration is implemented. Consider adding:
- Session TTL (time-to-live) of 30 days
- Automatic cleanup of expired sessions
- Monitoring for sessions over 10MB (potential abuse)

## Security Considerations

### Current Security
- Volume is mounted read-write by app only
- No external access to volume data
- Sessions use cryptographically secure IDs
- Pickle files are binary (not human-readable)

### Access Control
- **App process**: Full read/write access to `/data/session_storage/`
- **SSH console**: Root access for debugging (restricted to admin)
- **External access**: None (volume is not exposed)

## Future Enhancements

### Potential Improvements
1. **Session Expiration**: Auto-delete sessions after 30 days
2. **Compression**: Gzip large session files to save space
3. **Database Migration**: Move to Postgres when scale requires
4. **Redis Cache**: Add Redis for hot session data
5. **S3 Storage**: Offload generated images to object storage
6. **Monitoring**: Add alerts for storage >80% full

### Volume Expansion
If 5GB limit is reached:
```bash
# Create larger volume
flyctl volumes create session_storage_v2 --size 10 -a hunkofthemonth -r sjc

# Migrate data (manual process)
# 1. Stop app
# 2. Copy data from old to new volume
# 3. Update fly.toml to use new volume
# 4. Deploy
```

## Troubleshooting

### Data Not Persisting
1. Check volume is attached: `flyctl volumes list -a hunkofthemonth`
2. Verify mount in fly.toml: `[mounts] source = "session_storage"`
3. Check storage directory exists: `flyctl ssh console -a hunkofthemonth -C "ls -la /data"`
4. Verify app uses correct path: Check `STORAGE_DIR` in session_storage.py

### Storage Full
1. Check usage: `flyctl ssh console -a hunkofthemonth -C "df -h /data"`
2. Find large files: `flyctl ssh console -a hunkofthemonth -C "du -h /data/session_storage/* | sort -rh | head -20"`
3. Clean old sessions or expand volume

### Performance Issues
1. Check I/O wait: Monitor Fly.io metrics
2. Consider database migration if >1000 sessions
3. Add Redis cache for hot data

---

**Last Updated**: November 5, 2025
**Status**: ✅ Production-ready, working correctly
**Next Review**: When storage reaches 3GB or 6 months from now
