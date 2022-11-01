from lib2to3.pgen2 import driver
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import os

def get_next_homework_date():
    now = datetime.now()
    
    if datetime.weekday(now) == 4:
        #If its friday we add 3 days to current date 
        date =(datetime.now() + timedelta(days=3)).strftime("%d.%m.%Y")
    elif datetime.weekday(now) == 5:
        #If its saturday we add 2 days to current date
        date =(datetime.now() + timedelta(days=2)).strftime("%d.%m.%Y")
    else:
        #If its any other day of week
        date =(datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")

    return date


#This function make a file with html code for parse and return dict of the form: subject:homework.
def parse_next_homework(user_login, user_password):
    url = 'https://login.dnevnik.ru/esia/redirect/adygea'
    
    options = webdriver.ChromeOptions()  
    options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
    

    try:
        print("start selenium")
        driver.get(url)
        print("get succsesfull") 
        delay = 15

        # WebDriverWait need to wait loading. This code wait 10 sec (delay) while page will be loaded
        # Login field search with using By.ID
        login = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, "login")))
        login.clear()
        login.send_keys(user_login)

        password = driver.find_element("id", "password")
        password.clear()
        password.send_keys(user_password)

        login_button = driver.find_element("id", "loginByPwdButton")
        login_button.click()

        #This part of code wait while elemnt will be loaded and after it save link to "home_work" variable.
        #Also it search necessary link with using "By.LINK_TEXT" which search elements on their text.
        #If element is loaded, home_work.click() redirect to page with home work 
        home_work = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.LINK_TEXT, "Домашние задания")))
        home_work.click()

        print("next date")
        #Fills in fields with homework dates
        date = get_next_homework_date()

        date_from = driver.find_element(By.ID, 'datefrom')
        date_to = driver.find_element(By.ID, 'dateto')
        date_from.clear()
        date_to.clear()
        date_from.send_keys(date)
        date_to.send_keys(date)

        date_button = driver.find_element(By.ID, 'choose')
        date_button.click()

        print("Next beautifule soup")
        soup = BeautifulSoup(driver.page_source, 'lxml')

        #Split homeworks into groups and put it in the "lines", also create dict which need to contain ind like:  SUBJ:HOMEWORK
        lines = soup.find_all("tr")
        homework_dict = {}

        for i in range(1, len(lines)):
            #Find in this block subject and task and put it into variables
            subject = lines[i].find(class_="tac light").text
            task = lines[i].find(class_="breakword").text

            #Delete all unnecessary indents
            subject = " ".join(subject.split())
            task = " ".join(task.split())

            # If there is already a task in the dictionary, we add an additional task in this key
            if not(subject in homework_dict):
                homework_dict[subject] = task
            else:
                if homework_dict[subject] == task:
                    pass
                else:
                    homework_dict[subject] = homework_dict[subject] + ' ; ' + task
        return homework_dict
    except Exception as ex:
        parse_next_homework(user_login, user_password)
    finally:
        driver.close()
        driver.quit()
