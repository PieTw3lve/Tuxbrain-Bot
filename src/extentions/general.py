import hikari
import lightbulb
import miru
import sqlite3

from datetime import datetime
from typing import Optional
from io import BytesIO
from miru.abc.item import ViewItem
from miru.context import ViewContext
from miru.context.view import ViewContext
from miru.ext import nav
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageEnhance
from miru.ext.nav.items import NavButton
from miru.select.text import SelectOption
from bot import VERSION, get_setting, get_commands, verify_user
from .economy import remove_money, remove_ticket
from .pokemon import NavPageInfo

plugin = lightbulb.Plugin('General')

## Add Profile Cosmetics ##

# @plugin.listener(hikari.MemberUpdateEvent) 
# async def role(event: hikari.MemberUpdateEvent):
#     old = sorted((await event.old_member.fetch_roles())[1:], key=lambda role: role.position, reverse=True)
#     new = sorted((await event.member.fetch_roles())[1:], key=lambda role: role.position, reverse=True)
#     modified = abs(len(old) - len(new))
    
#     if modified > 0:
#         inventory = Inventory(event.member)
#         added = [item for item in new if item not in old]
#         removed = [item for item in old if item not in new]

#         rushsiteS1ID = str(get_setting('roles', 'rushsite_s1_id'))
#         rushsiteS2ID = str(get_setting('roles', 'rushsite_s2_id'))
#         rushsiteS3ID = str(get_setting('roles', 'rushsite_s3_id'))
#         rushsiteS4ID = str(get_setting('roles', 'rushsite_s4_id'))
#         rushsiteS5ID = str(get_setting('roles', 'rushsite_s5_id'))

#         items = {
#             rushsiteS1ID: ('rushsite_s1', 'banner'),
#             rushsiteS2ID: ('rushsite_s2', 'banner'),
#             rushsiteS3ID: ('rushsite_s3', 'banner'),
#             rushsiteS4ID: ('rushsite_s4', 'banner'),
#             rushsiteS5ID: ('rushsite_s5', 'banner'),
#         }

#         for role in added + removed:  # Combine added and removed roles into one loop
#             role_id = str(role.id)
#             item_info = items.get(role_id)

#             if item_info:
#                 user_id = event.user.id
#                 if role in added:
#                     inventory.add_item((user_id, *item_info, '0'))
#                 else:
#                     inventory.remove_item((user_id, *item_info))

## Help Command ##

