# -*- coding: utf-8 -*-
"""
@Time: 2024/12/8 17:52
@Auth: Zhang Hongxing
@File: tokenizer.py
@Note:   
"""
import os
import re
import jieba
import jieba.analyse
import logging
logging.getLogger('jieba').setLevel(logging.ERROR)


def text_filter(text):
    text = re.sub(r'[\u3000\xa0\xa9\n\t\r]', '', text)
    text = re.sub(r'nbsp+', '', text)
    text = re.sub(r'\d+', '', text)
    return text

def segment(text):
    return jieba.lcut(text)

def bi_mm_segment(text):
    # 创建词典
    word_dict = set()
    folder_path = r'U:\THE_WAY_TO_CODE\MonKeyWords\utils\word_dict'
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    word = line.strip()
                    if word:
                        word_dict.add(word)
    max_len = max(len(word) for word in word_dict)
    # 分别进行前后最大匹配算法
    forward_result = fmm_segment(text, max_len, word_dict)
    backward_result = bmm_segment(text, max_len, word_dict)
    # 取结果较好的
    if len(forward_result) < len(backward_result):
        return forward_result
    elif len(forward_result) > len(backward_result):
        return backward_result
    else:
        # 如果正向和逆向结果长度相同，选择单字数更少的结果
        forward_single_count = sum(1 for word in forward_result if len(word) == 1)
        backward_single_count = sum(1 for word in backward_result if len(word) == 1)
        return forward_result if forward_single_count < backward_single_count else backward_result


def fmm_segment(text, max_len, word_dict):
    result = []
    while text:
        sub_text = text[:max_len]
        for i in range(max_len, 0, -1):
            if sub_text[:i] in word_dict:
                result.append(sub_text[:i])
                text = text[i:]
                break
        else:
            result.append(sub_text[0])
            text = text[1:]
    return result


def bmm_segment(text, max_len, word_dict):
    result = []
    while text:
        sub_text = text[-max_len:]
        for i in range(max_len, 0, -1):
            if sub_text[:i] in word_dict:
                result.append(sub_text[:i])
                text = text[:-i]
                break
        else:
            result.append(sub_text[0])
            text = text[1:]
    return result[::-1]
