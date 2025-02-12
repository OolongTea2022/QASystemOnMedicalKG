#!/usr/bin/env python3
# coding: utf-8
# File: data_spider.py
# Author: lhy<lhy_in_blcu@126.com,https://huangyong.github.io>
# Date: 18-10-3


import urllib.request
import urllib.parse

import chardet
from lxml import etree
import pymongo
import crawl_drug


'''基于寻医问药的信息采集'''
class MedicalSpider:
    def __init__(self):
        self.conn = pymongo.MongoClient()
        self.db = self.conn['medical1']
        self.col = self.db['data']

    '''根据url，请求html'''
    def get_html(self, url):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/51.0.2704.63 Safari/537.36'}
        req = urllib.request.Request(url=url, headers=headers)
        res = urllib.request.urlopen(req)
        try:
            html = res.read().decode('gbk')
        except Exception:
            raw_data = res.read()
            # 使用chardet检测编码
            encoding = chardet.detect(raw_data)['encoding']
            html = raw_data.decode(encoding)
        return html

    '''url解析'''
    def url_parser(self, content):
        selector = etree.HTML(content)
        urls = ['http://www.anliguan.com' + i for i in  selector.xpath('//h2[@class="item-title"]/a/@href')]
        return urls

    '''测试'''
    def spider_main(self):
        with open('record.txt', 'a', encoding='utf-8') as file:
            for page in range(1, 11000):
                # time.sleep(0.01)
                try:
                    basic_url = f'http://jib.xywy.com/il_sii/gaishu/{page}.htm'
                    cause_url = f'http://jib.xywy.com/il_sii/cause/{page}.htm'
                    prevent_url = f'http://jib.xywy.com/il_sii/prevent/{page}.htm'
                    symptom_url = f'http://jib.xywy.com/il_sii/symptom/{page}.htm'
                    inspect_url = f'http://jib.xywy.com/il_sii/inspect/{page}.htm'
                    treat_url = f'http://jib.xywy.com/il_sii/treat/{page}.htm'
                    food_url = f'http://jib.xywy.com/il_sii/food/{page}.htm'

                    data = {}
                    data['url'] = basic_url
                    data['basic_info'], disease_name = self.basicinfo_spider(basic_url)

                    # 空页直接跳过
                    if disease_name == '':
                        continue

                    data['cause_info'] = self.common_spider(cause_url)
                    data['prevent_info'] = self.common_spider(prevent_url)
                    data['symptom_info'] = self.symptom_spider(symptom_url)
                    data['inspect_info'] = self.inspect_spider(inspect_url)
                    data['treat_info'] = self.treat_spider(treat_url)
                    data['food_info'] = self.food_spider(food_url)

                    # Modified 通过原网站找到的disease名称，在新网站进行搜索药品
                    data['drug_info'] = crawl_drug.drug_spider_new(disease_name)
                    info = f"{page:7} {disease_name}"

                    if not data['drug_info']:
                        file.write(info + '\n')
                        file.flush()  # 实时刷新文件内容到磁盘
                    self.col.insert(data)
                    print(page, '\t', disease_name)

                except Exception as e:
                    print(e, page)


    '''基本信息解析'''
    def basicinfo_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        title = selector.xpath('//title/text()')[0]
        category = selector.xpath('//div[@class="wrap mt10 nav-bar"]/a/text()')
        desc = selector.xpath('//div[@class="jib-articl-con jib-lh-articl"]/p/text()')
        ps = selector.xpath('//div[@class="mt20 articl-know"]/p')
        infobox = []
        for p in ps:
            info = p.xpath('string(.)').replace('\r','').replace('\n','').replace('\xa0', '').replace('   ', '').replace('\t','')
            infobox.append(info)
        basic_data = {}
        basic_data['category'] = category
        name = title.split('的简介')[0]
        basic_data['name'] = name
        basic_data['desc'] = desc
        basic_data['attributes'] = infobox
        return basic_data, name

    '''treat_infobox治疗解析'''
    def treat_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        ps = selector.xpath('//div[starts-with(@class,"mt20 articl-know")]/p')
        infobox = []
        for p in ps:
            info = p.xpath('string(.)').replace('\r','').replace('\n','').replace('\xa0', '').replace('   ', '').replace('\t','')
            infobox.append(info)
        return infobox

    '''treat_infobox治疗解析'''
    def drug_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        drugs = [i.replace('\n','').replace('\t', '').replace(' ','') for i in selector.xpath('//div[@class="fl drug-pic-rec mr30"]/p/a/text()')]
        return drugs



    '''food治疗解析'''
    def food_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        divs = selector.xpath('//div[@class="diet-img clearfix mt20"]')
        try:
            food_data = {}
            food_data['good'] = divs[0].xpath('./div/p/text()')
            food_data['bad'] = divs[1].xpath('./div/p/text()')
            food_data['recommand'] = divs[2].xpath('./div/p/text()')
        except:
            return {}

        return food_data

    '''症状信息解析'''
    def symptom_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        symptoms = selector.xpath('//a[@class="gre" ]/text()')
        ps = selector.xpath('//p')
        detail = []
        for p in ps:
            info = p.xpath('string(.)').replace('\r','').replace('\n','').replace('\xa0', '').replace('   ', '').replace('\t','')
            detail.append(info)
        symptoms_data = {}
        symptoms_data['symptoms'] = symptoms
        symptoms_data['symptoms_detail'] = detail
        return symptoms, detail

    '''检查信息解析'''
    def inspect_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        inspects  = selector.xpath('//li[@class="check-item"]/a/@href')
        return inspects

    '''通用解析模块'''
    def common_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        ps = selector.xpath('//p')
        infobox = []
        for p in ps:
            info = p.xpath('string(.)').replace('\r', '').replace('\n', '').replace('\xa0', '').replace('   ','').replace('\t', '')
            if info:
                infobox.append(info)
        return '\n'.join(infobox)


    '''检查项抓取模块'''
    def inspect_crawl(self):
        for page in range(1, 3684):
            try:
                url = 'http://jck.xywy.com/jc_%s.html'%page
                html = self.get_html(url)
                data = {}
                data['url'] = url
                data['html'] = html
                self.db['jc'].insert(data)
                print(url)
            except Exception as e:
                print(e)


handler = MedicalSpider()
# handler.inspect_crawl()
handler.spider_main()

