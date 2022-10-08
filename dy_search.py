import json
from multiprocessing.connection import wait
import os
import time

from lxml import etree
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

import spider_util

file_path = os.path.dirname(__file__)
tik_tok_prefix_url = 'https://www.douyin.com'
file_save_path = file_path + r'/spider/'

#方法的问题：
#已经解决的问题: 当路径过长会导致无法找到
#当前视频刷新的结束div的class=Bllv0dx6
#没有解决的问题: li[1]//a的获取存在问题
#下滑刷新出新的视频不能找到哪里是结尾
#出现的滑动人类检测无法自动完成
def begin_search(browser: WebDriver, keyword: str, expect_search_result_num: int):
    req_url = f"{tik_tok_prefix_url}/search/{keyword}?&type=video"
    print(req_url)
    browser.get(req_url)
    # print(browser.page_source)
    # test='//*[@id="root"]//div[@class="FtarROQM"]//ul[@class="qrvPn3bC H2eeMN3S"]/li[1]//a'
    # element=browser.find_element(by=By.XPATH,value=test)
    # str=element.get_attribute("href")
    # print(str)
    #等待加载出登录按钮
    time.sleep(2)
    spider_util.dy_login(browser)
    i = 1
    video_ur_list = []
    video_div_xpath = f'//*[@id="root"]//div[@class="FtarROQM"]//ul[@class="qrvPn3bC H2eeMN3S"]'
    WebDriverWait(browser, 30).until(lambda driver: spider_util.find_element_silent(driver, video_div_xpath) is not None)
    video = spider_util.find_element_silent(browser, video_div_xpath)
    if video is None:
        print(f"未发现视频")
    while i <= expect_search_result_num:
        video_url_info_xpath = f'//*[@id="root"]//div[@class="FtarROQM"]//ul[@class="qrvPn3bC H2eeMN3S"]/li[{i}]//a'
        video_url_info = spider_util.find_element_silent(browser, video_url_info_xpath)
        if video_url_info is None:
            print(f"视频获取错误或者视频读取结束，索引: {i}")
            break
        
        print(video_url_info.get_attribute("href"))
        video_ur_list.append(video_url_info.get_attribute("href"))
        i = i + 1
        end=spider_util.find_element_silent(browser,'//*[@class="Bllv0dx6"]')
        if end is not None:
            print("视频已完或者无法寻找，结束搜索")
            continue
        browser.execute_script('scroll(0,document.body.scrollHeight)')
        time.sleep(0.5)

    file_path = f"{file_save_path}/search/{keyword}"
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    file_name = 'video_url_list.json'

    with open(f"{file_path}/{file_name}", 'w', encoding='UTF-8') as file:
        file.write(json.dumps(video_ur_list, indent=3, ensure_ascii=False))
        file.close()
    browser.close()

#包括视频信息以及评论
def save_searched_video_list_data(browser: WebDriver):
    # req_url = f"{tik_tok_prefix_url}/search/{keyword}?&type=video"
    # browser.get(req_url)
    # time.sleep(3)
    # spider_util.dy_login(browser)
    # with open(f"{file_save_path}/search/{keyword}/video_url_list.json", 'r', encoding='UTF-8') as file:
    #     video_list_json = file.read()
    #     video_list = json.loads(video_list_json)
        # print(video_list)
    #test for single meta save
    # video_url="https://www.douyin.com/video/7147171499273735460"
    browser.get('https://www.douyin.com/')
    browser.maximize_window()
    time.sleep(1)
    # 获取cookies
    with open('cookies.txt', 'w') as f:
        f.write(json.dumps(browser.get_cookies()))
    f.close()
    # 加载已保存cookies
    with open('cookies.txt', 'r') as f:
        cookies_list = json.load(f)
        for cookie in cookies_list:
            if 'expiry' in cookie:
                del cookie['expiry']
            browser.add_cookie(cookie)
    time.sleep(1)
    browser.refresh()
    
    video_url="https://www.douyin.com/video/7128976477562883368"
    
    video_id = spider_util.get_video_id_from_url(video_url)
    video_meta_file_path = f"{file_save_path}/work/{video_id}/metadata.json"
    video_comment_file_path = f"{file_save_path}/work/{video_id}/comment_list.json"
    if os.path.exists(video_meta_file_path) and os.path.exists(video_comment_file_path):
        print(f"视频:{video_id}已处理")
    else:
        save_single_work(browser, video_id)


