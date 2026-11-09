# MailMate 📬

A lightweight AI-powered email assistant that fetches emails, processes them using the Hugging Face API to generate summaries and identify potential tasks, and sends useful notifications through Telegram.

MailMate is being built incrementally, with the goal of turning a regular inbox into a more useful and actionable assistant.

## Setup Instructions for Raspberry Pi

### 1. System Preparation

Open a terminal on your Raspberry Pi and run:

```bash
sudo apt update
sudo apt upgrade
sudo apt install python3 python3-pip python3-venv git
```

### 2. Clone/Copy the Project

Copy or clone the `mailmate` project to your Raspberry Pi, for example:

```bash
cd ~
git clone <repository-url> mailmate
cd mailmate
```

Or, if you already have the project folder, navigate to it:

```bash
cd ~/mailmate
```

### 3. Set Up the Virtual Environment

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### 4. Configuration

Create your environment configuration file from the example:

```bash
cp config/settings.example.env .env
```

Edit the `.env` file:

```bash
nano .env
```

Add the required credentials.

#### Gmail

MailMate uses the Gmail API to access emails.

You'll need to:

1. Create a project in Google Cloud Console.
2. Enable the Gmail API.
3. Configure OAuth credentials.
4. Provide the required Gmail configuration in `.env`.

#### Hugging Face

MailMate uses the Hugging Face API for AI-powered email processing.

Create a Hugging Face API token and add it to your `.env` configuration.

#### Telegram

MailMate uses Telegram to send email summaries and notifications.

Create a Telegram bot using **BotFather**, obtain the bot token, and configure the required Telegram credentials in `.env`.

### 5. Run MailMate Manually

Activate the virtual environment if it isn't already active:

```bash
cd ~/mailmate
source .venv/bin/activate
```

Then run:

```bash
python3 -m app.main
```

MailMate will:

1. Fetch the configured emails.
2. Process the emails using the AI service.
3. Generate summaries and identify potential tasks.
4. Send the results through Telegram.

## Current Status

MailMate is currently designed to be run manually while the core functionality is being developed and tested.

### Planned

The following automation is planned for a future iteration:

- ⏰ Scheduled email processing
- 🔄 Automatic periodic execution
- 📅 Calendar/task integration
- 🔔 Improved notification handling
- 👤 Support for multiple email accounts
- 🧠 Better context and task detection

**Scheduled execution has not been implemented yet.**

Once the scheduling layer is ready, MailMate can be configured to run automatically at a defined interval without requiring manual execution.
