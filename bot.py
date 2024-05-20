import discord
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
    check_reports.start()


@client.command()
async def report(ctx, *, arg):
    report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    reporter = ctx.message.author.name

    if ctx.message.author.id in dead:
        await ctx.send("Ur dead 💀. How do u expect to kill? Wait until respawn")
        return
    
    mentioned_users = [user.mention for user in ctx.message.mentions]

    if ctx.message.mentions[0].id == ctx.message.author.id:
        await ctx.send("You cannot report yourself.")
        return
    
    if ctx.message.mentions[0].id in dead:
        await ctx.send("That user is currently dead. Stop trolling.")
        return

    if mentioned_users:
        reported_user = mentioned_users[0]
    else:
        await ctx.send("Please mention a user in the report.")
        return

    report_message = f"Report received:\n" \
                     f"Time: {report_time}\n" \
                     f"Reporter: {reporter}\n" \
                     f"Reported User: {reported_user}\n" \
                     #f"Details: {arg}"

    reports.append({"time": report_time, "victim":reported_user, "victim_id": ctx.message.mentions[0].id})
    dead.add(ctx.message.mentions[0].id)
    print(reports)
    await ctx.send(report_message)


@tasks.loop(minutes=1)
async def check_reports():
    current_time = datetime.now()
    print("Checking Reports")
    for report in reports[:]:
        report_time = datetime.strptime(report["time"], '%Y-%m-%d %H:%M:%S')
        if current_time >= report_time + timedelta(minutes=5):
            victim_id = report["victim_id"]
            user = await client.fetch_user(victim_id)
            await user.send("It has been 5 minutes since your death. You have respawned.")
            reports.remove(report)



@client.command()
async def register(ctx):
    user_id = ctx.message.author.id
    username = ctx.message.author.name
    
    try:
        supabase.table('Players').insert({"id": user_id, "name": username, "kills":0, "deaths":0, "title":""}).execute()
        await ctx.send(f"User {username} with ID {user_id} has been registered.")
        
    except:
        await ctx.send(f"You are already registered! Type !profile to check your profile")
    


@client.command()
async def test(ctx, arg):
    await ctx.send(arg)



@client.command()
async def profile(ctx, user: discord.User = None):
    mentioned_users = ctx.message.mentions
    if mentioned_users:
        user = mentioned_users[0]
    else:
        user = ctx.message.author

    user_id = user.id
    response = supabase.table('Players').select('*').eq('id', str(user_id)).execute()
    
    if not response.data:
        await ctx.send("User statistics not found or user is not registered.")
        return
    
    user_data = response.data[0]
    # print(user_data)
    u_img = user.avatar.url if user_data["image"] == None else user_data["image"]
    embed = discord.Embed(title="User Profile", color=0x00ff00)
    embed.set_thumbnail(url=u_img)
    embed.add_field(name="Name", value=user_data.get("name", "Unknown"))
    embed.add_field(name="Number of Kills", value=user_data.get("kills", "0"))
    embed.add_field(name="Number of Deaths", value=user_data.get("deaths", "0"))
    embed.add_field(name="Title", value=user_data.get("title", "Unassigned"))
    embed.set_footer(text=f"Requested by {ctx.message.author.name}")
    await ctx.send(embed=embed)

client.run(auth_token)
