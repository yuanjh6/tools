import argparse
import os
import re
import shutil

from typing import Tuple, List

"""
基于vnote的博客自动发布(sphinx)

简单来说包含2部分功能:

1,将md和关联的img图片复制到sphinx路径

2,将非标准md(hexo兼容格式)转为标准md格式

帮助:python vnote2hexo.py -h

使用示例:python vnote2sphinx.py -v /home/john/文档/vnote_notebooks/ -s /home/john/opt/sphinx/python_study/source -f python进阶

"""
VNOTE_IMAGE_DIR = '_v_images'


def get_imgs(file_path: str) -> List[str]:
    """
    获取md文件中的所有图片路径和md文件标签信息

    :param file_path: md文件路径
    :return list: str为各图片路径
    """
    imgs = list()
    with open(file_path, 'r') as f:
        lines = f.readlines()
        content = ''.join(lines[9:])
        find_all_imgs = re.findall(r"([\d_]+\.(png|jpg|jpeg|gif))", content, re.I | re.S | re.M)
        if find_all_imgs:
            imgs = [k for k, v in find_all_imgs]

    return imgs


def get_file_imgs(vnote_dir: str, filter_reg: str) -> Tuple[str, str, List[str]]:
    """
    获取vnote_dir目录下满足filter_reg筛选条件的所有文件的,文件名,文件绝对路径,和文件内图片路径列表

    :param vnote_dir: vnote的文件夹路径
    :param filter_reg: 过滤条件
    :return tuple: tuple[0]:文件名 tuple[1]:文件路径 tuple[2]:文件内图片路径
    """
    ret_tuple_list = list()
    for dirpath, dirnames, filenames in os.walk(vnote_dir):
        if dirpath.find('_v_recycle_bin') > -1:
            continue
        for name in filenames:
            if name.endswith('md') and name.find('[博]') >= 0 and re.search(filter_reg, name, re.M | re.I):
                # 采集文中图片
                img_names = get_imgs(os.path.normpath("%s/%s" % (dirpath, name)))
                ret_tuple_list.append((name, dirpath,
                                       [os.path.normpath("%s/%s" % (VNOTE_IMAGE_DIR, img_name)) for img_name in
                                        img_names]))

    return ret_tuple_list


def copy_file_imgs(name: str, path: str, imgs: List[str], target_path: str) -> None:
    """
    拷贝md文件和关联的图片

    01,修改文件名中的[博]字段
    02,修改文件格式为md标准格式

    :param name: md文件名
    :param path: md文件路径
    :param imgs: 图片路径(相对 path)
    :param target_path: 目标路径
    """
    # 复制md
    shutil.copy(os.path.normpath("%s/%s" % (path, name)), os.path.normpath("%s/%s" % (target_path, name)))
    # 复制图片
    [shutil.copy(os.path.normpath("%s/%s" % (path, img)), os.path.normpath("%s/%s" % (target_path, img))) for img in
     imgs if os.path.exists(os.path.normpath("%s/%s" % (path, img)))]


def format_to_md(name, path) -> str:
    """
    md文件转为标准md格式

    :param name: 文件名
    :param path: 文件路径
    :return: new file name
    """
    # 改名
    new_name = name.replace('[博]', '')
    new_file = os.path.normpath("%s/%s" % (path, new_name))
    os.rename(os.path.normpath("%s/%s" % (path, name)), new_file)

    # 删除文件头部的特殊的标记部分
    file_content = open(new_file).readlines()
    file_index = 0
    for line in file_content[1:]:
        file_index += 1
        if line.startswith('---'):
            break
    file_title = new_name.replace('.md', '')
    file_content[file_index] = '# %s\n' % file_title

    # 将```标记外的文档的结尾空格替换为换行
    tmp_count = 0
    new_file_content = list()
    for i in range(file_index, len(file_content)):
        if file_content[i].startswith('```\n'):
            tmp_count += 1
        elif tmp_count % 2 == 0 and file_content[i].endswith('  \n'):
            new_file_content.append(file_content[i].rstrip() + '\n')
            new_file_content.append('\n')
            continue
        new_file_content.append(file_content[i])

    with open(new_file, 'w+') as f:
        f.writelines(new_file_content)
    return file_title


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--vnote_dir', type=str, help='vnote dir')
    parser.add_argument('-s', '--sphinx_source_dir', type=str, help='source of hexo dir')
    parser.add_argument('-f', '--filter_reg', type=str, help='md filter reg')

    args = parser.parse_args()

    vnote_dir = args.vnote_dir
    sphinx_source_dir = args.sphinx_source_dir
    filter_reg = args.filter_reg

    tmp = get_file_imgs(vnote_dir, filter_reg)

    # auto create img dir
    img_dir = '%s/%s' % (sphinx_source_dir, VNOTE_IMAGE_DIR)
    os.path.exists(img_dir) or os.makedirs(img_dir)

    # copy file and imgs
    [copy_file_imgs(name, path, imgs, sphinx_source_dir) for name, path, imgs in tmp]
    # format file
    file_titles = [format_to_md(name, sphinx_source_dir) for name, _, _ in tmp]
    print('\n'.join(sorted(file_titles)))
