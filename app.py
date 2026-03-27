from flask import Flask, jsonify, send_file, request, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from bakong_khqr import KHQR
import qrcode
import uuid
import os

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'khqr-payment-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

BAKONG_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImlkIjoiOTcyZDc1YzhiMzUwNGY4MiJ9LCJpYXQiOjE3NzQ1OTg4NDEsImV4cCI6MTc4MjM3NDg0MX0.hClAuSPgmAmR0ll_ao4tCOZjTs_2z_MBUi4_VYFd0sk"
BANK_ACCOUNT = "seyha_than@bkrt"

khqr = KHQR(BAKONG_TOKEN)

# Ensure folder exists
QR_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qr")
os.makedirs(QR_FOLDER, exist_ok=True)

# Store payment status in memory
payment_status = {}

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/status")
def status():
    """Health check endpoint"""
    import base64
    import json
    from datetime import datetime
    
    # Decode token to check expiry
    token_parts = BAKONG_TOKEN.split('.')
    try:
        # Decode payload (add padding if needed)
        payload = token_parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        decoded = base64.urlsafe_b64decode(payload)
        token_data = json.loads(decoded)
        exp_time = datetime.fromtimestamp(token_data.get('exp', 0))
        now = datetime.now()
        token_status = "✅ VALID" if exp_time > now else "❌ EXPIRED"
    except:
        token_status = "⚠️ UNABLE TO DECODE"
        exp_time = None
    
    return jsonify({
        "status": "✅ KHQR Payment Server Running",
        "webhook_url": "POST /webhook/bakong",
        "admin_force_confirm": "POST /admin/force-confirm/<md5>",
        "bill_info": "GET /bill-info/<md5>",
        "debug_payments": "GET /debug",
        "bakong_token_status": token_status,
        "token_expires": str(exp_time) if exp_time else "Unknown",
        "current_time": str(now)
    })


@app.route("/admin/force-confirm/<md5>", methods=['POST', 'GET'])
def force_confirm(md5):
    """ADMIN: Manually confirm payment (for testing/debugging when Bakong is slow)"""
    if md5 in payment_status:
        data = payment_status[md5]
        bill = data.get('bill', 'N/A')
        amount = data.get('amount', 'N/A')
        
        # Mark as paid
        payment_status[md5]['paid'] = True
        
        print(f"\n{'='*60}")
        print(f"👤 ADMIN FORCE-CONFIRM: Payment marked as PAID")
        print(f"   MD5: {md5}")
        print(f"   Bill: {bill}")
        print(f"   Amount: {amount}")
        print(f"{'='*60}")
        
        # Emit WebSocket event
        socketio.emit('payment_confirmed', {'md5': md5}, room=md5)
        
        return jsonify({
            "success": True,
            "message": "✅ Payment confirmed (admin override)",
            "md5": md5,
            "bill": bill,
            "amount": amount
        }), 200
    else:
        return jsonify({"error": "MD5 not found"}), 404


@app.route("/webhooks/history")
def webhooks_history():
    """View all webhooks received"""
    return jsonify({
        "total_received": len(webhook_logs),
        "webhooks": webhook_logs[-20:]  # Last 20
    })


@app.route("/bill-info/<md5>")
def bill_info(md5):
    """Get bill and QR string info for debugging"""
    if md5 in payment_status:
        data = payment_status[md5]
        return jsonify({
            "md5": md5,
            "bill": data.get('bill'),
            "amount": data.get('amount'),
            "qr_string": data.get('qr_string', '')[:200] + "..." if data.get('qr_string') else None,
            "paid": data.get('paid')
        })
    return jsonify({"error": "MD5 not found"}), 404


@app.route("/debug")
def debug():
    """Debug endpoint to see all payment statuses"""
    debug_info = {
        "payments": {},
        "count": len(payment_status),
        "bakong_token": "****" + BAKONG_TOKEN[-20:],
        "bank_account": BANK_ACCOUNT
    }
    
    for md5, data in payment_status.items():
        debug_info["payments"][md5] = {
            "paid": data.get('paid', False),
            "bill": data.get('bill', 'N/A'),
            "amount": data.get('amount', 'N/A'),
            "qr_string": data.get('qr_string', '')[:50] + "..." if data.get('qr_string') else 'N/A'
        }
    
    return jsonify(debug_info)

