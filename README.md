# Blasda Bistro – Smart Restaurant Web Application

A web application for an Irish restaurant: online menu, takeaway ordering, table bookings, customer accounts, an editable admin panel, a daily sales ledger, and an AI assistant powered by Google Gemini.

## Features
- Customer registration, login, and order history
- Menu with English and Irish (Gaeilge) text
- Shopping cart, takeaway ordering with scheduled pickup
- Table booking requests
- Admin panel (CMS) for menu, prices, opening hours, story text, orders, and bookings
- AI-generated dish descriptions (English and Irish) and a customer chat assistant
- Automatic daily sales ledger

## Tech stack
Python 3.12, Django 5.2 LTS, SQLite, Google Gemini API (`google-genai`), WhiteNoise, Gunicorn

## Run it on your own computer
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Edit `.env` first and set `DEBUG=True` for local use, plus your own `DJANGO_SECRET_KEY` and `GEMINI_API_KEY`.

## Put it online
See **[DEPLOYMENT.md](DEPLOYMENT.md)** for the step-by-step owner guide.