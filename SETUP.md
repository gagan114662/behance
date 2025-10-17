# Behance Scraper - Setup & Run Guide

## 📋 Overview

A high-performance, TDD-built Behance web scraper with anti-detection, account rotation, and MongoDB storage.

- **Test Coverage**: 95%
- **Tests Passing**: 358/358 (100%)
- **Architecture**: Async Python with Playwright

---

## 🚀 Quick Start

### Prerequisites Check

Your system already has:
- ✅ MongoDB running on `localhost:27017`
- ✅ Redis installed at `/usr/local/bin/redis-server`
- ✅ MongoDB Compass at `/Applications/MongoDB Compass.app`
- ✅ Python virtual environment at `./venv`

### 1. Start Required Services

```bash
# Navigate to project directory
cd /Users/gaganarora/Desktop/gagan_projects/behance

# Option A: Use Docker (Recommended)
docker-compose up -d

# Option B: Use existing MongoDB + start Redis locally
redis-server --daemonize yes

# Verify services are running
docker-compose ps  # If using Docker
# OR
ps aux | grep -E "mongod|redis"
```

### 2. Activate Virtual Environment

```bash
# Activate the existing venv
source venv/bin/activate
```

### 3. Install Playwright Browsers (If not already installed)

```bash
# Install Playwright browser binaries
playwright install chromium
```

### 4. Run the Example Scraper

```bash
# Run the example scraper
python example_scraper.py
```

---

## 📊 Run Tests

```bash
# Activate venv
source venv/bin/activate

# Run all tests
pytest tests/unit/ -v

# Run with coverage report
pytest tests/unit/ --cov=src --cov-report=html

# Open coverage report in browser
open htmlcov/index.html

# Run specific test file
pytest tests/unit/test_auth.py -v

# Run only unit tests (fast)
pytest tests/unit/ -m unit -v

# Run integration tests (requires browser)
pytest tests/unit/ -m integration -v
```

---

## 🛠️ Project Structure

```
behance/
├── src/                          # Source code
│   ├── auth/                     # Authentication & account management
│   │   ├── authenticator.py     # Behance login automation
│   │   ├── account_pool.py      # Account rotation strategies
│   │   └── session_manager.py   # Session persistence
│   ├── browser/                  # Browser automation
│   │   ├── manager.py            # Playwright browser manager
│   │   ├── behavior.py           # Human behavior simulation
│   │   └── stealth.py            # Anti-detection stealth
│   ├── captcha/                  # Captcha handling
│   │   ├── detector.py           # Captcha detection
│   │   ├── solver.py             # Captcha solving (2Captcha integration)
│   │   └── handler.py            # Strategy-based handling
│   ├── crawler/                  # Crawling logic
│   │   ├── orchestrator.py       # Main crawler orchestration
│   │   ├── rate_limiter.py       # Request rate limiting
│   │   └── strategies.py         # Crawl strategies (BFS, DFS)
│   ├── evasion/                  # Anti-detection
│   │   ├── fingerprint.py        # Browser fingerprint randomization
│   │   ├── webrtc.py             # WebRTC leak prevention
│   │   ├── timezone.py           # Timezone/locale spoofing
│   │   └── headers.py            # HTTP header normalization
│   ├── extractors/               # Data extraction
│   │   ├── project.py            # Project data extraction
│   │   ├── user.py               # User profile extraction
│   │   └── image.py              # Image download & metadata
│   ├── models/                   # Pydantic data models
│   │   ├── project.py            # Project model
│   │   ├── user.py               # User model
│   │   ├── image.py              # Image model
│   │   └── account.py            # Account credentials
│   ├── network/                  # Network handling
│   │   ├── interceptor.py        # Request/response interception
│   │   ├── csrf.py               # CSRF token extraction
│   │   └── cookie_manager.py    # Cookie management
│   ├── proxies/                  # Proxy management
│   │   ├── pool.py               # Proxy rotation
│   │   ├── provider.py           # Proxy providers
│   │   └── health.py             # Proxy health checks
│   ├── queue/                    # Task queue
│   │   ├── task_queue.py         # Redis-based task queue
│   │   ├── priority_queue.py    # Priority queue
│   │   └── scheduler.py          # Job scheduling
│   ├── storage/                  # Data persistence
│   │   ├── mongo_client.py       # MongoDB client wrapper
│   │   ├── project_repository.py # Project CRUD
│   │   ├── user_repository.py    # User CRUD
│   │   └── image_repository.py   # Image CRUD
│   └── monitoring/               # Observability
│       ├── logger.py             # Logging configuration
│       ├── metrics.py            # Prometheus metrics
│       └── health.py             # Health checks
├── tests/                        # Test suite (358 tests)
│   ├── unit/                     # Unit tests
│   └── conftest.py               # Pytest fixtures
├── example_scraper.py            # Example usage script
├── docker-compose.yml            # Infrastructure setup
└── pytest.ini                    # Test configuration
```

---

## 🔧 Configuration

### MongoDB Configuration

MongoDB is already running at:
- **Host**: `localhost:27017`
- **Database**: `behance_crawler`
- **Data Path**: `/Users/gaganarora/Desktop/gagan_projects/Database_migration/mongodb_data`

