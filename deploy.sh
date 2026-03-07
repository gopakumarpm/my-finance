#!/bin/bash
# Finance Tracker — Deploy with Public URL
# Creates a secure Cloudflare tunnel so you can access from anywhere (mobile data, etc.)
# No account needed. Free. URL changes each restart.

cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Get local IP
LOCAL_IP=$(ifconfig en0 2>/dev/null | grep "inet " | awk '{print $2}')

echo ""
echo "============================================"
echo "  Finance Tracker — Deploying..."
echo "============================================"
echo ""

# Start Streamlit in background
streamlit run app.py &
STREAMLIT_PID=$!

# Wait for Streamlit to start
sleep 3

echo "  Local:    http://localhost:8501"
echo "  WiFi:     http://${LOCAL_IP}:8501"
echo ""
echo "  Starting secure tunnel..."
echo "  (Look for the public URL below)"
echo "============================================"
echo ""

# Start Cloudflare tunnel — prints the public URL
cloudflared tunnel --url http://localhost:8501 2>&1 | while read line; do
    echo "$line"
    # Highlight the public URL when it appears
    if echo "$line" | grep -q "https://.*trycloudflare.com"; then
        URL=$(echo "$line" | grep -oE "https://[^ ]*trycloudflare.com[^ ]*")
        echo ""
        echo "============================================"
        echo "  YOUR PUBLIC URL (open on phone):"
        echo "  $URL"
        echo "============================================"
        echo ""
    fi
done

# Cleanup on exit
kill $STREAMLIT_PID 2>/dev/null
