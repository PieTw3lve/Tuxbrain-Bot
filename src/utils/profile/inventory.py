import hikari
import sqlite3

from bot import get_setting

class Inventory():
    def __init__(self, user: hikari.Member) -> None:
        self.db = sqlite3.connect(get_setting('general', 'database_data_dir'))
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
            embed = hikari.Embed(title="Profile Customization Shop", description='Welcome to our Profile Customization Shop, where you can transform your online presence and make a lasting impression. Our extensive menu offers a wide range of options to personalize and enhance your profile to truly reflect your unique style and personality.', color=get_setting('general', 'embed_color'))
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