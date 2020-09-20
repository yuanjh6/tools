# encoding: UTF-8
# 基于conda env:vnpy19(含有pandas即可)
"""
将pkl转为csv格式(方便直接导入数据库等）

帮助:python pkl2csv.py -h

使用示例:python pkl2csv.py -f '/home/john/下载/dd_price_vp_20200809_20200818.pkl' -m '{"index": "datetime", "volume": "vol"}'

步骤

1,依次取得pkl文件minor_xs轴维度 as df

2,df.reset_index(),df.dropna(),df拼接为all_df

3,all_df.rename()

4,all_df.to_csv(index=False)
"""
import argparse
import json
import os
import sys
from contextlib import suppress
from typing import Dict, Tuple

import pandas as pd
import logging

logger = logging.getLogger()


class PKl2Csv():
    @staticmethod
    def file_path_split(filename: str) -> Tuple[str, str, str]:
        """
        获取文件路径、文件名、后缀

        :param str filename: 文件全路径
        :return tuple: 文件路径、文件名、后缀
        """
        (filepath, tempfilename) = os.path.split(filename)
        (shotname, extension) = os.path.splitext(tempfilename)
        return filepath, shotname, extension

    def trans(self, file_path_pkl: str, rename_map: Dict[str, str] = None) -> None:
        """
        pkl文件转为csv文件

        :param file_path_pkl: pkl文件路径
        :param rename_map: 字段映射字典(dict)
        """
        filepath, shotname, extension = PKl2Csv.file_path_split(file_path_pkl)
        file_path_csv = '%s/%s.%s' % (filepath, shotname, 'csv')
        logger.info('to csv file:%s' % file_path_csv)
        future_data = pd.read_pickle(file_path_pkl)
        all_df = pd.DataFrame()  # columns=['datetime', 'open', 'high', 'low', 'close', 'vol', 'code']
        for minor_xs in future_data.minor_axis:
            logger.info('symbol', minor_xs)
            with suppress(Exception):
                df = future_data.minor_xs(minor_xs)
                df['minor_xs'] = minor_xs
                df = df.reset_index()
                # df.rename(columns={'index': 'datetime', 'volume': 'vol'}, inplace=True)
                df = df.dropna()
                all_df = all_df.append(df)
        if rename_map:
            all_df.rename(columns=rename_map, inplace=True)
        all_df.to_csv(file_path_csv, index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file_path', type=str, help='pkl file path')
    parser.add_argument('-m', '--rename_map', type=str, help='rename dataframe column')

    args = parser.parse_args()
    rename_map = json.loads(args.rename_map)
    pkl2csv = PKl2Csv()
    pkl2csv.trans(args.file_path, rename_map)
