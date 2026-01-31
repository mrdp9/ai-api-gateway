# Setup Guide: CloudFlare Tunnel + Email Notifications

## Prerequisites

1. **Docker & Docker Compose** installed on your machine
2. **CloudFlare Account** (free tier is sufficient)
3. **Gmail Account** with App Password (for email notifications)

---

## Step 1: CloudFlare Tunnel Setup

### 1a. Create a CloudFlare Tunnel

1. Go to [CloudFlare Dashboard](https://dash.cloudflare.com/)
2. Navigate to **Tunnels** (left sidebar under Zero Trust)
3. Click **Create a tunnel**
4. Choose a tunnel name (e.g., `ai-api-gateway`)
5. CloudFlare will provide a **TUNNEL_TOKEN**
6. Copy this token to `.env` file

### 1b. Get Your Tunnel Token

The tunnel creation will show you a command like:
```bash
cloudflared tunnel run --token <TOKEN>
```

Copy the `<TOKEN>` part to your `.env`:
```env
TUNNEL_TOKEN=eyJ...token...here
```

---

## Step 2: Gmail App Password Setup

### 2a. Enable 2-Step Verification (if not already enabled)

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**

### 2b. Generate App Password

1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select **Mail** and **Windows Computer** (or your device)
3. Generate a new app password
4. Copy this 16-character password to your `.env`:

```env
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
ADMIN_EMAIL=prjctxno@gmail.com
```

---

## Step 3: Configure Environment Variables

Create `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Security
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
ADMIN_USER=admin
ADMIN_PASS=your-secure-password

# Email
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-app-password-from-step-2
ADMIN_EMAIL=prjctxno@gmail.com

# CloudFlare Tunnel
TUNNEL_TOKEN=your-tunnel-token-from-step-1

# Optional (leave empty to auto-discover)
TUNNEL_URL=
```

---

## Step 4: Start with Docker Compose

### 4a. Build & Start Services

```bash
docker-compose up --build
```

This will:
1. Build the FastAPI container
2. Start the API service on port 3001 (localhost)
3. Start the CloudFlare tunnel
4. Attempt to register the tunnel URL with the API

### 4b. Wait for Tunnel to Establish

Watch the logs for:
```
tunnel-notifier | Found tunnel URL: https://your-tunnel-name.trycloudflare.com
tunnel-notifier | Notified API about tunnel URL
```

---

## Step 5: Check Your Email

You should receive an email from your Gmail account with:
- The tunnel URL
- Link to access the dashboard

Example email:
```
🔗 Your AI API Gateway Tunnel URL

Your CloudFlare Tunnel URL:
https://your-random-name.trycloudflare.com

Access your API Key Dashboard at:
https://your-random-name.trycloudflare.com/

Login with your admin credentials.
```

---

## Step 6: Access the Dashboard

### Local (without tunnel):
```
http://localhost:3001/
```

### Internet (with tunnel):
Use the URL from the email sent to your Gmail account.

Login with:
- **Username:** `admin` (or your `ADMIN_USER`)
- **Password:** Your `ADMIN_PASS`

---

## Step 7: Create & Use API Keys

1. Click **"Create New Key"** button
2. Set expiration (default: 30 days)
3. Click **"Create New Key"** to generate
4. Copy the key (shown once!)
5. Use in API requests with the header:
   ```
   x-api-key: your-api-key-here
   ```

---

## Troubleshooting

### Email Not Sending

- ✅ Check that SMTP credentials are in `.env`
- ✅ Ensure Gmail App Password is correctly set
- ✅ Check Docker logs: `docker-compose logs api`

### Tunnel Not Connecting

- ✅ Verify `TUNNEL_TOKEN` is correct
- ✅ Check internet connection
- ✅ Ensure CloudFlare account is active
- ✅ Check logs: `docker-compose logs tunnel`

### Can't Access Dashboard

- ✅ Verify admin credentials in `.env`
- ✅ Check that API is running: `docker ps`
- ✅ Local: ensure port 3001 is available
- ✅ Internet: wait 30-60 seconds for tunnel to stabilize

### Database Issues

- ✅ Ensure `./data/` directory exists and is writable
- ✅ Remove `.db` file to reset: `rm data/keys.db`

---

## Production Recommendations

1. **Change Default Credentials**: Update `ADMIN_USER` and `ADMIN_PASS`
2. **Use Strong SECRET_KEY**: Generate with `python -c "import secrets; print(secrets.token_hex(32))"`
3. **Monitor Logs**: Set up log aggregation (ELK, Datadog, etc.)
4. **Rate Limiting**: Already enabled with `slowapi`
5. **Backup Database**: Regular backups of `data/keys.db`
6. **SSL/TLS**: CloudFlare Tunnel provides automatic HTTPS

---

## Testing the API

### Generate Text

```bash
curl -X POST http://localhost:3001/generate \
  -H "x-api-key: YOUR-API-KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!"}'
```

### Health Check

```bash
curl http://localhost:3001/health
```

---

## Next Steps

- Monitor email deliverability
- Set up additional endpoints as needed
- Consider adding webhook notifications for key expirations
- Implement automated backups for the database
