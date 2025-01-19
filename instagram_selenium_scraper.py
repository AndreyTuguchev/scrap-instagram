import time
import json
import re
import urllib.request
from urllib.parse import urlencode
import ssl
import requests
import os
import threading
import random

from chromedriver_py import binary_path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from pathlib import Path, PureWindowsPath
from datetime import datetime
from datetime import date
from bs4 import BeautifulSoup

import pytz
import validators

# make sure that we run only one instance of this script at any given time. This is needed because we will have CRON task so we can rerun the script after reboot or manual termination
from tendo import singleton
me = singleton.SingleInstance()


options = webdriver.ChromeOptions() 

# save current script working directory path into variable
_CWD_ = os.path.dirname(os.path.abspath(__file__))

os.system('pkill -9 chrome')
time.sleep(1)


# ===================================================
# ===================================================

# read data from env file:
env_file_path = Path(_CWD_ + "/.env.local")

if os.path.isfile( env_file_path ):
	file_data = open( env_file_path, "r")
	env_file_data_string = file_data.read()
	file_data.close()
else:
	raise Exception("Error! Environment variables file is not found...")


env_file_data = env_file_data_string.split("\n")
env_file_data_obj = {}

for i in range(0, len(env_file_data)):
	if '=' in env_file_data[i]:
		temp_values = env_file_data[i].split('=');
		env_file_data_obj[temp_values[0]] = temp_values[1];

telegram_api_key = env_file_data_obj['telegram_api_key']
telegram_chat_id = env_file_data_obj['telegram_chat_id']
user_agent = env_file_data_obj['user_agent']

# set current timezone from env to log data based on this time
timezone = pytz.timezone(env_file_data_obj['timezone'])

ssl._create_default_https_context = ssl._create_unverified_context

# ===================================================
# ===================================================

options.add_argument('--headless=new')
options.add_argument("--window-size=1100,970")
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--no-sandbox')
options.add_argument("--dns-prefetch-disable")
options.add_argument("--disable-gpu")

options.add_argument("--profile-directory=Profile 3")  

current_os_user = os.getlogin()

options.add_argument("user-data-dir=/home/"+ current_os_user +"/.config/google-chrome")

options.add_argument("user-agent=" + user_agent)

service = Service(executable_path=binary_path)

work_log_path = Path(_CWD_ + "/work_logs")

if not os.path.exists(work_log_path):
	os.makedirs(work_log_path)

log_path = Path(_CWD_ + "/log")

if not os.path.exists(log_path):
	os.makedirs(log_path)

padlock_file = Path(_CWD_ + "/_padlock_file_")

if os.path.isfile(padlock_file):
	os.remove(padlock_file)

# ==================================================
# ==================================================

def telegram_send_text_func(message_content):

	data_values = {
	    "text" : message_content,
	    "parse_mode" : "html"
	}

	final_bot_url = 'https://api.telegram.org/bot'+ telegram_api_key +'/sendMessage' +'?chat_id='+ telegram_chat_id

	r = requests.post(final_bot_url, data=data_values, timeout=59)
	response_data = json.loads(r.text)

# ===================================================
# ===================================================


def remove_chrome_singletons():
	singletonlock_file = _CWD_ +"/chrome_instagram_profile/SingletonLock"

	list_of_singleton_files = [
		_CWD_ + "/chrome_instagram_profile/SingletonLock",
		_CWD_ + "/chrome_instagram_profile/SingletonSocket",
		_CWD_ + "/chrome_instagram_profile/SingletonCookie",
	]

	for i in range(0, len(list_of_singleton_files)):
		# remove the Chrome browser's lock files if browser crashed in the past
		if os.path.islink(list_of_singleton_files[i]):
			execution_result = subprocess.run(
				"rm -f " + singletonlock_file,
				shell=False,
				capture_output=True,
				text=True,
				)

			print('execution_result =', execution_result)

remove_chrome_singletons()


