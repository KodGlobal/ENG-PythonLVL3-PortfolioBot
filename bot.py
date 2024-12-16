import discord
from discord.ext import commands
from logic import DB_Manager
from config import DATABASE, TOKEN

intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)
manager = DB_Manager(DATABASE)

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')

@bot.command(name='start')
async def start_command(ctx):
    await ctx.send("Hi! I'm a project manager bot\nI'll help you store your projects and all the information about them! =)")
    await info(ctx)

@bot.command(name='info')
async def info(ctx):
    await ctx.send("""
Here are the commands you can use:

!new_project - add a new project
!projects - list all your projects
!update_projects - update project data
!skills - connect skills with a specific project
!delete - remove a project

You can also type in the name of the project to check out all the info about it!""")

@bot.command(name='new_project')
async def new_project(ctx):
    await ctx.send("Please enter the project's name")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    name = await bot.wait_for('message', check=check)
    data = [ctx.author.id, name.content]
    await ctx.send("Please send a link to the project")
    link = await bot.wait_for('message', check=check)
    data.append(link.content)

    statuses = [x[0] for x in manager.get_statuses()]
    await ctx.send("Please enter the current status of the project", delete_after=60.0)
    await ctx.send("\n".join(statuses), delete_after=60.0)
    
    status = await bot.wait_for('message', check=check)
    if status.content not in statuses:
        await ctx.send("The status you've selected is not on the list. Please try again!)", delete_after=60.0)
        return

    status_id = manager.get_status_id(status.content)
    data.append(status_id)
    manager.insert_project([tuple(data)])
    await ctx.send("The project has been saved")

@bot.command(name='projects')
async def get_projects(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"Project name: {x[2]} \nLink: {x[4]}\n" for x in projects])
        await ctx.send(text)
    else:
        await ctx.send('You do not have any projects yet!\nConsider adding one with the !new_project command? ')

@bot.command(name='skills')
async def skills(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        await ctx.send('Please select a project you would like to connect a skill to')
        await ctx.send("\n".join(projects))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        project_name = await bot.wait_for('message', check=check)
        if project_name.content not in projects:
            await ctx.send('You do not have  this project, please try again! Please select a project you would like to connect a skill to')
            return

        skills = [x[1] for x in manager.get_skills()]
        await ctx.send('Select a skill')
        await ctx.send("\n".join(skills))

        skill = await bot.wait_for('message', check=check)
        if skill.content not in skills:
            await ctx.send('Looks like the skiill you provided is not on the list! Please try again! Select a skill')
            return

        manager.insert_skill(user_id, project_name.content, skill.content)
        await ctx.send(f'The skill {skill.content} has been connected to the project {project_name.content}')
    else:
        await ctx.send('You do not have any projects yet!\nConsider adding one with the !new_project command?')

@bot.command(name='delete')
async def delete_project(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        await ctx.send("Select a project you would like to delete")
        await ctx.send("\n".join(projects))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        project_name = await bot.wait_for('message', check=check)
        if project_name.content not in projects:
            await ctx.send('You do not have  this project, please try again!')
            return

        project_id = manager.get_project_id(project_name.content, user_id)
        manager.delete_project(user_id, project_id)
        await ctx.send(f'The project {project_name.content} has been removed from the database!')
    else:
        await ctx.send('You do not have any projects yet!\nConsider adding one with the !new_project command?')

@bot.command(name='update_projects')
async def update_projects(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        await ctx.send("Please select a project you would like to update")
        await ctx.send("\n".join(projects))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        project_name = await bot.wait_for('message', check=check)
        if project_name.content not in projects:
            await ctx.send("Something went wrong! Please choose the project you would like to change again:")
            return

        await ctx.send("What would you like to change about the project?")
        attributes = {'Project name': 'project_name', 'Description': 'description', 'Link to project': 'url', 'Project status': 'status_id'}
        await ctx.send("\n".join(attributes.keys()))

        attribute = await bot.wait_for('message', check=check)
        if attribute.content not in attributes:
            await ctx.send("Oops, an error! Please try again!")
            return

        if attribute.content == 'Status':
            statuses = manager.get_statuses()
            await ctx.send("Please select a new status for your project")
            await ctx.send("\n".join([x[0] for x in statuses]))
            update_info = await bot.wait_for('message', check=check)
            if update_info.content not in [x[0] for x in statuses]:
                await ctx.send("Incorrect status selected, please try again!")
                return
            update_info = manager.get_status_id(update_info.content)
        else:
            await ctx.send(f"Enter a new attribute for {attribute.content}")
            update_info = await bot.wait_for('message', check=check)
            update_info = update_info.content

        manager.update_projects(attributes[attribute.content], (update_info, project_name.content, user_id))
        await ctx.send("All done! The project has been updated!")
    else:
        await ctx.send('You do not have any projects yet!\nConsider adding one with the !new_project command?')

bot.run(TOKEN)
