# coding=utf-8
# 基于conda env:tools
"""
工具:将vnote的md格式转为hexo的md格式

功能说明

个人博客采用hexo博客,但书写工具惯用vnote,二者均支持markdown格式,但hexo博客支持部分markdown扩展标记(类别,标签等)

这部分并非标准md格式要求,所以发布博客前都需要手工做格式转换(主要是在md头部增加一些信息),

属于固定的体力活,将其交给脚本更合适

在标准md文档头部,

生成类似下面的内容作为文件前缀(同时，删除文件正文首行的title)
---
title: 理财_保险[博]
date: 2019-12-02 15:24:52
categories: ['生活', '其他']
tags: []
toc: true

---
帮助:python vnote_md_format.py -h

使用示例:

递归查询目录下所有md文件，生成md文件的前缀信息

python vnote_md_format.py -f 目录

生成文件的前缀，此时文件的cate=目录1,目录2

python vnote_md_format.py -f ./目录1/目录2/文件.md(x)

python vnote_md_format.py -f 文件.md


特殊说明：

01,文章的categories其实是文件路径切分，所以执行脚本前,vnoteMdFormat.py文件位置最好和md文件或者文件夹同级位置

比如：脚本位置:/xxx/yyy/zzz/vnoteMdFormat.py

你的md文件位置:/fff/mmm/kkk/vnote/生活/日记20200328.md

此时如果你在路径:/xxx/yyy/zzz/下执行脚本,python vnoteMdFormat.py /fff/mmm/kkk/vnote/生活/日记20200328.md

这样的话md文件的categories,是，fff,mmm,kkk,vnote,生活,但大多数情况，fff,mmm,可能是没用的，比如home/username/等无意义的

所以建议，将vnoteMdFormat.py放到/fff/mmm/kkk/vnote/下面，在/fff/mmm/kkk/vnote/下执行:python vnoteMdFormat.py 生活/日记20200328.md

如此的化，生成的文章的categories则为['生活'],基本符合本意

如下命令是：

1,vnoteMdFormat.py复制到md所在文件夹　/home/john/文档/vnote_notebooks/vnote/

2,在md所在文件夹外执行python vnoteMdFormat.py $(ls -I _v_recycle_bin)

3,删除第１步复制过来的vnoteMdFormat.py脚本文件

建议使用前，单个步骤执行下，看下各个命令都什么效果，避免错了，还要在修改.md文件
```
cp vnoteMdFormat.py /home/john/文档/vnote_notebooks/vnote/ && cd /home/john/文档/vnote_notebooks/vnote/ && conda activate py35 && python vnoteMdFormat.py $(ls -I _v_recycle_bin) && rm vnoteMdFormat.py
```
02,阅读代码可以发现，对于文章标题(也即是文件名)如果含有[密]，则自动增加字段password: xxxxyyyy ,为了实现对文章添加密码，没有密码无法访问（需要hexo插件配合)

"""
import argparse
import io
import os
import re
import sys
import time
from pprint import pprint
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.nlp.v20190408 import nlp_client, models
import hashlib
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')

TencentSecretId = os.environ.get('TencentSecretId')
TencentSecretKey = os.environ.get('TencentSecretKey')
# 访问凭证去腾讯找，参考：https://console.cloud.tencent.com/nlp/basicguide
cred = credential.Credential(TencentSecretId, TencentSecretKey)
http_profile = HttpProfile()
http_profile.endpoint = "nlp.tencentcloudapi.com"

client_profile = ClientProfile()
client_profile.httpProfile = http_profile
client = nlp_client.NlpClient(cred, "ap-guangzhou", client_profile)
req = models.KeywordsExtractionRequest()

# 记录addr对应文章，用于输出冲突文章，手工处理
abbr_map = dict()


# 时间戳转换
def timestamp_to_time(timestamp):
    """
    时间戳转为字符串形式日期(格式:%Y-%m-%d %H:%M:%S)

    :param timestamp: 时间戳
    :return: 字符串形式日期
    """
    time_struct = time.localtime(timestamp)
    return time.strftime('%Y-%m-%d %H:%M:%S', time_struct)


def get_file_datetime(fullFilePath: str):
    """
    文件创建时间

    :param fullFilePath: 文件路径
    :return: 字符串格式文件创建时间
    """
    return timestamp_to_time(os.path.getctime(fullFilePath))


def get_file_categories(fullFilePath: str):
    """
    文件类别,文件全路径的层次切分

    :param fullFilePath: 文件全路径
    :return: 文件路径切分
    """
    return filter(lambda x: x != '.' and x != '/' and x != '', fullFilePath.split('/')[:-1])


def get_file_keywords(title: str):
    """
    从文章标题中提取出关键词(腾讯云-自然语言处理)

    :param title: 文章标题
    :return: 文章关键词
    """
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.nlp.v20190408 import nlp_client, models

    # todo should't here,but outer can't use sphinx autodoc
    # 访问凭证去腾讯找，参考：https://console.cloud.tencent.com/nlp/basicguide
    cred = credential.Credential("xxx", "yyy")
    http_profile = HttpProfile()
    http_profile.endpoint = "nlp.tencentcloudapi.com"

    client_profile = ClientProfile()
    client_profile.httpProfile = http_profile
    client = nlp_client.NlpClient(cred, "ap-guangzhou", client_profile)
    req = models.KeywordsExtractionRequest()

    title = re.sub(r'\[.*?\]', r'', title).replace('_', ',')  # 去除[]中的东西
    title = re.sub(r'\d+', r'', title)
    params = '{"Num":10,"Text":"%s"}' % title
    req.from_json_string(params)
    resp = client.KeywordsExtraction(req)
    return [item.Word for item in resp.Keywords]


