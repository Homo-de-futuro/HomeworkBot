from aiogram.utils import executor
from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram import Dispatcher, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import os
import lxml

from SETTINGS import *
import db_connect



#variables and const
chat_id = 0
load_dotenv(find_dotenv())


#create bot
bot = Bot(token=os.getenv('TOKEN'), parse_mode='HTML')
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()



async def on_startup(_):
    #Connect db and start sheduler

    print('ok')
    db_connect.sql_start()
    await check_homework_update(dp)

    #Set sheduler for automaticaly message sending
    scheduler.add_job(scheduler_message_start, 'interval', minutes=HOMEWORK_CHECKING_INTERVAL, id='sheduler_message_start')

    scheduler.add_job(scheduler_sleep_mode_on, 'cron', hour=SCHEDULER_SLEEP_MODE_ON)
    scheduler.add_job(scheduler_sleep_mode_off, 'cron', hour=SCHEDULER_SLEEP_MODE_OFF)

    scheduler.add_job(scheduller_wekend_on, 'cron', day_of_week=SCHEDULER_DAY_ON)
    scheduler.add_job(scheduller_wekend_off, 'cron', day_of_week=SCHEDULER_DAY_OFF)
    


#Sending homework on schedule
async def send_homework_message(dp:Dispatcher, now_date):
    global last_message_with_homework

    current_homework_dict = await db_connect.sql_get_homework(now_date)
    
    #Create message with homework
    message_text = ''

    for subj in current_homework_dict:
        message_text+= '\n' + subj + '  -  ' + current_homework_dict[subj]

    #Save sended message in variables and pin it
    message = await dp.bot.send_message(chat_id, message_text)   
    await bot.pin_chat_message(chat_id, message['message_id'])

    #Save last sent homework message parameters (message object, message_id and send date) for next updating
    last_message_with_homework = {
        'message' : message,
        'message_id' : message['message_id'],
        'date' : now_date,
    }


async def update_homework_message(dp:Dispatcher, now_date):
    global last_message_with_homework

    current_homework_dict = await db_connect.sql_get_homework(now_date)

    #Create message with homework
    message_text = ''

    for subj in current_homework_dict:
        message_text+= '\n' + subj + '  -  ' + current_homework_dict[subj]

    #Update homework message text
    await bot.edit_message_text(message_text, chat_id, last_message_with_homework['message_id'])   


async def check_homework_update(dp:Dispatcher):
    print('---Start checking')
    now_date = datetime.now().strftime("%d.%m.%Y")
    
    if await db_connect.sql_is_record_exist(now_date) and chat_id:
        update_status = await db_connect.sql_get_update_status(now_date)
        if update_status == "True":
            #If variable exist
            if 'last_message_with_homework' in globals():

                #If last message has been sent not today unpin last message and send next message with homework
                if last_message_with_homework['date'] != now_date:
                    print('---Send message')
                    print(last_message_with_homework['date'])
                    await bot.unpin_chat_message(chat_id, last_message_with_homework['message_id'])
                    await send_homework_message(dp, now_date)     

                #If it has been sent today - update it         
                else:      
                    print('---Update')     
                    await update_homework_message(dp, now_date)
            else:
                #Если еще нет такой переменной (last_message_with_homework), просто отправляем сообщение и создаем её
                await send_homework_message(dp, now_date)

    elif not(await db_connect.sql_is_record_exist(now_date)):     
        #If there is no homework in database call sql_add_homework() func
        await db_connect.sql_add_homework(os.getenv('LOGIN'), os.getenv('PASSWORD'))


#Shedulers
async def scheduler_message_start():
    await db_connect.sql_add_homework(os.getenv('LOGIN'), os.getenv('PASSWORD'))
    await check_homework_update(dp)


def scheduler_sleep_mode_on():
    scheduler.pause_job('sheduler_message_start')

def scheduler_sleep_mode_off():
    scheduler.resume_job('sheduler_message_start')


def scheduller_wekend_on():
    scheduler.pause_job('sheduler_message_start')

def scheduller_wekend_off():
    scheduler.resume_job('sheduler_message_start')



#---------------------------
#---------HANDLERS----------
#---------------------------

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message : types.Message):
    global chat_id 

    if not(chat_id):
        chat_id = message.chat.id

    welcome_text = '''Привет! Я бот, который будет скидывать тебе дз
        \nДля просмотра доступных команд напиши'''
    await message.answer(welcome_text)


@dp.message_handler(commands=['дз'])
async def send_homework_with_comand(message : types.Message):
    await check_homework_update(dp)



#If we haven`t chat_id it start message handler and get it
if not(chat_id):
    @dp.message_handler()
    async def get_chat_id(message : types.message):
        global chat_id 
        chat_id = message.chat.id
        print('check id is sucsesfull')



if __name__ == '__main__':
    scheduler = AsyncIOScheduler() 
    scheduler.start()
    #skip_updates - if bot was offline it will not answer on users messages
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)