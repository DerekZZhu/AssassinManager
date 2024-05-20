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

    print(dead)
    if ctx.message.author.id in dead:
        await ctx.send("You are dead. You're not allowed to report...")
        return
    
    mentioned_users = [user.mention for user in ctx.message.mentions]
    
    if mentioned_users:
        reported_user = mentioned_users[0]
    else:
        await ctx.send("Please mention a user in the report.")
        return

    report_message = f"Report received:\n" \
                     f"Time: {report_time}\n" \
                     f"Reporter: {reporter}\n" \
                     f"Reported User: {reported_user}\n" \
                     f"Details: {arg}"

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
    
    supabase.table('Players').insert({"id": user_id, "name": username, "kills":0, "quote":""}).execute()
    await ctx.send(f"User {username} with ID {user_id} has been registered.")


@client.command()
async def test(ctx, arg):
    await ctx.send(arg)


client.run(auth_token)