def get_file_abbr(title: str):
    """
    通过文章标题产生md5

    :param title: 文章标题
    :return: 文章md5
    """
    return hashlib.md5(title.encode('utf-8')).hexdigest()[-8:]


class MdArticle(object):
    # 从文件中初始化
    def __init__(self, full_file_path=''):
        self.full_file_path = full_file_path
        self.title = ''
        self.date = ''
        self.categories = ''
        self.tags = ''
        self.keywords = ''
        self.abbrlink = ''
        self.data = []
        self.modifyed = False
        if self.full_file_path.strip():
            # 操作文件
            with open(self.full_file_path, 'r+') as f:
                end_line_num = 0
                lines = f.readlines()
                if len(lines) > 0 and lines[0] == '---\n':
                    for i in range(1, len(lines)):
                        if lines[i] != '---\n':
                            if lines[i].startswith('title: '):
                                self.title = lines[i][7:].strip()
                            elif lines[i].startswith('date: '):
                                self.date = lines[i][6:].strip()
                            elif lines[i].startswith('categories: '):
                                self.categories = lines[i][12:].strip()
                            elif lines[i].startswith('keywords: '):
                                self.keywords = lines[i][9:].strip()
                            elif lines[i].startswith('tags: '):
                                self.tags = lines[i][5:].strip()
                            elif lines[i].startswith('abbrlink: '):
                                self.abbrlink = lines[i][10:].strip()
                        else:
                            end_line_num = i
                            break
                # 拼接新文件
                if end_line_num == 0:
                    self.data.extend(lines[0:])
                else:
                    self.data.extend(lines[end_line_num + 1:])
                f.close()
        return

    # 填充修改自身信息
    def fill_info(self) -> None:
        """
        为原始文章补充hexo字段信息

        补充信息:文件创建日期,文章类别(文件路径的切分),文章关键词,文章标签(和关键词一样),文章永久链接(标题的md5)等信息

        :return: None
        """
        (file_path, full_filename) = os.path.split(self.full_file_path)
        (filename, file_extension) = os.path.splitext(full_filename)

        self.title = filename.replace('[博]', '')
        if not self.date:
            self.modifyed = True
            self.date = get_file_datetime(self.full_file_path)
        self.categories = str(list(get_file_categories(self.full_file_path)))
        if len(self.keywords) <= 0:
            self.modifyed = True
            self.keywords = ','.join(get_file_keywords(title=file_path.replace('/', ',') + ',' + self.title))

        if len(self.tags) <= 2:  # str形式list,至少含有[]2个字符
            self.modifyed = True
            self.tags = '[' + self.keywords + ']'

        if len(self.abbrlink.strip()) == 0:
            self.modifyed = True
            self.abbrlink = str(get_file_abbr(self.title))
        abbr_map[self.abbrlink] = abbr_map.get(self.abbrlink, list()) + [filename]
        return

    # 保存到文件中
    def save(self) -> None:
        """
        保存文章到磁盘

        :return: None
        """
        # 获得文章date和tags(优先使用原有数据)
        file_prefix_lines = ['---\n']
        # 文件名，填充title
        file_prefix_lines.append('title: %s  \n' % self.title)
        # 文件创建时间，填充date
        file_prefix_lines.append('date: %s  \n' % self.date)
        # 文件相对路径，填充categories
        file_prefix_lines.append('categories: %s  \n' % str(self.categories))
        file_prefix_lines.append('keywords: %s  \n' % str(self.keywords))
        file_prefix_lines.append('tags: %s  \n' % str(self.tags))
        # 收尾
        file_prefix_lines.append('toc: true  \n')
        file_prefix_lines.append('abbrlink: %s  \n' % self.abbrlink)
        if self.title.find('[密]') > -1:
            file_prefix_lines.append('password: xxxxyyyy  \n')
        file_prefix_lines.append('\n---\n')
        # 标题也重新生成,标题不重新生成
        # filePrefixLines.append('# %s\n' % self.title)
        file_prefix_lines.extend(self.data)

        # 操作文件
        with open(self.full_file_path, 'r+') as f:
            f.truncate()
            f.writelines(file_prefix_lines)
            f.flush()
            f.close()
        return


# 处理单文件
def handle_file(full_file_path: str) -> bool:
    """
    处理单个md文件

    :param full_file_path: md文件路径
    :return: bool: 文件是否被更新
    """
    if not full_file_path.endswith('.md'):
        return

    md_article = MdArticle(full_file_path)
    md_article.fill_info()
    md_article.save()
    return md_article.modifyed


# 处理目录
def handle_dir(file_dir: str):
    """
    处理md文件目录(批量处理目录下md文件)

    :param file_dir: md文件目录
    """
    # for root, dirs, files in os.walk(fileDir):
    #     for file in files:
    #         print(os.path.join(root, file))
    all_full_file_path = [os.path.join(root, file) for root, dirs, files in os.walk(file_dir) for file in files]
    [handle_file(full_file_path) for full_file_path in all_full_file_path]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file_or_dir_list', type=str, nargs='+', help='file or dir list')

    args = parser.parse_args()
    file_or_dir_list = args.file_or_dir_list

    print('params: %s' % file_or_dir_list)
    modifyed_files = list()
    for param in file_or_dir_list:
        if os.path.isdir(param):
            handle_dir(param)
        elif os.path.isfile(param):
            handle_file(param) and modifyed_files.append(param)

    print('modifyed_files')
    pprint(modifyed_files, width=160)
    abbr_conflict_map = {k: v for k, v in abbr_map.items() if len(v) > 1}
    print('abbr_conflict_map')
    pprint(abbr_conflict_map, width=160)
