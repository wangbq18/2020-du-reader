import os
import config
import torch
import random
import pickle
from tqdm import tqdm
from torch import nn, optim

from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader
from transformers import BertTokenizer, BertForQuestionAnswering, BertConfig

from transformers import BertForQuestionAnswering, BertConfig
from utils import *
# 随机种子
random.seed(config.seed)
torch.manual_seed(config.seed)
import json


def load_test_data(filename):
    D = []
    for d in json.load(open(filename))['data'][0]['paragraphs']:
        for qa in d['qas']:
            # if qa['id']!='231442c96235d3acd16ed5042600a60d':continue
            D.append([
                qa['id'], d['context'], qa['question']
                # [a['text'] for a in qa.get('answers', [])]
            ])
    return D


def predict():
    # 1 封装数据

    VOCAB_PATH = '../lm_pretrained/ernie/vocab.txt'
    #VOCAB_PATH = Path(VOCAB_PATH)
    tokenizer = BertTokenizer.from_pretrained(
                    VOCAB_PATH, cache_dir=None, do_lower_case=True)
    test_set = ReaderDataset(test_data, tokenizer=tokenizer, mode='test')
    test_dataloader = DataLoader(test_set, batch_size=60,
                                  shuffle=False, num_workers=0, collate_fn=collate_fn_test)

    # 2 载入模型
    # 加载预训练bert
    MODEL_PATH = '../lm_pretrained/ernie/'
    model = BertForQuestionAnswering.from_pretrained(MODEL_PATH)
    device = config.device
    model.to(device)

    # 3 载入权重

    model.load_state_dict(torch.load("../model/ernie_epoch_1_f1_82.569.pt"))

    # 4 开始预测
    with torch.no_grad():
        model.eval()
        pred_results = {}
        for batch in tqdm(test_dataloader):
            q_ids, raw_sentence, input_ids, segment_ids = batch
            input_ids, segment_ids = \
                input_ids.to(device), segment_ids.to(device)
            input_mask = (input_ids > 0).to(device)
            start_prob, end_prob = model(input_ids.to(device),
                                         token_type_ids=segment_ids.to(device),
                                         attention_mask=input_mask.to(device)
                                         )
            # start_prob = start_prob.squeeze(0)
            # end_prob = end_prob.squeeze(0)
            for i in range(len(batch[0])):
                try:
                    (best_start, best_end), max_prob = find_best_answer_for_passage(start_prob[i], end_prob[i])
                    if type(max_prob) == int:
                        max_prob = 0
                    else:
                        max_prob = max_prob.cpu().numpy()[0]
                except:
                    pass
                if q_ids[i] in pred_results:
                    pred_results[q_ids[i]].append(
                        (raw_sentence[i][best_start.cpu().numpy()[0]:best_end.cpu().numpy()[0]], max_prob))
                else:
                    pred_results[q_ids[i]] = [(raw_sentence[i][best_start.cpu().numpy()[0]:best_end.cpu().numpy()[0]], max_prob)]
        # 保留最大概率的答案
        for id in pred_results:
            pred_results[id] = sorted(pred_results[id], key=lambda x: x[1], reverse=True)[0]

        submit = {}
        for item in test_data:
            q_id = item[0]
            question = item[2]
            if q_id not in pred_results:continue
            submit[q_id] = pred_results[q_id][0].strip()
            print(question, pred_results[q_id][0].strip())

        submit_path = '../submit/submit-0509_v1.json'

        predict_to_file(submit, submit_path)


def predict_to_file(submit_dict, out_file):
    """预测结果到文件，方便提交
    """
    fw = open(out_file, 'w', encoding='utf-8')
    R = json.dumps(submit_dict, ensure_ascii=False, indent=4)
    fw.write(R)
    fw.close()


if __name__ == "__main__":
    # 1 载入数据
    test_data = load_test_data('../data/test1.json')
    print(len(test_data))
    predict()
