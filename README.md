Absolutely! Here’s a **ready-to-copy `README.md` text** for your GitHub repo. You can just open `README.md` in your project folder and paste everything below:

---

````markdown
# KHQR Payment API (Flask)

A simple **Python Flask API** for generating and checking **Bakong KHQR payments**.  
This project allows you to create QR codes for payments, check payment status, and view QR images.  

---

## Features

- Generate dynamic QR codes for Bakong payments.
- Save QR codes as PNG files locally.
- Check payment status using MD5 hash.
- View QR codes via `/qr/<md5>` endpoint.
- Fully compatible with Windows and Python virtual environments.

---

## Requirements

- Python 3.9+  
- Install dependencies:

```bash
pip install Flask bakong-khqr[image] Pillow
````

* Bakong Developer Token (from Bakong sandbox or live environment).

---

## Folder Structure

```
khqr-payment/
│
├─ app.py               # Main Flask application
├─ requirements.txt     # Python dependencies
├─ README.md            # This file
├─ .gitignore           # Git ignore file
├─ qr/                  # Generated QR images
├─ venv/                # Python virtual environment (ignored in Git)
```

---

## Setup & Run

1. **Clone the repository**:

```bash
git clone https://github.com/seyha29/qrcode_payment.git
cd qrcode_payment
```

2. **Create virtual environment**:

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
```

4. **Run the Flask app**:

```bash
python app.py
```

* Server will run on: `http://127.0.0.1:5000`

---

## API Endpoints

### 1. Home

```http
GET /
```

* Returns: `"KHQR Payment API Running"`

---

### 2. Create QR Payment

```http
GET /create?amount=<amount>
```

* Parameters:

  * `amount` (optional) — Payment amount (default = 1)
* Returns JSON:

```json
{
  "bill": "TRX-e5160466",
  "md5": "e0a1c8004203b999cff47fe2387eb8fe",
  "qr": "/qr/e0a1c8004203b999cff47fe2387eb8fe"
}
```

---

### 3. View QR Image

```http
GET /qr/<md5>
```

* Returns the QR code PNG file.

---

### 4. Check Payment

```http
GET /check/<md5>
```

* Returns payment status:

```json
{
  "status": "UNPAID"
}
```

---

## Notes

* QR codes are stored in the `qr/` folder.
* Dynamic QR codes expire after 1 day (configurable in `app.py`).
* Do **not include `venv/` or `qr/` in Git** — use `.gitignore`.
* Replace your Bakong token in `app.py`:

```python
BAKONG_TOKEN = "YOUR_BAKONG_TOKEN_HERE"
```

---

## Optional: XAMPP/MySQL Integration

You can extend this project to **store all transactions in MySQL**:

* Save `bill_number`, `md5`, `amount`, `status` in a database.
* Update status automatically when checking payment.
* Provides persistent record of all transactions.

---

## License

MIT License

```

---
