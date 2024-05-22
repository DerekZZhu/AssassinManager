import discord
from discord import app_commands
from discord.ext import commands, tasks
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
        await interaction.response.send_message("Team doesn't exist. Try again?", ephemeral=True)
        return 

    try:
        supabase.table('Players').insert({"id": user_id, "name": username, "kills":0, "deaths":0, "title":"", "points":0, "team":team_id, "streak":0}).execute()
        await interaction.response.send_message(f"Registered {username} as **{agent_name}** on team **{team_name}** (ID: {team_id})")
    except:
        await interaction.response.send_message(f"You are already registered! Type !profile to check your profile", ephemeral=True)

@client.command()
async def test(ctx, arg):
    await ctx.send(arg)


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
    u_img = user.avatar.url if user_data["image"] == None else user_data["image"]
    embed = discord.Embed(title="User Profile", color=0x00ff00)
    embed.set_thumbnail(url=u_img)
    embed.add_field(name="Name", value=user_data.get("name", "Unknown"))
    embed.add_field(name="Number of Kills", value=user_data.get("kills", "0"))
    embed.add_field(name="Number of Deaths", value=user_data.get("deaths", "0"))
    embed.add_field(name="Title", value=user_data.get("title", "Unassigned"))
    embed.set_footer(text=f"Requested by {interaction.user.name}")
    await interaction.response.send_message(embed=embed)


client.run(auth_token)
