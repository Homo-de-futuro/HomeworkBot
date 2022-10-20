import sqlite3
from datetime import datetime
import json
from parse import parse

#Init database with homeworks
def sql_start():
    global database, cur
    database = sqlite3.connect("base.db")
    cur = database.cursor()
    #Update status needs for understanig: is it necessary to update homework message or not
    cur.execute("CREATE TABLE IF NOT EXISTS homework(date PRIMARY KEY, hw, update_status)")
    database.commit()


#Add or update homeworks in database
async def sql_add_homework(login, password):
    now_date = datetime.now().strftime("%d.%m.%Y")
    curretn_homework = cur.execute("SELECT hw FROM homework WHERE date == ?", (now_date,)).fetchone()
    #parse actual homework
    actual_homework = json.dumps(parse.parse_next_homework(login, password))

    #Check availability of homework for today in database
    if curretn_homework is None:
        #If there aren`t homework in database at today
        cur.execute("INSERT INTO homework VALUES(?, ?, ?)", (now_date, actual_homework, "True"))
        database.commit()
    else:
        #If homework has been apdated, update it into database
        if curretn_homework[0] != actual_homework and not(actual_homework is None):          
            cur.execute("UPDATE homework SET hw == ?, update_status == ? WHERE date == ?", (actual_homework, "True", now_date))
            database.commit()


async def sql_get_homework(now_date):
    curretn_homework = cur.execute("SELECT hw FROM homework WHERE date == ?", (now_date,)).fetchone()[0]
    cur.execute("UPDATE homework SET update_status == ? WHERE date == ?", ("False", now_date))

    #Convert from str to dict
    homework_message = json.loads(curretn_homework)
    database.commit()

    return homework_message


#Use to get update status of current homework
async def sql_get_update_status(now_date):
    update_status = cur.execute("SELECT update_status FROM homework WHERE date == ?", (now_date,)).fetchone()[0]
    database.commit()

    return update_status


async def sql_is_record_exist(now_date):
    hw = cur.execute("SELECT hw FROM homework WHERE date == ?", (now_date,)).fetchone()
    database.commit()
    if not(hw is None):
        return True
    else:
        return False
    
