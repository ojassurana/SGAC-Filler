# Singapore Arrival Card Telegram Bot

**🤖 Bot:** [@SGAC_filler_bot](https://t.me/SGAC_filler_bot)  
**📄 Privacy Policy:** [View Document](https://docs.google.com/document/d/1gc5WjsPp8KS6Is4FWrfEiZcODx1_0po76Qsiq6fxyUM/edit?usp=sharing)  
**📋 Terms & Conditions:** [View Document](https://docs.google.com/document/d/12W7b2xAbcxVBbfdcpU1xvMPcv_2gsk1D0ar0had1LsI/edit?usp=sharing)

⚡️ Skip the hassle of manual form filling! This smart Telegram bot instantly submits your Singapore Arrival Card in seconds. A seamless one-time setup that lets you breeze through future submissions. Perfect for frequent travelers and residents returning to Singapore! 🇸🇬✈️

## Features

- **New Users** (`/start`): Register with IC/FIN, Date of Birth, and Email
- **Returning Users** (`/enter`): Quick submission with saved information
- **Data Management** (`/delete`): Delete all stored personal data
- **Help System** (`/help`): Get information about available commands
- Validates Singapore NRIC/FIN format
- Email validation and collection
- Automatically fills and submits the arrival card form
- Handles CAPTCHA solving using OpenAI Vision API
- Downloads and sends the PDF arrival card to users
- PDPA compliant with privacy policy and terms & conditions

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

### 3. Configure Bot Token

1. Create a new bot on Telegram using [@BotFather](https://t.me/botfather)
2. Get your bot token
3. Either:
   - Set environment variable: `export TELEGRAM_BOT_TOKEN="your_bot_token"`
   - Or update the token in `main.py` (line 574)

### 4. Configure OpenAI API Key

Update the API key in `obtain_captcha.py`:
```python
client = OpenAI(api_key='your_openai_api_key')
```

## Usage

### Starting the Bot

```bash
python main.py
```

### Bot Commands

- `/start` - Register as a new user or update existing information
- `/enter` - Quick submission for returning users  
- `/delete` - Delete all your stored personal data
- `/help` - Show available commands and instructions
- `/cancel` - Cancel current operation

### User Flow

#### New Users:
1. User sends `/start`
2. Bot shows welcome message and PDPA disclaimer with privacy policy links
3. Bot asks for IC/FIN (validates format)
4. Bot asks for Date of Birth (DD/MM/YYYY format)
5. Bot asks for Email address (validated)
6. Bot shows 3 date options (today, tomorrow, day after)
7. Bot asks health declaration (symptoms and Yellow Fever travel)
8. If healthy, bot submits form and sends PDF
9. Bot saves user data for future use

#### Returning Users:
1. User sends `/enter` (or `/start` if already registered)
2. Bot shows saved IC, DOB, and Email for confirmation
3. User can confirm or update information
4. If correct, bot asks for travel date
5. Bot asks health declaration
6. If healthy, bot submits form and sends PDF

#### Data Deletion:
1. User sends `/delete`
2. Bot shows stored data and asks for confirmation
3. User confirms deletion
4. All personal data is permanently removed

## File Structure

- `main.py` - Telegram bot logic and conversation handlers
- `clicker.py` - Web automation for form submission
- `obtain_captcha.py` - CAPTCHA solving using OpenAI Vision
- `validate_IC.py` - Singapore IC/FIN validation
- `user_data.json` - Stores user information (created automatically)

## Data Storage

User data is stored in JSON format with the following structure:
```json
{
  "telegram_user_id": {
    "ic": "S1234567A",
    "dob": "01/01/1990",
    "email": "user@example.com"
  }
}
```

## Privacy & Security

- The bot includes PDPA compliance notices and privacy policy links
- User data can be deleted at any time using `/delete`
- PDFs are automatically cleaned up after sending
- User data is stored locally in JSON format
- Health declaration ensures compliance with entry requirements

## Health Declaration

Users must confirm they:
- Have no symptoms (fever, cough, sore throat, runny nose, etc.)
- Have not visited countries with Yellow Fever risk in the past 6 days

If either condition is true, users are directed to submit manually on the ICA website.

## Notes

- The bot automatically determines if the user is a resident (NRIC starting with S/T) or foreigner (FIN starting with F/G)
- PDFs are generated with the user's actual email address
- The bot handles both new registrations and updates to existing information
- Comprehensive error handling with user-friendly messages

## Security Considerations

- Keep your bot token and OpenAI API key secure
- The `user_data.json` file contains sensitive information (IC numbers, DOB, emails)
- Consider implementing encryption for stored data in production
- Regular backups of user data are recommended
- Monitor bot usage for any suspicious activity 
