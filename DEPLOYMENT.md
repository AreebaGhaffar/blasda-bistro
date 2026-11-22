# Blasda Bistro – Deployment Guide (for the owner)

This guide puts your website online. Allow about 1 hour. You do not need to write code, only copy and paste. If you have a web developer, you can simply hand them this file.

## What you need

- **A hosting account that can run Python websites.** This guide uses **PythonAnywhere** as the example. Hosting and your domain name are paid separately from the website itself. Before you sign up, check the host's current prices and plan features on its website. Two things matter:
  - To use your own domain (for example `blasdabistro.ie`) you need a **paid** plan, not a free one.
  - The AI features (dish descriptions and the chat assistant) need a plan that lets your website connect to outside services. Free plans on some hosts block this.
- **Your domain name** (optional at first; you can test on the host's free address).
- **A free Google Gemini key** from https://aistudio.google.com/apikey (only needed for the AI features; the rest of the website works without it).

The zip file you received is called `blasda-bistro.zip`. Keep a copy somewhere safe.

---

## Part 1 – Put the code on the server

1. Log in to PythonAnywhere. Open the **Files** tab, click **Upload a file**, and upload `blasda-bistro.zip` into your home folder.
2. Open the **Consoles** tab and start a **Bash** console.
3. Unpack the zip:

```
unzip blasda-bistro.zip
```

This creates a folder called `blasda-bistro`.

## Part 2 – Install the project

In the Bash console, run these lines one at a time:

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
   - `DJANGO_SECRET_KEY` – create one with the command below and paste the result:
     `python -c "import secrets; print(secrets.token_urlsafe(50))"`
   - `FIELD_ENCRYPTION_KEY` – the key that protects your customers' personal data. Create it with the command below, paste the result, and **read "Protecting your encryption key" further down before you continue**:
     `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
   - `DEBUG` – keep it as `False`
   - `ALLOWED_HOSTS` – your website address(es), separated by commas, for example `blasdabistro.ie,www.blasdabistro.ie`. While testing on the host's free address, use that instead, for example `yourusername.pythonanywhere.com`.
   - `CSRF_TRUSTED_ORIGINS` – the same addresses, each starting with `https://`
   - `ADMIN_URL` – choose a secret address for your admin page, for example `manage-blasda-7421/` (keep the slash at the end)
   - `BEHIND_PROXY` – keep it as `True`
   - `GEMINI_API_KEY` – your own Gemini key (leave it as it is if you do not want the AI features yet)
3. Save in nano with `Ctrl + O`, then Enter, then exit with `Ctrl + X`.

**Never share the `.env` file or send it by email. It contains your secrets.**

## Protecting your encryption key (important)

Your customers' names, phone numbers, emails and order or booking notes are stored **encrypted** in the database. The `FIELD_ENCRYPTION_KEY` in your `.env` file is the only thing that can unlock them.

- **Back the key up now.** Copy it into a password manager or another safe place that is **separate from the website and from your database backups.**
- **Never change it** once you have customers. A different key cannot unlock data saved with the old one.
- **If the key is lost, that personal data cannot be recovered by anyone.** There is no reset.
- If someone has both your database file **and** your key, they can read the data. Keep them apart.

**What is and is not encrypted:** customer names, phone numbers, emails and notes on orders and bookings are encrypted. The menu, prices, order totals, order status and dates are not, and neither are the usernames and email addresses of customer login accounts (their passwords are stored in scrambled form and cannot be read). Searching orders and bookings by name or phone number is not possible in the admin, because that data is encrypted. Search by order or booking number instead.

## Part 4 – Set up the database and your admin account

```
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Choose a strong password for the admin account and keep it safe.

## Part 5 – Connect the website

1. Open the **Web** tab and click **Add a new web app**. Choose your domain (or the free address), then **Manual configuration**, then the Python version you used in Part 2.
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

6. If the Web tab offers a **Force HTTPS** switch, turn it on. Then click the green **Reload** button and open your website address.

(Replace `YOURUSERNAME` everywhere with your PythonAnywhere username.)

## Part 6 – Use your own domain

In the **Web** tab, follow the domain and DNS instructions your host shows. You add a record at the company where you bought your domain. It can take from a few minutes to a few hours to start working. Make sure HTTPS (the padlock) is switched on for your domain; your host's help pages explain how.

## Part 7 – First-time setup (about 15 minutes)

1. Open `https://yourdomain.ie/YOUR_ADMIN_URL` (the secret address from Part 3) and log in.
2. Open **Site settings** and enter your name, phone number, email, address, opening hours, home page heading, and your story text in English and Irish.
3. Add your **Categories** (for example Starters, Mains, Desserts), then your **Menu items** with prices and photos.
4. In **Menu items**, tick some dishes, choose **Generate descriptions with AI**, and click **Go**. **Always proofread the English and the Irish text, and write allergy information yourself. Never trust the AI for allergens.**

---

## Everyday use

- **Orders:** open **Orders**. Change the status (Pending, Confirmed, Preparing, Ready, Completed, Cancelled) and tick **Is paid** when you take payment. Customers pay at the restaurant when they collect; no money is taken online.
- **Bookings:** open **Bookings** and set each one to Confirmed or Cancelled. **The website does not send emails or texts.** Please phone or email the customer to confirm.
- **Prices and menu:** edit directly in **Menu items**. Untick **Is available** to hide a sold-out dish. The website and the chat assistant update straight away.
- **Stop online orders:** untick **Accepting orders** in **Site settings**.
- **Daily sales:** open **Daily sales logs**. It updates by itself and cannot be edited. The admin's **Recent actions** panel shows who changed what.

## Keeping your data safe (backups)

Once a week, download these two items from your host's file manager and keep them somewhere safe:
- `db.sqlite3` (all orders, bookings, customers and menu data)
- the `media` folder (dish photos)

Keep your **encryption key** backed up separately, as described above. A database backup without the key cannot be read, and the key alone is useless without the database.

## Updating the website later

If your developer sends you an updated `blasda-bistro.zip`:

1. Make a backup first (see above), and make sure your `FIELD_ENCRYPTION_KEY` is saved safely.
2. Upload the new zip to your home folder, then in a Bash console run:

```
unzip -o blasda-bistro.zip
cd ~/blasda-bistro
workon blasda
pip install -r requirements.txt
python manage.py migrate
python manage.py encrypt_existing_data
python manage.py collectstatic --noinput
```

3. Click **Reload** in the Web tab.

**If you are upgrading from the first version of the website (before data encryption was added):** before step 2, open your `.env` file (`nano .env`) and add a line `FIELD_ENCRYPTION_KEY=` followed by a new key, created with the command in Part 3, and back that key up. The `encrypt_existing_data` command then encrypts all the customer data you already have. It says how many orders and bookings it processed. It is safe to run more than once.

Your `.env`, `db.sqlite3` and `media` folder are not inside the zip, so they will not be overwritten.

## Using a different host

Any host that runs Python websites will work. In short:

1. Install Python 3.12, then run `pip install -r requirements.txt`.
2. Set the values from `.env.example` as environment variables or in a `.env` file.
3. Run `python manage.py migrate` and `python manage.py collectstatic --noinput`.
4. Start the site with `gunicorn config.wsgi:application`.
5. Make sure your host keeps the `db.sqlite3` file and the `media` folder on permanent storage, and serves the `/media/` folder to visitors.
6. Serve the site over HTTPS only.

## If something goes wrong

- **Blank or error page:** open your host's error log (on PythonAnywhere: the **Web** tab, then **Error log**).
- **Page looks unstyled:** check the Static files rows in Part 5 and run `collectstatic` again.
- **"Bad request" errors:** check `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in `.env`.
- **"Too many redirects":** check that `BEHIND_PROXY=True` is in `.env`, then Reload.
- **"FIELD_ENCRYPTION_KEY is not set" or "Could not decrypt data":** the encryption key is missing from `.env` or is different from the one used when the data was saved. Put the original key back, then Reload.
- **Chat assistant says it is unavailable:** check your Gemini key in `.env`, make sure your hosting plan allows outside connections, then Reload.
- **Admin page not found:** use the secret `ADMIN_URL` you chose in Part 3, not `/admin/`.
- **Screens look different from this guide:** hosts change their menus from time to time. Follow your host's current help pages for the same task.