# ===================================================
# ===================================================

def telegram_send_message_func(msg_send, telegram_api_key=telegram_api_key, telegram_chat_id=telegram_chat_id):
	telegram_link = "https://api.telegram.org/bot"+ telegram_api_key +"/sendMessage?chat_id="+ telegram_chat_id +"&text=" + msg_send + "&parse_mode=html"
	return telegram_link

# ===================================================
# ===================================================

def telegram_send_single_file_func(file_data, file_type="", caption=""):

	if "photo" == file_type:
		tg_method = "sendPhoto"

		final_bot_url = 'https://api.telegram.org/bot'+ telegram_api_key +'/'+ tg_method +'?chat_id='+ telegram_chat_id
		data_values = {file_type: file_data, 'caption': caption}


	if "" == file_type:
		tg_method = "sendMessage"
		file_type = "text"
		

		final_bot_url = 'https://api.telegram.org/bot'+ telegram_api_key +'/'+ tg_method +'?chat_id='+ telegram_chat_id
		data_values = {file_type: file_data, 'caption': caption}


	if "video" == file_type:
		tg_method = "sendVideo"
		supports_streaming = "TRUE"
		final_bot_url = 'https://api.telegram.org/bot'+ telegram_api_key +'/'+ tg_method +'?chat_id='+ telegram_chat_id
		data_values = {file_type: file_data, 'caption': caption, 'supports_streaming': "TRUE", 'timeout': '50000'}

	r = requests.post(final_bot_url, data=data_values, timeout=59)

	response_data = json.loads(r.text)
	
	if response_data["ok"] == False:
		response_message = response_data["description"].replace("#", '№').replace(":", '_').replace("/", '  or  ')
		telegram_send_text_func("<code>" + response_message + "</code>\n\n" + file_data)
		telegram_send_text_func("<code>" + json.dumps(data_values) + "</code>\n\n" )

	return r.text


# ===================================================
# ===================================================

def telegram_send_localfile_func( file_data, telegram_chat_id=telegram_chat_id, caption="" ):

	tg_method = "sendDocument"
	final_bot_url = 'https://api.telegram.org/bot'+ telegram_api_key +'/'+ tg_method
	fPath = file_data
	
	params = {
		'chat_id': telegram_chat_id,
		'caption': caption + "\n" + file_data,
	}

	files  = {
		'document': open(fPath, 'rb'),
	}

	r = requests.post(final_bot_url, params=params, files=files, timeout=59 )
	response_data = json.loads(r.text)

# ===================================================
# ===================================================

def telegram_send_selenium_screenshot (driver, type_of_screenshot='error', tg_chat_id_to_send=telegram_chat_id, is_like_btn_pressed=False):

	error_screenshot_path = _CWD_ + "/"+ type_of_screenshot +"_screenshot_path"

	if not os.path.exists( Path(error_screenshot_path) ):
		os.makedirs( Path(error_screenshot_path) )

	error_screenshot_name = str(int(time.time())) + "_" 

	screenshot_filename = error_screenshot_path + '/'+ type_of_screenshot +'_'+ error_screenshot_name +'.png'

	driver.get_screenshot_as_file( screenshot_filename)
	time.sleep( random.uniform(2, 3) )

	try:
		telegram_send_localfile_func( screenshot_filename,  tg_chat_id_to_send, "\n.\n" + driver.current_url + "\n")
	except Exception as error:
		telegram_send_text_func("cannot send screenshot... " + str(error_message))
		
	os.remove(screenshot_filename)

# ===================================================
# ===================================================

