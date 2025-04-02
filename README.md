# Flask Web Honeypot

A simple Flask-based web honeypot designed to detect unauthorized access attempts to fake admin panels.

## Features
- Fake WordPress admin login page (`wp-admin.html`)
- Captures and logs unauthorized login attempts
- Stores logs in a CSV file
- Can be deployed locally or on a cloud server

## Requirements
- Python 3.8+
- Flask

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/flask-honeypot.git
   cd flask-honeypot
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Start the Flask server:**
   ```bash
   python web_honeypot.py
   ```
   By default, the app will run on `http://127.0.0.1:5000/`.

2. **Access the honeypot page:**
   Open your browser and go to:
   ```
   http://127.0.0.1:5000/wp-admin-loggin
   ```

##  Deployment

### Deploy on Heroku (Example)
1. Install Heroku CLI:
   ```bash
   curl https://cli-assets.heroku.com/install.sh | sh  # Linux/macOS
   winget install heroku-cli                            # Windows
   ```
2. Login to Heroku:
   ```bash
   heroku login
   ```
3. Create a Heroku app:
   ```bash
   heroku create flask-honeypot
   ```
4. Push your code to Heroku:
   ```bash
   git add .
   git commit -m "Deploy Flask honeypot"
   git push heroku main
   ```
5. Open the deployed app:
   ```bash
   heroku open
   ```

### Deploy on Render (Easier Alternative)
1. Create an account on [Render](https://render.com)
2. Create a **new web service**
3. Connect your GitHub repository
4. Set the **Start Command** to:
   ```bash
   gunicorn web_honeypot:app
   ```
5. Deploy! 

## Logging Unauthorized Access
All login attempts are stored in `logs.csv`, capturing:
- IP Address
- Timestamp
- Username & Password entered

## Security Note
This is **not a real security solution** but a honeypot for detecting unauthorized access attempts. **Do not deploy on a critical system.**

