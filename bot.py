from time import sleep
import discord
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from discord.ext import commands
import logging
import requests
import json
logging.basicConfig(format='%(asctime)s : %(message)s', datefmt='%m/%d/%Y %H:%M:%S', filename='logs.txt', encoding='utf-8')

settings = json.loads(open("settings.json").read())
#chargement des settings

prefix = settings["prefix"]
famille_name = settings["famille"]
token = settings["TOKEN"]

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(settings["credentials"], scope)
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/"+settings["id_googlesheet"]).sheet1
activity = discord.Activity(type=discord.ActivityType.watching, name=settings["activite"])
bot = commands.Bot(command_prefix = prefix, description = famille_name, help_command=None, activity=activity, status=discord.Status.do_not_disturb)

def getdoc():
    response = requests.get("https://opensheet.elk.sh/"+settings["id_googlesheet"]+"/"+settings["name_sheetpage"])
    return(json.loads(response.content.decode('utf-8')))

async def logs(message):
    if bot.user.id == 772169233869176844:
        return
    logchannel = bot.get_channel(settings["logs_channel"])
    embedinfo = discord.Embed(title = message, colour=discord.Color.from_rgb(57, 111, 255), timestamp = datetime.datetime.now())
    embedinfo.set_thumbnail(url= settings["logo_famille"])
    await logchannel.send(embed = embedinfo)
    print(message)
    logging.warning(message)

def now():
    now = datetime.datetime.now()
    return(now.day, now.hour, now.minute)

#command
@bot.command()
async def info(message, *params):
    if len(params)==0:
        await message.channel.send(content="Merci de renseigner un joueur")
        return
    for elt in getdoc():
        if str(" ".join(params)).lower() in elt["nom"].lower():
            if elt["nom de code"]!='/':
                embedtitle= "**["+ elt["nom de code"]+ "] "+ elt["nom"]+ "**"
            else:
                embedtitle= "**"+elt["nom"]+"**"
            discordplayer = "<@", elt["discordid"], ">"
            discordplayer = "".join(discordplayer)
            embedinfo = discord.Embed(title = embedtitle, colour=discord.Color.from_rgb(57, 111, 255))
            embedinfo.set_thumbnail(url=settings["logo_famille"])
            embedinfo.add_field(name="WitheList", value=elt['whitelist'], inline=False)
            embedinfo.add_field(name="Grade", value=elt['grade'], inline=False)
            embedinfo.add_field(name="Playtime", value=elt['Playtime'], inline=False)
            embedinfo.add_field(name="SteamID", value=elt['steamid'], inline=True)
            embedinfo.add_field(name="Discord", value=discordplayer, inline=True)
            embedinfo.add_field(name="Armes", value=elt['armes'], inline=False)
            embedinfo.add_field(name="Sanctions", value=elt['averto'], inline=True)
            if elt["Dernier UP"]!='/':
                embedinfo.add_field(name="Dernier UP", value=elt['Dernier UP'], inline=True)
            await logs(message.author.display_name+ "a demandé les infos de "+ elt['nom'])
            await message.channel.send(embed = embedinfo)
            return
    await message.channel.send(content="Joueur Introuvable")

@bot.command()
async def map(ctx):
    embed = discord.Embed(title="", timestamp=datetime.datetime.now(), colour=discord.Color.random(), description="Violet : Cambriolable\nJaune : Pas touche")
    embed.set_image(url="https://zupimages.net/up/21/52/zlis.png")
    await ctx.channel.send(embed=embed)


aidejoeur = """
{prefix}jeu - permet de commencer à jouer
{prefix}deco - permet d'arrêter de jouer
{prefix}info [pseudonyme] - voir ses informations où d'un autre joueur 
""".format(prefix=prefix)
utilitaire="""
{prefix}map - voir la map des zones cambriolables
{prefix}help - affiche ceci
{prefix}lzco - affiche les {famille_name} connectés
{prefix}playtime - affiche tous les playtimes de tous les joueur
{prefix}lyg - affiche le nombre de joueurs connecté 
""".format(prefix=prefix, famille_name=famille_name)
staff= """
Rien
"""


@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Page d'aide de {famille_name}".format(famille_name=famille_name), timestamp=datetime.datetime.now(), colour=discord.Color.random())
    embed.add_field(name="Section {famille_name}".format(famille_name=famille_name), value=aidejoeur, inline=False)
    embed.add_field(name="Section Utilitaire", value=utilitaire, inline=False)
    if ctx.author.guild_permissions.administrator:
        embed.add_field(name="Section Leader", value=staff, inline=False)
    await ctx.channel.send(embed=embed)

@bot.command()
async def lzco(ctx):
    message = await ctx.channel.send("Recherche en cours...")
    lz=[]
    for row in range(1, sheet.row_count+1):
        rowlist = list(sheet.row_values(row))
        if "TRUE" in rowlist[10]:
            lz.append((rowlist[0], (rowlist[11].split(";"))))
    string = []
    for elt in range(0, len(lz)):
        string.append(lz[elt][0]+ " est connecté depuis "+ lz[elt][1][1]+"h"+lz[elt][1][2])
    embed = discord.Embed(title="Voici les Joueurs connectés en {famille_name} :".format(famille_name=famille_name), colour=discord.Color.random(), timestamp=datetime.datetime.now(), description="\n".join(string))
    embed.set_thumbnail(url= settings["logo_famille"])
    embed.set_author(name=ctx.author.display_name,icon_url=ctx.author.avatar_url)
    await message.edit(content=None, embed=embed)
    await logs(ctx.author.display_name + " à fait {prefix}lzco".format(prefix=prefix))

