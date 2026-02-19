# Market Tick System

Real-time cryptocurrency tick collector using Django, Celery, Redis, MySQL and Binance WebSocket.

## Stack

| Service | Role |
|---------|------|
| Django | Web app + Admin UI |
| Celery | Async task worker |
| Redis | Celery broker |
| MySQL 8 | Persistent storage |
| Tick Producer | Binance WebSocket listener |

---

## 1. Bring Up the Stack

```bash
docker compose up -d
```

This starts MySQL, Redis, Django (with auto-migrations), and Celery worker.
The **superuser is created automatically** — no manual step needed.

---

## 2. Django Admin Login

URL: **http://localhost:8000/admin**

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `changeme123` |

---

## 3. Add Broker + Scripts

**Create Broker:**
- Go to **Brokers → Add Broker**
- Type: `BINANCE` | Name: `Binance Live` | Api config: `{}`
- Save

**Create Scripts (under that Broker):**
- Go to **Scripts → Add Script**, add all three:

| Name | Trading Symbol |
|------|---------------|
| Bitcoin | BTCUSDT |
| Ethereum | ETHUSDT |
| Pepe | PEPEUSDT |

---

## 4. Run the Tick Producer

The producer is started manually after broker + scripts are configured:

```bash
docker compose --profile producer up tick_producer
```

Or run it directly via the web container:

```bash
docker compose exec web python manage.py run_tick_producer --broker_id=1
```

---

## 5. Verify Ticks in the DB

**Via Django Admin:**
Go to **Ticks** in the admin — records appear within seconds.

**Via MySQL:**

```bash
docker compose exec mysql mysql -u root -prootpassword123 market_ticks_db -e "
SELECT s.trading_symbol, COUNT(t.id) as ticks
FROM scripts s
LEFT JOIN ticks t ON s.id = t.script_id
GROUP BY s.trading_symbol;
"
```

---

## Common Commands

```bash
# View logs
docker compose logs -f
docker compose logs -f tick_producer

# Check service status
docker compose ps

# Stop everything
docker compose down

# Stop and wipe database
docker compose down -v

# Rebuild from scratch
docker compose down -v && docker compose build --no-cache && docker compose up -d
```

---

## Project Structure

```
├── docker-compose.yml
├── Dockerfile                      # web + celery image
├── Dockerfile.producer             # tick producer image
├── .env                            # environment variables
├── market_tick_system/
│   ├── settings.py
│   └── celery.py
├── tick_consumer/
│   ├── models.py                   # Broker, Script, Ticks
│   ├── tasks.py                    # get_broker, consume_tick
│   └── admin.py
└── tick_producer/
    ├── websocket_client.py         # Binance WebSocket handler
    └── management/commands/
        └── run_tick_producer.py    # management command
```
