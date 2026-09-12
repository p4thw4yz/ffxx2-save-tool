# Deploying to Cloudflare Pages

The FFX/FFX2 Save Tool TypeScript app is ready to deploy to Cloudflare Pages!

## Quick Start

### Prerequisites
- Cloudflare account (free tier works)
- GitHub account (for automatic deployments)
- GitHub repository with this code

### Steps

#### 1. Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/ffx-converter.git
git branch -M main
git push -u origin main
```

#### 2. Connect to Cloudflare Pages
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Select **Pages** → **Create a project** → **Connect to Git**
3. Select your GitHub repository
4. Choose **Deploy with Git**
5. Configure build settings:
   - **Production branch**: `main`
   - **Framework**: `None` (or Vite if available)
   - **Build command**: `cd typescript && npm install && npm run build`
   - **Build output directory**: `typescript/dist`
6. Click **Save and Deploy**

#### 3. Custom Domain (Optional)
- In Cloudflare Pages settings, add a custom domain
- Point your DNS to Cloudflare nameservers
- Pages will automatically provision SSL/TLS

## Alternative: Manual Deployment with Wrangler

If you prefer CLI deployment:

### 1. Install Wrangler
```bash
npm install -g wrangler
```

### 2. Authenticate
```bash
wrangler login
```

### 3. Deploy
```bash
cd typescript
npm run build
wrangler pages deploy dist/ --project-name=ffx-save-tool
```

## Environment Details

- **Static Site**: No backend needed, runs entirely in browser
- **Build Output**: `typescript/dist/`
- **Build Time**: ~135ms
- **Gzip Size**: ~75 KB (JavaScript + CSS)
- **Data Storage**: Browser localStorage only (no uploads)

## What Gets Deployed

✓ Fully functional FFX/FFX2 save editor  
✓ Overview, Fields, Story Position, Export tabs  
✓ Hex viewer with coverage stats  
✓ Stats Editor with presets and sliders  
✓ Support for PC, Vita, and Switch saves  
✓ Platform conversion (PC ↔ Vita ↔ Switch)  
✓ Checksum recomputation  

## After Deployment

Your site will be available at:
- `https://ffx-save-tool.pages.dev` (default)
- Or your custom domain

**Key Features:**
- No files uploaded anywhere (100% client-side processing)
- Works offline once loaded
- Instant load times
- Auto-deploys on git push

## Troubleshooting

**Build fails?**
- Check that `cd typescript && npm run build` runs locally first
- Verify Node.js 16+ is available

**Page shows blank?**
- Check browser console for errors
- Verify `typescript/dist/index.html` exists locally

**Stats Editor not working?**
- Ensure you uploaded a valid FFX/FFX2 save file
- Try with the test saves in `mysaves/`

## Support

For issues or questions, check the README.md or test locally with:
```bash
cd typescript && npm run dev
```
