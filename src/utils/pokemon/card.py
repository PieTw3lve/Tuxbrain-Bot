import hikari

from bot import get_setting

class PokemonCard:
    def __init__(self, user: hikari.User, card_id, date, name, pokemon_id, rarity, shiny=False):
        self.user = user
        self.card_id = card_id
        self.name = name
        self.date = date
        self.pokemon_id = pokemon_id
        self.rarity = rarity
        self.shiny = shiny

    def display(self, pages: list) -> list:
        if self.shiny:
            rarity_symbol = '🌟'
        else:
            rarity_symbol = '⭐'
        
        embed = hikari.Embed(title=f'{self.name} Card' if not self.shiny else f'Shiny {self.name} Card', color=get_setting('general', 'embed_color'))
        embed.set_image(f'https://img.pokemondb.net/sprites/home/normal/{self.name.lower()}.png' if not self.shiny else f'https://img.pokemondb.net/sprites/home/shiny/{self.name.lower()}.png')
        # embed.set_image(f'https://raw.githubusercontent.com/harshit23897/Pokemon-Sprites/master/assets/imagesHQ/{"{:03d}".format(pokemon_id)}.png') # If you want 2d sprites. This does not support shiny sprites.
        embed.add_field(name='Pokémon Name', value=self.name, inline=True)
        embed.add_field(name='Card Quality', value=" ".join([rarity_symbol for i in range(self.rarity)]), inline=True)
        embed.add_field(name='Card ID', value=f'`{self.card_id}`', inline=False)
        embed.set_footer('Type `/packinventory view` to view your cards and packs.')
        
        pages.append(embed)
        return pages
    
    def display_overview(self, embed: hikari.Embed) -> hikari.Embed:
        if self.shiny:
            name_symbol = '**'
            rarity_symbol = '🌟'
        else:
            name_symbol = ''
            rarity_symbol = '⭐'

        if len(embed.fields) == 0:
            embed.add_field(name='Pokémon Name', value=f'• {name_symbol}{self.name}{name_symbol}', inline=True)
            embed.add_field(name='Card Quality', value=" ".join([rarity_symbol for i in range(self.rarity)]), inline=True)
            embed.add_field(name='Card ID', value=f'{self.card_id}', inline=True)
        else:
            embed.edit_field(0, embed.fields[0].name, f'{embed.fields[0].value}\n• {name_symbol}{self.name}{name_symbol}')
            embed.edit_field(1, embed.fields[1].name, f'{embed.fields[1].value}\n{" ".join([rarity_symbol for i in range(self.rarity)])}')
            embed.edit_field(2, embed.fields[2].name, f'{embed.fields[2].value}\n{self.card_id}')
        
        return embed