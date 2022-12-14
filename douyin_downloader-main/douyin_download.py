# Batch download tools for Douyin videos and pictures
# @author  palm.wang@hotmail.com
# version 1.0, 2022.09.28 : basic user video and picture download function

import random
import time
import re
from selenium import webdriver
from bs4 import BeautifulSoup
import requests
import os
import json
from lxml import etree
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

import spider_util

# General web browser using selenium and chrome
class WebBrowser:
    def __init__(self, driver_path, silent=False):
        chrome_options = webdriver.ChromeOptions()
        if silent:   # set Chrome to run under background
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
        # Open Chrome browser
        self.browser = webdriver.Chrome(executable_path=driver_path, options=chrome_options)

    # Close browser Tab
    def close_browser_tab(self):
        self.browser.close()

    # Quit browser, close the full window
    def close_entire_browser(self):
        self.browser.quit()

    # Get page source of the specific url using browser
    # Attention: the dynamic webpage cannot be acquired with requests.get(url)
    def get_main_page_source(self, url):
        try:
            self.browser.get(url)
            return self.browser.page_source
        except Exception as e:
            print('Unable to open url: %s', url)
            print(e)

    # Load and get the full page with scrolling
    def get_full_page_source(self):
        self.scroll_the_page_to_the_end()
        return self.browser.page_source

    # Close the nonsense little account window
    # Find the position of the 'x' class, and take a click function
    def close_nonsense_window_by_class(self, item_class):
        try:
            self.browser.find_element("class name", item_class).click()
            # self.browser.find_element(By.CLASS_NAME, item_class).click()
        except Exception as e:
            print('There is no class name: %s', item_class)
            print(e)

    # scroll the page to the end, to load the full page
    def scroll_the_page_to_the_end(self):
        # Scroll to the end of the page, in order to load the full page
        # Reference: https://blog.csdn.net/cai5/article/details/114250924
        get_height_js = 'return action=document.body.scrollHeight'
        scroll_height_js = 'window.scrollTo(0, document.body.scrollHeight)'
        height = self.browser.execute_script(get_height_js)
        self.browser.execute_script(scroll_height_js)
        time.sleep(5)
        t1 = int(time.time())
        status = True
        num = 0
        cnt = 0
        equal_num = 0
        while status and cnt < 100:
            t2 = int(time.time())
            if t2 - t1 < 30:
                cnt = cnt + 1
                n_height = self.browser.execute_script(get_height_js)
                if n_height > height:
                    self.browser.execute_script(scroll_height_js)
                    time.sleep(1)
                    height = n_height
                    t1 = int(time.time())
                elif n_height == height:
                    equal_num = equal_num + 1
                    if equal_num >= 5:
                        break
            elif num < 3:
                time.sleep(3)
                num = num + 1
            else:
                status = False
                break


# Douyin video and picture downloader
class DouyinDownloader:
    def __init__(self, driver_path, data_path, browser_silent=False):
        self.web_browser = WebBrowser(driver_path, browser_silent)
        self.data_path = data_path
        self.file_path = os.path.dirname(__file__)
        self.tik_tok_prefix_url = 'https://www.douyin.com'
        self.file_save_path = self.file_path + r'/spider/'

