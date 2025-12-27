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

## **📱 Screenshots - WhatsApp Interface**

See Stock Sentinel in action through these WhatsApp conversation examples:

### 1️⃣ Getting Help - Your Personal Trading Assistant

<p align="center">
  <img src="public/Screenshot 2025-12-27 at 4.08.49 PM.png" alt="Help Command" width="600"/>
</p>

**What's happening here:**
When you send `help`, the bot responds with a friendly, comprehensive guide showing all available commands. The interface is designed to be conversational and easy to understand:

- **Stock Price Queries** - Check real-time prices instantly
- **Alert Setup** - Configure price drop alerts (📉), spike alerts (📈), and intraday movement tracking (⚡)
- **Alert Management** - List and remove your active alerts
- **Natural Language** - Just chat normally if you have questions!

**Key Features Shown:**
- ✅ User-friendly emoji-based navigation
- ✅ Clear examples for each command
- ✅ Market hours information (9:15 AM - 3:30 PM IST)
- ✅ AI-powered conversational fallback

---

### 2️⃣ Real-Time Stock Price Lookup

<p align="center">
  <img src="public/Screenshot 2025-12-27 at 4.09.05 PM.png" alt="Price Command" width="600"/>
</p>

**What's happening here:**
User sends: `price TCS`

The bot instantly responds with:
- **Current Price**: ₹3,320.00
- **Previous Close**: ₹3,370.00
- **Change**: -1.48% 📉

**Behind the Scenes:**
1. Request hits the FastAPI webhook endpoint `/whatsapp`
2. Command parser identifies this as a `price` query
3. Yahoo Finance API fetches latest TCS stock data
4. Redis caches the result for 60 seconds (configurable)
5. Response formatted and sent via Twilio WhatsApp API

**Technical Details:**
- **Cache Strategy**: Multi-level (Redis → PostgreSQL → Yahoo Finance)
- **Response Time**: ~200ms (cached) / ~800ms (fresh fetch)
- **Data Source**: Yahoo Finance API for Indian stocks (.NS suffix)

---

### 3️⃣ Setting Up Stock Alerts - Smart Duplicate Detection

<p align="center">
  <img src="public/Screenshot 2025-12-27 at 4.09.39 PM.png" alt="Add Alert Command" width="600"/>
</p>

**What's happening here:**

**Message 1 (Warning):**
User tries: `alert add TCS -8`
Bot detects: "⚠️ You already have active 8% drop alerts for TCS"
- Shows existing Alert ID: #1
- Suggests using `alert remove TCS` to clear all TCS alerts first

**Message 2 (Success):**
User sends: `alert add TCS +8`
Bot confirms: "✅ 3 Alerts created successfully!"

**The 3 alerts created:**
1. **Gap Up Alert** (ID: #2)
   - Triggers if TCS opens 8% above yesterday's close
   - Checks once at market open (9:15 AM IST)

2. **1-Hour Spike Alert** (ID: #3)
   - Triggers if TCS spikes 8% from lowest price in last 60 minutes
   - Checked every 5 minutes during market hours

3. **2-Hour Spike Alert** (ID: #4)
   - Triggers if TCS spikes 8% from lowest price in last 120 minutes
   - Provides longer-term perspective on price movements

**What the bot explains:**
- 🎯 Detailed description of each alert's behavior
- ⏱️ Frequency: "Every 15 minutes" (configurable via `ALERT_CHECK_INTERVAL`)
- 🕒 Active during: Market hours only (9:15 AM - 3:30 PM IST)
- 🔔 Alerts stay active until manually removed

**Technical Implementation:**
- **Celery Beat Scheduler**: Triggers periodic alert checks
- **Celery Workers**: Process alert evaluation in background
- **PostgreSQL**: Stores alert configurations with user_phone mapping
- **Alert Cooldown**: 1-hour cooldown prevents spam (configurable)

---

### 4️⃣ Managing Your Active Alerts

<p align="center">
  <img src="public/Screenshot 2025-12-27 at 4.09.57 PM.png" alt="List Alerts Command" width="600"/>
</p>

**What's happening here:**
User sends: `alert list`

The bot shows all active alerts with:
- **Alert IDs**: #4, #3, #2, #1
- **Stock Symbol**: TCS
- **Alert Types**:
  - 2h Spike 8% (monitors 2-hour rolling window)
  - 1h Spike 8% (monitors 1-hour rolling window)
  - Gap Up 8% (market open gap detection)
  - 2h Drop 8% (from an earlier setup)
- **Total Count**: 4 alert(s)

**How to Remove Alerts:**
```
alert remove 4       → Removes specific alert #4
alert remove TCS     → Removes all 4 TCS alerts at once
```

**Database Schema:**
```python
class Alert(Base):
    id: int
    user_phone: str              # whatsapp:+919730526650
    stock_symbol: str            # TCS
    alert_type: AlertType        # SPIKE_1H, SPIKE_2H, GAP_UP, etc.
    threshold_percent: float     # 8.0
    created_at: datetime
    last_triggered_at: datetime  # For cooldown logic
```

---

## **🔧 How It All Works Together**

### Architecture Flow:

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   WhatsApp  │ ─────>  │  Twilio API  │ ─────>  │  FastAPI    │
│   Message   │         │   Webhook    │         │   Server    │
└─────────────┘         └──────────────┘         └─────────────┘
                                                         │
                                                         ▼
                                               ┌──────────────────┐
                                               │ Command Parser   │
                                               │ (price/alert/AI) │
                                               └──────────────────┘
                                                         │
                        ┌────────────────────────────────┼────────────────┐
                        ▼                                ▼                ▼
                ┌──────────────┐              ┌──────────────┐   ┌──────────┐
                │ Stock Service│              │Alert Service │   │Gemini AI │
                │(Yahoo Finance│              │(CRUD + Check)│   │ Service  │
                └──────────────┘              └──────────────┘   └──────────┘
                        │                                │
                        ▼                                ▼
                ┌──────────────┐              ┌──────────────────┐
                │ Redis Cache  │              │   PostgreSQL     │
                │ (60s TTL)    │              │ (Persistent DB)  │
                └──────────────┘              └──────────────────┘
                                                         ▲
                                                         │
                                               ┌─────────┴─────────┐
                                               │  Celery Beat      │
                                               │  (Scheduler)      │
                                               └───────────────────┘
                                                         │
                                                         ▼
                                               ┌───────────────────┐
                                               │  Celery Workers   │
                                               │ (Alert Checking)  │
                                               └───────────────────┘
```

### Alert Monitoring Workflow:

1. **User Creates Alert** → Stored in PostgreSQL
2. **Celery Beat** (every 5 min) → Triggers alert check task
3. **Celery Worker** → Fetches all active alerts from DB
4. **For each alert:**
   - Fetch current stock price (with caching)
   - Calculate rolling window high/low (for DROP/SPIKE alerts)
   - Check if threshold crossed
   - Verify cooldown period (default: 1 hour)
5. **If triggered** → Send WhatsApp notification via Twilio
6. **Update `last_triggered_at`** → Prevents duplicate notifications

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
From: whatsapp:+919730526650
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