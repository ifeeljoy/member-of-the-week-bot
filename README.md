[![IMG-3230.jpg](https://i.postimg.cc/hGz726nS/IMG-3230.jpg)](https://postimg.cc/SX4ssZj5)

[![IMG-3231.jpg](https://i.postimg.cc/xTHRj6Fp/IMG-3231.jpg)](https://postimg.cc/zVzW0FNT)

[![IMG-3232.jpg](https://i.postimg.cc/h404FnK2/IMG-3232.jpg)](https://postimg.cc/8sjgWqJv)

# About

A Discord bot for managing nominations and voting for a member of the week. The bot will create a poll every Friday at 12:00 AM UTC, and announce the winner the following Sunday at 6:00 PM UTC. Each member is limited to one vote, and you can't vote for yourself! (No cheating.) Thank you to [r/fuckipswitch](https://www.reddit.com/r/Discord_Bots/s/7QXdKdt5Mx) and [r/Silent_Department529](https://www.reddit.com/r/Discord_Bots/s/1Kj26gHGmg) for the idea!

# Dependencies

discord.py 2.5.0

python-dotenv 1.0.1

apscheduler 3.11.0

# Installation

Make sure you have Python 3.12+

Clone the repository.

```
git clone https://github.com/ifeeljoy/member-of-the-week-bot
```

Install dependencies. 

```
pip install discord.py python-dotenv apscheduler
```

Rename `.env-example` to .env and add your bot token and channel ID.

```
# Your bot's token.
DISCORD_TOKEN=here
# The channel creating the poll and announcing the winner.
DISCORD_CHANNEL_ID=here
```

Run the bot.

```
python index.py
```

# License
This project is licensed under the GNU General Public License v3.0. See the LICENSE file for more details.

# Buy Me A Coffee
[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/mozzarella)

# Support
[Support server](https://discord.gg/kJ8eRH4kfe)