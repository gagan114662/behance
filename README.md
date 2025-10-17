# Behance Crawler

A sophisticated web crawler for Behance with advanced anti-detection, distributed architecture, and MongoDB storage.

## Features

- **Browser Automation**: Playwright with stealth plugins for realistic browsing
- **Anti-Detection**: Fingerprint randomization, human behavior simulation, TLS fingerprinting
- **Distributed Architecture**: Redis-based task queue with multiple workers
- **Session Management**: Account pool, session warming, cookie persistence
- **Proxy Support**: Residential proxy rotation with health checking
- **Captcha Handling**: Automatic detection and solving
- **Data Extraction**: Projects, users, images, relationships
- **MongoDB Storage**: Flexible schema for all crawled data
- **Monitoring**: Prometheus metrics and Sentry error tracking

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
```

## Quick Start

```bash
# Start infrastructure
docker-compose up -d

# Run tests
pytest

# Start crawler
python -m src.main
```

## Architecture

```
src/
├── models/          # Pydantic models and MongoDB schemas
├── browser/         # Playwright automation with stealth
├── network/         # Request interception and API discovery
├── proxies/         # Proxy pool management
├── auth/            # Authentication and account management
├── evasion/         # Anti-detection mechanisms
├── extractors/      # Data parsers for Behance content
├── queue/           # Redis task queue
├── storage/         # MongoDB operations and image pipeline
├── crawler/         # Main crawler orchestration
└── monitoring/      # Metrics and logging
```

## Development

Tests are written first (TDD approach) with no hardcoded data.

```bash
# Run all tests
pytest

# Run specific test category
pytest -m unit
pytest -m integration

# Run with coverage
pytest --cov=src --cov-report=html
```

## License

MIT
