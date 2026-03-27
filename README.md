# KHQR Payment API (Flask)

A simple **Python Flask API** for generating and checking **Bakong KHQR payments**.  
This project allows you to create QR codes for payments, check payment status, and view QR images.  

---

## **Features**

- Generate dynamic QR codes for Bakong payments.
- Save QR codes as PNG files locally.
- Check payment status using MD5 hash.
- View QR codes via `/qr/<md5>` endpoint.
- Fully compatible with Windows and Python virtual environments.

---

## **Requirements**

- Python 3.9+  
- `pip install` dependencies:

```bash
pip install Flask bakong-khqr[image] Pillow
