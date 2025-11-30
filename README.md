
# NorthStar Goods – Final Project

NorthStar Goods is a full‑stack e‑commerce web application built using **Flask**, **SQLAlchemy**, **JWT authentication**, **Stripe checkout**, and a clean, responsive frontend.

This README includes:
- Project Overview  
- Features  
- Project Structure  
- How to Run (Locally & via Docker)  
- Environment Variables  
- Notes for the Instructor  

---

## 🛒 Project Overview
NorthStar Goods simulates a modern online store where users can:
- Browse products  
- Create an account / Log in  
- Add items to their cart  
- Checkout using Stripe test payments  
- View order confirmations  
- Interact with an integrated AI chatbot (Gemma via Ollama)

The backend is built in **Python/Flask**, the frontend uses HTML/CSS/JS, and data is stored using **SQLite**.

---

## ✨ Features

### 🔐 User Authentication
- Register & login  
- JWT-based sessions  
- Secure password hashing  

### 🛍 Product System
- Products stored in the database  
- Product list stored in `campaign.json` on startup  
- Dynamic product rendering on the frontend  

### 🛒 Cart & Checkout
- Add/remove items from cart  
- Prices auto-calculated  
- Stripe Checkout Session integration  
- Success/failure redirect pages  

### 🤖 Chatbot
- Integrated AI assistant  
- Uses **Ollama** locally via `OLLAMA_URL`  
- Helps users browse or ask questions  

### 🗄 Database
- SQLite file automatically created  
- Tables:
  - `User`
  - `Product`
  - `CartItem`
  - `Order`

### 🐳 Docker Support
- Fully containerized  
- Instructor can build & run with **no manual setup**

---

## 📁 Project Structure

```
final/
│── app.py
│── models.py
│── routes/
│   ├── auth.py
│   ├── products.py
│   ├── payment.py
│   └── chat.py
│── static/
│── templates/
│── campaign.json  (generated automatically)
│── requirements.txt
│── Dockerfile
│── .env  (not included – you create this)
```

---

## ⚙️ Environment Variables (`.env`)

Create a `.env` file:

```
STRIPE_SECRET_KEY=sk_test_51SRCVt0RNCB3m8QSaIRumhWoMmjlrilyhdXjaG0p7E8yLpEyjp6pR8e6HNpG0V72OJA9Ki2I6JklwiFF0BgIuss900WNlkVK7o
SECRET_KEY=supersecretkey321
STRIPE_PUBLIC_KEY=pk_test_51SRCVt0RNCB3m8QSpZhxFBpOZr8mMSpIO8MO43DcfLXX1AArhDGLlcWUpcMKVOUsLLwl8keO00YdPFiKjkua5FYH00mnsHFca3
SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3
```

---

## ▶️ Running the App Locally

### 1. Install dependencies
```
pip install -r requirements.txt
```

### 2. Run the application
```
python app.py
```

### 3. Visit the site
```
http://localhost:5000
```

On first run:
- Database tables are created  
- `campaign.json` is generated  

---

## 🐳 Running with Docker 

### 1. Build the Docker image
```
docker build -t northstar-goods .
```

### 2. Run the container
```
docker run -p 5000:5000 northstar-goods
```

### 3. Open the app
```
http://localhost:5000
```

Everything (database creation, `campaign.json`, authentication) runs automatically.

---

## 📬 Contact Info
If issues occur, please contact:  
**Student: Kowsikan Arudchelvan and Seyon Ranjithkumar **  
**Course: Advanced Web Development **

---