class InfoView(miru.View):
    def __init__(self, commands: dict) -> None:
        super().__init__(timeout=None)
        self.commands = commands
    
    @miru.text_select(
        custom_id='info_select',
        placeholder='Choose a category',
        options=[
            miru.SelectOption(label='About', emoji='💬', value='About', description='More info about Tuxbrain Bot.'),
            miru.SelectOption(label='Invite Bot', emoji='🤖', value='Invite', description='How do I invite Tuxbrain Bot to my server?'),
            miru.SelectOption(label='General Commands', emoji='📝', value='General', description='Explore an array of versatile and essential commands.'),
            miru.SelectOption(label='Economy Commands', emoji='💰', value='Economy', description='Strategize, amass wealth, become the richest.'),
            miru.SelectOption(label='Pokémon Commands', emoji='<:standard_booster_pack:1073771426324156428>', value='Pokemon', description='Embark on a journey of collecting and trading Pokémon.'),
            miru.SelectOption(label='Fun Commands', emoji='🎲', value='Fun', description='Play fun interactive games with users.'),
        ]
    )
    async def select_menu(self, select: miru.TextSelect, ctx: miru.Context) -> None:
        option = select.values[0]
        hide = ['rushsite-admin']
        commands = []
        description = []
        
        embed = hikari.Embed(color=get_setting('settings', 'embed_color'))   
        match option:
            case 'About':
                author = await ctx.bot.rest.fetch_user('291001658362560513')
                embed.title = '💬 About'
                embed.description = f'Tuxbrain Bot is an [open source](https://github.com/PieTw3lve/Tux_Bot), multi-use Discord bot written in [hikari.py](https://www.hikari-py.dev/), a new static-typed Python API wrapper. It is programmed by <@{author.id}> to serve as the official Tuxbrain.org Discord bot. The bot is currently still in development, so there may be some bugs. Although it was designed for Tuxbrain.org servers, the bot can be hosted and used on any server.\n\nIf any bugs are encountered, please submit them on [Github](https://github.com/PieTw3lve/Tuxbrain-Bot/issues).'
                embed.set_thumbnail(author.avatar_url)
                return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            case 'Invite':
                embed.title = '🤖 Invite Bot'
                embed.description = 'Tuxbrain Bot is not currently available for direct invite to personal servers, but can be hosted locally by downloading from [Github](https://github.com/PieTw3lve/Tux_Bot). Instructions for hosting Tuxbrain Bot can be found on the GitHub repository.'
                return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            case 'General':
                embed.title = '📝 General Commands'
                sections = ['General', 'Music', 'Rushsite', 'Admin']
            case 'Economy':
                embed.title = '💰 Economy Commands'
                sections = ['Economy']
            case 'Pokemon':
                embed.title = '<:standard_booster_pack:1073771426324156428> Pokémon Commands'
                sections = ['Pokemon']
            case 'Fun':
                embed.title = '🎲 Fun Commands'
                sections = ['Fun']

        for section in sections:
            for cmd, desc in self.commands[section]:
                if cmd not in hide:
                    commands.append(f'• {cmd.capitalize()}')
                    description.append(f'{desc}')
        
        embed.add_field('Commands', '\n'.join(commands) if len(commands) > 0 else 'None', inline=True)
        embed.add_field('Description', '\n'.join(description) if len(description) > 0 else 'None', inline=True)
        embed.set_footer('Some commands have subcommands or aliases.')
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
    async def view_check(self, context: miru.Context) -> bool:
        return True

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('help', 'Displays the help menu.')
@lightbulb.implements(lightbulb.SlashCommand)
async def help(ctx: lightbulb.Context) -> None:
    bot = await ctx.bot.rest.fetch_user('1045533498481577984')
    view = InfoView(get_commands(plugin.bot))
    
    embed = (hikari.Embed(title=f'Tuxbrain Bot  `v{VERSION}`', description='I am a simple and humble bot that can do really cool things!', color=get_setting('settings', 'embed_color'))
        .set_thumbnail(bot.avatar_url)
        .add_field('I have various cool features:', '• Economy Integration\n• Customizable Music Player\n• Pokémon Gacha\n• Easier Moderation\n• Fun Interactive Games\n• And Many More!', inline=True)
        .add_field('Want to learn more about Tuxbrain Bot?', 'Click on 💬 **About** to learn more about Tuxbrain Bot! \n\nSpecial thanks to **Ryan#3388** and **BoboTheChimp#6164** for helping!', inline=True)
        .set_footer('Use the select menu below for more info!')
    )
    
    message = await ctx.respond(embed, components=view.build())

    await view.start(message)

## Ping Command ##

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('ping', "Displays bot's latency.")
@lightbulb.implements(lightbulb.SlashCommand)
async def ping(ctx: lightbulb.Context) -> None:
    embed = (hikari.Embed(title='Pong!', description=f'{round(ctx.bot.heartbeat_latency * 1000)}ms 📶', color=get_setting('settings', 'embed_color')))
    await ctx.respond(embed)

## Profile Subcommand ##

