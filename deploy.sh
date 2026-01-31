#!/bin/bash

# ============================================================================
# AI API Gateway - One-Command Deployment Script
# ============================================================================
# This script automates the entire deployment process:
# 1. Check prerequisites (Docker, Docker Compose)
# 2. Create .env file if missing
# 3. Validate configuration
# 4. Build Docker images
# 5. Start services (API, Tunnel, Notifier)
# 6. Monitor deployment progress
# 7. Display access URLs and next steps
#
# Usage: ./deploy.sh
# ============================================================================

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

log_header() {
    echo -e "\n${BLUE}=================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=================================================================================${NC}\n"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

log_step() {
    echo -e "\n${CYAN}>>> $1${NC}"
}

# ============================================================================
# Check Prerequisites
# ============================================================================

check_prerequisites() {
    log_header "STEP 1: Checking Prerequisites"
    
    local missing=0
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        echo "   Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
        missing=$((missing + 1))
    else
        local docker_version=$(docker --version)
        log_success "Docker installed: $docker_version"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        echo "   Please install Docker Compose (usually included with Docker Desktop)"
        missing=$((missing + 1))
    else
        local compose_version=$(docker-compose --version)
        log_success "Docker Compose installed: $compose_version"
    fi
    
    # Check Docker daemon
    if ! docker ps > /dev/null 2>&1; then
        log_error "Docker daemon is not running"
        echo "   Please start Docker Desktop"
        missing=$((missing + 1))
    else
        log_success "Docker daemon is running"
    fi
    
    if [ $missing -gt 0 ]; then
        log_error "Missing $missing prerequisite(s). Please install and try again."
        exit 1
    fi
    
    log_success "All prerequisites met!"
}

# ============================================================================
# Configure Environment
# ============================================================================

configure_environment() {
    log_header "STEP 2: Configuring Environment"
    
    if [ -f ".env" ]; then
        log_info ".env file already exists"
        read -p "Do you want to update it? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Keeping existing .env file"
            return
        fi
    fi
    
    if [ ! -f ".env.example" ]; then
        log_error ".env.example not found"
        exit 1
    fi
    
    cp .env.example .env
    log_success "Created .env file from .env.example"
    
    log_info "Configuration required. Please edit .env file with:"
    echo ""
    echo "   Required:"
    echo "   - TUNNEL_TOKEN (from CloudFlare dashboard)"
    echo "   - SMTP_USER (your Gmail address)"
    echo "   - SMTP_PASSWORD (Gmail app password)"
    echo ""
    echo "   Optional (has defaults):"
    echo "   - ADMIN_PASS (admin dashboard password)"
    echo "   - SECRET_KEY (will be auto-generated if needed)"
    echo ""
    
    # Auto-generate SECRET_KEY if empty
    if grep -q "^SECRET_KEY=$" .env; then
        log_step "Auto-generating SECRET_KEY..."
        if command -v python3 &> /dev/null; then
            local secret=$(python3 -c "import secrets; print(secrets.token_hex(32))")
            sed -i.bak "s/^SECRET_KEY=$/SECRET_KEY=$secret/" .env
            rm -f .env.bak
            log_success "Generated SECRET_KEY"
        fi
    fi
    
    log_warning "Please edit .env file with your CloudFlare token and Gmail credentials"
    
    # Open editor if available
    if command -v nano &> /dev/null; then
        read -p "Open .env in nano? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            nano .env
        fi
    elif command -v vi &> /dev/null; then
        read -p "Open .env in vi? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            vi .env
        fi
    fi
}

# ============================================================================
# Validate Configuration
# ============================================================================

validate_configuration() {
    log_header "STEP 3: Validating Configuration"
    
    local errors=0
    
    # Check .env exists
    if [ ! -f ".env" ]; then
        log_error ".env file not found"
        exit 1
    fi
    
    # Check TUNNEL_TOKEN
    local tunnel_token=$(grep "^TUNNEL_TOKEN=" .env | cut -d= -f2 | xargs)
    if [ -z "$tunnel_token" ] || [ "$tunnel_token" == "your-cloudflare-tunnel-token" ]; then
        log_error "TUNNEL_TOKEN not configured in .env"
        errors=$((errors + 1))
    else
        log_success "TUNNEL_TOKEN configured"
    fi
    
    # Check SMTP credentials
    local smtp_user=$(grep "^SMTP_USER=" .env | cut -d= -f2 | xargs)
    local smtp_pass=$(grep "^SMTP_PASSWORD=" .env | cut -d= -f2 | xargs)
    
    if [ -z "$smtp_user" ] || [ "$smtp_user" == "your-gmail@gmail.com" ]; then
        log_warning "SMTP_USER not configured (email notifications will be logged only)"
    else
        log_success "SMTP_USER configured"
    fi
    
    if [ -z "$smtp_pass" ]; then
        log_warning "SMTP_PASSWORD not configured (email notifications will be logged only)"
    else
        log_success "SMTP_PASSWORD configured"
    fi
    
    # Check docker-compose.yml
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.yml not found"
        errors=$((errors + 1))
    else
        log_success "docker-compose.yml found"
    fi
    
    if [ $errors -gt 0 ]; then
        log_error "Configuration validation failed. Please fix the errors above."
        exit 1
    fi
    
    log_success "Configuration validated!"
}

# ============================================================================
# Build & Start Services
# ============================================================================

build_and_start() {
    log_header "STEP 4: Building & Starting Services"
    
    log_step "Building Docker images..."
    if docker-compose build > /dev/null 2>&1; then
        log_success "Docker images built successfully"
    else
        log_error "Failed to build Docker images"
        docker-compose build
        exit 1
    fi
    
    log_step "Starting services..."
    docker-compose up -d
    log_success "Services started (running in background)"
    
    log_info "Started services:"
    echo "   - API service (FastAPI)"
    echo "   - Tunnel service (CloudFlare)"
    echo "   - Notifier service (URL registration)"
}

# ============================================================================
# Wait for Tunnel
# ============================================================================

wait_for_tunnel() {
    log_header "STEP 5: Waiting for Tunnel to Establish"
    
    log_info "Waiting for CloudFlare Tunnel to connect (this may take 30-60 seconds)..."
    
    local max_attempts=60
    local attempt=0
    local tunnel_url=""
    
    while [ $attempt -lt $max_attempts ]; do
        attempt=$((attempt + 1))
        
        # Try to get tunnel URL from API logs
        tunnel_url=$(docker-compose logs api 2>/dev/null | grep -oP 'https://[a-z0-9\-\.]+\.trycloudflare\.com' | head -1)
        
        if [ ! -z "$tunnel_url" ]; then
            log_success "Tunnel URL detected: $tunnel_url"
            echo "$tunnel_url"
            return 0
        fi
        
        # Check if tunnel service is running
        if docker-compose logs tunnel 2>/dev/null | grep -q "Tunnel is running"; then
            log_info "Tunnel is running (attempt $attempt/$max_attempts)"
        else
            log_info "Connecting to CloudFlare (attempt $attempt/$max_attempts)"
        fi
        
        sleep 1
        
        # Print progress every 10 attempts
        if [ $((attempt % 10)) -eq 0 ]; then
            echo -ne "${CYAN}  ${attempt}s elapsed...${NC}\r"
        fi
    done
    
    log_warning "Tunnel URL not found in logs (it may have been sent via email)"
    return 1
}

# ============================================================================
# Display Status & URLs
# ============================================================================

display_status() {
    log_header "STEP 6: Deployment Status"
    
    log_success "Services are running!"
    
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
    
    echo ""
    echo "🌐 Access URLs:"
    echo ""
    echo "   Local (No Tunnel):"
    echo "   ${CYAN}http://localhost:3001/${NC}"
    echo ""
    echo "   Internet (Via CloudFlare Tunnel):"
    echo "   ${CYAN}Check your email at prjctxno@gmail.com${NC}"
    echo "   Subject: '🔗 Your AI API Gateway Tunnel URL'"
    echo ""
    
    echo "🔐 Default Login:"
    echo "   Username: admin"
    echo "   Password: (from ADMIN_PASS in .env)"
    echo ""
    
    echo "📝 API Key:"
    echo "   1. Go to dashboard"
    echo "   2. Click 'Create New Key'"
    echo "   3. Copy and use in x-api-key header"
    echo ""
}

# ============================================================================
# Show Logs & Troubleshooting
# ============================================================================

show_help() {
    log_header "USEFUL COMMANDS"
    
    cat << 'EOF'
View Logs:
  docker-compose logs -f api          # API service logs
  docker-compose logs -f tunnel        # CloudFlare tunnel logs
  docker-compose logs -f tunnel-notifier  # Notifier service logs
  docker-compose logs -f              # All services

Manage Services:
  docker-compose restart              # Restart all services
  docker-compose stop                 # Stop all services
  docker-compose down                 # Stop and remove services
  docker-compose up -d                # Start in background

Debugging:
  docker ps                           # List running containers
  docker-compose ps                   # Show service status
  docker-compose logs --tail 50 api   # Last 50 lines of API logs

Testing:
  curl http://localhost:3001/health   # Health check
  curl http://localhost:3001/         # Dashboard (requires auth)

Next Steps:
  1. Access dashboard: http://localhost:3001/
  2. Create API keys
  3. Check email for tunnel URL
  4. Read QUICK_START.md for more details

Troubleshooting:
  - Email not arriving? → Check SMTP_USER & SMTP_PASSWORD in .env
  - Tunnel not connecting? → Check TUNNEL_TOKEN in .env
  - Can't access dashboard? → Verify port 3001 is available
  - API key not working? → Ensure key copied exactly, check x-api-key header

EOF
}

# ============================================================================
# Cleanup on Exit
# ============================================================================

cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Deployment encountered an error (exit code: $exit_code)"
        echo ""
        log_info "To view errors, run: docker-compose logs"
        echo ""
    fi
    return $exit_code
}

trap cleanup EXIT

# ============================================================================
# Main Execution
# ============================================================================

main() {
    clear
    
    log_header "🚀 AI API Gateway Deployment Script"
    log_info "This script will deploy your complete system in one command"
    
    # Run all steps
    check_prerequisites
    configure_environment
    validate_configuration
    build_and_start
    
    # Wait for tunnel (non-blocking)
    wait_for_tunnel || true
    
    # Display status and URLs
    display_status
    
    # Show helpful commands
    show_help
    
    echo ""
    log_success "Deployment complete! 🎉"
    echo ""
    log_info "Your AI API Gateway is now running!"
    echo "   Local: http://localhost:3001/"
    echo "   Internet: Check email for tunnel URL"
    echo ""
    log_warning "To view logs: docker-compose logs -f"
    echo ""
}

# Run main function
main "$@"
