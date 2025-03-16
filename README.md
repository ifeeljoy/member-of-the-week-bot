[![IMG-3395.jpg](https://i.postimg.cc/Hny3Hj0X/IMG-3395.jpg)](https://postimg.cc/2LCn7kKS)

# About

A Discord bot for managing nominations and voting for a member of the week. The bot will create a poll every Friday at 12 AM UTC, and announce the winner the following Sunday at 12 PM UTC. Each member is limited to one vote, and you can't vote for yourself! (No cheating.) Thank you to [r/fuckipswitch](https://www.reddit.com/r/Discord_Bots/s/7QXdKdt5Mx) and [r/Silent_Department529](https://www.reddit.com/r/Discord_Bots/s/1Kj26gHGmg) for the idea!

The bot requires the `SEND MESSAGES`, `READ MESSAGE HISTORY`, and `ADD REACTIONS` permissions in the channel specified in `.env`

Several people can nominate one person, one person cannot nominate several people. 

The bot will recognize tied votes and no winner will be picked. Instead, it will announce a tie. The bot will subtract its reaction from the count when collecting votes. 

That's all. All you have to do is create the channel, specify the channel ID in `.env`, and use `/nominate` to start nominating users for member of the week!

# Commands

`/nominate user:` - Nominate a user for Member of the Week.

`/list_nominations` - List all nominations for Member of the Week.

`/clear_nominations` - Clear all nominations. (Admin only)

`/runpoll` - Manually run a poll for Member of the Week. (Admin only)

`/endpoll` - Manually end the poll and announce the winner. (Admin only)

# Dependencies

discord.py 2.5.0

python-dotenv 1.0.1

apscheduler 3.11.0

# Installation

Make sure you have Python 3.12+

Clone the repository.

```
git clone https://github.com/ifeeljoy/member-of-the-week.git
```

Install dependencies. 

```
pip install discord.py python-dotenv apscheduler
```

Rename `.env-example` to .env and add your bot token and channel ID.

```
# Your bot's token.
DISCORD_TOKEN=here

# The channel for creating the poll and announcing the winner.
DISCORD_CHANNEL_ID=here
```

Run the bot.

```
python index.py
```

# License
This project is licensed under the GNU General Public License v3.0. See the LICENSE file for more details.

# Donate
[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/mozzarella)

# Support
[Support server](https://discord.gg/kJ8eRH4kfe)
