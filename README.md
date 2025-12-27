# Stock Sentinel

Stock Sentinel is a professional intraday stock trading alert system via WhatsApp using the Twilio API. This intelligent chatbot monitors stock prices in real-time, detects gap downs/ups, price drops/spikes in rolling windows, and sends instant WhatsApp notifications during Indian market hours.

## **Features**
- 📊 Real-time stock price monitoring with 1-minute snapshots
- 🚨 Gap Down/Up Alerts: Detect 5%, 7%, 8%, 9%, 10% price gaps at market open
- 📉 Drop Alerts: Track price drops from rolling window highs (1-hour and 2-hour windows)
- 📈 Spike Alerts: Track price spikes from rolling window lows (1-hour and 2-hour windows)
- ⏰ Market Hours Intelligence: Only monitors during Indian market hours (9:15 AM - 3:30 PM IST, Monday-Friday)
- 💬 WhatsApp Command Interface: Manage alerts via simple commands
- 🤖 AI Fallback: Powered by Google Gemini for conversational queries
- 🐳 Containerized using **Docker & Docker Compose**
- 📦 Background task processing with **Celery + Redis**
- 🗄️ PostgreSQL database for persistent alert storage
- 🔄 Multi-level caching (Redis + PostgreSQL + Yahoo Finance API)

---

## **Getting Started**

### **Prerequisites**
Ensure you have the following installed:
- [Python 3.12.1](https://www.python.org/)
- [Docker & Docker Compose](https://www.docker.com/)
- [PostgreSQL](https://www.postgresql.org/) (running locally or remote)
- [uv](https://github.com/astral-sh/uv) (for dependency management)
- A [Twilio account](https://www.twilio.com/) with WhatsApp API access
- A [Google Gemini API key](https://ai.google.dev/)
- [ngrok](https://ngrok.com/) for webhook tunneling during development

---

## **Installation and Setup**

### **1. Clone the Repository**
```bash
git clone https://github.com/playgude2/stock-sentinel.git
cd stock-sentinel
```

### **2. Set Up the Development Environment**
We use `uv` for dependency management.

#### **Install `uv` (if not installed)**
```bash
pip install uv
```

#### **Create and Activate a Virtual Environment**
```bash
uv venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows (PowerShell)
```

#### **Install Dependencies**
```bash
uv pip install -r requirements.dev.txt
```

---

## **Running the Application Locally**

### **Using `docker-compose.dev.yml`**
For development, the environment is configured using Docker Compose.

#### **Start the Development Environment**
```bash
make up-dev
```
or
```bash
docker-compose -f docker/docker-compose.dev.yml up -d --force-recreate
```

#### **Stop the Development Environment**
```bash
make down-dev
```
or
```bash
docker-compose -f docker/docker-compose.dev.yml down
```

#### **Rebuild Containers**
```bash
make build-dev
```

#### **View Logs**
```bash
make logs-dev
```

---

## **WhatsApp Commands**

Stock Sentinel supports the following commands:

### **Stock Price Queries**
```
price <SYMBOL>
```
Example: `price TCS` → Returns current price with change percentage

### **Alert Management**

**Add Drop Alert (7%, 8%, 9%, 10%)**
```
alert add <SYMBOL> -<PERCENT>
```
Example: `alert add TCS -8` → Creates 3 alerts:
- Gap Down 8% (at market open)
- 1-hour Drop 8% (rolling window)
- 2-hour Drop 8% (rolling window)

**Add Spike Alert (5%, 7%, 8%, 9%, 10%)**
```
alert add <SYMBOL> +<PERCENT>
```
Example: `alert add TCS +8` → Creates 3 alerts:
- Gap Up 8% (at market open)
- 1-hour Spike 8% (rolling window)
- 2-hour Spike 8% (rolling window)

**List Alerts**
```
alert list
```
Shows all active alerts with IDs

**Remove Alert**
```
alert remove <ID>         → Remove specific alert by ID
alert remove <SYMBOL>     → Remove all alerts for a stock symbol
```

### **Help**
```
help
```
Shows command reference

### **AI Fallback**
Any message that doesn't match a command will be processed by Google Gemini AI for conversational responses.

---

## **API Endpoints**

### **POST /whatsapp**
Handles incoming WhatsApp webhook events from Twilio.

**Request Body (Form Data):**
```
From: whatsapp:+919730526660
To: whatsapp:+14155238886
Body: price TCS
MessageSid: SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Response:**
```json
{
  "message": "Message processed successfully"
}
```

For local development, use ngrok to expose your server:
```bash
ngrok http 8000
```
Then configure the ngrok URL in Twilio Console → Sandbox Settings → When a message comes in.

---

## **Environment Variables**
Create a `.env` file in `docker/env/.env` with the following variables:

```ini
# Ngrok Configuration
NGROK_AUTHTOKEN=your_ngrok_auth_token

# Twilio API Credentials
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
TWILIO_TEMPLATE_CONTENT_SID=your_template_content_sid

# Redis Configuration
REDIS_HOSTNAME=redis
REDIS_PORT=6379

# PostgreSQL Database
DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/whatsapp_bot

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Google Gemini AI
GEMINI_APIKEY=your_gemini_api_key

# Stock Service Configuration
STOCK_PRICE_CACHE_TTL=60        # Redis cache TTL (seconds)
STOCK_PRICE_DB_CACHE_TTL=300    # DB cache TTL (seconds)
ALERT_CHECK_INTERVAL=300         # Celery beat interval (5 minutes)
ALERT_COOLDOWN_PERIOD=3600      # Alert cooldown (1 hour)
```

---

## **Development Workflow**
### **Code Formatting & Linting**
Before committing, ensure code follows project standards.

#### **Run Formatters & Linters**
```bash
black . && ruff . && mypy --ignore-missing-imports .
```

#### **Enable `pre-commit` Hooks**
```bash
pre-commit install
```

To manually run checks on all files:
```bash
pre-commit run --all-files
```

---

## **Deployment**
For production, use:

```bash
make up-prod
```
or
```bash
docker-compose -f docker/docker-compose.prod.yml up -d --force-recreate
```

To stop the production environment:
```bash
make down-prod
```

---

## **Contributing**
We welcome contributions! See the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines.

---

## **License**
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## **Questions and Support**
For any questions, open an issue on GitHub:
- GitHub: [@playgude2](https://github.com/playgude2)