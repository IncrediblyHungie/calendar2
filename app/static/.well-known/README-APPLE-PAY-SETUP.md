# Apple Pay Domain Verification Setup

## Why Apple Pay Isn't Showing Up

Apple Pay requires domain verification through Stripe before it will appear on your website. This is a security requirement from Apple.

## Steps to Enable Apple Pay

### 1. Go to Stripe Dashboard
- Log in to your Stripe account at https://dashboard.stripe.com
- Navigate to: **Settings** → **Payment methods**

### 2. Enable Apple Pay
- Find "Apple Pay" in the list of payment methods
- If it's not already enabled, click to enable it

### 3. Add Your Domain
- Under Apple Pay settings, click **"Add new domain"**
- Enter your domain: `hunkofthemonth.shop`
- Also add: `hunkofthemonth.fly.dev` (for testing)

### 4. Download the Verification File
- Stripe will provide a file named: `apple-developer-merchantid-domain-association`
- Download this file

### 5. Place the File Here
- Put the downloaded file in this directory: `/home/peteylinux/Projects/KevCal/app/static/.well-known/`
- The file should be named EXACTLY: `apple-developer-merchantid-domain-association` (no extension)
- Replace this README or keep it - doesn't matter

### 6. Deploy to Production
```bash
cd /home/peteylinux/Projects/KevCal
git add app/static/.well-known/apple-developer-merchantid-domain-association
git commit -m "Add Apple Pay domain verification file"
/root/.fly/bin/flyctl deploy -a hunkofthemonth
```

### 7. Verify in Stripe Dashboard
- After deploying, go back to Stripe Dashboard
- Click "Verify" next to your domain
- Stripe will check that the file is accessible at:
  `https://hunkofthemonth.shop/.well-known/apple-developer-merchantid-domain-association`

### 8. Test on iPhone
- Open Safari on iPhone
- Go to `https://hunkofthemonth.shop`
- Create a calendar and get to the "Love what you see?" section
- You should now see **Apple Pay** as the first payment option!

## Important Notes

- **Must use Safari on iOS/macOS**: Apple Pay only appears in Safari browser on Apple devices
- **Must be HTTPS**: Your site is already HTTPS ✓
- **Verification takes ~5 minutes**: After adding the file, Stripe needs a few minutes to verify
- **Testing**: You can test on `hunkofthemonth.fly.dev` first, then verify `hunkofthemonth.shop`

## Troubleshooting

**Apple Pay still not showing?**
1. Verify the file is accessible: Visit `https://hunkofthemonth.shop/.well-known/apple-developer-merchantid-domain-association`
2. Check Stripe Dashboard shows domain as "Verified"
3. Test on actual iPhone with Safari (not Chrome, not Android)
4. Clear Safari cache and reload page
5. Wait 5-10 minutes after verification before testing

**File not found error?**
- Make sure filename is EXACT: `apple-developer-merchantid-domain-association` (no .txt, no extension)
- File should be in: `/home/peteylinux/Projects/KevCal/app/static/.well-known/`
- Redeploy after adding file

## Current Status
✅ Route configured to serve verification file at `/.well-known/apple-developer-merchantid-domain-association`
⏳ **Waiting for you to add the verification file from Stripe Dashboard**
