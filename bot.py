import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Button, View
from SECRET import client_secret, auth_token, sb_url, sb_secret_key
from supabase import create_client, Client
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True

supabase: Client = create_client(sb_url, sb_secret_key)
client = commands.Bot(command_prefix="!", intents=intents)

reports = []
dead = {"test"}

@client.event
async def on_ready():
    print(f'Bot is ready. Logged in as {client.user}')
    await client.tree.sync()
    check_reports.start()


@client.tree.command(name="report")
@app_commands.describe(user="The user to report")
async def report(interaction: discord.Interaction, user: discord.User):
    report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    reporter = interaction.user.name

    if interaction.user.id in dead:
        await interaction.response.send_message("Ur dead 💀. How do u expect to kill? Wait until respawn", ephemeral=True)
        return

    if user.id == interaction.user.id:
        await interaction.response.send_message("You cannot report yourself.", ephemeral=True)
        return

    if user.id in dead:
        await interaction.response.send_message("That user is currently dead. Stop trolling.", ephemeral=True)
        return

    details = interaction.data.get("options", [])
    details_str = " ".join([str(option["value"]) for option in details if option["type"] == 3])  # type 3 is string

    report_message = f"Report received:\n" \
                     f"Time: {report_time}\n" \
                     f"Reporter: {reporter}\n" \
                     f"Reported User: {user.mention}\n" \
                     f"Details: {details_str}"

    reports.append({"time": report_time, "victim": user.mention, "victim_id": user.id})
    dead.add(user.id)
    print(reports)

    # Get killer and victim data
    victim_response = supabase.table('Players').select('*').eq('id', str(user.id)).execute()
    killer_response = supabase.table('Players').select('*').eq('id', str(interaction.user.id)).execute()
    
    if not victim_response.data or not killer_response.data:
        await interaction.response.send_message("Either you are not registered or the reported user doesn't exist.", ephemeral=True)
        return
    
    victim_data = victim_response.data[0]
    killer_data = killer_response.data[0]

    victim_killstreak = victim_data.get("killstreak", 0)
    victim_deaths = victim_data.get("deaths", 0)
    killer_killstreak = killer_data.get("killstreak", 0)
    killer_points = killer_data.get("points", 0)
    killer_kills = killer_data.get("kills", 0)

    # Update killer and victim stats
    killer_new_points = killer_points + max(killer_killstreak + 2, 5) + (victim_killstreak + 2 if victim_killstreak >= 2 else 0)
    supabase.table('Player').update(
        {'deaths': victim_deaths + 1, 'killstreak': 0}
    ).eq('id', str(user.id)).execute()
    supabase.table('Player').update(
        {'kills': killer_kills + 1, 'killstreak': killer_killstreak + 1, 'points': killer_new_points}
    ).eq('id', str(interaction.user.id)).execute()

    await interaction.response.send_message(report_message)


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
            dead.remove(victim_id)


@client.tree.command(name="register")
@app_commands.describe(team_name="The name of the team", agent_name="The name of the agent")
async def register(interaction: discord.Interaction, team_name: str, agent_name: str):
    user_id = interaction.user.id
    username = interaction.user.name

    team_id = 0
    if team_name.lower() == "framework":
        team_id = 1
    elif team_name.lower() == "database":
        team_id = 2
    elif team_name.lower() == "ml":
        team_id = 3
    else:
        await interaction.response.send_message("Team doesn't exist. The valid teams are 'Framework', 'Database', and 'ML'. Try again?", ephemeral=True)
        return 

    try:
        supabase.table('Players').insert({
            "id": user_id,
            "name": username,
            "kills": 0,
            "deaths": 0,
            "killstreak": 0,
            "title": {agent_name},
            "points": 0,
            "team": team_id,
            "streak": 0
        }).execute()
        await interaction.response.send_message(f"Registered {username} as **{agent_name}** on team **{team_name}** (ID: {team_id})")
    except:
        await interaction.response.send_message(f"You are already registered! Type !profile to check your profile", ephemeral=True)

# @client.command()
# async def test(ctx, arg):
#     await ctx.send(arg)


@client.tree.command(name="profile")
@app_commands.describe(user="The user to view the profile of")
async def profile(interaction: discord.Interaction, user: discord.User = None):
    if user is None:
        user = interaction.user

    user_id = user.id
    response = supabase.table('Players').select('*').eq('id', str(user_id)).execute()
    
    if not response.data:
        await interaction.response.send_message("User statistics not found or user is not registered.", ephemeral=True)
        return
    
    user_data = response.data[0]

    team = ""
    if user_data['team'] == 1:
        team = "Framework"
        color = 0xF39C12
    elif user_data['team'] == 2:
        team = "Database"
        color = 0xF1C40F
    elif user_data['team'] == 3:
        team = "ML"
        color = 0x27AE60

    u_img = user.avatar.url if user_data["image"] == None else user_data["image"]
    embed = discord.Embed(title="User Profile", color=color)
    embed.set_thumbnail(url=u_img)
    embed.add_field(name="Name", value=user_data.get("name", "Unknown"))
    embed.add_field(name="Number of Kills", value=user_data.get("kills", "0"))
    embed.add_field(name="Number of Deaths", value=user_data.get("deaths", "0"))
    embed.add_field(name="Current Killstreak", value=user_data.get("killstreak", "0"))
    embed.add_field(name="Title", value=user_data.get("title", "Unassigned"))
    embed.add_field(name="Points", value=user_data.get("points", "0"))
    embed.add_field(name="Team", value=team)
    embed.set_footer(text=f"Requested by {interaction.user.name}")
    await interaction.response.send_message(embed=embed)



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
        embed.add_field(name=f"{idx+1}. {player['name']}", value=f"Kills: {player['kills']} | Points: {player['points']}", inline=False)
    return embed

@client.tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction):
    response = supabase.table('Players').select('*').execute()
    data = response.data if response.data else []
    view = LeaderboardView(data)
    embed = create_leaderboard_embed(data)
    await interaction.response.send_message(embed=embed, view=view)


client.run(auth_token)
