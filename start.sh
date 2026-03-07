#!/bin/bash
# Finance Tracker — Start Script
# Access locally: http://localhost:8501
# Access from phone (same WiFi): http://<your-mac-ip>:8501

cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Get local IP for display
LOCAL_IP=$(ifconfig en0 2>/dev/null | grep "inet " | awk '{print $2}')

echo ""
echo "============================================"
echo "  Finance Tracker Starting..."
echo "============================================"
echo ""
echo "  Local:   http://localhost:8501"
echo "  Mobile:  http://${LOCAL_IP}:8501"
echo ""
echo "  Open the Mobile URL on your phone"
echo "  (same WiFi network required)"
echo "============================================"
echo ""

streamlit run app.py