def save_single_work(browser: WebDriver, video_id: str):
    print(f"开始存储视频:{video_id}")
    req_url = f"{tik_tok_prefix_url}/video/{video_id}"

    # 打开新窗口,此项的作用不明亮
    # body = browser.find_element(By.TAG_NAME,"body")
    # body.send_keys(Keys.CONTROL + 't')
    browser.implicitly_wait(2)
    browser.get(req_url)
    #此项变慢了，等待加载
    
    # 切换窗口,无用处
    # windows = browser.window_handles
    # browser.switch_to.window(windows[-1])

    #获取有关视频的信息完成
    # save_video_meta_data(browser, video_id)
    video_meta = save_video_meta_data(browser, video_id)
    comment_num_str = video_meta["comment_num"]
    comment_num = spider_util.str_to_int(comment_num_str)
    if comment_num > 100:
        print(f"评论数量({comment_num})过多，会造成卡顿")
    save_comments_by_wait(browser, video_id)
    #关闭浏览页面
    body = browser.find_element(By.TAG_NAME,"body")
    body.send_keys(Keys.CONTROL + 'w')

# 用户名存在图片或者评论存在图片的问题
# 在图片后面出现的文字符号将会消失
# 对于用户名可以考虑使用抖音号，唯一标识替代
def save_video_meta_data(browser: WebDriver, video_id: str):
    req_url = f"{tik_tok_prefix_url}/video/{video_id}"
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
        print(f'标题: {title}') 
    video_meta_data["title"] = title
    
    # favorite_num = browser.find_element(By.XPATH,
    #                                     '//*[@id="root"]/div/div[2]/div/div/div[1]/div[3]/div/div[2]/div[1]/div[1]/span').text
    favorite_num=browser.find_element(By.XPATH,faNum_reg).text
    if favorite_num is None:
        print("favorite_num is None")
    else:
        print(f"获赞: {favorite_num}")
    video_meta_data["favorite_num"] = favorite_num

    # comment_num = browser.find_element(By.XPATH,
    #                                    '//*[@id="root"]/div/div[2]/div/div/div[1]/div[3]/div/div[2]/div[1]/div[2]/span').text
    comment_num=browser.find_element(By.XPATH,com_reg).text
    if comment_num is None:
        print("comNum is None")
    else:
        print(f"评论: {comment_num}")
    video_meta_data["comment_num"] = comment_num

    # collect_num = browser.find_element(By.XPATH,
    #                                    '//*[@id="root"]/div/div[2]/div/div/div[1]/div[3]/div/div[2]/div[1]/div[3]/span').text
    collect_num=browser.find_element(By.XPATH,col_reg).text
    if collect_num is None:
        print("col_num is None")
    else:
        print(f"收藏: {collect_num}")
    video_meta_data["collect_num"] = collect_num

    release_time = browser.find_element(By.XPATH,
                                        '//*[@id="root"]/div/div[2]/div/div/div[1]/div[3]/div/div[2]/div[2]/span').text
    release_time = release_time[5:]
    print(f"发布时间: {release_time}")
    video_meta_data["release_time"] = release_time

    author_info = {}
    video_meta_data["author_info"] = author_info
    author_name = browser.find_element(By.XPATH,
                                       '//*[@id="root"]/div/div[2]/div/div/div[2]/div/div[1]/div[2]/a/div/span/span/span/span/span').text
    print(f"作者: {author_name}")
    author_info["name"] = author_name

    author_main_page = browser.find_element(By.XPATH,
                                            '//*[@id="root"]/div/div[2]/div/div/div[2]/div/div[1]/div[1]/a').get_attribute(
        "href")
    print(f"作者主页: {author_main_page}")
    author_info["main_page"] = author_main_page

    author_follower_num = browser.find_element(By.XPATH,
                                              '//*[@id="root"]/div/div[2]/div/div/div[2]/div/div[1]/div[2]/p/span[2]').text
    print(f"作者粉丝: {author_follower_num}")
    author_info["follower_num"] = author_follower_num

    author_praise_num = browser.find_element(By.XPATH,
                                             '//*[@id="root"]/div/div[2]/div/div/div[2]/div/div[1]/div[2]/p/span[4]').text
    print(f"作者获赞: {author_praise_num}")
    author_info["praise_num"] = author_praise_num

    file_path = f"{file_save_path}/work/{video_id}"
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    file_name = 'metadata.json'

    with open(f"{file_path}/{file_name}", 'w', encoding='UTF-8') as file:
        file.write(json.dumps(video_meta_data, indent=3, ensure_ascii=False))
        file.close()
    return video_meta_data


