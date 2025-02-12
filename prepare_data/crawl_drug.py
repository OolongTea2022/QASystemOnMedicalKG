import urllib.request
import urllib.parse
from lxml import etree
import pymongo
import re
from pypinyin import pinyin, Style


'''根据url，请求html'''
def get_html(url):
    headers = {'User-Agent': ' Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0'}
    req = urllib.request.Request(url=url, headers=headers)
    res = urllib.request.urlopen(req)
    html = res.read().decode('utf-8')
    return html

def drug_spider_new(disease_name):
    initials = []
    for char in disease_name:
        if '\u4e00' <= char <= '\u9fff':  # 检查字符是否为中文
            initials.append(pinyin(char, style=Style.FIRST_LETTER)[0][0])
        elif char.isalpha():
            initials.append(char)
    initials = ''.join(initials)
    try:
        disease_url = 'https://jbk.39.net/%s/' % initials
        drug = drug_crawl(disease_name, disease_url)
        return drug
    except Exception:
        # print(disease_name)
        return []

'''先爬取疾病名称以及别称，再爬取对应药物'''
def drug_crawl(disease_name, url):
    html = get_html(url)
    selector = etree.HTML(html)

    # 先爬取疾病名称
    disease_div = selector.xpath('//div[@class="disease"]')
    if disease_div:
        disease_names = []
        
        # 提取 <h1> 标签内容
        h1_text = disease_div[0].xpath('.//h1/text()')
        if h1_text:
            disease_names.append(h1_text[0].strip())

        # 提取 <h2> 标签内容
        h2_text = disease_div[0].xpath('.//h2/text()')
        if h2_text:
            # 去除多余的空格和括号
            h2_content = h2_text[0].strip()
            # 使用正则表达式分割字符串，保留中文
            h2_items = re.findall(r'[\u4e00-\u9fa5]+', h2_content)
            disease_names.extend(h2_items)

        if disease_name not in disease_names:

            # TODO遇到同拼音首字母的病的情况
            return []
        
    else:
        return []

    #再爬取对应需要的药物
    li_elements = selector.xpath('//ul[@class="information_ul information_ul_bottom"]/li[1]')
    drugs = []

    for li in li_elements:
        a_texts = li.xpath('.//a/text()')
        drugs.extend([a.strip() for a in a_texts])  # 添加所有 <a> 标签的文本
    return drugs