@bot.command()
async def jeu(ctx):
    try:
        channelad = ctx.message.author.voice.channel.name
    except:
        channelad = None
    if channelad==None:
        message = await ctx.channel.send("Vous devez être dans un canal Escouade pour faire ceci !")
        await ctx.message.add_reaction("❌")
        sleep(5)
        await message.delete()
        await ctx.message.delete()
        return
    elif not "Escouade" in channelad:
        message = await ctx.channel.send("Vous devez être dans un canal Escouade pour faire ceci !")
        await ctx.message.add_reaction("❌")
        sleep(5)
        await message.delete()
        await ctx.message.delete()
        return
    for row in range(1, sheet.row_count+1):
        rowlist = list(sheet.row_values(row))
        if str(rowlist[7]) == str(ctx.author.id):
            if "FALSE" in rowlist[10]:
                sheet.update_cell(row, 11, "TRUE")
                sheet.update_cell(row, 12, str(now()[0]) +";"+ str(now()[1]) +";"+ str(now()[2]))
                embed = discord.Embed(title="Bon Jeu à toi dans {famille_name} !".format(famille_name=famille_name), timestamp=datetime.datetime.now(), colour=discord.Color.green())
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
                await ctx.author.send(embed=embed)
                await logs("début de jeu pour "+ctx.author.display_name+" à "+str(datetime.datetime.now()))
                await ctx.message.add_reaction("✅")
            else:
                await ctx.channel.send("Vous êtes déja en jeu !")
                await ctx.message.add_reaction("❌")
            break

@bot.command()
async def deco(ctx):
    for row in range(1, sheet.row_count+1):
        rowlist = list(sheet.row_values(row))
        if str(rowlist[7]) == str(ctx.author.id):
            if "TRUE" in rowlist[10]:
                oldtime = rowlist[11].split(";")
                newtime = now()
                day = newtime[0] - int(oldtime[0])
                hour = newtime[1] - int(oldtime[1])
                min = newtime[2] - int(oldtime[2])
                pt = min + hour*60 + day*1440
                oldpt = int(rowlist[9])
                newpt = oldpt+pt
                sheet.update_cell(row, 10, newpt)
                sheet.update_cell(row, 11, "FALSE")
                embed = discord.Embed(title="Merci d'avoir joué !", timestamp=datetime.datetime.now(), colour=discord.Color.dark_gold())
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
                embed.add_field(name="Nouveau Playtime", value=str(pt), inline=True)
                embed.add_field(name="Playtime Total", value=str(newpt), inline=True)
                await ctx.author.send(embed=embed)
                await logs("fin de playtime pour "+ctx.author.display_name+" à "+str(datetime.datetime.now()))
                await ctx.message.add_reaction("✅")
            else:
                await ctx.channel.send("Vous n'êtes pas en jeu !")
                await ctx.message.add_reaction("❌")
            break

@bot.command()
async def playtime(ctx):
    liste = []
    for row in getdoc():
        liste.append((row["nom"], int(row["Playtime"])))
    liste.sort(key = lambda x: x[1], reverse=True)
    if len(liste) < 3:
        await ctx.channel.send("il n'y a pas assez de membres dans votre famille")
        return
    embed = discord.Embed(title="Playtimes de la semaine :", timestamp=datetime.datetime.now(), colour=discord.Color.random())
    embed.set_thumbnail(url=settings["logo_famille"])
    embed.add_field(name=":first_place: - "+liste[0][0], value="A réalisé " + str(liste[0][1])+" minutes de playtime", inline=False)
    embed.add_field(name=":second_place: - "+liste[1][0], value="A réalisé " + str(liste[1][1])+" minutes de playtime", inline=False)
    embed.add_field(name=":third_place: - "+liste[2][0], value="A réalisé " + str(liste[2][1])+" minutes de playtime", inline=False)
    for elements in range(3, len(liste)):
        if int(liste[elements][1]) > 100:
            embed.add_field(name=":medal: - "+liste[elements][0], value="A réalisé " + str(liste[elements][1])+" minutes de playtime", inline=False)
        else:
            embed.add_field(name=":warning: - "+liste[elements][0], value="A réalisé " + str(liste[elements][1])+" minutes de playtime", inline=False)
    await ctx.channel.send(embed=embed)
    await logs("Tous les playtimes on été demandés par "+  ctx.author.display_name)

@bot.command()
async def lyg(ctx):
    response = requests.get("https://gmod-servers.com/api/?object=servers&element=detail&key=HQxNp0ydJncvbuYdY0XwY1toVWPMg1FniQH")
    lyg = json.loads(response.content.decode('utf-8'))
    embed = discord.Embed(timestamp=datetime.datetime.now(),description="Il y a actuelement **"+ str(lyg["players"])+"/85** joueurs connectées sur LYG#4 (Cliquez [ici](https://metrics.lyg.fr/d/1REiJKcGk/) pour plus de détails)" , title="Serveur 4 de LiveYourGame", url="https://lyg.fr/gmod4",colour=discord.Color.from_rgb(255, 120, 0), )
    url="https://liveyourgame.fr/forum/styles/lyg/logo_700.png"
    embed.set_thumbnail(url=url)
    embed.set_footer(text=ctx.author.display_name,icon_url=ctx.author.avatar_url)
    await ctx.channel.send(embed=embed)

@bot.event
async def on_ready():
    print("Bot is ready!")
    logging.warning("Bot started")

bot.run(token)
