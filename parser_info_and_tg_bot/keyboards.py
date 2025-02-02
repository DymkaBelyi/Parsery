from telegram import InlineKeyboardButton, InlineKeyboardMarkup


sports_category = InlineKeyboardMarkup([
    [InlineKeyboardButton("Футбол", callback_data="futbol"),
    InlineKeyboardButton("Хоккей", callback_data="hokkej")],
    [InlineKeyboardButton("Баскетбол", callback_data="basketbol"),
    InlineKeyboardButton("Бокс", callback_data="boks")],
    [InlineKeyboardButton("Теннис", callback_data="tennis"),
    InlineKeyboardButton("Единоборства", callback_data="edinoborstva")],
    [InlineKeyboardButton("Формула-1", callback_data="Avtosport/Formula_1"),
    InlineKeyboardButton("Биатлон", callback_data="biatlon")],
    [InlineKeyboardButton("Легкая атлетика", callback_data="light_attletics"),
    InlineKeyboardButton("Фигурное катание", callback_data="Figurnoe_katanie")],
])