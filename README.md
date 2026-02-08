# Discord Raffle Bot

A fully-featured Discord raffle bot for managing giveaways with role-based access control. Perfect for gaming communities like LEGEND OF YMIR.

## Features

✨ **Core Features:**
- 🎟️ Start raffles with customizable durations
- 🛡️ Role-based access control (all or specific class roles)
- 💳 VIP role requirement for participation (Donator, Elders, Master)
- 📜 Complete raffle history logging with JSON persistence
- ⏱️ Real-time countdown with Discord timestamps
- 🎉 Automatic winner selection and announcement
- ❌ Raffle cancellation with message cleanup
- 🏓 Bot latency checking

## Prerequisites

- Python 3.8 or higher
- A Discord Bot token
- discord.py 2.0+

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Discord-Raffle
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your Discord bot:**
   - Create a `.env` file in the project root
   - Add your Discord bot token:
     ```
     DISCORD_TOKEN=your_token_here
     ```

5. **Update configuration:**
   - Edit `main.py` and update these IDs:
     - `PUBLIC_CHANNEL_ID` - Where raffle messages are posted
     - `COMMAND_CHANNEL_ID` - Where bot commands are issued

## Usage

### Commands

All commands must be run in the designated **COMMAND_CHANNEL_ID**.

#### Start a Raffle
```
!roll <item_name> <seconds> [target_role]
```
- `item_name`: Name of the item being raffled
- `seconds`: Duration in seconds
- `target_role`: Optional. Specific role requirement (e.g., "Warrior", "Mage") or "All" for everyone with VIP access

**Examples:**
```
!roll "Legendary Sword" 300 Warrior
!roll "Mystery Box" 600 All
```

#### Cancel a Raffle
```
!cancel <message_id>
```
Immediately cancels a raffle and removes the message.

**Example:**
```
!cancel 1234567890123456789
```

#### View Raffle History
```
!logs
```
Displays the last 10 completed raffles with timestamps and winners.

#### Check Bot Status
```
!ping
```
Shows bot latency in milliseconds.

#### Get Channel ID
```
!check
```
Displays the current channel's ID (useful for configuration).

## File Structure

```
Discord-Raffle/
├── main.py                 # Main bot application
├── requirements.txt        # Python dependencies
├── raffle_history.json    # Raffle history log (auto-generated)
├── .env                   # Discord token (not committed to git)
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Configuration

### Channel IDs

Edit `main.py` to set your Discord server's channel IDs:

```python
PUBLIC_CHANNEL_ID = 1234567890123456789    # Raffle announcements
COMMAND_CHANNEL_ID = 1234567890123456789   # Command execution
```

### VIP Roles

Modify the VIP role requirements in `main.py`:

```python
ALLOWED_VIP_ROLES: list[str] = ["Donator", "Elders", "Master"]
```

## Running the Bot

Start the bot with:
```bash
python main.py
```

The bot will display a confirmation message when successfully logged in:
```
✅ Logged in as YourBotName#1234
📍 Bot ID: 1234567890123456789
```

## Security

⚠️ **Important:**
- **Never** commit `.env` files to version control
- Keep your Discord token secret
- Use environment variables for sensitive data
- The `.gitignore` file is configured to prevent accidental commits

## Raffle History

Raffle results are automatically saved to `raffle_history.json` with:
- Timestamp of completion
- Item name
- Winner Discord username
- Required role for that raffle

**Example:**
```json
[
  {
    "timestamp": "2024-02-09 15:30:45",
    "item": "Legendary Sword",
    "winner": "PlayerName",
    "role": "Warrior"
  }
]
```

## Error Handling

The bot gracefully handles:
- ✓ Missing channels or messages
- ✓ Invalid user permissions
- ✓ Network errors
- ✓ Corrupted history files
- ✓ Concurrent raffle operations

## Contributing

Feel free to fork and submit pull requests for improvements!

## License

Open source - Use freely in your projects.

## Support

For issues or questions:
1. Check the bot is logged in (`!ping` returns a response)
2. Verify channel IDs are correct
3. Ensure your Discord token is valid
4. Check that the bot has proper permissions in your server

## Changelog

**v1.0.0** - Initial release
- Core raffle functionality
- Role-based access control
- History logging
- Complete command set
