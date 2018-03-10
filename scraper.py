from selenium import webdriver
import json
import os
from os.path import expanduser
import binascii
import sys
from time import sleep

dl_folder = binascii.b2a_hex(os.urandom(8))

homedir = expanduser("~")
downloads = os.path.join(homedir, 'Downloads', dl_folder)

if not os.path.exists(downloads):
    os.makedirs(downloads)
else:
    sys.exit("Folder %s already exists" % downloads);

#chrome_profile = webdriver.ChromeOptions()
options = webdriver.ChromeOptions()
options.add_experimental_option("prefs", {
  "download.default_directory": downloads,
  "download.prompt_for_download": False,
  "download.directory_upgrade": True,
  "safebrowsing.enabled": True
})
driver = webdriver.Chrome(chrome_options=options)

kv_cookies = json.loads ('''[
{
    "domain": ".karaoke-version.com",
    "expirationDate": 1583718731,
    "hostOnly": false,
    "httpOnly": false,
    "name": "_ga",
    "path": "/",
    "sameSite": "no_restriction",
    "secure": false,
    "session": false,
    "storeId": "0",
    "value": "GA1.2.1939082954.1520488613",
    "id": 1
},
{
    "domain": ".karaoke-version.com",
    "expirationDate": 1520733131,
    "hostOnly": false,
    "httpOnly": false,
    "name": "_gid",
    "path": "/",
    "sameSite": "no_restriction",
    "secure": false,
    "session": false,
    "storeId": "0",
    "value": "GA1.2.512994047.1520646129",
    "id": 2
},
{
    "domain": "www.karaoke-version.com",
    "hostOnly": true,
    "httpOnly": false,
    "name": "flashmessage",
    "path": "/",
    "sameSite": "no_restriction",
    "secure": false,
    "session": true,
    "storeId": "0",
    "value": "",
    "id": 3
},
{
    "domain": "www.karaoke-version.com",
    "expirationDate": 1836007566.107409,
    "hostOnly": true,
    "httpOnly": false,
    "name": "karaoke-version",
    "path": "/",
    "sameSite": "no_restriction",
    "secure": false,
    "session": false,
    "storeId": "0",
    "value": "1520647565|s-i:1|c-i:USD|u-i:1762810^timechange^fd268431dba46678099adf7ff257043a^1|lu-i:1762810",
    "id": 4
}]
''')

#for cookie in kv_cookies :
#    #driver.add_cookie(cookie)
#    driver.add_cookie({k: cookie[k] for k in cookie.keys()})

# login
driver.get('https://www.karaoke-version.com/my/login.html')
form_groups = driver.find_elements_by_class_name('form-group')
login_btn = None
for form_group in form_groups:
    if form_group.text == 'Username or email':
        form_group.find_element_by_tag_name('input').send_keys('timechange')
    elif form_group.text == 'Password':
        form_group.find_element_by_tag_name('input').send_keys('password')
    else:
        login_btn = form_group.find_element_by_tag_name('input')
        break

login_btn.click()

# go to song
result = driver.get('http://www.karaoke-version.com/custombackingtrack/portugal-the-man/feel-it-still.html')
captions = driver.find_element_by_class_name('captions')
divs = captions.find_elements_by_tag_name('div')

instruments = []
for div in divs:
    instruments.append(div.text)

# first instrument is always the click track
instruments[0] = 'click'
#reset_button =  driver.find_element_by_id('mixer-refresh_btn')

sound__controls = driver.find_element_by_class_name('sound__controls')
mutes = sound__controls.find_elements_by_class_name('sound__controls__mute')

# first, mute everything
for i in range(0, len(instruments)):
    # mute all
    #reset_button.click()
    for mute in mutes:
        span = mute.find_element_by_tag_name('span')
        clazz = span.get_attribute('class')
        if clazz != 'active':
            mute.click()

# go thru each instrument
for j in range(0, len(instruments)):

    mute = mutes[j]
    span = mute.find_element_by_tag_name('span')
    clazz = span.get_attribute('class')
    # unmute track "j"
    if clazz == 'active':
        mute.click()

    # locate DL button and click it
    dl = driver.find_element_by_id('link_addcart_53498')
    existing_files = os.listdir(downloads)
    dl.click()

    eventual_directory_name = None
    # wait for DL to complete
    print 'stop here'
    newfile = ''
    while True:
        sleep(0.05)
        newfiles = os.listdir(downloads)
        newfile = ''
        if len(newfiles) == (len(existing_files) + 1):
            newfile = [x for x in newfiles if x not in existing_files][0]
        if newfile.endswith('.mp3'):
            break

    if newfile is not None and newfile.endswith('.mp3'):
        os.rename(os.path.join(downloads, newfile), os.path.join(downloads, instruments[j] + '.mp3'))
        if eventual_directory_name is None:
            eventual_directory_name = newfile[:-4]

    '''
        -- wait for crdownload file to appear
        -- note the name
        -- wait for extension to change to .mp3
        -- rename file to instruments[j]        
    '''

    # close modal dialog
    diag_close = driver.find_element_by_class_name('ui-dialog-titlebar-close')
    diag_close.click()
    # re-unmute track "j"
    mute.click()

os.rename(downloads, os.path.join(homedir, 'Downloads', eventual_directory_name))