def save_comments_by_wait(browser: WebDriver, video_id: str):
    comlist_reg="//div[@data-e2e='comment-list']"
    com_item_reg="//div[@data-e2e='comment-item']"
    comment_list = []
    i = 1
    while True:
        print(f"第{i}次滚动")
        browser.execute_script('scroll(0,document.body.scrollHeight)')
        #模拟人的滚动
        spider_util.fake_human_scroll(browser,800)
        tree = spider_util.get_lxml_etree(browser)
        #查看结束标志
        end_mark1 = tree.xpath('//*[@class="BbQpYS5o HO1_ywVX"]')
        end_mark2 = tree.xpath('//*[@class="yCJWkVDx"]')

        if len(end_mark1) != 0 or len(end_mark2) != 0:
            print(f"发现结束标志")
            break
        i = i + 1

    html = spider_util.get_lxml_etree(browser)
    comment_divs = browser.find_element(By.XPATH, '//*[@id="root"]/div/div[2]/div/div/div[1]/div[5]/div/div/div[3]')
    #意义是什么
    browser.execute_script("arguments[0].scrollIntoView();", comment_divs)
    list = comment_divs.find_elements(By.XPATH,com_item_reg)
    # print("last list:",list[-1].text)
    li_len = len(list)
    print(f"评论总数：{li_len}")
    #这里为什么要-2
    # if i > 0:
    comment_list=spider_util.get_comment_info_by_lxml(html)
    if comment_list is None:
        print("无评论 或者 无法显示与查看")
        
    # while i < li_len:
    #     comment_info = spider_util.get_comment_info_by_lxml(html,i+1)
    #     if comment_info is not None:
    #         comment_list.append(comment_info)
    #     i = i + 1

    file_path = f"{file_save_path}/work/{video_id}"
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    file_name = 'comment_list.json'
    with open(f"{file_path}/{file_name}", 'w', encoding='UTF-8') as file:
        file.write(json.dumps(comment_list, indent=3, ensure_ascii=False))
        file.close()


def save_comments_manually(browser: WebDriver, video_id: str):
    """
    存储评论，需要手动参与
    一般适用于评论很多的视频，因为自动化往下滚动加载会导致视频
    1. 通过在搜索框输入结束表示评论加载完毕
    2. 评价加载不动的时候要多动一动，抖音就会认为不是爬虫，然后就能加载动了
    :param browser:
    :param video_id:
    :return:
    """
    comment_list = []

    i = 0

    search_btn = browser.find_element(By.XPATH,
                                      '//*[@id="douyin-header"]/header/div[2]/div[1]/div/div[2]/div/form')

    while True:
        # browser.execute_script("arguments[0].scrollIntoView();", list[i])
        # user_name = list[i].find_elements_by_xpath("div/div[2]/div[1]/div[1]/div/a/span/span/span/span/span")[0].text
        comment_obj = spider_util.find_element_silent(browser,
            f'//*[@id="root"]/div/div[2]/div/div/div[1]/div[3]/div/div/div[4]/div[{i + 1}]')
        if comment_obj is None or comment_obj.text == "加载中":
            browser.execute_script('scroll(0,document.body.scrollHeight)')
            print(f"检测到评论暂未刷新，开始往下翻页，当前已加载{i + 1}条评论")
            time.sleep(3)

            if search_btn.text == "结束":
                print(f"检测评论框输入了结束，结束评论获取")
                break
        else:
            comment_info = spider_util.get_comment_info_by_selenium(browser, i)

            i = i + 1
            comment_list.append(comment_info)

    file_path = f"{file_save_path}/work/{video_id}"
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    file_name = 'comment_list.json'
    with open(f"{file_path}/{file_name}", 'w', encoding='UTF-8') as file:
        file.write(json.dumps(comment_list, indent=3, ensure_ascii=False))
        file.close()


def save_comments_automatically(browser: WebDriver, video_id: str):
    """
    自动化地存储评论
    1. 通过在搜索框输入结束表示评论加载完毕
    2. 评价加载不动的时候要多动一动，抖音就会认为不是爬虫，然后就能加载动了
    :param browser:
    :param video_id:
    :return:
    """
    comment_list = []
    spider_util.handle_page_lazy_loading(browser, 3)

    comment_divs = browser.find_element(By.XPATH, '//*[@id="root"]/div/div[2]/div/div/div[1]/div[5]/div/div/div[3]')

    browser.execute_script("arguments[0].scrollIntoView();", comment_divs)
    list = comment_divs.find_elements_by_xpath('div')
    li_len = len(list)
    print(f"评论总数：{li_len}")
    i = 0

    while i < li_len - 2:
        # browser.execute_script("arguments[0].scrollIntoView();", list[i])
        # user_name = list[i].find_elements_by_xpath("div/div[2]/div[1]/div[1]/div/a/span/span/span/span/span")[0].text

        comment_info = spider_util.get_comment_info_by_selenium(browser, i)
        i = i + 1
        comment_list.append(comment_info)

    file_path = f"{file_save_path}/work/{video_id}"
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    file_name = 'comment_list.json'
    with open(f"{file_path}/{file_name}", 'w', encoding='UTF-8') as file:
        file.write(json.dumps(comment_list, indent=3, ensure_ascii=False))
        file.close()

