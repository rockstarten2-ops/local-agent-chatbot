# 🆘 Startup Troubleshooting Guide

## ❌ Error: "Max retries exceeded" / "Connection refused"

**This means**: Backend is not running!

### ✅ Quick Fix

**You MUST start the backend BEFORE the UI:**

```bash
# Terminal 1: Start backend FIRST
python -m uvicorn backend:app --reload --host 0.0.0.0 --port 8000

# Wait for message:
# Uvicorn running on http://0.0.0.0:8000

# Then, in Terminal 2: Start frontend
streamlit run streamlit_app.py
```

### Why This Happens

The Streamlit UI needs the FastAPI backend to be running. If backend isn't available, UI can't upload files or search documents.

**Connection Flow:**
```
Streamlit UI (localhost:8501)
        ↓
    HTTP Request
        ↓
FastAPI API (localhost:8000)  ← Must be running!
```

---

## 🔍 Diagnose the Issue

### Check if backend is running:

```bash
# In any terminal, run:
curl http://localhost:8000/health

# If running, you'll see:
# {"status":"ok","message":"API is running"}

# If not running, you'll see:
# curl: (7) Failed to connect to localhost port 8000
```

### Check if port is in use:

```bash
# See what's using port 8000
lsof -i :8000

# If something is using it:
# COMMAND   PID   USER   FD TYPE DEVICE...
# python  12345  user    5 IPv4 ...

# Kill it:
kill -9 12345
```

---

## 🚀 Correct Startup Sequence

### Step 1: Install Dependencies (First Time Only)
```bash
pip install -r requirements.txt
```

### Step 2: Terminal 1 - Start Backend
```bash
cd /workspaces/local-agent-chatbot
python -m uvicorn backend:app --reload --host 0.0.0.0 --port 8000
```

**You should see:**
```
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**⚠️ DO NOT proceed until you see this message!**

### Step 3: Terminal 2 - Start Frontend
```bash
cd /workspaces/local-agent-chatbot
streamlit run streamlit_app.py
```

**You should see:**
```
  Local URL: http://localhost:8501
  Network URL: http://XXX.XXX.XXX.XXX:8501
```

### Step 4: Open Browser
Visit: **http://localhost:8501**

---

## ❓ Common Issues & Solutions

### Issue 1: Port 8000 Already in Use

```bash
# Find what's using it
lsof -i :8000

# Output example:
# COMMAND    PID    USER   FD TYPE DEVICE...
# python   15000   user    6 IPv4 ...

# Kill the process
kill -9 15000

# Try again
python -m uvicorn backend:app --reload
```

### Issue 2: Port 8501 Already in Use

```bash
# Run Streamlit on different port
streamlit run streamlit_app.py --server.port 8502
```

### Issue 3: Module Not Found

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Or install specific module
pip install chromadb sentence-transformers
```

### Issue 4: Connection Reset

```bash
# Check backend is still running
curl http://localhost:8000/health

# If it crashed, restart it
python -m uvicorn backend:app --reload
```

### Issue 5: ChromaDB Lock Issues

```bash
# ChromaDB got corrupted
rm -rf data/chroma_db/

# Restart backend
python -m uvicorn backend:app --reload
```

---

## 📋 Pre-Upload Checklist

Before uploading a file, verify:

- [ ] Backend is running (`curl http://localhost:8000/health` returns OK)
- [ ] Streamlit UI is loading (http://localhost:8501 shows page)
- [ ] No errors in either terminal
- [ ] File is in supported format (PDF, TXT, CSV, JSON, MD)
- [ ] File is not too large (< 100MB recommended)

---

## 🔍 Debug Mode

### View Detailed Backend Logs

```bash
# Keep logs visible
python -m uvicorn backend:app --reload --log-level debug
```

### View Detailed Streamlit Logs

```bash
# In Streamlit terminal, check output
# Red text = errors
# Yellow text = warnings
```

---

## ✅ Verify Everything Works

### Test 1: Backend Health
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok",...}
```

### Test 2: Backend Docs
```
Visit: http://localhost:8000/docs
# Should show interactive Swagger docs
```

### Test 3: Streamlit Loads
```
Visit: http://localhost:8501
# Should show chat interface
```

### Test 4: Upload a File
1. Click "+" in chat
2. Select a TXT file
3. Should see: "Document loaded!"

### Test 5: Ask a Question
1. Type: "Hello"
2. Should respond with greeting

---

## 🎯 If Still Having Issues

1. **Check all errors** - Screenshot and note exact error message
2. **Kill and restart** everything:
   ```bash
   # Press Ctrl+C on both terminals
   # Kill any lingering processes:
   pkill -f "uvicorn"
   pkill -f "streamlit"
   
   # Wait 5 seconds
   sleep 5
   
   # Start fresh:
   python -m uvicorn backend:app --reload
   # In new terminal:
   streamlit run streamlit_app.py
   ```

3. **Reset data**:
   ```bash
   rm -rf data/
   mkdir -p data/uploaded_files
   mkdir -p data/chroma_db
   ```

4. **Reinstall dependencies**:
   ```bash
   pip install --upgrade --force-reinstall -r requirements.txt
   ```

---

## 📞 Still Stuck?

Provide these details:

1. Error message (exact text)
2. Your OS (Windows/Mac/Linux)
3. Python version (`python --version`)
4. What terminal output shows when you:
   - Start backend
   - Start Streamlit
   - Try to upload file

---

## 🎉 Once It Works

You'll see:
- Backend terminal shows: `INFO:     Started server`
- Streamlit terminal shows: `Local URL: http://localhost:8501`
- Browser shows chat interface with "+" button
- Can upload files and chat!

**That's it - you're done! 🚀**
