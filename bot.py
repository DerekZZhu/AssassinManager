import discord
from discord.ext import commands, tasks
from SECRET import client_secret, auth_token, sb_url, sb_secret_key
from discord.ui import Button, View
from supabase import create_client, Client
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True

supabase: Client = create_client(sb_url, sb_secret_key)
client = commands.Bot(command_prefix="!", intents=intents)

reports = []
dead_players = {"test"}  # Assuming 'test' is a username or ID
response = supabase.table('Reports').select("*").execute()
for report in response.data:
    print(report)
    reports.append({"time": report["time"], "victim_id": report["id"]})
    dead_players.add(report["id"])

@client.event
async def on_ready():
    print(f'Bot is ready. Logged in as {client.user}')

    
    check_reports.start()


@client.command()
async def register(ctx, team_name: str, agent_name: str):
    print("Register called")
    user_id = ctx.message.author.id
    username = ctx.message.author.name
    
    team_id = 0
    if team_name.lower() == "framework":
        team_id = 1
    elif team_name.lower() == "database":
        team_id = 2
    elif team_name.lower() == "ml":
        team_id = 3
    else:
        await ctx.send("Team doesn't exist. The valid teams are 'Framework', 'Database', and 'ML'. Try again?")
        return 
    
    existing_user = supabase.table('Players').select('*').eq('id', str(user_id)).execute()
    if existing_user.data:
        await ctx.send("You are already registered! Type !profile to check your profile.")
        return

    data, count = supabase.table('Players').insert({
            "id": user_id,
            "name": username,
            "kills": 0,
            "deaths": 0,
            "killstreak": 0,
            "title": agent_name,
            "points": 0,
            "team": team_id,
            "streak": 0
    }).execute()
    print(data)
    await ctx.send(f"Registered {username} as **{agent_name}** on team **{team_name}** (ID: {team_id})")


@register.error
async def register_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Error: You need to provide both team_name and agent_name arguments. Usage: `!register <team_name> <agent_name>`")

@client.command()
async def report(ctx, *, arg):
    print("Report fired")
    report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(type(report_time))
    reporter = ctx.message.author.name

    if ctx.message.author.id in dead_players:
        await ctx.send("You're dead 💀. How do you expect to report? Wait until respawn.")
        return
    
    if not ctx.message.mentions:
        await ctx.send("Please mention a user in the report.")
        return

    mentioned_user = ctx.message.mentions[0]
    if mentioned_user.id == ctx.message.author.id:
        await ctx.send("You cannot report yourself.")
        return
    
    if mentioned_user.id in dead_players:
        await ctx.send("That user is currently dead. Stop trolling.")
        return

    report_message = f"Report received:\n" \
                     f"Time: {report_time}\n" \
                     f"Killed by: {reporter}\n" \
                     f"Killed: {mentioned_user.mention}"

    reports.append({"time": report_time, "victim_id": mentioned_user.id})
    dead_players.add(mentioned_user.id)
    print(reports)

    victim_response = supabase.table('Players').select('*').eq('id', mentioned_user.id).execute()
    killer_response = supabase.table('Players').select('*').eq('id', ctx.message.author.id).execute()

    if not victim_response.data or not killer_response.data:
        await ctx.send("Either you are not registered or the reported user doesn't exist.", ephemeral=True)
        return
    victim_data = victim_response.data[0]
    killer_data = killer_response.data[0]

    #print(victim_data)
    #print(killer_data)

    victim_killstreak = victim_data.get("killstreak", 0)
    victim_deaths = victim_data.get("deaths", 0)
    killer_killstreak = killer_data.get("killstreak", 0)
    killer_points = killer_data.get("points", 0)
    killer_kills = killer_data.get("kills", 0)   

    #print(killer_kills)

    killer_new_points = killer_points + min(killer_killstreak + 2, 5) + (victim_killstreak + 2 if victim_killstreak >= 2 else 0)
    #print(killer_points)
    victim_deaths += 1
    supabase.table('Players').update({'deaths': victim_deaths, 'killstreak': 0}).eq('id', mentioned_user.id).execute()
    killer_kills += 1
    killer_killstreak += 1
    supabase.table('Players').update({'kills': killer_kills, 'killstreak': killer_killstreak, 'points': killer_new_points}).eq('id', ctx.message.author.id).execute()

    supabase.table('Reports').insert({'id': mentioned_user.id, 'time':report_time}).execute()
    await ctx.send(report_message)


@tasks.loop(minutes=1)
async def check_reports():
    current_time = datetime.now()
    print("Checking Reports")
    for report in reports[:]:
        report_time = datetime.strptime(report["time"], '%Y-%m-%d %H:%M:%S')
        if current_time >= report_time + timedelta(hours=1):
            victim_id = report["victim_id"]
            user = await client.fetch_user(victim_id)
            await user.send("It has been 1 hour since your death. You have respawned.")
            reports.remove(report)

            try:
                supabase.table('Reports').delete().eq('id', victim_id).execute()
                print("report successfully deleted")
            except:
                pass

            dead_players.remove(victim_id)