#??????????????????
#?????????????????????: ????????????????????????????????????
#???????????????????????????div???class=Bllv0dx6
#?????????????????????: li[1]//a?????????????????????
#??????????????????????????????????????????????????????
#?????????????????????????????????????????????
    def begin_search(self,browser: WebDriver, keyword: str, expect_search_result_num: int):
        req_url = f"{self.tik_tok_prefix_url}/search/{keyword}?&type=video"
        print(req_url)
        browser.get(req_url)
        # print(browser.page_source)
        # test='//*[@id="root"]//div[@class="FtarROQM"]//ul[@class="qrvPn3bC H2eeMN3S"]/li[1]//a'
        # element=browser.find_element(by=By.XPATH,value=test)
        # str=element.get_attribute("href")
        # print(str)
        #???????????????????????????
        time.sleep(2)
        spider_util.dy_login(browser)
        i = 1
        video_ur_list = []
        video_div_xpath = f'//*[@id="root"]//div[@class="FtarROQM"]//ul[@class="qrvPn3bC H2eeMN3S"]'
        WebDriverWait(browser, 30).until(lambda driver: spider_util.find_element_silent(driver, video_div_xpath) is not None)
        video = spider_util.find_element_silent(browser, video_div_xpath)
        if video is None:
            print(f"???????????????")
        while i <= expect_search_result_num:
            video_url_info_xpath = f'//*[@id="root"]//div[@class="FtarROQM"]//ul[@class="qrvPn3bC H2eeMN3S"]/li[{i}]//a'
            video_url_info = spider_util.find_element_silent(browser, video_url_info_xpath)
            if video_url_info is None:
                print(f"???????????????????????????????????????????????????: {i}")
                break
            
            print(video_url_info.get_attribute("href"))
            video_ur_list.append(video_url_info.get_attribute("href"))
            i = i + 1
            end=spider_util.find_element_silent(browser,'//*[@class="Bllv0dx6"]')
            if end is not None:
                print("?????????????????????????????????????????????")
                continue
            browser.execute_script('scroll(0,document.body.scrollHeight)')
            time.sleep(0.5)

        file_path = f"{self.file_save_path}/search/{keyword}"
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        file_name = 'video_url_list.json'

        with open(f"{file_path}/{file_name}", 'w', encoding='UTF-8') as file:
            file.write(json.dumps(video_ur_list, indent=3, ensure_ascii=False))
            file.close()
        browser.close()

    # Find the video id from the input string
    #vedio_list???????????????????????????????????????
    def get_video_list_from_string(self, str_data):
        video_strs_pattern1 = r'<a href="/video/(.*?)"'
        video_list = re.findall(video_strs_pattern1, str_data)
        print('video_list1: ', video_list)
    #????????????????????????????????????????????????????????????????????????????????????????????????
    #??????video_list2???????????????
        if len(video_list) == 0:
            video_strs_pattern2 = r'<a href="//www.douyin.com/video/(.*?)"'
            video_list = re.findall(video_strs_pattern2, str_data)
            print('video_list2: ', video_list)
        return video_list


    # Find the note(picture) id from the input string
    def get_note_list_from_string(self, str_data):
        note_strs_pattern1 = r'<a href="/note/(.*?)"'
        note_list = re.findall(note_strs_pattern1, str_data)
        print('note_list1: ', note_list)
        if len(note_list) == 0:
            note_strs_pattern2 = r'<a href="//www.douyin.com/note/(.*?)"'
            note_list = re.findall(note_strs_pattern2, str_data)
            print('note_list2: ', note_list)
        return note_list

    # Get the real video url from video page
    def get_real_video_url_from_videopage(self, video_id, user_id=''):
        #??????????????????????????????
        video_url = "https://www.douyin.com/video/{0}".format(video_id)
        page_source1 = self.web_browser.get_main_page_source(video_url)
        # time.sleep(2)
        # self.web_browser.close_nonsense_window_by_class('dy-account-close')
        
        soup_data = str(BeautifulSoup(page_source1.replace('&nbsp',' '), 'html.parser'))
        #????????????????????????????????????mp4????????????
        real_video_url_pattern = r'www.douyin.com/aweme/v1/play/(.*?)"'
        real_video_url_str = re.findall(real_video_url_pattern, soup_data)
        #???????????????????????????????????????note??????
        if len(real_video_url_str) == 0:
            # This is a note page
            # print(soup_data)
            print('parse notes in video page...')
            user_data_path = './{0}/{1}'.format(self.data_path, user_id)
            self.download_note_in_video_page(soup_data, user_data_path, video_id)
            return '', ''
        real_video_url = 'https://www.douyin.com/aweme/v1/play/' + real_video_url_str[0]
        # find the video title
        # video_title_pattern = r'<title>(.*?) - ??????</title>'
        video_title_pattern = r'<title>(.*?) - ??????</title>'
        video_title_str = re.findall(video_title_pattern, soup_data)
        if len(video_title_str) == 0:
            # print("title not found: ", soup_data)
            return real_video_url, ''
            # print('real_video_url: %s', real_video_url)
        # print('video title: %s', video_title_str)
        return real_video_url, video_title_str[0]

    def download_note_in_video_page(self, soup_data, user_data_path, video_id):
        real_note_url_pattern = r'<img class="V5BLJkWV" src="(.*?)"'
        
        real_note_url_strs = re.findall(real_note_url_pattern, soup_data)
        real_note_urls = []
        print(real_note_url_strs)
        for i in range(len(real_note_url_strs)):
            temp_url = str(real_note_url_strs[i]).replace('&amp;', '&')
            real_note_urls.append(temp_url)
        print('real_note_urls in video page: ', real_note_urls)
        for j in range(len(real_note_urls)):
            file_name = "{0}/{1}_{2}.webp".format(user_data_path, video_id, j)
            self.download_image(real_note_urls[j], file_name)
            time.sleep(random.random() * 1)

    # Get the real notes url from note page
    def get_real_note_urls_from_notepage(self, note_id):
        #note-url????????????
        note_url = "https://www.douyin.com/note/{0}".format(note_id)
        print('noteUrl',note_url)
        page_source1 = self.web_browser.get_main_page_source(note_url)
        # time.sleep(2)
        # self.web_browser.close_nonsense_window_by_class('dy-account-close')
        notes = spider_util.get_lxml_etree(self.web_browser.browser)
        note_xpath = "//img[@class='V5BLJkWV']/@src"
        # soup_data = str(BeautifulSoup(page_source1, 'html.parser'))
        # soup_data=soup_data.replace(u'\xa0',u' ')
        # print('note_page',soup_data)
        real_note_url_strs = notes.xpath(note_xpath)
        
        # real_note_url_pattern = r'<img class="V5BLJkWV" src="(.*?)"'
        # real_note_url_strs = re.findall(real_note_url_pattern, soup_data)
        real_note_urls = []
        print('',real_note_url_strs)
        for i in range(len(real_note_url_strs)):
            temp_url = str(real_note_url_strs[i]).replace('&amp;', '&')
            real_note_urls.append(temp_url)
        print('real_note_urls: ', real_note_urls)
        return real_note_urls

    # download one video stream
    #??????????????????????????????????????????
    def download_video_stream(self, video_url, video_file_name):
        try:
            if os.path.isfile(video_file_name):
                # # Ignore the file if the file exist
                print("%s was downloaded ok\n" % video_file_name)
                return True
                # # re-download the file if the file exist
                # os.remove(video_file_name)

            video_response = requests.get(video_url, stream=True)
            with open(video_file_name, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print("%s is downloaded ok\n" % video_file_name)
            f.close()
            
            return True
        except Exception as e:
            print("failed to download video (url=", video_url, ")")
            print(e)
            return False

    # Download the specified video_list
    #
    def download_specified_videos(self, video_list, user_id=''):
        # if no user_id is set, set it to be 'general'
        if user_id == '':
            user_id = 'general'
        # check if the path exist, and mkdir if not exist
        #???????????????????????????
        user_data_path = './{0}/{1}'.format(self.data_path, user_id)
        if not os.path.exists(user_data_path):
            os.makedirs(user_data_path)
        # Download the videos
        video_num = len(video_list)
        print('video_num:',video_num)
        # video_num = 1  # For test ...
        for i in range(video_num):
            #????????????title ???????????? ????????????
            video_url, video_title = self.get_real_video_url_from_videopage(video_list[i], user_id)
            # file_name = "{0}/{1}.mp4".format(user_data_path, video_list[i])
            file_name = "{0}/{1}.mp4".format(user_data_path, '{0}_{1}'.format(video_list[i], video_title))
            self.download_video_stream(video_url, file_name)
            time.sleep(random.random()*3)

    # Download one webp image
    #??????????????????
    def download_image(self, image_url, iamge_file_name):
        if os.path.isfile(iamge_file_name):
            # # Ignore the file if the file exist
            print("%s was downloaded ok\n" % iamge_file_name)
            return True
        response = requests.get(url=image_url, stream=True)
        with open(iamge_file_name, 'wb') as f:
            f.write(response.content)

    # Download the specified note_list
    #??????spcified??????????????????
    def download_specified_notes(self, note_list, user_id=''):
        # if no user_id is set, set it to be 'general'
        if user_id == '':
            user_id = 'general'
        # check if the path exist, and mkdir if not exist
        user_data_path = './{0}/{1}'.format(self.data_path, user_id)
        if not os.path.exists(user_data_path):
            os.makedirs(user_data_path)
        # Download the notes
        note_num = len(note_list)
        for i in range(note_num):
            note_urls = self.get_real_note_urls_from_notepage(note_list[i])
            for j in range(len(note_urls)):
                file_name = "{0}/{1}_{2}.webp".format(user_data_path, note_list[i], j)
                self.download_image(note_urls[j], file_name)
                time.sleep(random.random() * 1)

    # Get user url from 4 kinds of input string
    # take the main page of 'Missingziyu' for example, u can input:
    #  str01 = '6GAWU8G'
    #  str02 = 'https://v.douyin.com/6GAWU8G/'
    #  str03 = 'MS4wLjABAAAAeeO77c3knyeN7D2RD6f9YbcGXl2-RRvcHluTiLwWmt8LsRaaeICfEdkwgdwYwpP_'
    #  str04 = 'https://www.douyin.com/user/MS4wLjABAAAAeeO77c3knyeN7D2RD6f9YbcGXl2-RRvcHluTiLwWmt8LsRaaeICfEdkwgdwYwpP_'
    def get_user_url_and_user_id(self, input_str):
        user_url_pattern01 = r'https://v.douyin.com/(.*?)/'
        user_url_pattern02 = r'https://www.douyin.com/user/(.*)'
        user_id01 = re.findall(user_url_pattern01, input_str)
        user_id02 = re.findall(user_url_pattern02, input_str)

        # Type1: https://v.douyin.com/6GAWU8G/
        if len(user_id01) > 0:
            user_id = user_id01[0]
            user_url = 'https://v.douyin.com/{0}/'.format(user_id)
        # Type2: https://www.douyin.com/user/MS4wLjABAAAAeeO77c3knyeN7D2RD6f9YbcGXl2-RRvcHluTiLwWmt8LsRaaeICfEdkwgdwYwpP_
        elif len(user_id02) > 0:
            user_id = user_id02[0]
            user_url = 'https://www.douyin.com/user/{0}/'.format(user_id)
        else:
            if len(input_str) < 10:
                user_id = input_str
                user_url = 'https://v.douyin.com/{0}/'.format(user_id)
            else:
                user_id = input_str
                user_url = 'https://www.douyin.com/user/{0}'.format(user_id)
        print(user_id, user_url)
        return user_url, user_id

    # get user_name from the input string
    # ???????????????????????????
    # userid ???????????????????????? username?????????????????????
    def get_user_name_from_string(self, str_data):
        # print(str_data)
        # str_data = '<span class="kbjj_psh">???????????? Missingziyu</span><span class="WXnH80ht">IP???????????????</span></p>'
        user_name_pattern = r'????????????(.*?)</span>'
        user_name = re.findall(user_name_pattern, str_data)
        if len(user_name) == 0:
            print("??????????????????")
        # print('user_name: ', user_name[0])
        return user_name[0]

    # ?????????????????????????????????
    def get_user_data_list(self, user_url):
        # Open the user url web page
        self.web_browser.get_main_page_source(user_url)
        # Click on the 'x' of the account dy-account window
        time.sleep(2)
        self.web_browser.close_nonsense_window_by_class('dy-account-close')
        # roll the page to the end to loading the full page
        page_source = self.web_browser.get_full_page_source()
        user_name = self.get_user_name_from_string(page_source)
        video_list = self.get_video_list_from_string(page_source)
        note_list = self.get_note_list_from_string(page_source)
        return video_list, note_list, user_name

    # Download specific user data (both video and notes)
    # userid ????????? userid+????????????
    # input_str ???????????????????????????
    def download_specified_user_data(self, input_str):
        user_url, user_id = self.get_user_url_and_user_id(input_str)
        video_list, note_list, user_name = self.get_user_data_list(user_url)
        user_id = '{0}_{1}'.format(user_id, user_name)
        user_data_path = './{0}/{1}'.format(self.data_path, user_id)
        self.download_specified_videos(video_list, user_id)
        self.download_specified_notes(note_list, user_id)
        # user_data_path == "./download/user_id+user_name"
        # ???????????? user_data_path/video_id
        # ?????????web_browser???browser?????????????????????????????????
        self.save_user_video_list_data(self.web_browser.browser,video_list,user_data_path, method=0)
        self.save_user_video_list_data(self.web_browser.browser,note_list,user_data_path, method=1)

    # Download a group of users, in list format
    def download_user_data(self, input_str_list):
        user_num = len(input_str_list)
        try:
            for user_i in range(user_num):
                print("download user_i = %d/%d", user_i, user_num)
                self.download_specified_user_data(input_str_list[user_i])
            self.web_browser.close_browser_tab()
        except Exception as e:
            print(e)

    #??????????????????????????????
    #?????????????????????????????????note?????????????????????
    def save_user_video_list_data(self,browser: WebDriver,video_list,file_save_path, method):
        # req_url = f"{tik_tok_prefix_url}/search/{keyword}?&type=video"
        # browser.get(req_url)
        # time.sleep(3)
        # spider_util.dy_login(browser)
        # with open(f"{file_save_path}/search/{keyword}/video_url_list.json", 'r', encoding='UTF-8') as file:
        #     video_list_json = file.read()
        #     video_list = json.loads(video_list_json)
        #     print(video_list)
        
        for video_id in video_list:
            if method == 0:
                video_url = "https://www.douyin.com/video/{0}".format(video_id)
            else:
                video_url = "https://www.douyin.com/note/{0}".format(video_id)
            print(video_url)
            video_id = spider_util.get_video_id_from_url(video_url, method)
            video_meta_file_path = f"{file_save_path}/{video_id}/metadata.json"
            video_comment_file_path = f"{file_save_path}/{video_id}/comment_list.json"
            if os.path.exists(video_meta_file_path) and os.path.exists(video_comment_file_path):
                print(f"??????:{video_id}?????????")
            else:
                self.save_single_work(browser, video_id, file_save_path, method)
                
    #??????list_json????????????????????????meta
    def save_searched_video_list_data(self,browser: WebDriver, keyword: str):
        req_url = f"{self.tik_tok_prefix_url}/search/{keyword}?&type=video"
        browser.get(req_url)
        # time.sleep(3)
        # spider_util.dy_login(browser)
        with open(f"{self.file_save_path}/search/{keyword}/video_url_list.json", 'r', encoding='UTF-8') as file:
            video_list_json = file.read()
            video_list = json.loads(video_list_json)
            print(video_list)
        for video_url in video_list:
            video_id = spider_util.get_video_id_from_url(video_url)
            video_meta_file_path = f"{self.file_save_path}/work/{video_id}/metadata.json"
            video_comment_file_path = f"{self.file_save_path}/work/{video_id}/comment_list.json"
            if os.path.exists(video_meta_file_path) and os.path.exists(video_comment_file_path):
                print(f"??????:{video_id}?????????")
            else:
                self.save_single_work(browser, video_id)


    def save_single_work(self,browser: WebDriver, video_id: str,file_save_path="./spider/work", method=0):
        print(f"??????????????????:{video_id}")
        if method == 0:
            req_url = f"{self.tik_tok_prefix_url}/video/{video_id}"
        else:
            req_url = f"{self.tik_tok_prefix_url}/note/{video_id}"

        # ???????????????
        # body = browser.find_element_by_tag_name("body")
        # body.send_keys(Keys.CONTROL + 't')

        browser.get(req_url)
        #??????????????????????????????
        browser.implicitly_wait(2)
        # ????????????,?????????
        # windows = browser.window_handles
        # browser.switch_to.window(windows[-1])
        if method == 0:
            video_meta = self.save_video_meta_data(browser, video_id, file_save_path)
        else:
            video_meta = self.save_note_meta_data(browser, video_id, file_save_path)
            
        comment_num_str = video_meta["comment_num"]
        comment_num = spider_util.str_to_int(comment_num_str)
        if comment_num > 100:
            print(f"????????????({comment_num})????????????????????????")
        self.save_comments_by_wait(browser, video_id, file_save_path)
        #??????????????????
        body = browser.find_element(By.TAG_NAME,"body")
        body.send_keys(Keys.CONTROL + 'w')
        
    
        
        
    def save_video_meta_data(self,browser: WebDriver, video_id: str,file_save_path):
        
        req_url = f"{self.tik_tok_prefix_url}/video/{video_id}"
        video_meta_data = {}
        video_meta_data["id"] = video_id
        video_meta_data["url"] = req_url
        title_reg="//head//meta[@name='description']"
        faNum_reg="//div[@class='UwvcKsMK']/div[1]//span"
        com_reg="//div[@class='UwvcKsMK']/div[2]//span"
        col_reg="//div[@class='UwvcKsMK']/div[3]//span"
        # title = browser.find_element(By.XPATH,
        #                              '//*[@id="root"]/div/div[2]/div/div/div[1]/div[3]/div/div[1]/div/h1/span[2]').text
        title=browser.find_element(By.XPATH,title_reg).get_attribute("content")
        if title is None:
            print("title is None")
        else:
            print(f'??????: {title}') 
        video_meta_data["title"] = title
        
        # favorite_num = browser.find_element(By.XPATH,
        #                                     '//*[@id="root"]/div/div[2]/div/div/div[1]/div[3]/div/div[2]/div[1]/div[1]/span').text
        favorite_num=browser.find_element(By.XPATH,faNum_reg).text
        if favorite_num is None:
            print("favorite_num is None")
        else:
            print(f"??????: {favorite_num}")
        video_meta_data["favorite_num"] = favorite_num

        # comment_num = browser.find_element(By.XPATH,
        #                                    '//*[@id="root"]/div/div[2]/div/div/div[1]/div[3]/div/div[2]/div[1]/div[2]/span').text
        comment_num=browser.find_element(By.XPATH,com_reg).text
        if comment_num is None:
            print("comNum is None")
        else:
            print(f"??????: {comment_num}")
        video_meta_data["comment_num"] = comment_num

        # collect_num = browser.find_element(By.XPATH,
        #                                    '//*[@id="root"]/div/div[2]/div/div/div[1]/div[3]/div/div[2]/div[1]/div[3]/span').text
        collect_num=browser.find_element(By.XPATH,col_reg).text
        if collect_num is None:
            print("col_num is None")
        else:
            print(f"??????: {collect_num}")
        video_meta_data["collect_num"] = collect_num

        release_time = browser.find_element(By.XPATH,
                                            '//*[@id="root"]/div/div[2]/div/div/div[1]/div[3]/div/div[2]/div[2]/span').text
        release_time = release_time[5:]
        print(f"????????????: {release_time}")
        video_meta_data["release_time"] = release_time

        author_info = {}
        video_meta_data["author_info"] = author_info
        author_name = browser.find_element(By.XPATH,
                                        '//*[@id="root"]/div/div[2]/div/div/div[2]/div/div[1]/div[2]/a/div/span/span/span/span/span').text
        print(f"??????: {author_name}")
        author_info["name"] = author_name

        author_main_page = browser.find_element(By.XPATH,
                                                '//*[@id="root"]/div/div[2]/div/div/div[2]/div/div[1]/div[1]/a').get_attribute(
            "href")
        print(f"????????????: {author_main_page}")
        author_info["main_page"] = author_main_page

        author_follower_num = browser.find_element(By.XPATH,
                                                '//*[@id="root"]/div/div[2]/div/div/div[2]/div/div[1]/div[2]/p/span[2]').text
        print(f"????????????: {author_follower_num}")
        author_info["follower_num"] = author_follower_num

        author_praise_num = browser.find_element(By.XPATH,
                                                '//*[@id="root"]/div/div[2]/div/div/div[2]/div/div[1]/div[2]/p/span[4]').text
        print(f"????????????: {author_praise_num}")
        author_info["praise_num"] = author_praise_num

        file_path = f"{file_save_path}/{video_id}"
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        file_name = 'metadata.json'

        with open(f"{file_path}/{file_name}", 'w', encoding='UTF-8') as file:
            file.write(json.dumps(video_meta_data, indent=3, ensure_ascii=False))
            file.close()
        return video_meta_data


    def save_comments_by_wait(self,browser: WebDriver, video_id: str,file_save_path):
        # comlist_reg="//div[@data-e2e='comment-list']"
        com_item_reg="//div[@data-e2e='comment-item']"
        comment_list = []
        i = 1
        while True:
            print(f"???{i}?????????")
            browser.execute_script('scroll(0,document.body.scrollHeight)')
            #??????????????????
            spider_util.fake_human_scroll(browser,800)
            tree = spider_util.get_lxml_etree(browser)
            #??????????????????
            end_mark1 = tree.xpath('//*[@class="BbQpYS5o HO1_ywVX"]')
            end_mark2 = tree.xpath('//*[@class="yCJWkVDx"]')

            if len(end_mark1) != 0 or len(end_mark2) != 0:
                print(f"??????????????????")
                break
            i = i + 1

        html = spider_util.get_lxml_etree(browser)
        
        
        # comment_divs = browser.find_element(By.XPATH, '//*[@id="root"]/div/div[2]/div/div/div[1]/div[5]/div/div/div[3]')
        comment_divs = browser.find_element(By.XPATH, '//div[@data-e2e="comment-list"]')

        #???????????????
        browser.execute_script("arguments[0].scrollIntoView();", comment_divs)
        list = comment_divs.find_elements(By.XPATH,com_item_reg)
        # print("last list:",list[-1].text)
        li_len = len(list)
        print(f"???????????????{li_len}")

        comment_list=spider_util.get_comment_info_by_lxml(html,i+1)
        if comment_list is None:
            print("????????? ?????? ?????????????????????")
            
        file_path = f"{file_save_path}/{video_id}"
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        file_name = 'comment_list.json'
        with open(f"{file_path}/{file_name}", 'w', encoding='UTF-8') as file:
            file.write(json.dumps(comment_list, indent=3, ensure_ascii=False))
            file.close()
            
        
    def save_note_meta_data(self,browser: WebDriver, video_id: str,file_save_path):#,file_save_path
            
        req_url = f"{self.tik_tok_prefix_url}/note/{video_id}"
        browser.get(req_url)
        video_meta_data = {}
        video_meta_data["id"] = video_id
        video_meta_data["url"] = req_url
        title_reg="//head//meta[@name='description']"
        page_source1 = browser.page_source
        soup_data = str(BeautifulSoup(page_source1.replace('&nbsp',' '), 'html.parser'))
        note_metas_regex = r'<span class="ccH7ZaBs">(.*?)</span>'
        note_metas = re.findall(note_metas_regex, soup_data)
    
        title=browser.find_element(By.XPATH,title_reg).get_attribute("content")
        if title is None:
            print("title is None")
        else:
            print(f'??????: {title}') 
        video_meta_data["title"] = title
        
        # favorite_num = browser.find_element(By.XPATH,
        #                                     '//*[@id="root"]/div/div[2]/div/div/div[1]/div[3]/div/div[2]/div[1]/div[1]/span').text
        favorite_num = note_metas[0]
        if favorite_num is None:
            print("favorite_num is None")
        else:
            print(f"??????: {favorite_num}")
        video_meta_data["favorite_num"] = favorite_num

        # comment_num = browser.find_element(By.XPATH,
        #                                    '//*[@id="root"]/div/div[2]/div/div/div[1]/div[3]/div/div[2]/div[1]/div[2]/span').text
        comment_num = note_metas[1]
        if comment_num is None:
            print("comNum is None")
        else:
            print(f"??????: {comment_num}")
        video_meta_data["comment_num"] = comment_num

        # collect_num = browser.find_element(By.XPATH,
        #                                    '//*[@id="root"]/div/div[2]/div/div/div[1]/div[3]/div/div[2]/div[1]/div[3]/span').text
        collect_num = note_metas[2]
        if collect_num is None:
            print("col_num is None")
        else:
            print(f"??????: {collect_num}")
        video_meta_data["collect_num"] = collect_num
        # soup_data = soup_data.replace(' ','')
        release_time = browser.find_element(By.XPATH,
                                        '//div[@class="ElSNZcuB"]//span[@class="giPD3AqJ"]').text
        release_time = release_time[5:]
        print(f"????????????: {release_time}")
        video_meta_data["release_time"] = release_time
        author_info = {}
        video_meta_data["author_info"] = author_info
        author_name = browser.find_element(By.XPATH,
                                        '//div[@class="CjPRy13J"]/a/div/span/span/span/span/span/span').text
        print(f"??????: {author_name}")
        author_info["name"] = author_name

        author_main_page = browser.find_element(By.XPATH,
                                                '//div[@class="CjPRy13J"]/a').get_attribute(
            "href")
        print(f"????????????: {author_main_page}")
        author_info["main_page"] = author_main_page

        author_follower_num = browser.find_element(By.XPATH,
                                                '//p[@class="yibO9njB"]/span[2]').text
        print(f"????????????: {author_follower_num}")
        author_info["follower_num"] = author_follower_num

        author_praise_num = browser.find_element(By.XPATH,
                                                '//p[@class="yibO9njB"]/span[4]').text
        print(f"????????????: {author_praise_num}")
        author_info["praise_num"] = author_praise_num

        file_path = f"{file_save_path}/{video_id}"
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        file_name = 'metadata.json'

        with open(f"{file_path}/{file_name}", 'w', encoding='UTF-8') as file:
            file.write(json.dumps(video_meta_data, indent=3, ensure_ascii=False))
            file.close()
        return video_meta_data