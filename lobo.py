import discord
from discord.ext import commands
#from discord.ext.commands import MemberConvert

import random
import asyncio





description = '''A bot to play The Werewolves via private messages'''
command_prefix = '?'
bot = commands.Bot(command_prefix=command_prefix, description=description)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------------')

@bot.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == bot.user:
        return

    await bot.process_commands(message)


@bot.command(description='For rolling dices')
async def roll(dice : str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await bot.say('Format has to be NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await bot.say(result)


@bot.command(description='For when you wanna settle the score some other way')
async def choose(*choices : str):
    """Chooses between multiple choices."""
    await bot.say(random.choice(choices))


'''

CHARACTERS:
-THIEF: If the thief is played, two cards more than the number of players need to be played. After each player receives a card,
	the two cards are put in the center of the table. The thief can, if he/she/they want to, during the first night, exchange
	his cards with one of those cards that he will play until the end of the game. If the two cards are werewolf, the thief has
	to take one of the two werewolf cards, until the end of the game.
-CUPID: The first night, Cupid chooses 2 players and make them fall in love, then becomes a villager. 
	If one dies, the other dies too. A lover can't vote against the other lover. If the lovers are a villager and a werewolf,
	their objective changes; they must eliminate all the players except them.
-WEREWOLVES: Each night, the werewolves pick 1 player to kill.
-LITTLE GIRL: The little girl can secretly look at the werewolves during their turn. If she is caught in the act, she dies instead of the victim.
	(Not implemented since she would be hard to balance or implement in the way the game will be played in discord)
-WITCH: She has two potions: one to save the werewolves's victim, one to eliminate a player. She can only use each potion once during the game. 
-ORACLE: Each night, they can discover the real identity of a player. They must help the other villagers but discreetly to not be found by werewolves.
-HUNTER: If they are killed by werewolves or eliminated by vote, they must immediately kill another player of their choice.
-VILLAGERS: They don't have any special power except thinking and the right to vote.
-CAPTAIN: This card is given to a player besides their card. They are elected by a vote. This player's vote counts for two instead of one.
-IDIOT: If he is chosen by the village to be eliminated, he stays alive, but he cannot vote anymore.
-ANCIENT: He can resist the first werewolf's attack, but if he is killed by the witch, the huntsman, or the villagers, the villagers lose their powers.
-SCAPEGOAT: If the village can't agree about whom to eliminate, the scapegoat is eliminated. Nevertheless, he can decide about who can vote the next day.
-GUARD: Each night, he can protect a player from being attack by the werewolves. He can protect himself, but he can't protect the same player two consecutive nights.
-PIED PIPER: His objective is to charm all the players alive except him (he can't charm himself). Each night, he can charm two players that wake up 
and recognise with those of the nights before. IF all players are charmed he wins.

DISTRIBUTION:
-WEREWOLVES: 1 (<8), 2 (8-11), 3 (>11)
-VILLAGERS: same number as werewolves
-SPECIAL VILLAGERS: 1 of each.

ROUNDS:
The bot gives each player a role and procedes through the rounds on 2 stages: DAY and NIGHT.
	During DAY the last night's actions are revealed, everyone can talk to eachother and vote together someone to get killed.
	During NIGHT, each player enforces its role when asked by the bot.
DAY interactions with the bot are public. NIGHT intereactions are private via DM.

TURNS:
	1st Night Only
		-Thief
		-Cupid
		-Lovers
	Every night
		-Werewolves
		-Little Girl
		-Seer
		-Witch

GOALS:
the werewolves: their goal is to kill all the special villagers and all the normal villagers.
the villagers: their goal is to kill all the werewolves.

'''

@bot.command(description="Let's play The Werewolves of Millers Hollow", pass_context=True)
async def werewolves(ctx):

	# Checks if the user that triggered the command is in a voice channel,
	# in case it is, signs everyone else in that voice channel to the game
	if ctx.message.author.voice.voice_channel != None:
		await bot.say("Let's play: The Werewolves of Millers Hollow")
		members = ctx.message.author.voice.voice_channel.voice_members

	else:
		await bot.say("You must be in a voice channel with the rest of players to start the game")
		return

	# We need the number of werewolves per player, and the rest of characters in a list
	characters = ["THIEF",
				"CUPID",
				"WITCH",
				"ORACLE",
				"HUNTER",
				"IDIOT",
				"ANCIENT",
				"SCAPEGOAT",
				"GUARD",
				"PIED PIPER"]

	#add some villagers and shuffle the pile
	characters = ["VILLAGER" for i in range(max(1,len(members)/4))] + characters
	random.shuffle(characters)
	#make sure there's the needed number of werewolves
	characters = ["WEREWOLF" for i in range(max(1,len(members)/4))] + characters

	random.shuffle(members)

	players = {}
	for role, player in zip(characters, members):
		players.setdefault(role, []).append(player)


	await bot.say("    The roles have been assigned and will be notificated via DM")

	for role in players.keys():
		for player in players[role]:
			await sendDM(player, role)


	await asyncio.sleep(5)
	await bot.say("    Now that everyone knows their roles")
	
	await voteMayor(players)

	await bot.say("    The first election was so exhausting, you people wanted to go to sleep.")
	await night(players, True)




async def sendDM(user: discord.User,  msg: str):
	await bot.send_message(user, msg)


async def voteMayor(players):

	# reset the mayor
	if "MAYOR" in players.keys():
		del players["MAYOR"]

	await bot.say("    You shall vote the MAYOR.\nThe MAYOR's vote will count as 2 votes in case of a draw, until after the next voting")
	await bot.say("    To vote for a player, add an emoji/reaction to the message with it's name. A draw will result in no elections taken (you have 1 minute)")
	
	pool = []
	# we use a set in case players appear twice on the list (lovers, charmed,...)
	for player in {x for playerlist in players.values() for x in playerlist}:
		msg = await bot.say("    - "+player.mention)
		pool.append((msg.channel, msg.id))

	await asyncio.sleep(50)
	await bot.say("    10seconds left...")
	await asyncio.sleep(10)
	await bot.say("    OK, let's check the votes:")


	winner = ""
	maxVotes = 0
	for candidate in pool:
		candidate = await bot.get_message(candidate[0], candidate[1])
		if candidate.reactions:
			votes= sum(list(map(lambda x: x.count,candidate.reactions)))
			# beats the last best guy
			if votes > abs(maxVotes):
				maxVotes = votes
				winner = candidate.mentions[0]
			# ties best guy
			elif votes == abs(maxVotes):
				maxVotes = -votes


	# If there's a draw no one wins
	if maxVotes == 0 or maxVotes < 0:
		await bot.say("    You failed to elect a MAYOR, no one takes the role")

	# Else add the role to the role pool
	else:
		await bot.say("    The MAYOR is: "+winner.mention+". CONGRATULATIONS 🥳!")
		players["MAYOR"] = winner
	
# Any run a poll with all the players given, and returns a winner
async def poll(players, timeGiven):
	pass

async def night(players, first):

	if players["THIEF"] and first:
		# chooses from 2 roles that were left to pick (including 2 werewolves and 1 villager)
		characters = ["THIEF",
				"CUPID",
				"WITCH",
				"ORACLE",
				"HUNTER",
				"IDIOT",
				"ANCIENT",
				"SCAPEGOAT",
				"GUARD",
				"PIED PIPER",
				"WEREWOLF",
				"WEREWOLF",
				"VILLAGER"]
		random.shuffle(characters)
		options = [x for role in characters if role not in players.keys() or role == "WEREWOLF" or role == "VILLAGER"][:2]
		# send messages and collect response
		del players["THIEF"]

	if players["CUPID"] and first:
		# choose 2 people, then tell those 2 that they are lovers
		available = {x for playerlist in players.values() for x in playerlist}.discard(players["CUPID"][0])
		# send messages and collect response
		

	if players["WEREWOLF"] and not first:
		# vote who to kill via DMs
		available = {x for playerlist in players.values() for x in playerlist if x not in players["WEREWOLF"]}
		# send messages and collect response

	if players["WITCH"] and not first:
		# chooses to use life potion and/or death potion or none
		#maybe will have to make a subclass of discord.user that keeps track of potions in order for witch to work
		pass

	if players["ORACLE"] and not first:
		# chooses a player, to know it's identity (it's role) 
		available = {x for playerlist in players.values() for x in playerlist}.discard(players["ORACLE"][0])
		# send messages and collect response


	if players["GUARD"] and not first:
		# chooses someone, that player can't die this night
		guarded = players.setdefault("GUARDED",[])
		available = {x for playerlist in players.values() for x in playerlist if x not in guarded}.discard(players["GUARD"][0])
		# send messages and collect response

	if players["PIED PIPER"] and not first:
		# chooses 2 people that get charmed, they meet the other charmed people during that night 
		charmed = players.setdefault("CHARMED",[])
		available = {x for playerlist in players.values() for x in playerlist if x not in charmed}.discard(players["PIED PIPER"][0])
		# send messages and collect response




if __name__ == '__main__':

	bot.run(open('TOKEN').read().strip())