@client.command()
async def dead(ctx):
    print("Checking dead")
    embed = discord.Embed(title="Dead Users", color=0xFF0000)
    current_time = datetime.now()

    for report in reports[:]:
        victim_id = report['victim_id']
        report_time = datetime.strptime(report['time'], '%Y-%m-%d %H:%M:%S')
        time_left = (report_time + timedelta(hours=1)) - current_time
        
        if time_left.total_seconds() > 0:
            user = await client.fetch_user(victim_id)
            respawn_time = report_time + timedelta(hours=1)
            time_left_str = str(time_left).split('.')[0]
            embed.add_field(name=f"{user.name}", value=f"Respawn Time: <t:{int(respawn_time.timestamp())}:R> (Time left: {time_left_str})", inline=False)


    await ctx.send(embed=embed)


@client.command()
async def man(ctx):
    embed = discord.Embed(title="Command List", color=0x00ff00)
    embed.add_field(name="!register <team_name> <agent_name>", value="Register for the game", inline=False)
    embed.add_field(name="!report <player>", value="Make a report of a killing", inline=False)
    embed.add_field(name="!dead", value="Get a list of all dead players", inline=False)
    embed.add_field(name="!profile", value="Get your player profile", inline=False)
    embed.add_field(name="!leaderboard", value="Get the leaderboard", inline=False)
    embed.add_field(name="!tip", value="[ONLY USABLE IN DM] Anonymously tip", inline=False)
    embed.add_field(name="Have fun!", value="Enjoy the game!", inline=False)
    await ctx.send(embed=embed)
    
@client.command()
async def rules(ctx, *, arg):
    await ctx.send(arg)


@client.command()
async def profile(ctx, user: discord.User = None):
    user = user or ctx.message.author

    user_id = user.id
    response = supabase.table('Players').select('*').eq('id', str(user_id)).execute()
    
    if not response.data:
        await ctx.send("User statistics not found or user is not registered.")
        return
    
    user_data = response.data[0]

    team = ""
    color = 0x000000  # Default color
    if user_data['team'] == 1:
        team = "Framework"
        color = 0xF39C12
    elif user_data['team'] == 2:
        team = "Database"
        color = 0xF1C40F
    elif user_data['team'] == 3:
        team = "ML"
        color = 0x27AE60

    u_img = user.avatar.url if user.avatar else None
    embed = discord.Embed(title="User Profile", color=color)
    embed.set_thumbnail(url=u_img)
    embed.add_field(name="Name", value=user_data.get("name", "Unknown"))
    embed.add_field(name="Number of Kills", value=user_data.get("kills", "0"))
    embed.add_field(name="Number of Deaths", value=user_data.get("deaths", "0"))
    embed.add_field(name="Current Killstreak", value=user_data.get("killstreak", "0"))
    embed.add_field(name="Title", value=user_data.get("title", "Unassigned"))
    embed.add_field(name="Points", value=user_data.get("points", "0"))
    embed.add_field(name="Team", value=team)
    embed.set_footer(text=f"Requested by {ctx.author.name}")
    await ctx.send(embed=embed)


class LeaderboardView(View):
    def __init__(self, data):
        super().__init__()
        self.data = data

    @discord.ui.button(label="Kills", style=discord.ButtonStyle.primary, custom_id="sort_kills")
    async def sort_kills(self, interaction: discord.Interaction, button: Button):
        self.data.sort(key=lambda x: x['kills'], reverse=True)
        embed = create_leaderboard_embed(self.data)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Points", style=discord.ButtonStyle.primary, custom_id="sort_points")
    async def sort_points(self, interaction: discord.Interaction, button: Button):
        self.data.sort(key=lambda x: x['points'], reverse=True)
        embed = create_leaderboard_embed(self.data)
        await interaction.response.edit_message(embed=embed, view=self)

def create_leaderboard_embed(data):
    embed = discord.Embed(title="Leaderboard", color=0x00ff00)
    for idx, player in enumerate(data):
        embed.add_field(name=f"{idx+1}. {player['name']}", value=f"Kills: {player['kills']} | Deaths: {player['deaths']} | Points: {player['points']}", inline=False)
    return embed

@client.command(name="leaderboard")
async def leaderboard(ctx):
    response = supabase.table('Players').select('*').order('points', desc=True).execute()
    data = response.data if response.data else []
    view = LeaderboardView(data)
    embed = create_leaderboard_embed(data)
    await ctx.send(embed=embed, view=view)


@client.command()
async def tip(ctx, *, message: str):
    if isinstance(ctx.channel, discord.DMChannel):
        print(client.guilds)
        guild = discord.utils.get(client.guilds)
        
        channel = guild.get_channel(1234954914946486412)
        if channel:
            await channel.send(f"An anonymous source reports:\n{message}")
            await ctx.send("Your message has been sent to the server.")
        else:
            await ctx.send("Could not find the specified channel in the server.")
    else:
        await ctx.send("This command can only be used in DMs.")


target_user_id = 660714139026587651
@client.event
async def on_message(message):
    if message.author.id == target_user_id:
        await message.reply(f'你妈妈')
    await client.process_commands(message)

client.run(auth_token)
