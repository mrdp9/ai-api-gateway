# cloudflared (Cloudflare Tunnel) setup

This folder contains a template/config guidance for running Cloudflare Tunnel with the `cloudflared` Docker image used in `docker-compose.yml`.

Two ways to provide credentials to the container:

1. **Token (recommended for automation)**
   - Create a tunnel in Cloudflare via `cloudflared` locally and retrieve a tunnel token.
   - Set `CLOUDFLARE_TUNNEL_TOKEN=<token>` in `.env` or environment. The compose `tunnel` service will use it.

2. **Credentials file**
   - Run `cloudflared tunnel login` on your machine and copy the `cert.pem` into this folder.
   - Mount this folder (already done by compose) and the container will use it.

Quick start (token-based):

```bash
# put token in .env (or export it in the shell)
export CLOUDFLARE_TUNNEL_TOKEN=eyJhbGciOiJI...
# from project root
docker-compose up --build
```

After started the tunnel will route a public HTTPS URL to `http://api:8000` inside the compose network. Follow Cloudflare docs for managing tunnels and DNS.
