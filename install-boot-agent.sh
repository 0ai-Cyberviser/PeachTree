#!/bin/bash
# Install Hancock Boot-Time Agent
# Run after Colab training completes

set -e

echo "════════════════════════════════════════════════════════════"
echo "  HANCOCK BOOT-TIME AGENT INSTALLATION"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (sudo bash install-boot-agent.sh)"
    exit 1
fi

# Check for trained model
if [ ! -d "hancock-ultimate" ]; then
    echo "❌ Trained model not found!"
    echo ""
    echo "Please extract hancock-ultimate.zip from Colab first:"
    echo "  unzip hancock-ultimate.zip"
    echo ""
    exit 1
fi

echo "📦 Installing Hancock AI Agent..."
echo ""

# Create directories
echo "Creating directories..."
mkdir -p /opt/hancock/models
mkdir -p /opt/hancock/cache
mkdir -p /var/log/hancock

# Copy model
echo "Installing model..."
cp -r hancock-ultimate/* /opt/hancock/models/final/
echo "✅ Model installed to /opt/hancock/models/final/"

# Copy agent script
echo "Installing agent..."
cp hancock_agent.py /opt/hancock/
chmod +x /opt/hancock/hancock_agent.py
echo "✅ Agent installed"

# Install systemd service
echo "Installing systemd service..."
cp hancock-agent.service /etc/systemd/system/
systemctl daemon-reload
echo "✅ Service installed"

# Enable service
echo "Enabling boot-time startup..."
systemctl enable hancock-agent.service
echo "✅ Boot-time startup enabled"

# Start service
echo "Starting agent..."
systemctl start hancock-agent.service
sleep 3

# Check status
if systemctl is-active --quiet hancock-agent.service; then
    echo "✅ Agent running!"
else
    echo "⚠️  Agent not running. Check status:"
    echo "  sudo systemctl status hancock-agent.service"
    exit 1
fi

# Create CLI command
echo "Creating CLI command..."
cat > /usr/local/bin/hancock << 'EOF'
#!/bin/bash
curl -s -X POST http://127.0.0.1:8080 \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"$*\"}" | jq -r '.response'
EOF
chmod +x /usr/local/bin/hancock
echo "✅ CLI command created"

# Test API
echo ""
echo "Testing agent..."
sleep 2

RESPONSE=$(curl -s -X POST http://127.0.0.1:8080 \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is SQL injection?"}')

if [ $? -eq 0 ] && [ ! -z "$RESPONSE" ]; then
    echo "✅ Agent responding!"
else
    echo "⚠️  Agent not responding. Check logs:"
    echo "  sudo journalctl -u hancock-agent.service -f"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  INSTALLATION COMPLETE!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "✅ Hancock AI Agent installed and running"
echo ""
echo "📊 Service status:"
echo "   Status: $(systemctl is-active hancock-agent.service)"
echo "   API: http://127.0.0.1:8080"
echo ""
echo "🔧 Usage:"
echo "   hancock \"Your question here\""
echo ""
echo "Example:"
echo "   hancock \"How do I use nmap?\""
echo ""
echo "📝 Logs:"
echo "   sudo journalctl -u hancock-agent.service -f"
echo ""
echo "🔄 Control:"
echo "   sudo systemctl restart hancock-agent.service"
echo "   sudo systemctl stop hancock-agent.service"
echo "   sudo systemctl status hancock-agent.service"
echo ""
