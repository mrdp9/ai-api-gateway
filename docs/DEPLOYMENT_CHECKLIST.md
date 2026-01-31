# Deployment Checklist ✅

This checklist ensures your AI API Gateway is properly configured before deployment.

---

## Pre-Deployment Checklist

### 1. CloudFlare Setup ☁️
- [ ] Create CloudFlare account (free tier is fine)
- [ ] Navigate to Zero Trust > Tunnels
- [ ] Create a new tunnel and get the `TUNNEL_TOKEN`
- [ ] Save token to `.env` as `TUNNEL_TOKEN`

### 2. Gmail Configuration 📧
- [ ] Enable 2-Step Verification on Google Account
- [ ] Generate App Password at myaccount.google.com/apppasswords
- [ ] Save 16-character app password to `.env` as `SMTP_PASSWORD`
- [ ] Set `SMTP_USER` to your Gmail address in `.env`

### 3. Environment Setup 🔧
- [ ] Copy `.env.example` to `.env`
  ```bash
  cp .env.example .env
  ```
- [ ] Generate strong `SECRET_KEY`:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] Update all required variables in `.env`:
  - [ ] `SECRET_KEY` (strong random string)
  - [ ] `ADMIN_USER` (default: `admin`)
  - [ ] `ADMIN_PASS` (strong password)
  - [ ] `TUNNEL_TOKEN` (from CloudFlare)
  - [ ] `SMTP_USER` (your Gmail)
  - [ ] `SMTP_PASSWORD` (16-char app password)
  - [ ] `ADMIN_EMAIL` (email to receive tunnel URL)

### 4. Docker Verification 🐳
- [ ] Docker installed: `docker --version`
- [ ] Docker Compose installed: `docker-compose --version`
- [ ] Docker daemon running: `docker ps`

### 5. Project Structure 📁
- [ ] Verify all files exist:
  ```
  ├── api/
  │   ├── main.py
  │   ├── Dockerfile
  │   ├── requirements.txt
  │   └── templates/
  │       └── index.html
  ├── scripts/
  │   ├── migrate_schema.py
  │   ├── notify-tunnel.sh
  │   ├── update_context.py
  │   └── validate-setup.py
  ├── docker-compose.yml
  ├── .env.example
  ├── .env (created)
  ├── README.md
  ├── SETUP_GUIDE.md
  └── context.md
  ```

### 6. Test Setup (Optional)
- [ ] Run validation script:
  ```bash
  python scripts/validate-setup.py
  ```
- [ ] Check for any missing dependencies or configurations

---

## Deployment Steps

### Step 1: Build
```bash
docker-compose build
```
- [ ] Build completes without errors
- [ ] FastAPI image created
- [ ] CloudFlare tunnel image pulled

### Step 2: Start Services
```bash
docker-compose up
```
- [ ] API service starts on port 3001
- [ ] CloudFlare tunnel initializes
- [ ] Tunnel notifier attempts to register URL
- [ ] Watch for log messages

### Step 3: Wait for Tunnel
```
Expected logs:
- "tunnel | ... Tunnel is running"
- "tunnel-notifier | Found tunnel URL: https://..."
- "tunnel-notifier | Notified API about tunnel URL"
```
- [ ] Wait 30-60 seconds for tunnel to stabilize
- [ ] Check tunnel notifier logs for URL

### Step 4: Check Email
- [ ] Check Gmail inbox for email from `SMTP_USER`
- [ ] Email subject: "🔗 Your AI API Gateway Tunnel URL"
- [ ] Email contains tunnel URL (e.g., `https://your-name.trycloudflare.com`)
- [ ] Verify URL is accessible in browser

### Step 5: Access Dashboard
#### Local (without tunnel):
- [ ] Open http://localhost:3001/
- [ ] Login with `ADMIN_USER` / `ADMIN_PASS`

#### Internet (with tunnel):
- [ ] Use URL from email
- [ ] Login with `ADMIN_USER` / `ADMIN_PASS`
- [ ] Dashboard loads successfully

### Step 6: Test API Key Creation
- [ ] Click "Create New Key" button
- [ ] Set expiration (e.g., 30 days)
- [ ] Click "Create New Key"
- [ ] API key is generated and displayed
- [ ] Copy key (note: shown only once)
- [ ] Key appears in "Existing Keys" table

### Step 7: Test API Endpoint
```bash
# Replace YOUR-API-KEY with the key you just created
curl -X POST http://localhost:3001/health \
  -H "x-api-key: YOUR-API-KEY"
```
- [ ] Endpoint returns `{"db": true, "ollama": false}` or similar
- [ ] Confirms API key authentication works

### Step 8: Verify Key Revocation
- [ ] Go back to dashboard
- [ ] Click "Revoke" on the test key
- [ ] Key status changes to "Revoked"
- [ ] Test API with revoked key: should return 401 error

---

## Post-Deployment

### Monitoring
- [ ] Check Docker logs regularly:
  ```bash
  docker-compose logs -f api
  ```
- [ ] Monitor for email send errors
- [ ] Ensure tunnel stays connected

### Maintenance
- [ ] Back up database regularly:
  ```bash
  cp data/keys.db data/keys.db.backup-$(date +%Y%m%d)
  ```
- [ ] Rotate API keys periodically
- [ ] Review and revoke unused keys
- [ ] Update admin password if compromised

### Security
- [ ] Never share `ADMIN_PASS` or `SECRET_KEY`
- [ ] Keep `SMTP_PASSWORD` secure
- [ ] Rotate CloudFlare tunnel token if exposed
- [ ] Monitor API key usage in logs

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Email not sent | Check `SMTP_USER` and `SMTP_PASSWORD` in `.env`. Ensure Gmail 2FA enabled. |
| Tunnel not connecting | Verify `TUNNEL_TOKEN` is correct. Check CloudFlare account status. |
| Can't access dashboard | Ensure services are running: `docker-compose ps`. Check port 3001 is available. |
| API key not working | Ensure key is copied exactly. Check it's not revoked. Verify `x-api-key` header is correct. |
| Database errors | Check `data/` directory exists and is writable. Delete `data/keys.db` to reset. |

---

## Success Criteria ✨

Your deployment is successful when:

1. ✅ CloudFlare tunnel is connected and stable
2. ✅ Email received with tunnel URL
3. ✅ Dashboard accessible via both local and internet URLs
4. ✅ Can create and revoke API keys
5. ✅ API endpoints work with valid keys
6. ✅ Invalid keys are rejected with 401 error
7. ✅ Database contains created keys
8. ✅ Docker services remain running and healthy

---

## Next Steps

Once deployed:

1. **Customize Endpoints**: Modify `api/main.py` to add custom endpoints
2. **Connect to Ollama**: Ensure `OLLAMA_URL` points to your Ollama instance
3. **Set Up Monitoring**: Add logging, metrics, and alerts
4. **Scale if Needed**: Adjust Docker Compose for load balancing
5. **Secure Credentials**: Rotate passwords and tokens regularly

---

## Support

- **Setup Issues**: See [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Development Context**: See [context.md](context.md)
- **API Documentation**: See [README.md](README.md)
