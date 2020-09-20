# coding=utf-8
# 基于conda env:py35
"""
基于vnote的博客自动发布(hexo)

简单来说包含2部分功能:

01,将vnote中的符合条件的文章（.md文件）,复制到hexo/source/_posts/,

02,符合条件的md文章里面涉及的图片，复制到hexo/source/images/(并修改其内部引用路径格式,以及为图片添加水印)

帮助:python vnote2hexo.py -h

使用示例: python vnote2hexo.py -v /home/john/文档/vnote_notebooks/vnote -s /home/john/opt/hexo/source -f '\[博\].*\.md' -w '/home/john/opt/hexo/source/images_out/water.png'
"""
import argparse
import os
import re
import shutil
import subprocess
from collections import defaultdict, Counter
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
        head=''.join(lines[:9])
        tagsStr = re.findall(r"tags: \[(.*?)\]", head, re.I | re.S | re.M)[0]
        tags = tagsStr.replace('\'', '').replace('\"', '').replace(' ', '').split(',')

        content = ''.join(lines[9:])
        find_all_imgs = re.findall(r"([\d_]+\.(png|jpg|jpeg|gif))", content, re.I | re.S | re.M)
        if find_all_imgs:
            imgs = [k for k, v in find_all_imgs]

    return imgs, tags


# 添加水印
def water_mark(file_path: str, water_path: Optional[str] = None)->None:
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
    parser.add_argument('-s', '--hexo_source_dir', type=str, help='source of hexo dir')
    parser.add_argument('-f', '--filter_reg', type=str, help='md filter reg')
    parser.add_argument('-w', '--water_path', type=str, help='img water path')

    args = parser.parse_args()

    vnote_dir = args.vnote_dir
    hexo_source_dir = args.hexo_source_dir
    filter_reg = args.filter_reg
    water_path = args.water_path

    print('清空hexo文件夹_posts,images')
    hexo_md_dir = hexo_source_dir + '/_posts'
    hexo_img_dir = hexo_source_dir + '/images'
    clean_hexo_cmd = 'rm -rf %s/*' % (hexo_md_dir)
    subprocess.call(clean_hexo_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    hexo_md_paths = list()
    lost_imgs = list()
    new_imgs = list()
    hexo_exist_imgs = set(os.listdir(hexo_img_dir))
    path_tags_map = defaultdict(list)

    for dirpath, dirnames, filenames in os.walk(vnote_dir):
        if dirpath.find('_v_recycle_bin') > -1:
            continue
        for name in filenames:
            if name.endswith('md') and re.search(filter_reg, name, re.M | re.I):
                # 采集文中图片
                img_names, tags = get_imgs_and_tags(dirpath + '/' + name)
                # 文章copy到文章文件夹
                shutil.copy(dirpath + '/' + name, hexo_md_dir)
                # 图片copy到图片文件夹
                img_names = list(set(img_names) - set(hexo_exist_imgs))
                if img_names:
                    try:
                        vnote_img_dir = dirpath + '/_v_images'
                        # 图片复制
                        list(map(lambda img_name: shutil.copy(vnote_img_dir + '/' + img_name, hexo_img_dir), img_names))
                        # 图片加水印
                        list(map(lambda img_name: water_mark(hexo_img_dir + '/' + img_name, water_path), img_names))
                        new_imgs.extend(img_names)
                    except Exception as e:
                        lost_imgs.append(e.filename)
                # 文章内部修改图片引用路径
                hexo_md_path = hexo_md_dir + '/' + name
                hexo_md_paths.append(hexo_md_path)
                with open(hexo_md_path, 'r+', encoding='utf-8') as f:
                    content = ''.join(f.readlines())
                    # _v_images => images
                    content = content.replace('_v_images/', '/images/')
                    # (xx.png =500x) => (xx.png)
                    content = re.sub(r"(png|jpg|jpeg|gif) =\d+x", r"\1", content)
                    f.seek(0)
                    f.truncate()
                    f.seek(0)
                    f.write(content)

                # 收集各路径下的tags
                key = ','.join(dirpath.replace(vnote_dir, '').split('/')[:2])
                path_tags_map[key].extend(tags)
    for key, value in path_tags_map.items():
        path_tags_map[key] = Counter(value)
    print('标签信息')
    tagDf = pd.DataFrame(columns=['path1', 'path2', 'tags'])
    for key, count_map in path_tags_map.items():
        keys = key.split(',')
        tagDf.loc[tagDf.shape[0]] = [keys[0], keys[1] if keys[1:] else '', ','.join(
            ['<a href="/tags/%s" >%s(%s)</a>' % (tag, tag, value) for tag, value in count_map.items()])]
    tagDf = tagDf.sort_values(['path1', 'path2'])
    print('hexo_md_paths:\n%s \n %d' % ('\n'.join(hexo_md_paths), len(hexo_md_paths)))
    print('hexo_img_new:\n%s \n %d' % ('\n'.join(new_imgs), len(new_imgs)))
    print('hexo_img_lost:\n%s \n %d' % ('\n'.join(lost_imgs), len(lost_imgs)))
    print('records')
    print(tagDf.to_dict('records'))