@app.route("/create")
def create():
    try:
        amount = float(request.args.get("amount", 1))
    except ValueError:
        return jsonify({"error": "Invalid amount"}), 400

    bill = "TRX-" + str(uuid.uuid4())[:8]

    try:
        print(f"📝 Creating QR for amount: {amount}, bill: {bill}")
        qr_string = khqr.create_qr(
            bank_account=BANK_ACCOUNT,
            merchant_name="My Shop",
            merchant_city="Phnom Penh",
            amount=amount,
            currency="USD",
            store_label="MyShop",
            phone_number="85512345678",
            bill_number=bill,
            terminal_label="POS-01",
            static=False,
            expiration=1
        )

        md5 = khqr.generate_md5(qr_string)

        # Store QR string for later use
        payment_status[md5] = {
            'paid': False,
            'qr_string': qr_string,
            'bill': bill,
            'amount': amount,
            'created_at': __import__('time').time()
        }

        # Generate and save QR image using qrcode library
        path = os.path.join(QR_FOLDER, f"{md5}.png")
        qr = qrcode.QRCode()
        qr.add_data(qr_string)
        qr.make()
        img = qr.make_image()
        img.save(path)
        
        print(f"✅ QR Created: {md5} | Amount: {amount} | Bill: {bill}")
        print(f"   QR String: {qr_string[:100]}...")

    except Exception as e:
        print(f"❌ Error creating QR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "bill": bill,
        "md5": md5,
        "qr": f"/qr/{md5}"
    })

@app.route("/qr/<md5>")
def qr(md5):
    path = os.path.join(QR_FOLDER, f"{md5}.png")
    if os.path.exists(path):
        return send_file(path, mimetype="image/png")
    return jsonify({"error": "QR not found"}), 404

@app.route("/check/<md5>")
def check(md5):
    try:
        print(f"\n{'='*60}")
        print(f"🔍 Payment Check Request for MD5: {md5}")
        print(f"{'='*60}")
        
        # Check if MD5 exists
        if md5 not in payment_status:
            print(f"❌ MD5 not found in payment_status")
            return jsonify({"status": False, "source": "not_found", "message": "MD5 not found"}), 200
        
        status_data = payment_status[md5]
        print(f"✓ Found payment record:")
        print(f"   Bill: {status_data.get('bill')}")
        print(f"   Amount: {status_data.get('amount')}")
        print(f"   Paid: {status_data.get('paid')}")
        
        # Check 1: Already marked as paid?
        if status_data.get('paid'):
            print(f"✅ Already marked as PAID (from webhook or manual)")
            return jsonify({"status": True, "source": "cached"}), 200
        
        # Check 2: Try Bakong API ONLY if payment not yet confirmed
        bill = status_data.get('bill')
        if bill:
            try:
                print(f"\n📡 Querying Bakong API for real payment...")
                print(f"   Bill: {bill}")
                
                api_status = khqr.check_payment(bill)
                
                print(f"   Raw Response: {repr(api_status)}")
                print(f"   Type: {type(api_status).__name__}")
                
                # Handle different response types
                is_paid = False
                
                if api_status is True or api_status == 1 or api_status == '1':
                    is_paid = True
                    print(f"   ✓ Payment confirmed!")
                    
                elif isinstance(api_status, str):
                    response_lower = api_status.lower().strip()
                    print(f"   String response: '{response_lower}'")
                    
                    if response_lower == 'true':
                        is_paid = True
                        print(f"   ✓ Payment confirmed!")
                    elif response_lower == 'paid':
                        is_paid = True
                        print(f"   ✓ Payment confirmed!")
                    elif response_lower in ['unpaid', 'false', '0', 'none', 'null']:
                        print(f"   ⏳ Status: {response_lower} - Payment not yet detected")
                        is_paid = False
                    else:
                        # Unknown response - log it
                        print(f"   ⚠️ Unknown response: {api_status}")
                        is_paid = False
                
                if is_paid:
                    print(f"✅ BAKONG CONFIRMS PAYMENT IS RECEIVED!")
                    payment_status[md5]['paid'] = True
                    
                    # Emit WebSocket event to all listening clients
                    print(f"📢 Broadcasting WebSocket event: payment_confirmed")
                    socketio.emit('payment_confirmed', {'md5': md5}, room=md5)
                    
                    return jsonify({"status": True, "source": "bakong_api", "message": "Payment confirmed!"}), 200
                else:
                    print(f"⏳ Payment still pending (Bakong response: {api_status})")
                    print(f"   Checking again in 2 seconds...")
                    return jsonify({"status": False, "source": "bakong_api", "api_response": str(api_status)}), 200
                
            except Exception as e:
                print(f"❌ API Error: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({"status": False, "source": "api_error", "error": str(e)}), 200
        
        print(f"⏳ No payment detected")
        return jsonify({"status": False, "source": "pending"}), 200
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "status": False}), 200


