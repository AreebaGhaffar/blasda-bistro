# Blasda Bistro – Deployment Guide (for the owner)

This guide puts your website online. It takes about 45 minutes. You do not need to write code, only copy and paste.

You will need:
- A paid hosting account (this guide uses **PythonAnywhere**, which keeps your database and photos safe on a permanent disk)
- Your domain name (for example `blasdabistro.ie`)
- A free **Google Gemini API key** from https://aistudio.google.com/apikey

---

## Part 1 – Get the code onto the server

1. Create your PythonAnywhere account and log in.
2. Open the **Consoles** tab and start a **Bash** console.
3. Upload or clone the project so that it sits in `/home/YOURUSERNAME/blasda-bistro`.
   (If the code is on GitHub, run: `git clone YOUR_REPOSITORY_LINK blasda-bistro`.)

## Part 2 – Install the project

In the same Bash console, run these lines one at a time (replace nothing unless told):

```
cd ~/blasda-bistro
mkvirtualenv --python=python3.12 blasda
pip install -r requirements.txt
```

If Python 3.12 is not offered, use the newest Python version available.

## Part 3 – Add your private settings

1. Make your settings file from the template:

```
cp .env.example .env
nano .env
```

2. Change every value in the file:
   - `DJANGO_SECRET_KEY` – run this to create one, then paste the result:
     `python -c "import secrets; print(secrets.token_urlsafe(50))"`
   - `DEBUG` – keep it as `False`
   - `ALLOWED_HOSTS` – your domain, for example `blasdabistro.ie,www.blasdabistro.ie`
   - `CSRF_TRUSTED_ORIGINS` – the same domains starting with `https://`
   - `ADMIN_URL` – choose a secret address for your admin page, for example `manage-blasda-7421/` (keep the slash at the end)
   - `BEHIND_PROXY` – keep it as `True`
   - `GEMINI_API_KEY` – your own Gemini key
3. Save in nano with `Ctrl + O`, Enter, then exit with `Ctrl + X`.

**Never share the `.env` file or put it on GitHub.** It contains your secrets.

## Part 4 – Set up the database and your admin account

```
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Choose a strong password for the admin account and keep it safe.

## Part 5 – Connect the website

1. Open the **Web** tab and click **Add a new web app**. Choose your domain, then **Manual configuration**, then the Python version you used in Part 2.
2. In **Virtualenv**, enter: `/home/YOURUSERNAME/.virtualenvs/blasda`
3. In **Code**, set the source directory to `/home/YOURUSERNAME/blasda-bistro`
4. Click the **WSGI configuration file** link, delete everything, and paste:

```
import os
import sys

path = "/home/YOURUSERNAME/blasda-bistro"
if path not in sys.path:
    sys.path.append(path)

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

5. In the **Static files** section, add two rows:

| URL | Directory |
|---|---|
| `/static/` | `/home/YOURUSERNAME/blasda-bistro/staticfiles` |
| `/media/` | `/home/YOURUSERNAME/blasda-bistro/media` |

6. Turn on **Force HTTPS**, then click the green **Reload** button.

## Part 6 – Use your own domain

In the **Web** tab, follow the **domain / DNS** instructions shown there. You add one record at the company where you bought your domain. It can take up to a few hours to start working. HTTPS is switched on in the Web tab.

## Part 7 – First-time setup (5 minutes)

1. Open `https://yourdomain.ie/YOUR_ADMIN_URL` and log in.
2. Open **Site settings** and enter your name, phone number, address, opening hours and Irish story text.
3. Add your **Categories** (for example Starters, Mains, Desserts), then your **Menu items** with prices and photos.
4. Tick dishes in **Menu items**, choose **Generate descriptions with AI**, and click **Go**. **Always proofread the English and Irish text, and add allergy information yourself. The AI must not be trusted for allergens.**

---

## Everyday use

- **Orders:** open **Orders**. Change the status (Pending, Confirmed, Preparing, Ready, Completed, Cancelled) and tick **Is paid** when you take payment.
- **Bookings:** open **Bookings** and set each one to Confirmed or Cancelled. Please call or email the customer to let them know.
- **Prices and menu:** edit directly in **Menu items**. Untick **Is available** to hide a sold-out dish. The website and the chat assistant update straight away.
- **Stop online orders:** untick **Accepting orders** in **Site settings**.
- **Daily sales:** open **Daily sales logs**. It updates by itself and cannot be edited.

## Keeping your data safe (backups)

Once a week, download these two items from PythonAnywhere's **Files** tab and keep them somewhere safe:
- `db.sqlite3` (all orders, bookings, customers, menu)
- the `media` folder (dish photos)

## Updating the website later

```
cd ~/blasda-bistro
git pull
workon blasda
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Then click **Reload** in the Web tab.

## If something goes wrong

- Blank or error page: open the **Web** tab and read the **Error log**.
- Page looks unstyled: check the Static files rows in Part 5 and run `collectstatic` again.
- Chat assistant says it is unavailable: check your Gemini key in `.env`, then Reload.
- "Bad request" errors: check `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in `.env`.