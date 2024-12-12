import json

VERSION = '1.4.3'

def get_setting_json():
    bot = {
        'version': VERSION, # DO NOT CHANGE
        'token': '', # BOT TOKEN (REQUIRED)
        'owner_id': [], # BOT OWNER IDS (REQUIRED)
        'test_guild_id': [], # APPLICATION COMMAND ENABLED GUILDS (OPTIONAL)
        'wordnik_api_key': '', # WORDNIK API KEY (OPTIONAL)
    }
    general = {
        'database_data_dir': 'database/database.sqlite',
        'command_cooldown': 5,
        'embed_color': '#249EDB',
        'embed_important_color': 'b03f58',
        'embed_success_color': '#32CD32',
        'embed_error_color': '#FF0000',
        'auto_translate_conf': 0.80,
        'auto_translate_min_relative_distance': 0.90,
    }
    economy = {
        'starting_balance': 300,
        'starting_tux_pass': 0,
        'daily_max_streak': 30,
    }
    profile = {
        'coin': {
            'gray-banner': 200,
            'float-nametag': 200,
            'separator-nametag': 200,
            'tuxedo-nametag': 200,
            'apple-base': 500,
            'burgundy-base': 500,
            'blueberry-base': 500,
            'grape-base': 500,
            'snow-base': 1000,
            'snow-nametag': 1000,
            'plastic-banner': 1000,
            'plastic-base': 1000,
            'plastic-nametag': 1000,
            'blue-banner': 2000,
            'orange-banner': 2000,
            'grassiant-banner': 5000,
            'sky-banner': 5000,
            'purp-banner': 5000,
            'purp-base': 5000,
            'purp-nametag': 5000,
            'charged_rose-banner': 5000,
            'rushsite_s3-banner': 7000,
            'france-banner': 10000,
            'usa-banner': 10000,
        },
        'tpass': {
            'nippuwu-banner': 1,
        }
    }
    fishing = {
        'salvage_rate_min': 0.7,
        'salvage_rate_max': 1.3,
        'weather': {
            '1': {
                'name': 'Sunny',
                'emoji': '☀️',
                'description': 'Today will be bright and sunny with clear skies and comfortable temperatures. Great conditions for fishing!',
                'weight': 200,
                'success_rate_bonus': 0,
                'quantity_bonus': 0,
                'rarity_bonus': 0,
            },
            '2': {
                'name': 'Light Winds',
                'emoji': '🍃',
                'description': 'Expect light winds with clear skies today. Pleasant weather that’s ideal for fishing.',
                'weight': 20,
                'success_rate_bonus': 0.1,
                'quantity_bonus': 0,
                'rarity_bonus': 0,
            },
            '3': {
                'name': 'Cloudy',
                'emoji': '☁️',
                'description': 'Today\’s forecast includes light cloud cover with no rain. Good conditions for fishing are expected.',
                'weight': 20,
                'success_rate_bonus': 0,
                'quantity_bonus': 0,
                'rarity_bonus': 0.1,
            },
            '4': {
                'name': 'Rainy',
                'emoji': '🌧️',
                'description': 'Light rain showers are on the horizon today. Fish are likely to be more active, making it a promising day for fishing.',
                'weight': 20,
                'success_rate_bonus': 0,
                'quantity_bonus': 0.1,
                'rarity_bonus': 0,
            },
            '5': {
                'name': 'Overcast',
                'emoji': '☁️',
                'description': 'Expect thick cloud cover throughout the day with no rain. Favorable conditions for a successful fishing trip.',
                'weight': 15,
                'success_rate_bonus': 0.2,
                'quantity_bonus': 0,
                'rarity_bonus': 0,
            },
            '6': {
                'name': 'Foggy',
                'emoji': '🌫️',
                'description': 'Thick fog and low visibility are expected today. Fishing might be challenging but could offer some rewards.',
                'weight': 15,
                'success_rate_bonus': -0.15,
                'quantity_bonus': 0,
                'rarity_bonus': 0.3,
            },
            '7': {
                'name': 'Snowy',
                'emoji': '❄️',
                'description': 'Snowfall and cold temperatures are forecasted for today. Fishing may be less productive due to the weather.',
                'weight': 15,
                'success_rate_bonus': -0.1,
                'quantity_bonus': -0.1,
                'rarity_bonus': 0, 
            },
            '8': {
                'name': 'Windy',
                'emoji': '💨',
                'description': 'Expect strong winds today, which could make fishing conditions difficult.',
                'weight': 10,
                'success_rate_bonus': -0.2,
                'quantity_bonus': 0,
                'rarity_bonus': -0.1,
            },
            '9': {
                'name': 'Thunderstorm',
                'emoji': '⛈️',
                'description': 'Thunderstorms and heavy rain are forecasted today. Not ideal for fishing, as conditions will be challenging.',
                'weight': 10,
                'success_rate_bonus': 0,
                'quantity_bonus': -0.1,
                'rarity_bonus': -0.2,
            },
            '10': {
                'name': 'Snowstorm',
                'emoji': '🌨️',
                'description': 'Heavy snowfall and blizzard conditions are expected today. Fishing will be severely affected by the extreme weather',
                'weight': 10,
                'success_rate_bonus': 0,
                'quantity_bonus': -0.2,
                'rarity_bonus': -0.1,
            },
            '11': {
                'name': 'Tornado',
                'emoji': '🌪️',
                'description': 'Tornadoes and extreme weather conditions are expected today. Fishing will be extremely hazardous and not recommended.',
                'weight': 5,
                'success_rate_bonus': -0.3,
                'quantity_bonus': -0.1,
                'rarity_bonus': -0.2,
            },
        },
        'location': {
            '1': {
                'name': 'Lake',
                'emoji': '🏞️',
                'description': 'A peaceful lake where you have a better chance of a successful catch.',
                'fish': ['3', '4', '5', '6', '12', '14', '18', '19'],
                'success_rate_bonus': 0.1,
                'quantity_bonus': 0,
                'rarity_bonus': 0,
            },
            '2': {
                'name': 'River',
                'emoji': '🏞️',
                'description': 'A lively river where you might catch more fish, though the waters can be tricky.',
                'fish': ['1', '2', '5', '6', '11', '14', '20'],
                'success_rate_bonus': 0,
                'quantity_bonus': 0.1,
                'rarity_bonus': 0,
            },
            '3': {
                'name': 'Ocean',
                'emoji': '🏖️',
                'description': 'A vast ocean offering a chance to find rare fish. Be prepared for a bit of a challenge in these expansive waters.',
                'fish': ['7', '8', '9', '10', '13', '14', '15', '16', '17'],
                'success_rate_bonus': -0.1,
                'quantity_bonus': 0,
                'rarity_bonus': 0.05,
            },
        },
        'bait': {
            '1': {
                'name': 'Worms',
                'emoji': '🪱',
                'description': 'A classic choice for anglers, known for their versatility and effectiveness in various fishing conditions.',
                'tooltip': 'Slightly attracts fish with no special bonus.',
                'price': 9,
                'success_rate_bonus': 0.5,
                'quantity_bonus': 0,
                'rarity_bonus': 0,
            },
            '2': {
                'name': 'Minnows',
                'emoji': '🐟',
                'description': 'Small fish that attract larger fish by mimicking their natural prey, making them a popular choice for consistent catches.',
                'tooltip': 'Moderately attracts fish with no special bonus.',
                'price': 12,
                'success_rate_bonus': 0.7,
                'quantity_bonus': 0,
                'rarity_bonus': 0,
            },
            '3': {
                'name': 'Crickets',
                'emoji': '🦗',
                'description': 'Known for their high activity levels, which can entice fish looking for a lively snack.',
                'tooltip': 'Significantly attracts fish with no special bonus.',
                'price': 17,
                'success_rate_bonus': 0.9,
                'quantity_bonus': 0,
                'rarity_bonus': 0,
            },
            '4': {
                'name': 'Bread Crumbs',
                'emoji': '🍞',
                'description': 'Works well in shallow waters, especially to attract smaller, common fish.',
                'tooltip': 'Slightly attracts common fish with increased quantity.',
                'price': 0,
                'success_rate_bonus': 0.4,
                'quantity_bonus': 0.2,
                'rarity_bonus': -0.15,
            },
            '5': {
                'name': 'Corn Kernels',
                'emoji': '🌽',
                'description': 'An inexpensive bait option that can be surprisingly effective, particularly for smaller fish species.',
                'tooltip': 'Slightly attracts common fish with increased quantity.',
                'price': 0,
                'success_rate_bonus': 0.35,
                'quantity_bonus': 0.1,
                'rarity_bonus': -0.2,
            },
            '6': {
                'name': 'Boiled Eggs',
                'emoji': '🥚',
                'description': 'A traditional bait that can lure fish due to their unique scent and texture.',
                'tooltip': 'Moderately attracts common fish with increased quantity.',
                'price': 0,
                'success_rate_bonus': 0.6,
                'quantity_bonus': 0.2,
                'rarity_bonus': -0.05,
            },
            '7': {
                'name': 'Nightcrawlers',
                'emoji': '🪱',
                'description': 'Prized by anglers for their effectiveness, especially during nighttime or in low-light conditions.',
                'tooltip': 'Moderately attracts fish with increased quantity.',
                'price': 0,
                'success_rate_bonus': 0.6,
                'quantity_bonus': 0.2,
                'rarity_bonus': 0,
            },
            '8': {
                'name': 'Insects Mix',
                'emoji': '🪰',
                'description': 'Provides a diverse bait option that can cater to different fish preferences and increase your chances of success.',
                'tooltip': 'Significantly attracts fish with increased quantity.',
                'price': 0,
                'success_rate_bonus': 0.7,
                'quantity_bonus': 0.4,
                'rarity_bonus': 0,
            },
            '9': {
                'name': 'Shrimp',
                'emoji': '🍤',
                'description': 'Highly appealing for many fish species, especially those that feed on crustaceans.',
                'tooltip': 'Moderately attracts fish with increased quantity.',
                'price': 0,
                'success_rate_bonus': 0.55,
                'quantity_bonus': 0.3,
                'rarity_bonus': 0,
            },
            '10': {
                'name': 'Mini Crabs',
                'emoji': '🦀',
                'description': 'A great choice for attracting fish that prey on crustaceans, offering a more substantial bait option.',
                'tooltip': 'Slightly attracts rare fish.',
                'price': 0,
                'success_rate_bonus': 0.45,
                'quantity_bonus': -0.1,
                'rarity_bonus': 0.05,
            },
            '11': {
                'name': 'Scented Lures',
                'emoji': '🎣',
                'description': 'Designed to mimic the smell of prey, making them particularly effective for attracting rare fish.',
                'tooltip': 'Significantly attracts rare fish.',
                'price': 0,
                'success_rate_bonus': 0.75,
                'quantity_bonus': -0.1,
                'rarity_bonus': 0.3,
            },
            '12': {
                'name': 'Jumbo Crickets',
                'emoji': '🦗',
                'description': 'Larger and more robust than regular crickets, Jumbo Crickets are highly effective for attracting fish due to their increased size and scent.',
                'tooltip': 'Significantly attracts fish with increased quantity.',
                'price': 0,
                'success_rate_bonus': 0.95,
                'quantity_bonus': 0.15,
                'rarity_bonus': 0.05,
            },
            '13': {
                'name': 'Squid Strips',
                'emoji': '🦑',
                'description': 'Favored for their strong scent and texture, making them ideal for catching rare and large fish.',
                'tooltip': 'Moderately attracts rare fish.',
                'price': 0,
                'success_rate_bonus': 0.65,
                'quantity_bonus': -0.1,
                'rarity_bonus': 0.15,
            },
            '14': {
                'name': 'Silk Moths',
                'emoji': '🦋',
                'description': 'Silk moths are known for their fluttery movement and enticing scent, making them effective for drawing in a variety of fish.',
                'tooltip': 'Significantly attracts fish and increased quantity.',
                'price': 0,
                'success_rate_bonus': 0.8,
                'quantity_bonus': 0.4,
                'rarity_bonus': 0,
            },
            '15': {
                'name': 'Golden Minnows',
                'emoji': '✨',
                'description': 'Renowned for their unmatched effectiveness in attracting all types of fish.',
                'tooltip': 'The finest of all baits that no fish can turn down.',
                'price': 0,
                'success_rate_bonus': 0.98,
                'quantity_bonus': 0.8,
                'rarity_bonus': 0.5,
            },
            '16': {
                'name': 'Celestial Bait',
                'emoji': '☄️',
                'description': 'A legendary item with extraordinary power, said to attract even the most elusive fish.',
                'tooltip': 'Legendary bait with extraordinary power.',
                'price': 0,
                'success_rate_bonus': 1.2,
                'quantity_bonus': 0.8,
                'rarity_bonus': 0.3,
            },
        },
        'fish': {
            '1': {
                'name': 'Bluegill',
                'emoji': '🐟',
                'description': 'Do you think it calls me "pinklung"?',
                'price': 2,
                'salvage': ['4'],  # Bread Crumbs
                'weight': 100,
                'min': 1,
                'max': 3,
            },
            '2': {
                'name': 'Bass',
                'emoji': '🐟',
                'description': 'If I can catch a drummer, maybe I\'ll form a band!',
                'price': 8,
                'salvage': ['6'],  # Boiled Eggs
                'weight': 60,
                'min': 1,
                'max': 3,
            },
            '3': {
                'name': 'Tadpole',
                'emoji': '🐟',
                'description': 'It\'s just a tad small.',
                'price': 1,
                'salvage': ['5'],  # Corn Kernels
                'weight': 110,
                'min': 2,
                'max': 5,
            },
            '4': {
                'name': 'Frog',
                'emoji': '🐸',
                'description': 'Or maybe it\'s a prince in disguise?',
                'price': 12,
                'salvage': ['6'],  # Boiled Eggs
                'weight': 50,
                'min': 1,
                'max': 2,
            },
            '5': {
                'name': 'Crayfish',
                'emoji': '🦞',
                'description': 'Or else it\'s a lobster, and I\'m a giant!',
                'price': 6,
                'salvage': ['4'],  # Bread Crumbs
                'weight': 70,
                'min': 1,
                'max': 3,
            },
            '6': {
                'name': 'Catfish',
                'emoji': '🐠',
                'description': 'Do you think it has 9 lives?',
                'price': 14,
                'salvage': ['7', '7'],  # Live Worms
                'weight': 40,
                'min': 1,
                'max': 2,
            },
            '7': {
                'name': 'Clownfish',
                'emoji': '🐠',
                'description': 'How many can fit in a carfish?',
                'price': 1,
                'salvage': ['5'],  # Corn Kernels
                'weight': 110,
                'min': 1,
                'max': 4,
            },
            '8': {
                'name': 'Sea Bass',
                'emoji': '🐟',
                'description': 'No, wait- it\'s at least a C+!',
                'price': 10,
                'salvage': ['8'],  # Insects Mix
                'weight': 50,
                'min': 1,
                'max': 3,
            },
            '9': {
                'name': 'Puffer fish',
                'emoji': '🐡',
                'description': 'I thought you would be tougher, fish!',
                'price': 8,
                'salvage': ['9'],  # Shrimp
                'weight': 60,
                'min': 1,
                'max': 2,
            },
            '10': {
                'name': 'Horse Mackerel',
                'emoji': '🐠',
                'description': 'Holy mackerel!',
                'price': 8,
                'salvage': ['8'],  # Insects Mix
                'weight': 50,
                'min': 1,
                'max': 3,
            },
            '11': {
                'name': 'Snapping Turtle',
                'emoji': '🐢',
                'description': 'How can it snap without fingers?',
                'price': 14,
                'salvage': ['14'],  # Glow Worms
                'weight': 30,
                'min': 1,
                'max': 3,
            },
            '12': {
                'name': 'Sturgeon',
                'emoji': '🐟',
                'description': 'Wonder if it can perform sturgery...',
                'price': 10,
                'salvage': ['11'],  # Scented Lures
                'weight': 50,
                'min': 1,
                'max': 3,
            },
            '13': {
                'name': 'Barred Knifejaw',
                'emoji': '🐠',
                'description': 'I\'ll have to use it to cut veggies!',
                'price': 5,
                'salvage': ['9'],  # Shrimp
                'weight': 90,
                'min': 1,
                'max': 4,
            },
            '14': {
                'name': 'Salmon',
                'emoji': '🐟',
                'description': 'I\'ll have to scale back my excitement!',
                'price': 10,
                'salvage': ['12'],  # Specialized Crickets
                'weight': 50,
                'min': 1,
                'max': 3,
            },
            '15': {
                'name': 'Squid',
                'emoji': '🦑',
                'description': 'Do they... not actually "bloop"?',
                'price': 8,
                'salvage': ['13', '13'],  # Squid Strips
                'weight': 60,
                'min': 1,
                'max': 3,
            },
            '16': {
                'name': 'Octopus',
                'emoji': '🐙',
                'description': 'I\'m a sucker for these!',
                'price': 12,
                'salvage': ['13', '13', '13'],  # Squid Strips
                'weight': 40,
                'min': 1,
                'max': 2,
            },
            '17': {
                'name': 'Shark',
                'emoji': '🦈',
                'description': 'There’s just some-fin about you…',
                'price': 50,
                'salvage': ['16', '16', '16'],  # Celestial Bait
                'weight': 10,
                'min': 1,
                'max': 2,
            },
            '18': {
                'name': 'Carp',
                'emoji': '🐟',
                'description': 'If I catch another they can carpool!',
                'price': 2,
                'salvage': ['5', '5'],  # Corn Kernels
                'weight': 100,
                'min': 1,
                'max': 3,
            },
            '19': {
                'name': 'Goldfish',
                'emoji': '🐠',
                'description': 'It\'s worth its weight in fish!',
                'price': 7,
                'salvage': ['15'],  # Golden Minnows
                'weight': 7,
                'min': 4,
                'max': 8,
            },
            '20': {
                'name': 'Mitten Crab',
                'emoji': '🦀',
                'description': 'One more and I\'m ready for winter!',
                'price': 10,
                'salvage': ['10', '10'],  # Mini Crabs
                'weight': 50,
                'min': 1,
                'max': 2,
            },
        }
    }

    json = {
        'bot': bot,
        'general': general,
        'economy': economy,
        'profile': profile,
        'fishing': fishing,
    }
        
    return json

def update_settings():
    settings = get_setting_json()
    with open('settings.json', 'r') as openfile:
        data = json.load(openfile)
    
    # Add or update settings
    for section in settings:
        if section not in data:
            data[section] = settings[section]
        else:
            for option in settings[section]:
                if option not in data[section]:
                    data[section][option] = settings[section][option]

    # Remove settings not present in get_setting_json()
    sections_to_remove = [section for section in data if section not in settings]
    for section in sections_to_remove:
        del data[section]
    
    for section in data:
        options_to_remove = [option for option in data[section] if option not in settings[section]]
        for option in options_to_remove:
            del data[section][option]

    with open('settings.json', 'w') as openfile:
        json.dump(data, openfile, indent=4)

def get_setting(section: str, option: str = None):
    with open('settings.json', 'r') as openfile:
        data = json.load(openfile)
        if option:
            if section in data and option in data[section]:
                return data[section][option]
            else:
                return None
        elif section in data:
            return data[section]
        else:
            return None

def write_setting(section: str, option: str, value):
    with open('settings.json', 'r') as openfile:
        data = json.load(openfile)

    if section not in data:
        data[section] = {}

    data[section][option] = value

    with open('settings.json', 'w') as openfile:
        json.dump(data, openfile, indent=4)