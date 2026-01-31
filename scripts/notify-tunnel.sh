#!/bin/sh
# Script to fetch tunnel URL from cloudflared and notify the API

# Wait for tunnel to be ready
RETRY_COUNT=0
MAX_RETRIES=30

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # Try to get tunnel info
    TUNNEL_INFO=$(cloudflared tunnel info 2>/dev/null || echo "")
    
    if [ ! -z "$TUNNEL_INFO" ]; then
        # Extract public URL from tunnel info
        # The format varies; this is a basic extraction
        TUNNEL_URL=$(echo "$TUNNEL_INFO" | grep -oP 'https://[a-z0-9\-\.]+' | head -1)
        
        if [ ! -z "$TUNNEL_URL" ]; then
            echo "Found tunnel URL: $TUNNEL_URL"
            
            # Notify the API
            curl -X POST "$API_URL/admin/set-tunnel-url" \
                -H "Content-Type: application/json" \
                -d "{\"tunnel_url\": \"$TUNNEL_URL\"}" \
                && echo "Notified API about tunnel URL" \
                || echo "Failed to notify API"
            
            exit 0
        fi
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for tunnel... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo "Failed to get tunnel URL after $MAX_RETRIES attempts"
exit 1
