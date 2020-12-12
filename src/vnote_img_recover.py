# coding=utf-8
# 基于conda env:tools

"""
基于vnote的图片链接自动修复  


问题原因：vnote的小bug

导致图片链接和图片无法对应（图片误删到了回收站里），同时由于回收站的图片可能是有用的，也不敢随意删除其图片文件，导致其日益臃肿  


问题出现场景  

vnote中如果将一篇文章和另一篇文章合并（复制，粘贴） 

情景01：

比如把（同一个目录下的）文章A的一部分拷贝到文章B中，文章A包含部分图片0001.jpg  

那么保存后，vnote会将A中的图片删掉（移动到回收站目录），导致B中的图片成为失效链接  

情景02：

跨文件夹复制时，如果包含图片，也会导致A的图片移动到A所在目录的回收站中，粘贴到的文章B中，只包含图片连接，不包含图片（图片不会自动复制过来）  


解决方案：

收集所有文章中的图片链接，然后按照文件名匹配的方式将回收站中的图片复制到文章对应的路径中

同时，文章中的缺失的图片被修复后，就可以放心的删除各路径回收站里的图片了，避免了部分无用图片长期占用空间的麻烦  

代码思路：

01，找到所有文章中图片，文章路径+图片地址=》图片理论存在地址

02，图片理论存在地址，有没有相应图片，有=》ok，无=》记录下来

03, 遍历vnote回收站里的图片文件，建立 文件名=》文件路径 的字典

04，对于无法对应的图片（上面的“无”），搜索vnote回收站，如果，有=》复制到图片应该存在的位置，无=》记录下图片缺失信息

05，输出自动修复了那些文件链接，哪些是无法自动修复的

06, 自动删除回收站里的图片（减少空间占用）（可选参数）


帮助:python vnote_img_recover.py -h

使用示例: python vnote_img_recover.py -v /home/john/opt/vnote/vnote/ -d false

参考本博客博文：脚本_vnote同步到hexo步骤[博]（自行搜索）
"""
import argparse
import os
import re
import shutil
import subprocess
from collections import defaultdict, Counter
from pprint import pprint
from typing import Optional
import pandas as pd


def get_imgs_and_tags(file_path: str):
    """
    获取md文件中的所有图片路径和md文件标签信息

    :param file_path: md文件路径
    :return tuple: tuple[0]:list[str] md文件中的所有图片路径,tuple[1]:list[str] md文件的标签信息
    """
    imgs = list()
    tags = list()
    with open(file_path, 'r') as f:
        lines = f.readlines()

        content = ''.join(lines[9:])
        find_all_imgs = re.findall(r"([\d_]+\.(png|jpg|jpeg|gif))", content, re.I | re.S | re.M)
        if find_all_imgs:
            imgs = [k for k, v in find_all_imgs]

    return imgs, tags


# 添加水印
def water_mark(file_path: str, water_path: Optional[str] = None) -> None:
    """
    为图片加水印(借助ffmpeg)

    :param file_path: 需要添加水印的图片
    :param water_path: 水印图片
    :return: None
    """
    if not water_path:
        return
    ffmpeg_cmd = "ffmpeg -i %s -i %s -filter_complex 'overlay=main_w-overlay_w-10 : main_h-overlay_h-10' %s -y" % (
        file_path, water_path, file_path)
    subprocess.call(ffmpeg_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--vnote_dir', type=str, help='vnote dir')
    parser.add_argument('-d', '--auto_delete', type=bool, help='auto delete useless imgs in _v_recycle_bin',
                        default=False)
    args = parser.parse_args()

    vnote_dir = args.vnote_dir
    delete_img_dir = vnote_dir + '_v_recycle_bin'

    lost_imgs_map = dict()  # key:img name ,value:img full path
    deleted_imgs_map = dict()  # key:img name,value:img full path

    # md file link imgs
    for dirpath, dirnames, filenames in os.walk(vnote_dir):
        if dirpath.find('_v_recycle_bin') > -1:
            # ignore deleted md file
            continue
        for name in filenames:
            if name.endswith('md'):
                # 采集文中图片
                img_names, tags = get_imgs_and_tags(dirpath + '/' + name)
                if img_names:
                    vnote_img_dir = dirpath + '/_v_images'
                    for img_name in img_names:
                        img_full_path = vnote_img_dir + '/' + img_name
                        if not os.path.exists(img_full_path):
                            lost_imgs_map[img_name] = img_full_path

    # deleted imgs
    for dirpath, dirnames, filenames in os.walk(delete_img_dir):
        if filenames:
            deleted_imgs_map.update({img_name: dirpath + '/' + img_name for img_name in filenames if
                                     img_name[-3:] in ('png', 'jpg', 'peg', 'gif')})

    # copy deleted imgs => md imgs
    # success recover imgs
    recoverd_imgs = list()
    recoverd_failt_imgs = list()
    for img_name, img_full_path in lost_imgs_map.items():
        if img_name not in deleted_imgs_map:
            recoverd_failt_imgs.append((img_name, img_full_path))
            continue
        source_path = deleted_imgs_map[img_name]
        to_path = img_full_path
        shutil.copy(source_path, img_full_path)
        recoverd_imgs.append((source_path, img_full_path))
    print('recoverd_imgs')
    pprint(recoverd_imgs, width=160)
    print('recoverd_failt_imgs')
    pprint(recoverd_failt_imgs, width=160)
