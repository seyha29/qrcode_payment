# KHQR Payment - Webhook Setup Guide

## How Real-Time Payment Confirmation Works

### Current System:
1. **QR Code Generated** → Flask creates QR and stores MD5 + Bill number
2. **Payment Made** → Customer pays via Bakong KHQR app
3. **Auto-Detection** → Frontend polls Bakong API every 2 seconds for payment status
4. **Bakong Callback (Optional)** → Bakong webhook sends POST to `/webhook/bakong` (if registered)
5. **Real-Time Update** → WebSocket notifies frontend + shows "✅ Payment Confirmed"

### Setup Steps:

#### 1. Get Your Server URL
- **Local Testing**: `http://localhost:5000`
- **Production**: `https://your-domain.com` (must be HTTPS)

#### 2. Register Webhook with Bakong (OPTIONAL but recommended)
Contact Bakong developer support and register your webhook URL:
```
POST URL: https://your-domain.com/webhook/bakong
```

#### 3. Check Webhook History
View all webhooks received:
```
http://localhost:5000/webhooks/history
```

#### 4. Debug Payment Status
Get bill information and QR details:
```
http://localhost:5000/bill-info/{md5}
```

#### 5. Manual Payment Confirmation (Admin)
If Bakong is slow or for testing:
```
http://localhost:5000/admin/force-confirm/{md5}
```

#### 6. Bakong Webhook Payload Format
Expected JSON from Bakong:
```json
{
  "md5": "abc123...",
  "hash": "abc123...",
  "transactionId": "abc123...",
  "status": "completed",
  "transactionStatus": "success",
  "amount": 1.00,
  "currency": "USD"
}
```

### Endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Payment checkout UI |
| `/create?amount=X` | GET | Create QR code |
| `/qr/<md5>` | GET | Get QR image PNG |
| `/check/<md5>` | GET | Check payment status (polls Bakong API) |
| `/webhook/bakong` | POST | Bakong payment callback (webhook) |
| `/bill-info/<md5>` | GET | Get bill details and QR info |
| `/admin/force-confirm/<md5>` | GET/POST | Admin manual confirmation |
| `/webhooks/history` | GET | View all webhooks received |
| `/debug` | GET | View all payment records |
| `/status` | GET | Health check + token status |

### Real-Time Features:
- ✅ **Auto-polling every 2 seconds** - Detects payments automatically
- ✅ **WebSocket real-time** - Instant notification when payment confirmed
- ✅ **Webhook fallback** - Also listens for Bakong webhook callbacks
- ✅ **3-minute QR expiration** - Auto-expires unpaid QR codes
- ✅ **No manual interaction needed** - Fully automatic detection
- ✅ **Admin override** - Manual confirmation if needed

### Troubleshooting:

#### Payment not detected?
1. Check `/status` - Verify Bakong token is valid (not expired)
2. Check `/webhooks/history` - See if Bakong webhook was sent
3. Check `/bill-info/{md5}` - Verify bill number format
4. Use `/admin/force-confirm/{md5}` - Manual confirmation for testing

#### Bakong Token Expired?
- Contact Bakong support to get a new token
- Replace `BAKONG_TOKEN` in `app.py`
- Restart server: `python app.py`

#### Webhook not arriving?
- Ensure server is accessible from internet (not behind firewall)
- Verify webhook URL is registered with Bakong
- Check `/webhooks/history` to confirm receipt

### For Production:
1. Set `debug=False` in app.py
2. Use production WSGI server: `gunicorn --worker-class socketio.async_workers.AsyncWorker -b 0.0.0.0:5000 app:app`
3. Enable HTTPS/SSL certificate
4. Register webhook URL with Bakong developer portal
5. Monitor server logs: `tail -f app.log`
6. Keep Bakong token fresh and updated