# Store webhook logs for debugging
webhook_logs = []

@app.route("/webhook/bakong", methods=['POST'])
def bakong_webhook():
    """Bakong payment callback webhook"""
    try:
        data = request.json or request.get_json(force=True)
        
        print(f"\n{'='*60}")
        print(f"📲 WEBHOOK RECEIVED FROM BAKONG")
        print(f"{'='*60}")
        print(f"Headers: {dict(request.headers)}")
        print(f"Raw Data: {data}")
        print(f"{'='*60}\n")
        
        # Store webhook log
        webhook_logs.append({
            'timestamp': __import__('time').time(),
            'data': data,
            'headers': dict(request.headers)
        })
        
        md5 = data.get('md5') or data.get('hash') or data.get('transactionId')
        status = data.get('status') or data.get('transactionStatus')
        
        print(f"Extracted MD5/Hash: {md5}")
        print(f"Extracted Status: {status}")
        
        if md5:
            # Update payment status
            if md5 in payment_status and isinstance(payment_status[md5], dict):
                payment_status[md5]['paid'] = True
                print(f"✅ Updated existing record: {md5}")
            else:
                payment_status[md5] = {'paid': True}
                print(f"✅ Created new record: {md5}")
            
            print(f"✅ Payment webhook confirmed for {md5}")
            
            # Emit WebSocket event
            socketio.emit('payment_confirmed', {'md5': md5}, room=md5)
            print(f"📢 WebSocket event emitted to room: {md5}")
            
            return jsonify({"success": True, "message": "Payment confirmed"}), 200
        else:
            print(f"❌ No MD5/Hash found in webhook data")
            return jsonify({"success": False, "error": "No MD5 found"}), 400
            
    except Exception as e:
        print(f"❌ Webhook error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Store error log
        webhook_logs.append({
            'timestamp': __import__('time').time(),
            'error': str(e),
            'type': type(e).__name__
        })
    
    return jsonify({"success": False}), 400


# Test endpoint to simulate Bakong payment (for testing)
@app.route("/test/payment/<md5>", methods=['POST', 'GET'])
def test_payment(md5):
    """Test endpoint - simulates Bakong sending a payment confirmation"""
    if md5 in payment_status and isinstance(payment_status[md5], dict):
        payment_status[md5]['paid'] = True
    else:
        payment_status[md5] = {'paid': True}
    
    print(f"🧪 TEST: Payment confirmed for {md5}")
    socketio.emit('payment_confirmed', {'md5': md5}, room=md5)
    return jsonify({
        "success": True, 
        "message": f"✅ Test Payment Confirmed for {md5}",
        "md5": md5
    }), 200


@app.route("/admin/manual-confirm/<md5>", methods=['POST', 'GET'])
def manual_confirm(md5):
    """Manual payment confirmation endpoint (for testing/admin)"""
    if md5 in payment_status and isinstance(payment_status[md5], dict):
        payment_status[md5]['paid'] = True
        bill = payment_status[md5].get('bill', 'N/A')
        amount = payment_status[md5].get('amount', 'N/A')
    else:
        payment_status[md5] = {'paid': True}
        bill = 'N/A'
        amount = 'N/A'
    
    print(f"👤 MANUAL: Payment confirmed for {md5} - Bill: {bill} - Amount: {amount}")
    socketio.emit('payment_confirmed', {'md5': md5}, room=md5)
    return jsonify({
        "success": True, 
        "message": f"✅ Manual Payment Confirmed",
        "md5": md5,
        "bill": bill,
        "amount": amount
    }), 200


# WebSocket connection for real-time updates
@socketio.on('connect')
def handle_connect():
    print(f"✅ Client connected: {request.sid}")

@socketio.on('join_payment')
def on_join_payment(data):
    if data and 'md5' in data:
        md5 = data['md5']
        join_room(md5)
        print(f"👤 Client joined room: {md5}")
        emit('joined', {'message': f'Watching for payment {md5}', 'md5': md5})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"❌ Client disconnected: {request.sid}")

if __name__ == "__main__":
    socketio.run(app, port=5000, debug=True, host='0.0.0.0')