View data using MongoDB Compass (already installed).

### Environment Variables

Create a `.env` file for sensitive data:

```bash
# .env (optional)
BEHANCE_EMAIL=your_email@example.com
BEHANCE_PASSWORD=your_password
TWOCAPTCHA_API_KEY=your_2captcha_key
PROXY_API_KEY=your_proxy_key
```

---

## 🎯 Usage Examples

### Basic Scraping (No Authentication)

```python
import asyncio
from src.browser.manager import BrowserManager, BrowserConfig
from src.extractors.user import UserExtractor

async def scrape_user():
    browser_config = BrowserConfig(headless=True, stealth_mode=True)
    manager = BrowserManager(browser_config)

    await manager.launch()
    context = await manager.create_context()
    page = await context.new_page()

    await page.goto("https://www.behance.net/adobe")

    extractor = UserExtractor()
    user = await extractor.extract_from_page(page)

    print(f"User: {user.display_name}")
    print(f"Followers: {user.stats.followers}")

    await manager.close()

asyncio.run(scrape_user())
```

### Authenticated Scraping with Account Rotation

```python
import asyncio
from src.auth.account_pool import AccountPool, AccountRotationStrategy
from src.auth.authenticator import BehanceAuthenticator
from src.models.account import AccountCredentials

async def authenticated_scrape():
    accounts = [
        AccountCredentials(email="email1@example.com", password="pass1"),
        AccountCredentials(email="email2@example.com", password="pass2"),
    ]

    pool = AccountPool(accounts, strategy=AccountRotationStrategy.LEAST_USED)
    authenticator = BehanceAuthenticator()

    # ... browser setup ...

    account = await pool.get_next()
    result = await authenticator.login(page, account)

    if result.success:
        print("Logged in successfully!")
        await pool.mark_used(account.email)

asyncio.run(authenticated_scrape())
```

### Full Pipeline with Storage

```python
import asyncio
from src.storage.mongo_client import MongoClient, MongoConfig
from src.storage.project_repository import ProjectRepository

async def scrape_and_store():
    # Setup MongoDB
    mongo = MongoClient(MongoConfig(
        url="mongodb://localhost:27017",
        database="behance_crawler"
    ))
    await mongo.connect()

    project_repo = ProjectRepository(mongo)

    # ... scrape project ...

    await project_repo.save(project)
    print(f"Saved project {project.id} to MongoDB!")

    await mongo.disconnect()

asyncio.run(scrape_and_store())
```

---

## 🐛 Troubleshooting

### MongoDB Connection Issues

```bash
# Check if MongoDB is running
ps aux | grep mongod

# If not running, start with Docker
docker-compose up -d mongodb

# Or start existing MongoDB
/Users/gaganarora/Downloads/mongodb-macos-aarch64--8.2.1/bin/mongod \
  --dbpath /Users/gaganarora/Desktop/gagan_projects/Database_migration/mongodb_data \
  --port 27017
```

### Redis Connection Issues

```bash
# Check if Redis is running
ps aux | grep redis

# Start Redis
redis-server --daemonize yes

# Test connection
redis-cli ping
# Should return: PONG
```

### Playwright Browser Issues

```bash
# Reinstall browsers
playwright install chromium --force

# Check installed browsers
playwright install --help
```

### Test Failures

```bash
# Make sure services are running
docker-compose ps

# Clean test cache
pytest --cache-clear

# Run with verbose output
pytest tests/unit/ -vv
```

---

## 📈 Monitoring

### View MongoDB Data

```bash
# Open MongoDB Compass
open '/Applications/MongoDB Compass.app'

# Connect to: mongodb://localhost:27017
# Database: behance_crawler
```

### Check Prometheus Metrics (Optional)

```bash
# Start Prometheus via Docker
docker-compose up -d prometheus

# Access dashboard
open http://localhost:9090
```

### View Logs

```bash
# Logs are printed to stdout
# For production, configure logging in src/monitoring/logger.py
```

---

## 🔒 Security & Ethics

⚠️ **Important Notes:**

1. **Rate Limiting**: Use `RateLimiter` to avoid overwhelming Behance servers
2. **Account Safety**: Rotate accounts and use delays to avoid bans
3. **Captcha Handling**: Respect captcha challenges, don't abuse solvers
4. **Terms of Service**: Review Behance's ToS before scraping
5. **Personal Data**: Handle user data responsibly per GDPR/CCPA

---

## 🚦 Next Steps

1. **Customize `example_scraper.py`** with your target URLs
2. **Add your Behance credentials** for authenticated scraping
3. **Configure proxies** in `src/proxies/` for production
4. **Set up 2Captcha** API key in `.env` file
5. **Run tests** to ensure everything works
6. **Start scraping!**

---

## 📞 Support

- **Tests failing?** Run `pytest tests/unit/ -v` for details
- **Coverage report**: `pytest --cov=src --cov-report=html`
- **Current coverage**: 95% (358/358 tests passing)

Built with ❤️ using Test-Driven Development (TDD)
