# 🚀 Deploy to Koyeb - No Credit Card Required

## Step-by-Step Deployment Guide

### 1. **Prepare Your Repository**
Your project is already prepared with:
- ✅ `api_bot.py` - Main application
- ✅ `Dockerfile` - Container configuration  
- ✅ `requirements.txt` - Dependencies
- ✅ Selenium-only mode configured

### 2. **Sign Up to Koyeb**
1. Go to [koyeb.com](https://www.koyeb.com)
2. Click "Sign up" (no credit card required)
3. Use GitHub, Google, or email to register

### 3. **Deploy Your App**
1. **Create New App** → "Deploy from GitHub"
2. **Connect GitHub** and select your repository
3. **Configuration:**
   - **Build method**: Dockerfile
   - **Port**: 8000
   - **Instance type**: Free (1 vCPU, 256MB RAM)

### 4. **Environment Variables**
Set these in Koyeb dashboard under "Environment":

```
USE_SELENIUM=true
API_PORT=8000
AUTO_START_MONITORING=true
POLL_INTERVAL=30
LOG_LEVEL=INFO
DOCKER=true
```

### 5. **Deploy & Access**
- Click "Deploy"
- Wait 3-5 minutes for build
- Access your API at: `https://your-app-name.koyeb.app`

### 6. **Test Your Deployment**
```bash
# Check status
curl https://your-app-name.koyeb.app/status

# Start monitoring
curl -X POST https://your-app-name.koyeb.app/start

# View jobs
curl https://your-app-name.koyeb.app/jobs
```

## 🎯 **API Endpoints Available**

Once deployed, your bot will provide:
- `GET /` - Service health check
- `GET /status` - Monitoring status  
- `GET /jobs` - List detected jobs
- `POST /start` - Start job monitoring
- `POST /stop` - Stop monitoring
- `GET /logs` - View recent logs

## 🔧 **Advantages of Koyeb for Your Project**

1. **No Credit Card** - Start immediately
2. **Docker Native** - Perfect for your Selenium setup
3. **Always On** - No cold starts like some platforms
4. **Global CDN** - Fast access worldwide
5. **Auto HTTPS** - Secure by default

## 🚀 **Alternative: Railway Deployment**

If Koyeb doesn't work, try Railway:

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub (no CC required)
3. "New Project" → "Deploy from GitHub"
4. Select your repository
5. Railway auto-detects Dockerfile
6. Set same environment variables
7. Deploy!

## 📊 **Expected Performance**

**Free Tier Limits:**
- **Koyeb**: 256MB RAM, always-on
- **Railway**: 512MB RAM, $5/month credit
- **Fly.io**: 256MB RAM, 160 hours/month

**Your Bot Requirements:**
- ~100MB RAM usage
- ~10MB/hour bandwidth
- 30-second polling interval

✅ **All platforms can handle your bot easily!**

## 🛠️ **Troubleshooting**

If deployment fails:
1. Check build logs in platform dashboard
2. Ensure all environment variables are set
3. Verify Docker builds locally first:
   ```bash
   docker build -t amazon-bot .
   docker run -p 8000:8000 amazon-bot
   ```

---

**Ready to deploy for FREE!** 🎉