# Django + Celery + Docker Market Tick System

A real-time cryptocurrency price collection system that connects to Binance WebSocket API, processes tick data asynchronously using Celery, and stores everything in MySQL.

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  Binance WS API │────▶│ Tick Producer│────▶│   Celery    │
│  (Live Ticks)   │     │  (WebSocket) │     │   Worker    │
└─────────────────┘     └──────────────┘     └──────┬──────┘
                                                     │
                                                     ▼
                        ┌──────────────┐     ┌──────────────┐
                        │ Django Admin │◀────│    MySQL     │
                        │      UI      │     │   Database   │
                        └──────────────┘     └──────────────┘
```

**Components:**
- **Django Web App** - Admin interface for managing brokers and scripts
- **Celery Worker** - Processes async tick consumption tasks
- **Redis** - Message broker for Celery
- **MySQL 8** - Persistent data storage
- **Tick Producer** - WebSocket listener that receives live market data

## 📋 Prerequisites

- Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop))
- Docker Compose installed (included with Docker Desktop)
- Git (optional, for version control)

**No Python, Django, or MySQL installation required!** Everything runs in containers.

## 🚀 Quick Start (5 Minutes)

### Step 1: Start All Services

```bash
# Make sure Docker is running
docker-compose up -d
```

This single command will:
- Start MySQL database
- Start Redis
- Build and start Django web app
- Run database migrations
- Start Celery worker
- Start tick producer (will wait for broker configuration)

### Step 2: Create Admin Superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

Follow the prompts:
- Username: `admin`
- Email: `admin@example.com`
- Password: `changeme123` (or choose your own)

### Step 3: Access Django Admin

Open your browser and navigate to:
```
http://localhost:8000/admin
```

Login with the credentials you just created.

### Step 4: Configure Broker and Scripts

#### Create Broker:
1. Click on **"Brokers"** → **"Add Broker"**
2. Fill in the form:
   - **Type**: Select "Binance"
   - **Name**: "Binance Live"
   - **Api config**: `{}` (empty JSON object)
3. Click **"Save"**

#### Add Scripts (Trading Symbols):
1. Click on **"Scripts"** → **"Add Script"**
2. Add Bitcoin:
   - **Broker**: Select "Binance Live"
   - **Name**: "Bitcoin"
   - **Trading symbol**: "BTCUSDT"
   - **Additional data**: `{}` (empty JSON object)
3. Click **"Save and add another"**
4. Add Ethereum:
   - **Broker**: "Binance Live"
   - **Name**: "Ethereum"
   - **Trading symbol**: "ETHUSDT"
   - **Additional data**: `{}`
5. Click **"Save and add another"**
6. Add Pepe:
   - **Broker**: "Binance Live"
   - **Name**: "Pepe"
   - **Trading symbol**: "PEPEUSDT"
   - **Additional data**: `{}`
7. Click **"Save"**

### Step 5: Restart Tick Producer

The tick producer needs to be restarted after adding broker and scripts:

```bash
docker-compose restart tick_producer
```

### Step 6: Verify Ticks Are Being Collected

Wait 30 seconds, then check the logs:

```bash
# View tick producer logs
docker-compose logs -f tick_producer

# You should see messages like:
# "WebSocket connected - Subscribed to 3 symbols: BTCUSDT, ETHUSDT, PEPEUSDT"
# "Forwarded tick: BTCUSDT @ 95234.56"
```

View ticks in the admin UI:
1. Go to http://localhost:8000/admin
2. Click on **"Tickss"** (yes, plural with double 's')
3. You should see tick records appearing!

## 📊 Verification

### Check Running Services

```bash
docker-compose ps
```

All services should show "Up" status:
```
NAME                     STATUS
market_ticks_celery      Up
market_ticks_mysql       Up (healthy)
market_ticks_producer    Up
market_ticks_redis       Up (healthy)
market_ticks_web         Up
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f tick_producer
docker-compose logs -f celery_worker
docker-compose logs -f web
```

### Query Database Directly

```bash
# Access MySQL
docker-compose exec mysql mysql -u root -prootpassword market_ticks_db

# Run SQL query
mysql> SELECT COUNT(*) FROM ticks;
mysql> SELECT * FROM ticks ORDER BY received_at_producer DESC LIMIT 10;
mysql> exit;
```

Expected output after 1 minute: 30-60 ticks (about 1 tick per second per symbol)

### Check Tick Count by Symbol

```bash
docker-compose exec mysql mysql -u root -prootpassword market_ticks_db -e "
SELECT
    s.trading_symbol,
    COUNT(t.id) as tick_count,
    MAX(t.received_at_producer) as last_tick
FROM scripts s
LEFT JOIN ticks t ON s.id = t.script_id
GROUP BY s.id, s.trading_symbol;
"
```

## 🛠️ Manual Operations

### Run Tick Producer with Different Broker ID

```bash
docker-compose run --rm tick_producer python manage.py run_tick_producer --broker_id=1
```

### Run Celery Task Manually

```bash
docker-compose exec web python manage.py shell

>>> from tick_consumer.tasks import get_broker
>>> result = get_broker(1)
>>> print(result)
```

### Run Database Migrations

```bash
docker-compose exec web python manage.py migrate
```

### Create New Migrations After Model Changes

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### Access Django Shell

```bash
docker-compose exec web python manage.py shell
```

### Run Tests

```bash
docker-compose exec web python manage.py test
```

## 🔧 Configuration

### Environment Variables

All configuration is in `.env` file. Key variables:

```bash
# Django
SECRET_KEY=<auto-generated>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,web

