import lightbulb

import random

plugin = lightbulb.Plugin('Deck')

class Deck():
    def __init__(self) -> None:
        self.deck = [
        '1 ♥️', '1 ♠️', '1 ♣️', '1 ♦️', 
        '2 ♥️', '2 ♠️', '2 ♣️', '2 ♦️', 
        '3 ♥️', '3 ♠️', '3 ♣️', '3 ♦️', 
        '4 ♥️', '4 ♠️', '4 ♣️', '4 ♦️', 
        '5 ♥️', '5 ♠️', '5 ♣️', '5 ♦️',
        '6 ♥️', '6 ♠️', '6 ♣️', '6 ♦️',
        '7 ♥️', '7 ♠️', '7 ♣️', '7 ♦️',
        '8 ♥️', '8 ♠️', '8 ♣️', '8 ♦️',
        '9 ♥️', '9 ♠️', '9 ♣️', '9 ♦️',
        '10 ♥️', '10 ♠️', '10 ♣️', '10 ♦️',
        'J ♥️', 'J ♠️', 'J ♣️', 'J ♦️',
        'Q ♥️', 'Q ♠️', 'Q ♣️', 'Q ♦️',
        'K ♥️', 'K ♠️', 'K ♣️', 'K ♦️'
        ]
    
    def get_deck(self):
        return self.deck
    
    def get_card(self):
        card = self.deck[random.randint(0,len(self.deck)-1)]
        return card

    def get_card_str(card):
        string = ''.join(card.split(' '))
        return string

    def remove_card(self, card):
        self.deck.remove(card)
        return self.deck
    
    def reset_deck(self):
        self.deck = [
        '1 ♥️', '1 ♠️', '1 ♣️', '1 ♦️', 
        '2 ♥️', '2 ♠️', '2 ♣️', '2 ♦️', 
        '3 ♥️', '3 ♠️', '3 ♣️', '3 ♦️', 
        '4 ♥️', '4 ♠️', '4 ♣️', '4 ♦️', 
        '5 ♥️', '5 ♠️', '5 ♣️', '5 ♦️',
        '6 ♥️', '6 ♠️', '6 ♣️', '6 ♦️',
        '7 ♥️', '7 ♠️', '7 ♣️', '7 ♦️',
        '8 ♥️', '8 ♠️', '8 ♣️', '8 ♦️',
        '9 ♥️', '9 ♠️', '9 ♣️', '9 ♦️',
        '10 ♥️', '10 ♠️', '10 ♣️', '10 ♦️',
        'J ♥️', 'J ♠️', 'J ♣️', 'J ♦️',
        'Q ♥️', 'Q ♠️', 'Q ♣️', 'Q ♦️',
        'K ♥️', 'K ♠️', 'K ♣️', 'K ♦️'
        ]

## Add as a plugin ##

def load(bot):
    bot.add_plugin(plugin)