class Inventory():
    def __init__(self, user: hikari.Member) -> None:
        self.db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        self.cursor = self.db.cursor()
        self.user = user
    
    def get_inventory(self, type: str):
        self.cursor.execute("SELECT * FROM profile WHERE user_id=? AND type=? ORDER BY name ASC;", (self.user.id, type))
        items = self.cursor.fetchall()
        return items
    
    def get_profile_item(self, item: str):
        self.cursor.execute("SELECT * FROM profile WHERE user_id=? AND name=? AND type=?", (self.user.id, item[0].lower(), item[1].lower()))
        item = self.cursor.fetchall()

        if not item:
            return False
        else:
            return True

    def get_active_customs(self):
        self.cursor.execute("SELECT name, type FROM profile WHERE user_id=? AND active=? ORDER BY type ASC;", (self.user.id, 1))
        items = self.cursor.fetchall()

        # Define the types to check for
        typeList = ['banner', 'base', 'nametag']
        
        # Initialize a dictionary to keep track of the types found
        typeFound = {t: False for t in typeList}
        
        # Iterate through the input list and update the dictionary
        for item in items:
            if item[1] in typeList:
                typeFound[item[1]] = True
        
        # Create a list of tuples with missing types added as 'default'
        result = [(item[0], item[1]) for item in items]
        result.extend([('default', t) for t in typeList if not typeFound[t]])
        
        # Convert the result list to the desired format
        results = tuple(f'{result[i][0]}-{result[i][1]}' for i in range(3))
        return results
    
    def get_pages(self, items: list, maxItems: int):
        pages = []
        for i in range(0, len(items), maxItems):
            embed = hikari.Embed(title="Profile Customization Shop", description='Welcome to our Profile Customization Shop, where you can transform your online presence and make a lasting impression. Our extensive menu offers a wide range of options to personalize and enhance your profile to truly reflect your unique style and personality.', color=get_setting('settings', 'embed_color'))
            end = i + maxItems
            for option in items[i:end]:
                currency, name, price = option
                strName = str(name).replace('_', ' ').title().split('-')
                strCurrency = '🪙' if currency == 'coin' else '🎟️'
                owned = '\✔️' if self.get_profile_item(str(name).split('-')) else '\❌'
                if len(embed.fields) == 0:
                    embed.add_field(name='Profile Item', value=f'{strName[0]} ({strName[1].lower()})', inline=True)
                    embed.add_field(name='Price', value=f'{strCurrency} {price:,}', inline=True)
                    embed.add_field(name='Purchased', value=f'{owned}', inline=True)
                else:
                    embed.edit_field(0, embed.fields[0].name, f'{embed.fields[0].value}\n{strName[0]} ({strName[1].lower()})')
                    embed.edit_field(1, embed.fields[1].name, f'{embed.fields[1].value}\n{strCurrency} {price:,}')
                    embed.edit_field(2, embed.fields[2].name, f'{embed.fields[2].value}\n{owned}')
            pages.append(embed)
        return pages
    
    def add_item(self, item: tuple):
        try:
            self.cursor.execute('INSERT INTO profile (user_id, name, type, active) VALUES (?, ?, ?, ?)', item)
            self.db.commit()
        except sqlite3.Error as e:
            self.db.rollback()
            print("Error inserting item from the database:", e)
    
    def remove_item(self, item: tuple):
        try:
            self.cursor.execute('DELETE FROM profile WHERE user_id=? AND name=? AND type=?', item)
            self.db.commit()
        except sqlite3.Error as e:
            self.db.rollback()
            print("Error deleting item from the database:", e)
    
