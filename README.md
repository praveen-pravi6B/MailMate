# Email AI Assistant

A lightweight email assistant designed to run on a Raspberry Pi 2. It fetches emails periodically, processes them using the Hugging Face API to generate summaries and detect tasks, and sends a notification via Telegram.

## Setup Instructions for Raspberry Pi

### 1. System Preparation
Open a terminal on your Raspberry Pi and run:
```bash
sudo apt update
sudo apt upgrade
sudo apt install python3 python3-pip python3-venv git
```

### 2. Clone/Copy the Project
Copy this project folder (`email-ai-assistant`) to your Raspberry Pi, perhaps into your home directory (`~/email-ai-assistant`).

### 3. Setup Virtual Environment
Navigate to the project folder on the Pi:
```bash
cd ~/email-ai-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Configuration
Create a `.env` file from the example:
```bash
cp config/settings.example.env .env
```
Edit the `.env` file (`nano .env`) and fill in your credentials:
- **Gmail**: You need to create a project in Google Cloud Console, enable the Gmail API, and get OAuth credentials.
- **Hugging Face**: Get an API token from your Hugging Face account settings.
- **Telegram**: Use BotFather on Telegram to create a bot and get the token. Message your bot and use an API to find your Chat ID.

### 5. Running the Application
To run it manually:
```bash
python3 -m app.main
```

To schedule it with systemd to run every hour, you will copy the `.service` and `.timer` files (to be provided) to `/etc/systemd/system/` and enable the timer.
