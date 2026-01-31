# 🚀 Quick Start Guide

Welcome to the **AI API Gateway** project! This guide will get you up and running in minutes.

---

## What You're Getting

✅ **API Key Management Dashboard** - Create, view, and revoke API keys  
✅ **CloudFlare Tunnel Integration** - Secure public HTTPS access without opening ports  
✅ **Email Notifications** - Automatic tunnel URL sent to your inbox  
✅ **Modern Web UI** - Beautiful, responsive dashboard  
✅ **Secure Authentication** - HMAC-SHA256 key hashing + HTTP Basic Auth  
✅ **Docker Ready** - One command to deploy everything  

---

## Prerequisites (2 minutes)

Before you start, make sure you have:

1. **Docker & Docker Compose** installed on your machine
   - [Install Docker Desktop](https://www.docker.com/products/docker-desktop)

2. **CloudFlare Account** (free tier works!)
   - Go to [CloudFlare Dashboard](https://dash.cloudflare.com/)
   - Sign up or log in

3. **Gmail Account** with App Password
   - Required for email notifications
   - [Setup Instructions](#gmail-setup)

---

## 5-Minute Setup

### 1. Get Your CloudFlare Tunnel Token

1. Go to [CloudFlare Zero Trust](https://dash.cloudflare.com/)
2. Click **Tunnels** → **Create a tunnel**
3. Choose a name (e.g., `ai-api-gateway`)
4. CloudFlare will show you a `TUNNEL_TOKEN`
5. **Copy this token** - you'll need it in step 3

### 2. Get Your Gmail App Password

1. Go to [Google Account Settings](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (if not already enabled)
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Select **Mail** and your device type
5. Copy the **16-character password**

### 3. Configure Your Project

```bash
# Clone or navigate to the project
cd ai-api-gateway

# Create .env file from template
cp .env.example .env

# Edit .env with your values (use your text editor)
# Open .env and update:
# - TUNNEL_TOKEN (from step 1)
# - SMTP_USER (your Gmail address)
# - SMTP_PASSWORD (from step 2)
# - ADMIN_PASS (choose a strong password)
```

Example `.env` content:
```env
SECRET_KEY=your-secret-here-12345678901234567890
ADMIN_USER=admin
ADMIN_PASS=YourSecurePassword123!
TUNNEL_TOKEN=eyJ0eXAiOiJKV1QiLCJh...
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
ADMIN_EMAIL=prjctxno@gmail.com
```

### 4. Start the Services

```bash
# Build and start everything
docker-compose up --build

# Wait for messages like:
# - "tunnel | Tunnel is running"
# - "tunnel-notifier | Found tunnel URL: https://..."
# - "tunnel-notifier | Notified API about tunnel URL"
```

### 5. Check Your Email

✉️ Look for an email from your Gmail account with subject:
> 🔗 Your AI API Gateway Tunnel URL

The email contains your public URL:
> https://your-random-name.trycloudflare.com

---

## Access Your Dashboard

### 🏠 Local (No Tunnel)
```
http://localhost:3001/
```

### 🌐 Internet (Via Tunnel)
```
https://your-random-name.trycloudflare.com/
```

**Login with:**
- Username: `admin`
- Password: (whatever you set in `ADMIN_PASS`)

---

## Create Your First API Key

1. On the dashboard, click **"Create New Key"**
2. Set expiration (default: 30 days)
3. Click **"Create New Key"** button
4. **Copy the key immediately** (it's shown only once!)
5. The key appears in the table below

---

## Use Your API Key

### Example: Health Check

```bash
curl -X GET http://localhost:3001/health \
  -H "x-api-key: YOUR-API-KEY-HERE"
```

**Response:**
```json
{
  "db": true,
  "ollama": false
}
```

### Example: Generate Text (if Ollama is running)

```bash
curl -X POST http://localhost:3001/generate \
  -H "x-api-key: YOUR-API-KEY-HERE" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!"}'
```

---

## Common Tasks

### Stop the Services

```bash
docker-compose down
```

### View Logs

```bash
# All services
docker-compose logs -f

# Just the API
docker-compose logs -f api

# Just the tunnel
docker-compose logs -f tunnel
```

### Restart Services

```bash
docker-compose restart
```

### Reset Database

```bash
rm data/keys.db
docker-compose restart api
```

### Update Your Environment

Edit `.env` then restart:
```bash
docker-compose restart api
```

---

## Troubleshooting

### ❌ Email not arriving?

1. Check spam folder
2. Verify `SMTP_USER` and `SMTP_PASSWORD` in `.env`
3. Ensure Gmail 2-Step Verification is enabled
4. Check Docker logs: `docker-compose logs api`

### ❌ Can't access the dashboard?

1. Verify services are running: `docker-compose ps`
2. Check if port 3001 is available
3. For local: try `http://localhost:3001/`
4. For internet: wait 60 seconds for tunnel to stabilize

### ❌ Tunnel not connecting?

1. Verify `TUNNEL_TOKEN` is correct
2. Check CloudFlare account is active
3. Ensure internet connection
4. Check logs: `docker-compose logs tunnel`

### ❌ API key not working?

1. Verify key is copied exactly (no spaces)
2. Ensure key is not revoked (check dashboard)
3. Check header is `x-api-key` (lowercase)
4. Make sure you're using the right URL (local vs internet)

---

## Security Tips

🔐 **Before Production:**

1. Change `ADMIN_PASS` to a strong password
2. Use a strong `SECRET_KEY` (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
3. Keep `SMTP_PASSWORD` and `TUNNEL_TOKEN` secret
4. Use HTTPS for all API requests (tunnel provides this)
5. Rotate API keys periodically

---

## What's Next?

- 📖 Read [README.md](README.md) for full documentation
- 🔧 See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup instructions
- ✅ Use [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) before production
- 💻 Modify [context.md](context.md) as you make changes

---

## File Structure

```
ai-api-gateway/
├── api/
│   ├── main.py              # FastAPI application
│   ├── Dockerfile           # Docker image definition
│   ├── requirements.txt      # Python dependencies
│   └── templates/
│       └── index.html       # Dashboard UI
├── data/
│   └── keys.db             # SQLite database (created automatically)
├── scripts/
│   ├── migrate_schema.py   # Database setup
│   ├── notify-tunnel.sh    # Tunnel URL registration
│   ├── update_context.py   # Context automation
│   └── validate-setup.py   # Setup validation
├── docker-compose.yml       # Service orchestration
├── .env.example            # Configuration template
├── .env                    # Your configuration (create from example)
├── README.md               # Full documentation
├── SETUP_GUIDE.md          # Detailed setup instructions
├── DEPLOYMENT_CHECKLIST.md # Pre-deployment checklist
├── QUICK_START.md          # This file
└── context.md              # Development context
```

---

## Support & Documentation

- **Setup Help**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Full Docs**: [README.md](README.md)
- **Pre-Deploy Check**: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- **Development**: [context.md](context.md)

---

## 🎉 You're All Set!

Your AI API Gateway is now running and accessible to the world via CloudFlare Tunnel. 

**Next steps:**
1. ✅ Create some API keys
2. ✅ Test them with your applications
3. ✅ Monitor usage in the dashboard
4. ✅ Revoke keys as needed

**Questions?** Check the troubleshooting section above or review the detailed guides.

Happy coding! 🚀