class ProfileCard():
    def __init__(self, user: hikari.Member) -> None:
        self.db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        self.user = user

    async def draw_card(self, bg: Image, card: Image, nametag: Image, font: ImageFont = ImageFont.truetype('assets/font/UDDIGIKYOKASHON-B.TTC', size=92), subfont: ImageFont = ImageFont.truetype('assets/font/NTAILUB.TTF', size=48)):
        name = self.user.display_name[:14] if len(self.user.display_name) > 14 else self.user.display_name
        userID = str(self.user.id)

        created_at = datetime.fromtimestamp(int(self.user.created_at.timestamp()))
        created_year = self.get_year_difference(created_at)

        joined_at = datetime.fromtimestamp(int(self.user.joined_at.timestamp()))
        join_year = self.get_year_difference(joined_at)

        roles = (await self.user.fetch_roles())[1:]  # All but @everyone
        roles = sorted(roles, key=lambda role: role.position, reverse=True)  # sort them by position, then reverse the order to go from top role down
        role = f'@{roles[0].name}' if roles else ''
        color = roles[0].color.rgb if roles else None

        cursor = self.db.cursor()
        cursor.execute(f'SELECT balance, tpass FROM economy WHERE user_id = {self.user.id}')
        bal = cursor.fetchone() 
        
        try: # just in case for errors
            balance = bal[0]
            tpass = bal[1]
        except:
            balance = 0
            tpass = 0

        draw = ImageDraw.Draw(card)

        card.paste(bg, (0, 0), bg) # Background
        card.paste(nametag, (0, 0), nametag) # Nametag
        
        if any(role in self.user.role_ids for role in [get_setting('roles', 'owner_role_id'), get_setting('roles', 'admin_role_id'), get_setting('roles', 'staff_role_id')]):
            badge = Image.open('assets/img/general/profile/admin_badge/badge.png')
            card.paste(badge, (0, 0), badge) # Admin Badge
        
        try:
            pfp = self.circle(Image.open(BytesIO(await self.user.avatar_url.read())).convert('RGBA'), (432, 432))
            card.paste(pfp, (119, 327), pfp) # Profile Picture
        except AttributeError:
            pass
        
        draw.text((581, 499), name, font=font) # Name
        draw.text((109, 932), userID, font=subfont, fill=(171, 171, 171)) # User ID
        draw.text((778, 932), role, font=subfont, fill=color) # Top Role
        draw.text((109, 1177), f'{balance:,}', font=subfont, fill=(171, 171, 171)) # Coins
        draw.text((778, 1177), f'{tpass:,}', font=subfont, fill=(171, 171, 171)) # Tux Pass
        draw.text((109, 1429), created_at.strftime( "%m/%d/%Y %H:%M:%S" ), font=subfont, fill=(171, 171, 171)) # Creation Date
        draw.text((109, 1512 ), created_year, font=subfont, fill=(171, 171, 171)) # Creation Date Calculation
        draw.text((778, 1429), joined_at.strftime( "%m/%d/%Y %H:%M:%S" ), font=subfont, fill=(171, 171, 171)) # Join Date
        draw.text((778, 1512 ), join_year, font=subfont, fill=(171, 171, 171)) # Join Date Calculation

        with BytesIO() as a:
            card.save(a, 'PNG')
            a.seek(0)
            return a.getvalue()

    def get_year_difference(self, date: datetime):
        current = datetime.now()
        difference = current - date
        years = difference.days // 365
        months = (difference.days % 365) // 30  # Assuming an average of 30 days per month
        
        return f'({years} Years {months} Months)' if years > 1 else f'({months} Months)'

    def circle(self, pfp: Image, size: tuple):
        pfp = pfp.resize(size).convert("RGBA")
        
        bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
        mask = Image.new('L', bigsize, 0)
        draw = ImageDraw.Draw(mask) 
        draw.ellipse((0, 0) + bigsize, fill=255)
        mask = mask.resize(pfp.size)
        mask = ImageChops.darker(mask, pfp.split()[-1])
        pfp.putalpha(mask)
        return pfp

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('profile', "Customize or view user's profiles.", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def profile(ctx: lightbulb.Context) -> None:
    return

## Profile Command ##

@profile.child
@lightbulb.option('user', 'The user to get information about.', hikari.User, required=False)
@lightbulb.command('view', 'Get info on a server member.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def view(ctx: lightbulb.Context, user: Optional[hikari.Member] = None) -> None:
    user = user or ctx.member
    
    if not user:
        embed = hikari.Embed(description='That user is not in the server.', color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed)
        return
    
    inventory = Inventory(user)
    profile = ProfileCard(user)

    bg, card, nametag = inventory.get_active_customs()
    bg = Image.open(f'assets/img/general/profile/banner/{bg}.png').convert('RGBA')
    card = Image.open(f'assets/img/general/profile/base/{card}.png').convert('RGBA')
    nametag = Image.open(f'assets/img/general/profile/nametag/{nametag}.png').convert('RGBA')

    await ctx.respond(attachment=await profile.draw_card(bg, card, nametag))

## Profile Customize Command ##

class ProfileCustomizeView(miru.View):
    def __init__(self, inventory: Inventory, profile: ProfileCard, newPreset: list) -> None:
        super().__init__(timeout=None, autodefer=True)
        self.db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        self.cursor = self.db.cursor()
        self.inventory = inventory
        self.profile = profile
        self.newPreset = newPreset

    @miru.button(label='Save', emoji='🖨️', style=hikari.ButtonStyle.SUCCESS, row=1)
    async def save(self, button: miru.Button, ctx: miru.ViewContext):
        self.cursor.execute('UPDATE profile SET active = 0 WHERE user_id = ?', (ctx.user.id,))
        for item in self.newPreset:
            name, type = str(item).split('-')
            self.cursor.execute('UPDATE profile SET active = 1 WHERE user_id = ? AND name = ? AND type = ?', (ctx.user.id, name, type))
        self.db.commit()

        embed = hikari.Embed(description='Profile has been saved!', color=get_setting('settings', 'embed_success_color'))
        await ctx.edit_response(components=[])
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        self.stop()
    
    @miru.button(label='Cancel', emoji='✖️', style=hikari.ButtonStyle.DANGER, row=1)
    async def cancel(self, button: miru.Button, ctx: miru.ViewContext):
        await ctx.edit_response(components=[])
        self.stop()
    
    @miru.button(label='Preview', emoji='🔍', style=hikari.ButtonStyle.PRIMARY, row=1)
    async def preview(self, button: miru.Button, ctx: miru.ViewContext):
        bg = Image.open(f'assets/img/general/profile/banner/{self.newPreset[0]}.png').convert('RGBA')
        card = Image.open(f'assets/img/general/profile/base/{self.newPreset[1]}.png').convert('RGBA')
        nametag = Image.open(f'assets/img/general/profile/nametag/{self.newPreset[2]}.png').convert('RGBA')
        
        embed = hikari.Embed(title=f'Customization Preview', color=get_setting('settings', 'embed_color'))
        embed.set_image(await self.profile.draw_card(bg, card, nametag))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

    async def view_check(self, ctx: ViewContext) -> bool:
        return ctx.user.id == self.inventory.user.id

@profile.child
@lightbulb.option('nametag', 'The nametag is a label that users can customize to reflect their individual identity.', type=str, autocomplete=True, required=True)
@lightbulb.option('base', 'The base section is where users make fundamental changes to their profile.', type=str, autocomplete=True, required=True)
@lightbulb.option('banner', 'The banner is the top section of the profile and often serves as a visually appealing header.', type=str, autocomplete=True, required=True)
@lightbulb.command('set', 'Customize your profile!', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def set(ctx: lightbulb.Context, banner: str, base: str, nametag: str) -> None:
    inventory = Inventory(ctx.member)
    profile = ProfileCard(ctx.member)
    
    oldPreset = inventory.get_active_customs()
    activePreset = [banner, base, nametag]
    
    view = ProfileCustomizeView(inventory, profile, activePreset)
    
    for item in activePreset:
        strItem = item.split('-')
        if len(strItem) != 2:
            embed = hikari.Embed(description=f'This is not a valid item!', color=(get_setting('settings', 'embed_error_color')))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        elif strItem[0] != 'default' and inventory.get_profile_item(strItem) == False:
            embed = hikari.Embed(description=f'You do not own this {strItem[1]}!', color=(get_setting('settings', 'embed_error_color')))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    
    oldPreset = [f'- {item.title().replace("_", " ").split("-")[0]} ({item.split("-")[1]})' for i, item in enumerate(oldPreset)]
    activePreset = [f'- {item.title().replace("_", " ").split("-")[0]} ({item.split("-")[1]})' for i, item in enumerate(activePreset)]
    
    embed = (hikari.Embed(title='Are you sure you want to make changes?', color=get_setting('settings', 'embed_color'))
        .add_field('Old Profile', '\n'.join(oldPreset), inline=True)
        .add_field('New Profile', '\n'.join(activePreset), inline=True)
        .set_footer(text='This action cannot be undone.')
    )

    message = await ctx.respond(embed, components=view.build(), flags=hikari.MessageFlag.EPHEMERAL)
    await view.start(message)

@set.autocomplete('banner', 'base', 'nametag')
async def search_autocomplete(opt: hikari.AutocompleteInteractionOption, ctx: hikari.AutocompleteInteraction):
    inventory = Inventory(ctx.member)
    items = inventory.get_inventory(opt.name)
    items = [(None, 'default', opt.name, '0')] + items
    if len(opt.value) > 0:
        filtered_matches = [hikari.impl.AutocompleteChoiceBuilder(str(item[1]).replace('_', ' ').title(), f'{item[1]}-{item[2]}') for item in items if str(item[1]).lower().startswith(opt.value.lower())]
        return filtered_matches[:10]
    else:
        return [hikari.impl.AutocompleteChoiceBuilder(str(item[1]).replace('_', ' ').title(), f'{item[1]}-{item[2]}') for item in items][:10]

## Profile Shop Command ##

class ProfileShopSelect(miru.SelectOption):
    def __init__(self, item: tuple) -> None:
        super().__init__(label=item[0], description='Click To View', value=item[1])

class NavShopSelectView(nav.NavTextSelect):
    def __init__(self, inventory:Inventory, items: list, maxItems: int, row: int) -> None:
        self.inventory = inventory
        self.items = items
        self.maxItems = maxItems
        self.options = [ProfileShopSelect(item) for item in self.get_items(0)]
        
        super().__init__(
            placeholder='Select a Item',
            options=self.options,
            row=row,
        )
    
    async def callback(self, ctx: ViewContext) -> None:
        if self.inventory.user.id != ctx.user.id:
            return
        
        profile = ProfileCard(plugin.bot.cache.get_member(ctx.get_guild(), ctx.user))
        selected = self.values[0]
        name = selected.replace('_', ' ').title().split('-')
        
        if self.inventory.get_profile_item(selected.split('-')) == False:
            bg, card, nametag = self.inventory.get_active_customs()
            bg = Image.open(f'assets/img/general/profile/banner/{bg}.png').convert('RGBA')
            card = Image.open(f'assets/img/general/profile/base/{card}.png').convert('RGBA')
            nametag = Image.open(f'assets/img/general/profile/nametag/{nametag}.png').convert('RGBA')
            
            match selected.split('-')[1]:
                case 'banner':
                    bg = Image.open(f'assets/img/general/profile/banner/{selected}.png').convert('RGBA')
                case 'base':
                    card = Image.open(f'assets/img/general/profile/base/{selected}.png').convert('RGBA')
                case 'nametag':
                    nametag = Image.open(f'assets/img/general/profile/nametag/{selected}.png').convert('RGBA')
            
            embed = hikari.Embed(title=f'Do you want to purchase {name[0]} ({name[1]})?', description="This little maneuver's gonna cost you 51 years.", color=get_setting('settings', 'embed_color'))
            image = await profile.draw_card(bg, card, nametag)
            embed.set_image(image)
            embed.set_footer(text='This action cannot be undone.')
            view = ProfilConfirmView(self.inventory, image, self.items, selected)
            message = await ctx.respond(embed, components=view.build(), flags=hikari.MessageFlag.EPHEMERAL)
            await view.start(message)
        else:
            embed = hikari.Embed(description='You already own this item!', color=get_setting('settings', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

    async def before_page_change(self) -> None:
        self.options = [ProfileShopSelect(item) for item in self.get_items(self.view.current_page)]
    
    def get_items(self, index: int):
        pages = []
        for i in range(0, len(self.items), self.maxItems):
            end = i + self.maxItems
            page = []
            for option in self.items[i:end]:
                currency, name, price = option
                strName = str(name).replace('_', ' ').capitalize().split('-')
                strName = f'{strName[0].title()} ({strName[1]})'
                page.append((strName, name))
            pages.append(page)
        return pages[index]

class ProfilConfirmView(miru.View):
    def __init__(self, inventory: Inventory, image: bytes, items: list, selected: str) -> None:
        super().__init__(timeout=None, autodefer=True)
        self.inventory = inventory
        self.image = image
        self.items = items
        self.selected = selected
    
    @miru.button(label='Yes', style=hikari.ButtonStyle.SUCCESS, row=1)
    async def yes(self, button: miru.Button, ctx: miru.ViewContext):
        currency, name, price = [item for item in self.items if item[1] == self.selected][0]
        
        if verify_user(ctx.user) == None: # if user has never been register
            embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('settings', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        elif currency == 'coin' and remove_money(ctx.user.id, price, True) == False: # checks if user has enough money
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('settings', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        elif currency == 'tpass' and remove_ticket(ctx.user.id, price) == False: # checks if user has enough tickets
            embed = hikari.Embed(description='You do not have enough tickets!', color=get_setting('settings', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        self.inventory.add_item((ctx.user.id, name.split("-")[0], name.split("-")[1], 0))

        embed = hikari.Embed(title='Thank you for your purchase!', color=get_setting('settings', 'embed_success_color'))
        embed.set_image(self.image)
        await ctx.respond(embed)
    
    @miru.button(label='No', style=hikari.ButtonStyle.DANGER, row=1)
    async def no(self, button: miru.Button, ctx: miru.ViewContext): 
        await ctx.edit_response(components=[])
        self.stop()

class ChecksView(nav.NavigatorView):
    def __init__(self, inventory: Inventory, pages, buttons, timeout, autodefer: bool = True) -> None:
        super().__init__(pages=pages, buttons=buttons, timeout=timeout, autodefer=autodefer)
        self.inventory = inventory

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.inventory.user.id

@profile.child
@lightbulb.command('shop', 'Spend coins or tux passes on profile customization.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def customize(ctx: lightbulb.Context) -> None:
    inventory = Inventory(ctx.member)
    profiles = get_setting('profile')
    coinItems = []
    tpassItems = []

    # Iterate through 'coin' and add tuples to result
    for item, price in profiles['coin'].items():
        coinItems.append(('coin', item, price))
    coinItems.sort(key=lambda x: x[2], reverse=True)

    # Iterate through 'tpass' and add tuples to result
    for item, price in profiles['tpass'].items():
        tpassItems.append(('tpass', item, price))
    tpassItems.sort(key=lambda x: x[2], reverse=True)

    items =  coinItems + tpassItems

    pages = inventory.get_pages(items, 10)
    buttons = [NavShopSelectView(inventory, items, 10, row=1), nav.PrevButton(emoji='⬅️', row=2), NavPageInfo(len(pages), row=2), nav.NextButton(emoji='➡️', row=2)]
    navigator = ChecksView(inventory, pages, buttons, timeout=None)

    await navigator.send(ctx.interaction)

## Definitions ##

def load(bot):
    bot.add_plugin(plugin)