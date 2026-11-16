# Run Hassouna Green on your own server, on your own domain

No Streamlit Community Cloud. No Vercel. No hosting platform that runs
somebody else's application: the app runs in a container on a machine you
control, and Caddy gives it HTTPS on a domain you own.

```
visitor ──https://hassounagreen.com──▶ Caddy (your server) ──▶ app container
                                            │
                                        Let's Encrypt certificate
```

## How the deployment works

`deploy/entrypoint.sh` is what the container starts. It reads your domain from
`deploy/.env`, writes Streamlit's own configuration from it, and then starts
the app:

```toml
[server]
headless = true
address = "0.0.0.0"
port = 8501
enableCORS = false              # the proxy passes one origin only
enableXsrfProtection = true     # the upload routes stay protected
allowedHosts = ["your.domain", "www.your.domain", "localhost", "127.0.0.1"]
```

`allowedHosts` is what stops another site from reaching your app through a
forged host header. The same image therefore works for any domain: nothing
about the domain is baked into the image, it is only read at start-up.

The visitor's feedback and the cache of the AI replies are written to the
`app-data` volume, so they survive a rebuild.

## What you need

| | |
|---|---|
| **A domain** | about 10 EUR a year. Cloudflare Registrar sells `.com` at cost, Namecheap and Porkbun are similar. |
| **A server** | from about 4 EUR a month. A plain Linux VPS with 1 GB of RAM is enough. Hetzner (CX22, Helsinki/Falkenstein) and Contabo are the cheapest in Europe; DigitalOcean and OVH are easier to start with. |
| **DNS** | one A record pointing your domain at the server's IP address. |

You can also run this on a machine you already have at home, as long as you
can open ports 80 and 443 on your router and use a free dynamic DNS service.

## Step 1 - the domain

Buy the domain and point it at the server:

```
type     name     value
A        @        203.0.113.10     <- your server's IPv4 address
A        www      203.0.113.10
```

The address may take a few minutes to spread. Check it with
`nslookup yourdomain.com` until it returns your server.

## Step 2 - the server

Buy the smallest Linux VPS you can find and sign in over SSH:

```bash
ssh root@203.0.113.10
```

Install Docker (the official script for Debian/Ubuntu):

```bash
curl -fsSL https://get.docker.com | sh
```

Open the two ports in the firewall. On a Debian/Ubuntu server with ufw:

```bash
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw enable
```

## Step 3 - the app

Get the code onto the server and start it:

```bash
git clone https://github.com/Ahmed-Moustafa-ENG/Hassouna-Green.git
cd Hassouna-Green/deploy
cp .env.example .env
nano .env            # put your domain in DOMAIN=... and, if you have one, your OpenRouter key
./deploy.sh
```

That is the whole deployment. The script builds the image, starts the app and
the proxy, and waits until the app answers.

Open `https://yourdomain.com` in a browser. The first request takes a few
seconds while Caddy asks Let's Encrypt for the certificate; after that the
certificate renews itself.

## Step 4 - keep it updated

```bash
cd Hassouna-Green
git pull
cd deploy && docker compose up -d --build
```

## Step 5 - see what is happening

```bash
cd Hassouna-Green/deploy
docker compose logs -f app          # the application log
docker compose logs -f caddy        # the web server log, with the access lines
docker compose ps                   # is it running and is it healthy?
docker compose restart app          # restart the app
docker compose down                 # stop everything
```

The feedback that visitors leave and the cache of the AI replies are kept in a
Docker volume, so they survive a rebuild. Back them up with:

```bash
docker run --rm -v hassouna-green_app-data:/data -v "$PWD":/backup alpine \
    tar czf /backup/app-data.tar.gz -C /data .
```

## Without Docker

If you would rather not run containers, the same `deploy/entrypoint.sh` works
with a plain virtual environment. It writes the configuration and starts the
app:

```bash
sudo apt install python3-venv
git clone https://github.com/Ahmed-Moustafa-ENG/Hassouna-Green.git
cd Hassouna-Green
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
DOMAIN=your.domain .venv/bin/python deploy/entrypoint.sh
```

Run it under systemd so it starts with the machine
(`/etc/systemd/system/hassouna.service`):

```ini
[Unit]
Description=Hassouna Green
After=network.target

[Service]
User=www-data
WorkingDirectory=/srv/Hassouna-Green
Environment=DOMAIN=your.domain
Environment=HASSOUNA_FEEDBACK_FILE=/var/lib/hassouna/feedback.json
ExecStart=/srv/Hassouna-Green/.venv/bin/python /srv/Hassouna-Green/deploy/entrypoint.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now hassouna
```

Then put Caddy in front of it as a normal system service with the same
`Caddyfile` (pointing at `127.0.0.1:8501` instead of `app:8501`).

## What this setup does not do

- It does not give you a free static copy of the app; the server costs a few
  euro a month and the domain about ten euro a year.
- It does not scale on its own. One container on one small server is fine for
  a competition, a school project or a small group of visitors.
- GitHub is still where the code lives, so the project stays visible and
  versioned. Only the running copy sits on your own server.
