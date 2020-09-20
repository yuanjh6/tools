# encoding: UTF-8
# 基于conda env:py35(opencv)
"""
寻找过滤有效的rtmp,or,rtsp直播地址

python valid_rtmp.py -u https://blog.csdn.net/osle123/article/details/52757886

步骤:

1,下载页面：https://blog.csdn.net/osle123/article/details/52757886（避免使用csdn等，需点击触发显示全部的网页）

2,正则匹配：rtmp://, rtsp://等地址

3,[rtmp;//xx.com,rtsp://yy.com]使用ping+cv2.read()验证有效性
"""
import argparse
import logging
import re
from contextlib import suppress
from multiprocessing import cpu_count, Pool
from typing import List

import cv2
import requests

logger = logging.getLogger()


class ValidRtmp():
    """采集过滤有效的rtmp,or,rtsp播放地址"""

    headers = {
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Sec-Fetch-Dest': 'empty',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Referer': 'https://www.baidu.com/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7,tr;q=0.6,fr;q=0.5,zh-TW;q=0.4',
        'Cookie': 'BIDUPSID=8C26E1690527F4CB4ED508565EBE810E; PSTM=1586487982; BAIDUID=8C26E1690527F4CBE9EBFA9A228B6F9B:FG=1; BD_HOME=1; H_PS_PSSID=30971_1422_21088_30839_31186_31217_30823_31163; BD_UPN=123353'
    }

    @staticmethod
    def get_rtmp_url(url: str) -> List[str]:
        """
        获取url网页内容中的rtsp,rtmp地址

        :param str url: 待采集的种子url地址
        :return list: 种子url中的rtsp,rtmp地址
        """
        with suppress(Exception):
            response = requests.get(url, headers=headers, timeout=(3, 7))
            content = response.text.replace(" ", "")
            res_url = r"((rtsp|rtmp):\/\/[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?)"
            urls = re.findall(res_url, content, re.I | re.S | re.M)
            return [x[0] for x in urls]
        return list()

    @staticmethod
    def valid(url: str) -> str:
        """
        是否是合法的rtsp,rtmp地址

        :param str url:待验证的url(rtsp or rtmp)地址，
        :return str: 如果：是，返回入参的url，如果：不是，返回空串
        """
        with suppress(Exception):
            cap = cv2.VideoCapture(url)
            ret, frame = cap.read()
            if ret:
                return url
        return ''


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', help='url address')

    args = parser.parse_args()
    url = args.url
    valid_rtmp = ValidRtmp()
    candidate_urls = valid_rtmp.get_rtmp_url(url)
    logger.info('candidate_urls len:%d' % len(candidate_urls))
    valid_urls = list()

    pool = Pool(processes=max(1, cpu_count() - 1))
    valid_urls = pool.map(valid_rtmp.valid, candidate_urls)
    pool.close()
    pool.join()
    valid_urls = [x for x in set(valid_urls) if x]

    logger.info('valid_urls: len %d \n %s' % (len(valid_urls), valid_urls))
