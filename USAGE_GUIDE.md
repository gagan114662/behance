# Behance Crawler - Comprehensive Usage Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Core Components](#core-components)
3. [Advanced Usage](#advanced-usage)
4. [Best Practices](#best-practices)
5. [Troubleshooting](#troubleshooting)
6. [API Reference](#api-reference)

---

## Quick Start

### Basic Crawl Example

```python
import asyncio
from src.crawler.orchestrator import CrawlerOrchestrator, CrawlerConfig
from src.browser.manager import BrowserManager, BrowserConfig
from src.proxies.pool import ProxyPool, ProxyRotationStrategy
from src.models.proxy import ProxyConfig

async def main():
    # Configure crawler
    crawler_config = CrawlerConfig(
        max_concurrent_sessions=3,
        requests_per_minute=10,
        session_warmup_duration=300,
        max_retries=3,
    )

    # Configure browser
    browser_config = BrowserConfig(
        headless=True,
        stealth_mode=True,
        viewport_width=1920,
        viewport_height=1080,
    )

    # Initialize components
    orchestrator = CrawlerOrchestrator(crawler_config)
    browser_manager = BrowserManager(browser_config)

    # Launch browser
    await browser_manager.launch()

    # Create context and start crawling
    context = await browser_manager.create_context()
    page = await context.new_page()

    # Navigate to Behance
    await page.goto("https://www.behance.net")

    # Cleanup
    await page.close()
    await context.close()
    await browser_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Core Components

### 1. Browser Automation

#### Basic Browser Setup

```python
from src.browser.manager import BrowserManager, BrowserConfig

# Configure browser
config = BrowserConfig(
    headless=True,          # Run without UI
    stealth_mode=True,      # Enable anti-detection
    viewport_width=1920,
    viewport_height=1080,
)

manager = BrowserManager(config)
await manager.launch()

# Create context
context = await manager.create_context()
page = await context.new_page()
```

#### With Fingerprint Randomization

```python
from src.evasion.fingerprint import FingerprintRandomizer

randomizer = FingerprintRandomizer()
profile = randomizer.generate_profile()

# Apply to page
await randomizer.apply_to_page(page, profile)
```

#### With Session Restoration

```python
from src.models.session import BrowserSession

# Load existing session
session = BrowserSession(
    session_id="abc123",
    cookies=[...],
    user_agent="Mozilla/5.0...",
)

# Create context with session
context = await manager.create_context(session=session)
```

### 2. Proxy Management

#### Setting Up Proxy Pool

```python
from src.proxies.pool import ProxyPool, ProxyRotationStrategy
from src.models.proxy import ProxyConfig

# Define proxies
proxies = [
    ProxyConfig(
        host="proxy1.example.com",
        port=8080,
        username="user",
        password="pass",
        protocol="http",
        country="US",
    ),
    ProxyConfig(
        host="proxy2.example.com",
        port=8080,
        username="user",
        password="pass",
        protocol="http",
        country="UK",
    ),
]

# Create pool
pool = ProxyPool(
    proxies=proxies,
    strategy=ProxyRotationStrategy.WEIGHTED  # or ROUND_ROBIN, RANDOM
)

# Get next proxy
proxy = await pool.get_next()

# Create context with proxy
context = await manager.create_context(proxy=proxy)
```

#### Health Checking

```python
from src.proxies.health import ProxyHealthChecker

checker = ProxyHealthChecker(
    check_url="https://httpbin.org/ip",
    timeout_seconds=10,
)

# Check single proxy
health = await checker.check_health(proxy)

if health.status == ProxyStatus.HEALTHY:
    print(f"Proxy OK: {health.response_time_ms}ms")
else:
    print(f"Proxy failed: {health.error_message}")

# Check all proxies
results = await checker.check_multiple(pool.proxies)
```

### 3. Authentication

#### Account Pool Setup

```python
from src.auth.account_pool import AccountPool, AccountRotationStrategy
from src.models.account import AccountCredentials

# Define accounts
accounts = [
    AccountCredentials(
        email="user1@example.com",
        password="password1",
    ),
    AccountCredentials(
        email="user2@example.com",
        password="password2",
    ),
]

# Create pool
account_pool = AccountPool(
    accounts=accounts,
    strategy=AccountRotationStrategy.LEAST_USED
)

# Get account
account = await account_pool.get_next()
```

#### Logging In

```python
from src.auth.authenticator import BehanceAuthenticator

authenticator = BehanceAuthenticator()

# Login
result = await authenticator.login(page, account)

if result.success:
    print("Login successful!")
    # Save session for later
    session_cookies = result.session_cookies
else:
    print(f"Login failed: {result.error_message}")
```

### 4. Data Extraction

#### Extract Project Data

```python
from src.extractors.project import ProjectExtractor

extractor = ProjectExtractor()

# From HTML page
project = await extractor.extract_from_page(page)

# Or from API JSON
project = await extractor.extract_from_json(api_response)

print(f"Project: {project.title}")
print(f"Owner: {project.owner_username}")
print(f"Views: {project.stats.views}")
```

#### Extract User Data

```python
from src.extractors.user import UserExtractor

extractor = UserExtractor()

# From page
user = await extractor.extract_from_page(page)

print(f"User: {user.username}")
print(f"Followers: {user.stats.followers}")
```

#### Extract and Download Images

```python
from src.extractors.image import ImageExtractor
from src.storage.image_pipeline import ImagePipeline

image_extractor = ImageExtractor()
pipeline = ImagePipeline(output_dir="./downloads")

# Extract images from project
images = await image_extractor.extract_from_project(project_data)

# Download images
urls = [img.url for img in images]
results = await pipeline.download_many(urls)

for result in results:
    if result.success:
        print(f"Downloaded: {result.local_path}")
```

### 5. Storage

#### MongoDB Storage

```python
from src.storage.mongo_client import MongoClient, MongoConfig
from src.storage.project_repository import ProjectRepository

# Connect to MongoDB
config = MongoConfig(
    url="mongodb://localhost:27017",
    database="behance_crawler"
)

client = MongoClient(config)
await client.connect()

# Create repository
repo = ProjectRepository(client)

# Save project
await repo.save(project)

# Find project
found = await repo.find_by_id(project.id)

# Find all projects by owner
user_projects = await repo.find_by_owner(owner_id)

# Update project
project.stats.views += 100
await repo.update(project)

# Upsert (insert or update)
await repo.upsert(project)
```

### 6. Task Queue

#### Redis Task Queue

```python
from src.queue.task_queue import TaskQueue
from src.queue.priority_queue import PriorityQueue
from src.models.queue import CrawlTask, TaskPriority, TaskStatus
import redis.asyncio as aioredis

# Connect to Redis
redis_client = await aioredis.from_url("redis://localhost:6379")

# Create queue
queue = TaskQueue(redis_client)

# Enqueue task
task = CrawlTask(
    url="https://www.behance.net/gallery/123456/project",
    task_type="project",
    priority=TaskPriority.NORMAL,
    status=TaskStatus.PENDING,
    created_at=datetime.now(timezone.utc),
)

await queue.enqueue(task)

# Dequeue task
next_task = await queue.dequeue()

# Process task...
next_task.mark_in_progress()

# Mark complete
next_task.mark_completed()
```

#### Priority Queue

```python
priority_queue = PriorityQueue(redis_client)

# High priority task
urgent_task = CrawlTask(
    url="https://www.behance.net/urgent",
    task_type="project",
    priority=TaskPriority.HIGH,  # Will be processed first
    status=TaskStatus.PENDING,
    created_at=datetime.now(timezone.utc),
)

await priority_queue.enqueue(urgent_task)

# Dequeue always returns highest priority
next_task = await priority_queue.dequeue()
```

---

## Advanced Usage

### Complete Crawler Workflow

```python
import asyncio
from datetime import datetime, timezone

async def crawl_behance():
    # 1. Initialize all components
    browser_manager = BrowserManager(BrowserConfig(headless=True, stealth_mode=True))
    proxy_pool = ProxyPool(proxies=[...], strategy=ProxyRotationStrategy.WEIGHTED)
    account_pool = AccountPool(accounts=[...])
    task_queue = TaskQueue(redis_client)
    project_repo = ProjectRepository(mongo_client)

    # 2. Start crawler
    await browser_manager.launch()

    # 3. Process tasks
    while True:
        # Get task from queue
        task = await task_queue.dequeue()
        if not task:
            break

        # Get proxy and account
        proxy = await proxy_pool.get_next()
        account = await account_pool.get_next()

        # Create context
        context = await browser_manager.create_context(proxy=proxy)
        page = await context.new_page()

        # Apply anti-detection
        randomizer = FingerprintRandomizer()
        profile = randomizer.generate_profile()
        await randomizer.apply_to_page(page, profile)

        # Warm session
        warmer = SessionWarmer(warmup_duration=300)
        await warmer.warm_session(page)

        # Authenticate
        authenticator = BehanceAuthenticator()
        auth_result = await authenticator.login(page, account)

        if not auth_result.success:
            print(f"Auth failed: {auth_result.error_message}")
            continue

        # Navigate to target
        await page.goto(task.url)

        # Extract data
        extractor = ProjectExtractor()
        project = await extractor.extract_from_page(page)

        # Save to database
        await project_repo.save(project)

        # Mark task complete
        task.mark_completed()

        # Cleanup
        await page.close()
        await context.close()

    # 4. Cleanup
    await browser_manager.close()

asyncio.run(crawl_behance())
```

### Network Interception

```python
from src.network.interceptor import NetworkInterceptor
from src.network.api_discovery import APIDiscovery

# Enable interception
interceptor = NetworkInterceptor()
await interceptor.enable(page)

# Navigate
await page.goto("https://www.behance.net")

# Discover APIs
discovery = APIDiscovery()
await discovery.analyze_requests(interceptor.requests)

# Find GraphQL endpoints
graphql_endpoints = [e for e in discovery.endpoints if e.endpoint_type == EndpointType.GRAPHQL]

print(f"Found {len(graphql_endpoints)} GraphQL endpoints")
```

### Captcha Handling

```python
from src.captcha.detector import CaptchaDetector
from src.captcha.solver import CaptchaSolver, SolverProvider
from src.captcha.handler import CaptchaHandler, CaptchaStrategy

# Setup
detector = CaptchaDetector()
solver = CaptchaSolver(
    provider=SolverProvider.TWO_CAPTCHA,
    api_key="your_api_key",
)
handler = CaptchaHandler(
    detector=detector,
    solver=solver,
    strategy=CaptchaStrategy.AUTO_SOLVE,
)

# Handle captcha
result = await handler.handle(page)

if result.success:
    print("Captcha solved!")
else:
    print(f"Captcha failed: {result.error_message}")
```

---

## Best Practices

### 1. Session Management

- **Warm up sessions** before crawling important data
- **Rotate accounts** to avoid bans
- **Save session cookies** for reuse
- **Monitor ban indicators** (403, 429 errors)

### 2. Rate Limiting

```python
from src.crawler.rate_limiter import RateLimiter

limiter = RateLimiter(requests_per_minute=10)

# Before each request
await limiter.wait_if_needed()
await page.goto(url)
```

### 3. Error Handling

```python
from src.models.queue import CrawlTask

task = CrawlTask(...)

try:
    # Process task
    result = await process(task)
    task.mark_completed()
except Exception as e:
    if task.can_retry():
        task.increment_retry()
        await queue.requeue_for_retry(task)
    else:
        task.mark_failed()
        logger.error(f"Task failed permanently: {e}")
```

### 4. Monitoring

```python
from src.monitoring.metrics import MetricsCollector
from src.monitoring.logger import StructuredLogger

metrics = MetricsCollector()
logger = StructuredLogger(name="crawler")

# Track metrics
metrics.increment_counter("requests")
metrics.record_gauge("active_sessions", 5)
metrics.record_histogram("response_time", 150)

# Log events
logger.info("Crawling started", session_id="abc123")
logger.warning("High error rate", error_rate=0.15)
logger.error("Critical failure", error=str(e))
```

---

## Troubleshooting

### Common Issues

#### 1. Browser Not Launching

```bash
# Install Playwright browsers
playwright install chromium

# Or reinstall
playwright install --with-deps chromium
```

#### 2. MongoDB Connection Failed

```bash
# Start MongoDB
docker-compose up -d mongodb

# Check status
docker-compose ps mongodb
```

#### 3. Proxy Connection Failed

```python
# Test proxy directly
from src.proxies.health import ProxyHealthChecker

checker = ProxyHealthChecker()
health = await checker.check_health(proxy)

print(f"Status: {health.status}")
print(f"Error: {health.error_message}")
```

#### 4. Captcha Detection

```python
# Check if captcha is present
detector = CaptchaDetector()
captcha_type = await detector.detect(page)

if captcha_type:
    print(f"Captcha detected: {captcha_type}")
```

---

## API Reference

See individual module documentation in:
- `src/browser/` - Browser automation
- `src/proxies/` - Proxy management
- `src/auth/` - Authentication
- `src/extractors/` - Data extraction
- `src/storage/` - Data storage
- `src/queue/` - Task queue
- `src/crawler/` - Crawler orchestration
- `src/monitoring/` - Monitoring

---

**Last Updated:** 2025-10-16
