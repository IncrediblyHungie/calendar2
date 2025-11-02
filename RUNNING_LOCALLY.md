# Running Hunk of the Month Locally

## Why Run Locally?
- **MUCH faster**: Generate all 12 months in 2-3 minutes (vs 10+ on cloud)
- **No memory issues**: Your machine has way more RAM than Fly.io
- **Free**: No cloud hosting costs
- **Easy debugging**: Direct access to logs and code

## Quick Start

1. **Run the app:**
```bash
cd /home/peteylinux/Projects/KevCal
./run_local.sh
```

2. **Access at:** http://localhost:8080

3. **For public access** (optional):
```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8080
# You'll get a public URL like: https://abc123.ngrok.io
```

## Performance Tweaks for Local

### Enable Maximum Parallel Generation

With your beefy machine, you can generate all 12 at once!

**Edit:** `app/templates/generating.html`

**Change line 77 from:**
```javascript
const MAX_PARALLEL = 2; // Generate 2 months at a time (safer for 1GB RAM machine)
```

**To:**
```javascript
const MAX_PARALLEL = 12; // Generate all 12 at once (for local with 16GB+ RAM)
```

**Result:** 2-3 minutes total instead of 10!

## Stripe Webhooks (for local testing)

Stripe can't call localhost directly. Use Stripe CLI:

```bash
# Install Stripe CLI
stripe listen --forward-to localhost:8080/webhooks/stripe

# Test a webhook
stripe trigger payment_intent.succeeded
```

## Production Deployment

When ready for real users, deploy to Fly.io:

```bash
flyctl deploy -a hunkofthemonth
```

Best of both worlds:
- Local for fast development/testing
- Cloud for public access