def log_current_time():
	print("current time: ", datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S"));

# ===================================================
# ===================================================

def parse_website( request_string , path_to_file, service=service, options=options):

	f = open(padlock_file, "a")
	f.write(".")		
	f.close()

	os.system('pkill -9 chrome')
	time.sleep(1)

	f = open(path_to_file, "a")
	f.write(".")		
	f.close()

	driver = webdriver.Chrome(service=service, options=options)
	driver.get( request_string )

	soup__WebUrl = BeautifulSoup( driver.page_source, "lxml" )
	search_item_arr = soup__WebUrl.select('script[type="application/ld+json"]')

	if search_item_arr != None and search_item_arr != []:

		for search_item in search_item_arr:
				
			if '' == search_item.string:
				break
			json_data = json.loads(search_item.string)

			#--------------------------
			
			if "{" == search_item.string[:1]:
				post_video_arr = json_data['video']
			elif "[" == search_item.string[:1]:
				post_video_arr = json_data[0]['video']

			for post_video in post_video_arr:
				telegram_send_single_file_func(post_video["contentUrl"], "video")
				time.sleep( random.randint(1, 3) )
			
			#--------------------------

			if "{" == search_item.string[:1]:
				post_image_arr = json_data['image']
			elif "[" == search_item.string[:1]:
				post_image_arr = json_data[0]['image']

			for post_image in post_image_arr:
				telegram_send_single_file_func(post_image["url"], "photo")
				time.sleep( random.randint(1, 3) )

			if "{" == search_item.string[:1]:
				articleBody_var = json_data['articleBody']		
			elif "[" == search_item.string[:1]:
				articleBody_var = json_data[0]['articleBody']		

			if None != articleBody_var or [] != articleBody_var:
				telegram_send_text_func( articleBody_var )

			if "{" == search_item.string[:1]:
				try:
					instagram_account_name = json_data['author']['identifier']['value']
				except:
					try:
						instagram_account_name = json_data['author']['alternateName']
					except:
						instagram_account_name = "instagram_account_name is not found at JSON data"
			elif "[" == search_item.string[:1]:
				try:
					instagram_account_name = json_data[0]['author']['identifier']['value']
				except:
					try:
						instagram_account_name = json_data[0]['author']['alternateName']
					except:
						instagram_account_name = "instagram_account_name is not found at JSON data"

			if None != instagram_account_name or [] != instagram_account_name:
				telegram_send_text_func( 'instagram account: @'+ instagram_account_name )

	else:

		telegram_send_text_func( ".\n\n page is loading in the browser... \n\n." )

		if "/stories" in request_string:
			stories_video = False
			stories_image = False
			button_view_storie_found = False

			image_selection_css_code = "section div button + div div img"
			video_selection_css_code = "section div button + div video"

			# button_view_selection_css_code = 'section > div > div div div[role="button"]'
			button_view_selection_css_code = 'section > div > div span[role="link"] ~ div div[role="button"]'

			# total amount of current stories for this account
			amout_of_stories_css_code = "body section section div header > div:first-child > div"

			button_next_slide_css_code = 'body svg[aria-label="Next"]'
			button_pause_slide_css_code = 'body section svg[aria-label="Pause"]'

			for n in range(0, 25):
				time.sleep(1)
				page_content = BeautifulSoup( driver.page_source, "lxml" )
				
				if [] != page_content.select( button_view_selection_css_code ):
					time.sleep(1)
					
					storie_buttons = page_content.select( button_view_selection_css_code )

					itr_i = 0
					for button_selector in storie_buttons:

						if "view story" in button_selector.text.lower():
							driver.find_element( By.CSS_SELECTOR, '.' + ".".join(button_selector["class"]) ).click()

							button_view_storie_found = True
							break
						itr_i+= 1
				if button_view_storie_found:
					break

			if not button_view_storie_found:
				telegram_send_text_func( "button_view_storie_found = FALSE --- check the page's layout ")
			else:
				print(' button_view_storie_found = True')

			time.sleep(1)

			counter_variable = 0

			execute_js_to_click_pause_button = """document.querySelector('"""+ button_pause_slide_css_code +"""').parentElement.click()"""

			for item in range(0, 50):
				
				time.sleep(0.35)
				
				if "/stories" in str(driver.current_url):

					try:
						# pause storie so the script can send this file into telegram
						driver.execute_script(execute_js_to_click_pause_button)
					except:
						telegram_send_selenium_screenshot (driver)	
						telegram_send_text_func( ". STories PAUSE buttons click FAILED !!!." )

					button_next_slide_storie = BeautifulSoup( driver.page_source, "lxml" ).select( button_next_slide_css_code )

					img_in_storie = BeautifulSoup( driver.page_source, "lxml" ).select( 'body section div > img' )
					
					if [] != img_in_storie:
						telegram_send_single_file_func( img_in_storie[0]["src"], "photo" )

					video_in_storie = BeautifulSoup( driver.page_source, "lxml" ).select( 'section video' )
					
					if [] != video_in_storie:
						telegram_send_single_file_func( video_in_storie[0]["src"], "video" )

					if [] != BeautifulSoup( driver.page_source, "lxml" ).select( button_next_slide_css_code ):
						time.sleep(1.5)
						driver.find_element( By.CSS_SELECTOR, button_next_slide_css_code ).click()
					

					if [] == button_next_slide_storie:
						telegram_send_text_func( ".\n\n\n\n\n\n\n\n\n\n\n\n." )
						break

				counter_variable = counter_variable + 1

				# once we checked (watched) all stories for this account we can break out of this loop.
				if "/stories" not in str(driver.current_url):
					break



		# code below will be triggered if this is not a storie URL
		else:

			for n in range(0, 20):
				time.sleep(1)
				page_content = BeautifulSoup( driver.page_source, "lxml" )

				if [] != page_content.select("body main"):
					if "isn't available" in page_content.select("main")[0].text:
						telegram_send_text_func("This instagram post is not accessible. Make sure that this account is not private and try again.")
						break
					else:
						break
			
			soup__WebUrl = BeautifulSoup( driver.page_source, "lxml" )

			instagram_account_name = soup__WebUrl.select('meta[name="twitter:title"]')
			if [] != instagram_account_name:
				current_instagram_account = instagram_account_name[0]['content'].split(')')[0].replace("(", "")
			else:
				current_instagram_account = 'instagram_account_not_defiend'

			description = soup__WebUrl.select('meta[property="og:title"]')

			custom_caption_data = ""
			if len(description) > 0:
				description_data = description[0]['content'].replace("on Instagram :", "on Instagram:")
				if 'on Instagram:' in description_data:
					description_data = description_data.split('on Instagram:')[1]
					custom_caption_data = description_data
				
				if len(custom_caption_data) >= 900:
					custom_caption_data = ""
		

			slider_next_button_css = 'main button[aria-label="Next"]'
			slider_image_css = 'main div > div > div > img[crossorigin="anonymous"]:not([draggable="false"])'
			slider_video_css = 'main div > div > div > video'

			temp_data_arr = []

			while BeautifulSoup( driver.page_source, 'lxml').select('body'):

				video_items_arr = BeautifulSoup( driver.page_source, 'lxml').select( slider_video_css )

				if [] != video_items_arr:
					for video_item in video_items_arr:
						if video_item not in temp_data_arr:
							if None != video_item["src"] or [] != video_item["src"]:
								telegram_send_single_file_func( video_item["src"], "video", request_string + "\n\n" + current_instagram_account + "\n\n" + custom_caption_data )
								temp_data_arr.append( video_item )


				img_items_arr = BeautifulSoup( driver.page_source, 'lxml').select( slider_image_css )

				if [] != img_items_arr:
					for img_item in img_items_arr:
						if img_item not in temp_data_arr:
							if None != img_item["src"] or [] != img_item["src"]:
								telegram_send_single_file_func( img_item["src"], "photo", request_string + "\n\n" + current_instagram_account + "\n\n" + custom_caption_data )
								temp_data_arr.append( img_item )


				if [] != BeautifulSoup( driver.page_source, 'lxml').select(slider_next_button_css):
					driver.find_element( By.CSS_SELECTOR, slider_next_button_css ).click()
				else:
					break
					
				time.sleep( random.uniform(1, 2.7) )


			if len(description) > 0:
				if len(description_data) >= 900:
					telegram_send_text_func( description_data + "\n\n" + request_string )


	#--------------------------

	if 'challenge' in driver.current_url:
		telegram_send_selenium_screenshot( driver )
		telegram_send_text_func( "⚠️⚠️.\n Instagram challenge found!!! \n\n." )
		telegram_listen_father(driver)

	telegram_send_text_func( ".\n\n\n\n\n\n\n\n\n\n\n\n." )

	time.sleep( random.randint(3, 9) )

	try:
		driver.close()
	except:
		driver.close()

	time.sleep( 2 )

	os.remove(padlock_file)



# ===================================================================================
# ===================================================================================
# ===================================================================================

def parse_telegram_bot_message():

	final_bot_url = 'https://api.telegram.org/bot'+ telegram_api_key +'/getUpdates' +'?chat_id='+ telegram_chat_id + "&offset=-1"

	r = requests.get(final_bot_url, timeout=59)
	json_data = json.loads(r.text)

	message_id = json_data["result"][0]["update_id"]
	
	try:
		sender_chat_id = json_data["result"][0]["channel_post"]["sender_chat"]["id"]
	except:
		sender_chat_id = json_data["result"][0]["edited_channel_post"]["sender_chat"]["id"]

	# make sure that the message wasn't sent by our telegram bot itself
	if abs(int(sender_chat_id)) == abs(int(telegram_chat_id)):

		path_to_file = Path(_CWD_ + "/log/telegram_message_checked_" + str(message_id))

		if not os.path.isfile(path_to_file):

			if "channel_post" in json_data["result"][0]:
				if "text" in json_data["result"][0]["channel_post"]:
					message_text = json_data["result"][0]["channel_post"]["text"]

					if "remove chrome singletons" in message_text.lower() or "singletons" in message_text.lower():
						remove_chrome_singletons()

					if "instagram.com" in message_text:

						if message_text.count('instagram.com') > 1:

							if not os.path.isfile(path_to_file):

								telegram_send_text_func( ".\n\n\n\n\n\n\n\n\n\n\n\n." )

								for single_url in message_text.split(","):

									if "?" in single_url:
										single_url = single_url.split('?')[0]

									single_url = single_url.replace('\n', '').replace('\t', '').replace('\r', '')
									
									if "instagram.com" in single_url and validators.url( single_url ):
										current_time = datetime.now(timezone)
										current_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

										telegram_send_text_func( single_url )
										parse_website(single_url, path_to_file)

						else:
							if "?" in message_text:
								message_text = message_text.split('?')[0]
									
							if validators.url( message_text ):
								current_time = datetime.now(timezone)
								current_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

								if not os.path.isfile(path_to_file):
									parse_website(message_text, path_to_file)


# ===================================================================================
# ===================================================================================
# ===================================================================================

older_than_time_check = 60 * 7

def printit():
	# this will trigger the Telegram chat check every 3 seconds
	threading.Timer(3.0, printit).start()

	if os.path.isfile(padlock_file):

		# if padlock wasn't modified for a long time that probably means that browser crushed
		if (time.time() - os.path.getmtime(padlock_file)) > older_than_time_check:
			os.remove(padlock_file)
		
	if not os.path.isfile(padlock_file):
		
		try:
			# we need to use Try block because Telegram API has 'Max retries exceeded' error from time to time
			parse_telegram_bot_message()
		except Exception as error_message:
			if "Max retries exceeded with url" not in str(error_message) and "api.telegram.org" not in str(error_message) and "ConnectionResetError" not in str(error_message):
				print(f"Unexpected {error_message=}, {type(error_message)=}")
		
printit()