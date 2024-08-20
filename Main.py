import telebot
from telebot import types
from database import *
import os
import time
import pytz
from datetime import datetime
from config import GROUP, OWNER, CHANNEL, TOKEN

bot = telebot.TeleBot(f'{TOKEN}')

class User:  
    def __init__(self, user_id):
        self.user_id = user_id
        self.sex = None
        self.change = None
        self.state = None

user_dict = {}  
@bot.message_handler(commands=['start'])
def welcome(message):
    if check_user(user_id=message.from_user.id)[0]:
        mark = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        mark.add('🔍 Find a Partner')
        mark.add('📰 Profile Info', '🗑 Delete Profile')
        me = bot.get_me()
        bot.send_message(message.from_user.id, f"*Welcome to {me.first_name}🙊*\n\n_Hope you find a friend or partner_\n\n*NOTE:*\nMUST JOIN\n[👥 GROUP](t.me/{GROUP}) | [CHANNEL 📣](t.me/{CHANNEL}) | [📱OWNER](t.me/{OWNER})", parse_mode="markdown", disable_web_page_preview=True, reply_markup=mark)
        bot.register_next_step_handler(message, search_prof)
    else:
        # Create a new User object and store it in user_dict
        user = User(message.from_user.id)
        user_dict[message.from_user.id] = user

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton('Male👦'), types.KeyboardButton('Female👩🏻'))

        bot.send_message(message.from_user.id, "_👋Hello New User, To Proceed Please Select Your Gender!_", parse_mode="markdown", reply_markup=markup)
        bot.register_next_step_handler(message, handle_gender_selection)

def handle_gender_selection(message):
    try:
        user = user_dict[message.from_user.id]
        if message.text in ['Male👦', 'Female👩🏻']:
            user.sex = message.text
            # Prompt for partner preference
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('Male👦', 'Female👩🏻', 'Both👀')
            bot.send_message(message.from_user.id, "*What gender are you looking for?*", parse_mode="markdown", reply_markup=markup)
            bot.register_next_step_handler(message, reg_change)
        else:
            bot.send_message(message.from_user.id, '_Please Click the Options on the Keyboard!_', parse_mode="markdown")
            bot.register_next_step_handler(message, handle_gender_selection)
    except KeyError:
        bot.send_message(message.from_user.id, "An error occurred. Please restart by typing /start.")


@bot.message_handler(content_types=['text'])
def text_reac(message):  
    bot.send_message(message.chat.id, 'An error occurred\nPlease click /start to try again')

def reg_sex(message):  
    sex = message.text
    user = User(message.from_user.id)
    user_dict[message.from_user.id] = user
    
    # Creating a keyboard markup for gender selection
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton('Male👦'), types.KeyboardButton('Female👩🏻'))
    
    # Prompt the user to select their gender
    bot.send_message(message.from_user.id, '*Please select your gender:*', parse_mode="markdown", reply_markup=markup)
    bot.register_next_step_handler(message, handle_gender_selection)



def reg_change(message):  
    if message.text in ['Male👦', 'Female👩🏻', 'Both👀']:
        user = user_dict[message.from_user.id]
        user.change = message.text
        bot.send_message(message.from_user.id, "Great! Now, please select your state.")
        reg_state(message)  # Directly call reg_state to ask for the state after the gender preference
    else:
        bot.send_message(message.from_user.id, 'Please Click the Options on the Keyboard')
        bot.register_next_step_handler(message, reg_change)



def reg_state(message):  
    states = ['New South Wales', 'Victoria', 'Queensland', 'Western Australia', 'South Australia', 'Tasmania', 'Northern Territory', 'Australian Capital Territory']
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for state in states:
        markup.add(state)
    bot.send_message(message.from_user.id, '*Please select your state:*', parse_mode="markdown", reply_markup=markup)
    bot.register_next_step_handler(message, save_state)



def save_state(message):
    user = user_dict[message.from_user.id]
    user.state = message.text
    # Save the user information to the database
    reg_db(user_id=user.user_id, gender=user.sex, change=user.change, state=user.state)
    bot.send_message(message.from_user.id, "_Success...✅\nYour Account Has Been Registered!_", parse_mode="markdown")
    welcome(message)




def reg_accept(message):  
    if message.text == 'Yes ✔️':
        # If the user wants to change their profile, restart the registration
        bot.send_message(message.from_user.id, "*Let's update your profile. Please select your gender.*", parse_mode="markdown")
        bot.register_next_step_handler(message, handle_gender_selection)
    elif message.text == 'No ✖️':
        bot.send_message(message.from_user.id, "Alright, your profile remains unchanged.")
        welcome(message)
    else:
        bot.send_message(message.from_user.id, 'Please select an option from the keyboard.')
        bot.register_next_step_handler(message, reg_accept)


