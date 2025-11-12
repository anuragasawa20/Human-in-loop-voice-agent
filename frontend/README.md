# Streamlit Dashboard

Supervisor dashboard for Priyanka's Beauty Salon built with Streamlit.

## Why Streamlit?

**Design Decision:**
- All Python (no TypeScript/Node.js needed)
- Rapid development (< 300 lines of code)
- Built-in auto-refresh for real-time updates
- Simple deployment
- Perfect for internal dashboards

## Setup

```bash
# Install dependencies
uv sync

# Copy environment file
cp .env.example .env.local

# Edit .env.local:
# - Set API_URL (default: http://localhost:8000)
# - Set Firebase credentials (optional, for direct DB access)

# Run dashboard
streamlit run dashboard.py
```

## Features

### 📋 Pending Requests Tab
- View all pending help requests
- See caller info, question, and context
- Time since request created
- Priority indicators
- One-click "Respond" button

### ✅ Resolved Requests Tab
- History of resolved requests
- See supervisor responses
- Track who resolved what

### 📚 Knowledge Base Tab
- View all learned answers
- Filter by category
- Search functionality
- See confidence scores
- Track usage statistics

### Real-time Updates
- Auto-refresh every 10 seconds (configurable)
- Instant notification when new requests arrive
- Connection status indicator

## Usage

1. **Start the backend:**
   ```bash
   cd ../backend
   uv run uvicorn main:app --reload
   ```

2. **Start the dashboard:**
   ```bash
   streamlit run dashboard.py
   ```

3. **Access dashboard:**
   - Open browser to http://localhost:8501
   - View pending requests
   - Click "Respond" to answer
   - Submit response → Customer notified + KB updated

## Customization

### Change refresh interval
Edit `dashboard.py`:
```python
refresh_interval = st.slider("Refresh interval (seconds)", 5, 60, 10)
```

### Change theme
Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#ec4899"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

### Add authentication
Use Streamlit's authentication features:
```python
import streamlit_authenticator as stauth

authenticator = stauth.Authenticate(...)
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    # Show dashboard
    main()
```

## Deployment

### Option 1: Streamlit Cloud (Easiest)
1. Push code to GitHub
2. Go to https://share.streamlit.io/
3. Connect repository
4. Deploy!

### Option 2: Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501"]
```

### Option 3: Own Server
```bash
# Install Streamlit
pip install streamlit

# Run with systemd service
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0
```

## Advantages over React

| Feature | Streamlit | React |
|---------|-----------|-------|
| **Lines of Code** | ~300 | ~1000+ |
| **Setup Time** | 5 minutes | 30+ minutes |
| **Learning Curve** | Easy (just Python) | Medium (JS/TS/React) |
| **Real-time Updates** | Built-in | Need Firebase SDK |
| **Deployment** | One command | Build + deploy |
| **Maintenance** | Simple | Complex (dependencies) |

## Limitations

- Not suitable for public-facing UIs
- Less customizable than React
- Page reloads on interaction (but fast)
- Not ideal for mobile apps

For supervisor dashboards, these limitations don't matter!

## Screenshots

### Pending Requests
```
┌─────────────────────────────────────────┐
│ 📋 Pending Requests                     │
├─────────────────────────────────────────┤
│ 📞 +9876543210                          │
│ 🔵 Pending | Medium Priority            │
│ ⏰ 5 min ago                            │
│                                         │
│ Q: Do you offer hair extensions?       │
│ Context: Customer asked about services │
│                                         │
│ [Respond]                               │
└─────────────────────────────────────────┘
```

### Response Modal
```
┌─────────────────────────────────────────┐
│ 📝 Respond to Request                   │
├─────────────────────────────────────────┤
│ Caller: +1234567890                     │
│ Question: Do you offer hair extensions? │
│                                         │
│ Your Response:                          │
│ ┌─────────────────────────────────────┐ │
│ │ Yes, we offer tape-in and clip-in   │ │
│ │ hair extensions starting at $200.   │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Submit Response] [Cancel]              │
└─────────────────────────────────────────┘
```

## Tips

1. **Use auto-refresh** - Enable it in sidebar for real-time updates
2. **Filter by category** - In KB tab, filter to find specific info
3. **Search KB** - Use search box to quickly find answers
4. **Monitor stats** - Top bar shows pending/resolved counts

## Troubleshooting

**Dashboard won't start:**
- Check Python version: `python --version` (need 3.9+)
- Install dependencies: `uv sync`
- Check port 8501 is available

**Can't connect to backend:**
- Verify backend is running on port 8000
- Check `API_URL` in `.env.local`
- Look at sidebar connection status

**Auto-refresh not working:**
- Enable it in sidebar settings
- Adjust refresh interval if needed

## Development

To add new features:

1. **New tab:**
   ```python
   tab4 = st.tabs(["📊 Analytics"])
   with tab4:
       show_analytics()
   ```

2. **New API endpoint:**
   ```python
   def get_analytics():
       return API.get("/api/analytics")
   ```

3. **Custom styling:**
   ```python
   st.markdown("""
   <style>
   .custom-class { ... }
   </style>
   """, unsafe_allow_html=True)
   ```

That's it! Streamlit makes building dashboards incredibly fast and simple.
