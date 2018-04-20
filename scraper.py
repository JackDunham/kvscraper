from selenium import webdriver
import os
from os.path import expanduser
import binascii
import sys
from time import sleep
import io
import time

username = sys.argv[1]
password = sys.argv[2]
songlist = sys.argv[3]

dl_start_timeout_s = 30
max_retries = 3

# init download folder
dl_folder = 'kvscraper_' + binascii.b2a_hex(os.urandom(8))
homedir = expanduser("~")
downloads = os.path.join(homedir, 'Downloads', dl_folder)
if not os.path.exists(downloads):
    os.makedirs(downloads)
else:
    sys.exit("Folder %s already exists" % downloads);


def login(driver):
    # login
    driver.get('https://www.karaoke-version.com/my/login.html')
    form_groups = driver.find_elements_by_class_name('form-group')
    if form_groups == []:
        form_groups = driver.find_elements_by_class_name('form__group')
    login_btn = None

    for form_group in form_groups:
        if form_group.text == 'Username or email':
            form_group.find_element_by_tag_name('input').send_keys(username)
        elif form_group.text == 'Password':
            form_group.find_element_by_tag_name('input').send_keys(password)
        else:
            login_btn = form_group.find_element_by_tag_name('input')
            break
    login_btn.click()


def get_song(driver, songpath):
    # go to song
    driver.get('http://www.karaoke-version.com/custombackingtrack/' + songpath)
    captions = driver.find_element_by_class_name('captions')
    divs = captions.find_elements_by_tag_name('div')
    instruments = []
    for div in divs:
        instruments.append(div.text)
    # first instrument is always the click track
    instruments[0] = 'click'
    # reset_button =  driver.find_element_by_id('mixer-refresh_btn')
    sound__controls = driver.find_element_by_class_name('sound__controls')
    mutes = sound__controls.find_elements_by_class_name('sound__controls__mute')

    #turn on precount
    precount_btn = captions.find_element_by_id('precount')
    if not precount_btn.is_selected():
        precount_btn.click()

    # first, mute everything
    for i in range(0, len(instruments)):
        # mute all
        # reset_button.click()
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
        dl = driver.find_element_by_class_name('download')
        existing_files = os.listdir(downloads)

        numTries = 0
        finished_download = False
        while numTries < max_retries and not finished_download:
            dl.click()

            eventual_directory_name = None
            # wait for DL to complete
            newfile = ''

            timestart = time.time()
            dl_started = False
            while True:
                sleep(0.05)
                if (time.time() - timestart > dl_start_timeout_s) and not dl_started:
                    break
                newfiles = os.listdir(downloads)
                if len(newfiles) == (len(existing_files) + 1):
                    newfile = [x for x in newfiles if x not in existing_files][0]
                if newfile.endswith('.mp3'):
                    break
                elif newfile.endswith('.crdownload'):
                    dl_started = True

            if newfile == '':
                numTries += 1
            elif newfile.endswith('.mp3'):
                os.rename(os.path.join(downloads, newfile), os.path.join(downloads, instruments[j] + '.mp3'))
                if eventual_directory_name is None:
                    eventual_directory_name = newfile[:-4]
                finished_download = True

            # close modal dialog
            diag_close = driver.find_element_by_class_name('ui-dialog-titlebar-close')
            diag_close.click()

        # re-mute track "j"
        mute.click()

    target_dir = os.path.join(downloads, eventual_directory_name)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    else:
        sys.exit("Folder %s already exists" % target_dir);
    for filename in os.listdir(downloads):
        if filename.endswith('.mp3'):
            os.rename(os.path.join(downloads, filename), os.path.join(target_dir, filename))



if __name__ == "__main__":
    songs = []
    with io.open(songlist, mode='r', encoding='utf-8') as songlist_file:
        for line in songlist_file:
            songs.append(line.rstrip('\n'))
    # chrome_profile = webdriver.ChromeOptions()
    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", {
        "download.default_directory": downloads,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    driver = webdriver.Chrome(chrome_options=options)
    login(driver)
    for song in songs:
        get_song(driver, song)
    driver.quit()