def search_prof(message):  
    if message.text in ['🔍 Find a Partner', '📰 Profile Info', '🗑 Delete Profile']:
        if message.text == '🔍 Find a Partner':
            bot.send_message(message.from_user.id, '🚀 Looking for a partner for you . . .')
            search_partner(message)
        elif message.text == '📰 Profile Info':
            user_info = get_info(user_id=message.from_user.id)
            
            # Ensure the correct data is mapped
            user_id = user_info[1]
            gender = user_info[2] if user_info[2] else 'Not Set'
            partner_preference = user_info[3] if user_info[3] else 'Not Set'
            state = user_info[4] if user_info[4] else 'Not Set'
            
            bot.send_message(message.from_user.id,
                             f"📍Profile Data📍\n\n*ID: * `{user_id}`\n*Gender: * {gender}\n*Partner Preference: * {partner_preference}\n*State: * {state}",
                             parse_mode="markdown")
                             
            mark = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            mark.add('Yes ✔️', 'No ✖️')
            bot.send_message(message.from_user.id, '_Do You Want to Change Your Profile Data?_', parse_mode="markdown", reply_markup=mark)
            bot.register_next_step_handler(message, reg_accept)
        else:
            delete_user(user_id=message.from_user.id)
            tw = types.ReplyKeyboardRemove()
            bot.send_message(message.from_user.id, '_Please Wait..Deleting Profile❗️_', parse_mode="markdown")
            bot.send_message(message.from_user.id, '_Success..Your Profile Has Been Deleted✅_', parse_mode="markdown", reply_markup=tw)
            welcome(message)
    else:
        bot.send_message(message.from_user.id, 'Click the Options on the Keyboard')
        bot.register_next_step_handler(message, search_prof)




def search_partner(message): 
    user_info = get_info(user_id=message.from_user.id)
    user_state = user_info[5]  # Assuming the state is the 6th item returned by get_info
    select = select_free_by_state(user_state)
    is_open = check_open(first_id=message.from_user.id)
    if is_open[0][0]:  
        bot.register_next_step_handler(message, chat)
    else:
        success = False
        if not select:
            add_user(first_id=message.from_user.id)
        else:
            for sel in select:
                if check_status(first_id=message.from_user.id, second_id=sel[0]) or message.from_user.id == sel[0]:
                    continue
                else:
                    mark2 = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                    mark2.add('❌ Exit')
                    add_second_user(first_id=sel[0], second_id=message.from_user.id)
                    bot.send_message(message.from_user.id,
                          "⚠️*Partner Found*", parse_mode="markdown",
                          reply_markup=mark2)
                    bot.send_message(sel[0],
                          "⚠️*Partner Found*", parse_mode="markdown",
                          reply_markup=mark2)
                    success = True
                    break
        if not success:
            time.sleep(2)
            search_partner(message)
        else:
            bot.register_next_step_handler(message, chat)

def chat(message):  
    if message.text == "❌ Exit" or message.text == "/exit":
        mark1 = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        mark1.add('🔍 Find a Partner')
        mark1.add('📰 Profile Info', '🗑 Delete Profile')
        companion = check_companion(first_id=message.from_user.id)
        bot.send_message(message.from_user.id, "_You Have Left the Chat_",parse_mode="markdown", reply_markup=mark1)
        bot.send_message(companion, "_Your Partner Has Left the Conversation_", parse_mode="markdown", reply_markup=mark1)
        close_chat(first_id=message.from_user.id)
        welcome(message)
        return

    elif not check_open(first_id=message.from_user.id)[0][0]:
        welcome(message)
        return
    companion = check_companion(first_id=message.from_user.id)
    if message.sticker:
        bot.send_sticker(
                    companion, 
                    message.sticker.file_id
                )
    elif message.photo:
        file_id = None
        
        for item in message.photo:
            file_id = item.file_id
        bot.send_photo(
                    companion, file_id, 
                    caption=message.caption
                )
    elif message.video:
        bot.send_video(
                    companion,
                    message.video.file_id,
                    caption=message.caption,
                )
    elif message.audio:
        bot.send_audio(
                    companion,
                    message.audio.file_id,
                    caption=message.caption,
                )
    elif message.voice:
        bot.send_voice(
                    companion, 
                    message.voice.file_id
                )
    elif message.animation:
        bot.send_animation(
                    companion, 
                    message.animation.file_id
                )
    elif message.text:
        if (
            message.text != "/start"
            and message.text != "/exit"
        ):
            if message.reply_to_message is None:
                bot.send_message(companion, message.text)

            elif message.from_user.id != message.reply_to_message.from_user.id:
                bot.send_message(
                            companion,
                            message.text,
                            reply_to_message_id=message.reply_to_message.message_id - 1,
                           )
            else:
                bot.send_message(message.chat.id, "You cannot reply to your own message")

    bot.register_next_step_handler(message, chat)

           

if __name__ == '__main__':
    init_db()  # Initialize the database
    init_queue()  # Initialize the queue table
    print("BOT IS READY")
    bot.polling()