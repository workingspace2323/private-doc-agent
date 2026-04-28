# 📱 APK & Mobile Installation Guide

Complete step-by-step instructions to install the Private Document Agent
as a native-feeling app on your Android or iPhone.

---

## Option A: Access via Browser (Fastest — Works Right Now)

No installation needed. Works on any phone.

1. Start the server on your computer:
   ```
   python app.py
   ```

2. Note the "Mobile" URL printed at startup:
   ```
   Mobile: http://192.168.1.42:8000
   ```

3. On your phone (connected to same WiFi):
   - Android: Open Chrome → type the URL
   - iPhone: Open Safari → type the URL

4. The app works fully in the browser. ✓

---

## Option B: Install as PWA (Recommended — No APK needed)

A PWA looks and feels like a native app. No app store, no USB cable.

### Android (Chrome)

```
1. Open Chrome on your phone
2. Go to: http://YOUR_COMPUTER_IP:8000
3. Tap the ⋮ menu (top right corner)
4. Tap "Add to Home screen"
   (or "Install app" if shown)
5. Tap "Add" to confirm
```

The app now appears on your home screen.
Tap it — it opens full-screen, no browser bar. ✓

### iPhone / iPad (Safari)

```
1. Open Safari on your iPhone
2. Go to: http://YOUR_COMPUTER_IP:8000
3. Tap the Share button (box with ↑ arrow, bottom of screen)
4. Scroll down and tap "Add to Home Screen"
5. Tap "Add" (top right)
```

The app now appears on your home screen. ✓

---

## Option C: Build a Real Android APK

### Method 1: PWABuilder (Microsoft — Easiest, Free)

**Step 1: Get a public URL using ngrok**

```bash
# Install ngrok: https://ngrok.com/download
# Or via brew: brew install ngrok

# Run your server
python app.py

# In a new terminal, expose it publicly:
ngrok http 8000
```

ngrok will show a URL like: `https://abc123def.ngrok-free.app`

**Step 2: Generate APK with PWABuilder**

```
1. Go to: https://www.pwabuilder.com
2. Paste your ngrok URL (e.g., https://abc123.ngrok-free.app)
3. Click "Start"
4. PWABuilder validates your manifest and PWA features
5. Click "Package for Stores"
6. Choose "Android" → Click "Download Package"
7. You'll get a .apk file + optional AAB for Play Store
```

**Step 3: Install the APK on Android**

```
1. Transfer the APK to your phone:
   - Email it to yourself and open on phone, OR
   - Use Google Drive / WhatsApp file transfer, OR
   - Connect USB → copy to Downloads folder

2. On your Android phone:
   Settings → Apps → Special app access → Install unknown apps
   → Enable for your file manager or browser

3. Open the APK file on your phone
4. Tap "Install"
5. Tap "Open"
```

---

### Method 2: Bubblewrap CLI (Google's Official Tool)

For developers who want full control over the APK.

**Prerequisites:**
- Node.js 16+ installed
- Java 11+ (JDK) installed
- Android SDK (optional, Bubblewrap can download it)

```bash
# Install Bubblewrap
npm install -g @bubblewrap/cli

# Initialize the project (run from the project folder)
# Use your ngrok URL or local IP
bubblewrap init --manifest https://YOUR_NGROK_URL/static/manifest.json

# Bubblewrap will ask several questions:
# - App name: DocAgent
# - Package ID: com.yourname.docagent
# - Version: 1.0.0
# - Signing: generate a new key (for testing)

# Build the APK
bubblewrap build

# Output: app-release-unsigned.apk (or signed if you configured keystore)
```

**Sign the APK (required for installation):**

```bash
# Generate a keystore (one time)
keytool -genkey -v \
  -keystore docagent.keystore \
  -alias docagent \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000

# Sign the APK
jarsigner -verbose \
  -sigalg SHA1withRSA \
  -digestalg SHA1 \
  -keystore docagent.keystore \
  app-release-unsigned.apk \
  docagent

# Align the APK
zipalign -v 4 app-release-unsigned.apk docagent.apk
```

Install `docagent.apk` on your phone (same steps as above).

---

### Method 3: WebIntoApp (No Code Required)

```
1. Start server + ngrok (see Method 1, Step 1)
2. Go to: https://webintoapp.com
3. Enter your ngrok URL
4. App Name: DocAgent
5. Package Name: com.private.docagent
6. Click "Generate APK"
7. Download the APK
8. Install on Android phone
```

---

## Option D: Deploy to a Cloud Server (Access from Anywhere)

If you want to access the agent from anywhere (not just home WiFi):

### Deploy to a VPS (DigitalOcean, AWS, Render, Railway, etc.)

```bash
# On your server:
git clone your-repo or upload files
cd private-doc-agent
pip install -r requirements.txt
cp .env.example .env
# Edit .env → add ANTHROPIC_API_KEY
# Upload your documents to data/documents/
python main.py ingest
uvicorn app:app --host 0.0.0.0 --port 8000
```

Use your server's public IP or domain name.
Then the PWA install works from anywhere, not just home WiFi.

**Use a process manager to keep it running:**
```bash
pip install supervisor
# OR use systemd / screen / tmux
screen -S docagent -dm uvicorn app:app --host 0.0.0.0 --port 8000
```

**Add HTTPS with Caddy (needed for PWA features on iOS):**
```
# /etc/caddy/Caddyfile
yourdomain.com {
    reverse_proxy localhost:8000
}
```

---

## Troubleshooting Mobile Issues

**Phone can't reach the server:**
- Ensure both devices are on same WiFi
- Check if your firewall blocks port 8000:
  - Linux: `sudo ufw allow 8000`
  - macOS: System Preferences → Security → Firewall → Allow uvicorn
  - Windows: Windows Defender Firewall → Allow app → Add uvicorn

**"Add to Home Screen" not appearing on Chrome Android:**
- The app must be served over HTTPS for full PWA installation
- Over local WiFi (http://), Chrome may still show "Add to Home Screen"
  via the ⋮ menu even without HTTPS

**APK installation blocked:**
- Go to Settings → Security → Install unknown apps
- Grant permission to your file manager

**PWA icon looks blank:**
- This is normal if the PNG icons are placeholder. The app still installs.
- To add a real icon: replace static/icon-192.png and static/icon-512.png
  with a 192×192 and 512×512 PNG of your choice.
