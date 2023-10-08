import os
import urllib
import requests
from bs4 import BeautifulSoup
import re
import time
from hashlib import md5
from time import localtime

def get_name(img_type):
    prefix = md5(str(localtime()).encode('utf-8')).hexdigest()
    return f"{img_type}_{prefix}"

def get_starthtml(url,header):
    '''获取一页页面：缩略图列表页'''
    page = urllib.request.Request(url, headers=header)
    html = urllib.request.urlopen(page)
    return html

def find_imgurl_from_html(html, rule, count,save_path,img_type):
    '''爬取一整页：从缩略图列表页中找到原图的url，并返回这一页的图片数量'''
    soup = BeautifulSoup(html, "lxml")
    link_list = soup.find_all("a", class_="iusc")
    for link in link_list:
        result = re.search(rule, str(link))
        # 获取匹配内容
        url = result.group(0) # "murl":"http://file.koolearn.com/20190411/15549556098601.png
        # 提取url
        url = url[8:len(url)] # http://file.koolearn.com/20190411/15549556098601.png
        # 保存图片
        if save_image(url,save_path,img_type):
            count += 1
            # print("已爬取：{}张".format(count))
    # 完成一页，继续加载下一页
    return count

def save_image(url,save_path,img_type):
    '''从原图url中将原图保存到本地'''
    try:
        time.sleep(1)
        img_name = get_name(img_type)+'.jpg'
        urllib.request.urlretrieve(url, os.path.join(save_path,img_name))
    except Exception:
        time.sleep(1)
        # print("爬取失败，跳过")
        return False
    else:
        # print("爬取成功："+img_name)
        return True


def main(url,header,name,save_path,img_type,save_num):
    key = urllib.parse.quote(name) # 转义
    first = 1
    loadNum = 35
    sfx = 1
    count = 0 # 当前成功数量
    # 正则表达式
    rule = re.compile(r"\"murl\"\:\"http\S[^\"]+") # url在murl中
    # 图片保存路径
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    while count < save_num:
        this_url = url.format(key, first, loadNum, sfx) # 拼接本页链接地址
        html = get_starthtml(this_url,header) # 抓取本页页面
        count += find_imgurl_from_html(html, rule, count,save_path,img_type)
        first = count + 1
        sfx += 1

    return count


if __name__ == '__main__':
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 UBrowser/6.1.2107.204 Safari/537.36'
    }
    url = "https://cn.bing.com/images/async?q={0}&first={1}&count={2}&scenario=ImageBasicHover&datsrc=N_I&layout=ColumnBased&mmasync=1&dgState=c*9_y*2226s2180s2072s2043s2292s2295s2079s2203s2094_i*71_w*198&IG=0D6AD6CBAF43430EA716510A4754C951&SFX={3}&iid=images.5599"

    # 需要爬取的图片关键词
    cls_key = {"advertisement":['广告','海报','商品简洁广告','商品宣传海报','商品宣传广告'],"table":['尺码表','信息表','发票'],"paragraph":['文章段落','英文段落','论文','论文段落'],"socialize":['中文聊天记录','英文聊天记录','聊天截图'],"report":["报告"],'text':['句子','单词']}
    # 本地存储路径
    save_path = './itbd_from_internet'

    # 数据类别 用于命名
    # 保存数量（非精准，因为会一页一页保存）
    save_num = 30

    for cls,keys in cls_key.items():
        for key in keys:
            print("{}-{} Begin".format(cls,key))
            count = main(url,header,key,save_path,cls,save_num)
            print("{}-{} End Num:{}".format(cls,key,count))