# Database
DB_NAME=market_ticks_db
DB_USER=root
DB_PASSWORD=rootpassword
DB_HOST=mysql
DB_PORT=3306

# Redis & Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Binance WebSocket
BINANCE_WS_URL=wss://stream.binance.com:9443/ws

# Tick Producer
BROKER_ID=1  # Default broker ID for tick_producer service
```

To change database password:
1. Edit `.env` file: `DB_PASSWORD=new_password`
2. Rebuild containers: `docker-compose down && docker-compose up -d --build`

### Scaling Celery Workers

Edit `docker-compose.yml` to add more workers:

```yaml
celery_worker:
  # ... existing config
  deploy:
    replicas: 3  # Run 3 workers
```

Or run manually:
```bash
docker-compose up -d --scale celery_worker=3
```

## 🐛 Troubleshooting

### Issue: "mysql: Connection refused"

**Cause**: MySQL not ready when Django starts

**Solution**: Wait for health check to pass
```bash
docker-compose down
docker-compose up -d
# Wait 30 seconds for MySQL to be healthy
docker-compose logs mysql | grep "ready for connections"
```

### Issue: "Broker with ID X not found"

**Cause**: Tick producer started before broker was created in admin

**Solution**: Restart tick producer
```bash
docker-compose restart tick_producer
```

### Issue: No ticks appearing in database

**Diagnosis**:
```bash
# Check if WebSocket is connected
docker-compose logs tick_producer | grep "WebSocket connected"

# Check if ticks are being forwarded
docker-compose logs tick_producer | grep "Forwarded tick"

# Check Celery worker
docker-compose logs celery_worker | grep "consume_tick"
```

**Common causes**:
- Broker or scripts not created in admin
- Wrong trading symbols (must be valid Binance symbols)
- Network issues (firewall blocking WebSocket)

### Issue: "Too many connections" to MySQL

**Solution**: Increase connection limit in `docker-compose.yml`:
```yaml
mysql:
  command: --max_connections=200
```

### Issue: Celery tasks piling up

**Diagnosis**:
```bash
docker-compose exec redis redis-cli LLEN celery

# If > 10000, you have a backlog
```

**Solution**: Scale workers or check for task errors
```bash
docker-compose logs celery_worker | grep ERROR
```

## 📈 Performance

### Expected Throughput

- **Tick ingestion**: 100-500 ticks/second (depends on market activity)
- **Celery processing**: 1000+ ticks/second with bulk_create
- **Database writes**: Batched in groups of 1000 for efficiency

### Monitoring Tick Rate

```bash
# Count ticks in last minute
docker-compose exec mysql mysql -u root -prootpassword market_ticks_db -e "
SELECT COUNT(*) as ticks_last_minute
FROM ticks
WHERE received_at_producer > DATE_SUB(NOW(), INTERVAL 1 MINUTE);
"
```

### Database Size

Each tick is approximately 100 bytes. For 3 symbols receiving 1 tick/second:
- **Per hour**: ~1 MB
- **Per day**: ~25 MB
- **Per month**: ~750 MB

## 🔐 Security Notes

### For Development

- Default passwords are in `.env` (not secure!)
- DEBUG mode is enabled
- Admin interface is publicly accessible

### For Production

1. **Change all passwords** in `.env`:
   ```bash
   SECRET_KEY=<generate-new-50-char-secret>
   DB_PASSWORD=<strong-password>
   DJANGO_SUPERUSER_PASSWORD=<strong-password>
   ```

2. **Disable DEBUG**:
   ```bash
   DEBUG=False
   ALLOWED_HOSTS=yourdomain.com
   ```

3. **Use HTTPS** (configure reverse proxy like Nginx)

4. **Restrict database access** (don't expose port 3306 publicly)

5. **Use environment-specific configs** (separate .env for prod)

## 📁 Project Structure

```
assignment/
├── docker-compose.yml          # Service orchestration
├── Dockerfile                  # Django app container
├── Dockerfile.producer         # Tick producer container
├── wait-for-it.sh             # Service readiness script
├── .env                       # Environment variables
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
├── manage.py                  # Django management script
├── market_tick_system/        # Django project
│   ├── settings.py           # Main configuration
│   ├── celery.py             # Celery setup
│   ├── urls.py               # URL routing
│   └── ...
├── tick_consumer/             # Consumer app
│   ├── models.py             # Database models
│   ├── tasks.py              # Celery tasks
│   └── admin.py              # Admin customization
└── tick_producer/             # Producer app
    ├── websocket_client.py   # Binance WebSocket handler
    └── management/commands/
        └── run_tick_producer.py  # Producer command
```

## 🧪 Testing

Run all tests:
```bash
docker-compose exec web python manage.py test
```

Run specific app tests:
```bash
docker-compose exec web python manage.py test tick_consumer
docker-compose exec web python manage.py test tick_producer
```

## 🛑 Stopping and Cleaning Up

### Stop all services
```bash
docker-compose down
```

### Stop and remove all data (including database)
```bash
docker-compose down -v
```

### Rebuild from scratch
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/en/5.0/)
- [Celery Documentation](https://docs.celeryq.dev/en/stable/)
- [Binance WebSocket Streams](https://binance-docs.github.io/apidocs/spot/en/#websocket-market-streams)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)

## 🤝 Support

For issues or questions:
1. Check the **Troubleshooting** section above
2. Review logs: `docker-compose logs <service_name>`
3. Verify all services are running: `docker-compose ps`

## 📝 License

This is a candidate assignment project for educational purposes.

---

**Built with ❤️ using Django, Celery, Docker, and Binance API**
