#!/bin/bash
# =============================================================
# LASEM VOC Mesh — Dashboard-Only Deployment (No Docker)
# Builds the React dashboard locally and uploads static files
# to the Hostinger server via SCP/rsync.
#
# Target: https://app.lifeandsemiconductors.com/agro/
# Server: 195.35.34.245:65002 (u387905082)
# =============================================================

set -e

REMOTE_USER="u387905082"
REMOTE_HOST="195.35.34.245"
REMOTE_PORT="65002"
SSH_CMD="ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST}"
DASHBOARD_DIR="./voc-mesh-platform/apps/dashboard"

echo "============================================"
echo "  LASEM VOC Mesh — Dashboard Deploy"
echo "============================================"

# --- Step 1: Build dashboard locally ---
echo ""
echo "[1/4] Building dashboard..."
cd "${DASHBOARD_DIR}"
npm install
npm run build
cd -

echo ""
echo "[2/4] Checking remote directory structure..."
${SSH_CMD} << 'ENDSSH'
# Hostinger public_html structure
# The site app.lifeandsemiconductors.com maps to ~/domains/app.lifeandsemiconductors.com/public_html/
# or ~/public_html/ depending on the hosting plan

WEBROOT=""
if [ -d "$HOME/domains/app.lifeandsemiconductors.com/public_html" ]; then
    WEBROOT="$HOME/domains/app.lifeandsemiconductors.com/public_html"
elif [ -d "$HOME/public_html" ]; then
    WEBROOT="$HOME/public_html"
else
    echo "Looking for web root..."
    find $HOME -maxdepth 3 -name "public_html" -type d 2>/dev/null
fi

if [ -n "$WEBROOT" ]; then
    echo "WEBROOT=$WEBROOT"
    mkdir -p "$WEBROOT/agro"
    echo "Created $WEBROOT/agro/"
fi
ENDSSH

# --- Step 3: Upload built files ---
echo ""
echo "[3/4] Uploading dashboard files..."

# Try to find the webroot
WEBROOT=$(${SSH_CMD} 'if [ -d "$HOME/domains/app.lifeandsemiconductors.com/public_html" ]; then echo "$HOME/domains/app.lifeandsemiconductors.com/public_html"; elif [ -d "$HOME/public_html" ]; then echo "$HOME/public_html"; fi')

if [ -z "$WEBROOT" ]; then
    echo "ERROR: Could not determine web root on server."
    echo "Please provide the web root directory manually:"
    read -r WEBROOT
fi

echo "Deploying to: ${WEBROOT}/agro/"

rsync -avz --progress --delete \
    -e "ssh -p ${REMOTE_PORT}" \
    "${DASHBOARD_DIR}/dist/" \
    "${REMOTE_USER}@${REMOTE_HOST}:${WEBROOT}/agro/"

# --- Step 4: Create .htaccess for SPA routing ---
echo ""
echo "[4/4] Configuring SPA routing..."
${SSH_CMD} << ENDSSH
WEBROOT="${WEBROOT}"

# Create .htaccess for SPA fallback routing under /agro/
cat > "\${WEBROOT}/agro/.htaccess" << 'HTACCESS'
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /agro/

    # If the requested resource exists as a file or directory, serve it
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d

    # Otherwise, fallback to index.html (SPA routing)
    RewriteRule ^ index.html [QSA,L]
</IfModule>

# Enable gzip compression
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/css
    AddOutputFilterByType DEFLATE application/javascript application/json
    AddOutputFilterByType DEFLATE image/svg+xml
</IfModule>

# Cache static assets
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType text/css "access plus 1 year"
    ExpiresByType application/javascript "access plus 1 year"
    ExpiresByType image/svg+xml "access plus 1 year"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType image/jpeg "access plus 1 year"
    ExpiresByType font/woff2 "access plus 1 year"
</IfModule>
HTACCESS

echo ".htaccess created at \${WEBROOT}/agro/.htaccess"
echo ""
ls -la "\${WEBROOT}/agro/" | head -20
ENDSSH

echo ""
echo "============================================"
echo "  Dashboard deployed successfully!"
echo "  URL: https://app.lifeandsemiconductors.com/agro/"
echo "============================================"
