import hikari
import sqlite3

from datetime import datetime
from io import BytesIO
from PIL import Image, ImageChops, ImageDraw, ImageFont

from bot import get_setting

class Card():
    def __init__(self, user: hikari.Member, app: hikari.Application) -> None:
        self.db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        self.user = user
        self.app = app

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
        
        if self.user.id == self.app.owner.id:
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