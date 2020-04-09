# #! -*- coding: utf-8 -*-
# # 百度LIC2020的机器阅读理解赛道，非官方baseline
# # 直接用RoBERTa+Softmax预测首尾
# # BASE模型在第一期测试集上能达到0.67的F1，基本持平（略低于）官方baseline
# # 如果你显存足够，可以换用RoBERTa Large模型，F1可以到0.69+
#
# import json, os
# import numpy as np
# from bert4keras.backend import keras, K
# from bert4keras.models import build_transformer_model
# from bert4keras.tokenizers import Tokenizer
# from bert4keras.optimizers import Adam
# from bert4keras.snippets import sequence_padding, DataGenerator
# from bert4keras.snippets import open
# from keras.layers import Layer, Dense, Permute
# from keras.models import Model
# from tqdm import tqdm
#
# # 基本信息
# maxlen = 256
# epochs = 20
# batch_size = 32
# learing_rate = 1e-5
#
# # bert配置
# config_path = '/root/kg/bert/chinese_roberta_wwm_ext_L-12_H-768_A-12/bert_config.json'
# checkpoint_path = '/root/kg/bert/chinese_roberta_wwm_ext_L-12_H-768_A-12/bert_model.ckpt'
# dict_path = '/root/kg/bert/chinese_roberta_wwm_ext_L-12_H-768_A-12/vocab.txt'
#
#
# def load_data(filename):
#     D = []
#     for d in json.load(open(filename))['data'][0]['paragraphs']:
#         for qa in d['qas']:
#             D.append([
#                 qa['id'], d['context'], qa['question'],
#                 [a['text'] for a in qa.get('answers', [])]
#             ])
#     return D
#
#
# # 读取数据
# train_data = load_data(
#     'data/train.json'
# )
# #
# # # 建立分词器
# # tokenizer = Tokenizer(dict_path, do_lower_case=True)
#
#
# def search(pattern, sequence):
#     """从sequence中寻找子串pattern
#     如果找到，返回第一个下标；否则返回-1。
#     """
#     n = len(pattern)
#     for i in range(len(sequence)):
#         if sequence[i:i + n] == pattern:
#             return i
#     return -1
#
#
# class data_generator(DataGenerator):
#     """数据生成器
#     """
#     def __iter__(self, random=False):
#         batch_token_ids, batch_segment_ids, batch_labels = [], [], []
#         for is_end, item in self.sample(random):
#             context, question, answers = item[1:]
#             token_ids, segment_ids = tokenizer.encode(
#                 question, context, max_length=maxlen
#             )
#             a = np.random.choice(answers)
#             a_token_ids = tokenizer.encode(a)[0][1:-1]
#             start_index = search(a_token_ids, token_ids)
#             if start_index != -1:
#                 labels = [[start_index], [start_index + len(a_token_ids) - 1]]
#                 batch_token_ids.append(token_ids)
#                 batch_segment_ids.append(segment_ids)
#                 batch_labels.append(labels)
#                 if len(batch_token_ids) == self.batch_size or is_end:
#                     batch_token_ids = sequence_padding(batch_token_ids)
#                     batch_segment_ids = sequence_padding(batch_segment_ids)
#                     batch_labels = sequence_padding(batch_labels)
#                     yield [batch_token_ids, batch_segment_ids], batch_labels
#                     batch_token_ids, batch_segment_ids, batch_labels = [], [], []
#
#
# # class MaskedSoftmax(Layer):
# #     """在序列长度那一维进行softmax，并mask掉padding部分
# #     """
# #     def compute_mask(self, inputs, mask=None):
# #         return None
# #
# #     def call(self, inputs, mask=None):
# #         if mask is not None:
# #             mask = K.cast(mask, K.floatx())
# #             mask = K.expand_dims(mask, 2)
# #             inputs = inputs - (1.0 - mask) * 1e12
# #         return K.softmax(inputs, 1)
# #
#
# # model = build_transformer_model(
# #     config_path,
# #     checkpoint_path,
# # )
#
# # output = Dense(2)(model.output)
# # output = MaskedSoftmax()(output)
# # output = Permute((2, 1))(output)
# #
# # model = Model(model.input, output)
# # model.summary()
#
# #
# # def sparse_categorical_crossentropy(y_true, y_pred):
# #     # y_true需要重新明确一下shape和dtype
# #     y_true = K.reshape(y_true, K.shape(y_pred)[:-1])
# #     y_true = K.cast(y_true, 'int32')
# #     y_true = K.one_hot(y_true, K.shape(y_pred)[2])
# #     # 计算交叉熵
# #     return K.mean(K.categorical_crossentropy(y_true, y_pred))
# #
# #
# # def sparse_accuracy(y_true, y_pred):
# #     # y_true需要重新明确一下shape和dtype
# #     y_true = K.reshape(y_true, K.shape(y_pred)[:-1])
# #     y_true = K.cast(y_true, 'int32')
# #     # 计算准确率
# #     y_pred = K.cast(K.argmax(y_pred, axis=2), 'int32')
# #     return K.mean(K.cast(K.equal(y_true, y_pred), K.floatx()))
#
#
#
#
#
# # def extract_answer(question, context, max_a_len=16):
# #     """抽取答案函数
# #     """
# #     token_ids, segment_ids = tokenizer.encode(
# #         question, context, max_length=maxlen
# #     )
# #     probas = model.predict([[token_ids], [segment_ids]])[0]
# #     start_end, score = None, -1
# #     for start, p_start in enumerate(probas[0]):
# #         for end, p_end in enumerate(probas[1]):
# #             if end >= start and end < start + max_a_len:
# #                 if p_start * p_end > score:
# #                     start_end = (start, end + 1)
# #                     score = p_start * p_end
# #     answer_id = token_ids[start_end[0]:start_end[1]]
# #     return tokenizer.decode(answer_id).replace(' ', '')  # 去掉空格分数更高
#
#
# # def predict_to_file(infile, out_file):
# #     """预测结果到文件，方便提交
# #     """
# #     fw = open(out_file, 'w', encoding='utf-8')
# #     R = {}
# #     for d in tqdm(load_data(infile)):
# #         a = extract_answer(d[2], d[1])
# #         R[d[0]] = a
# #     R = json.dumps(R, ensure_ascii=False, indent=4)
# #     fw.write(R)
# #     fw.close()
#
#
# # def evaluate(filename):
# #     """评测函数（官方提供评测脚本evaluate.py）
# #     """
# #     predict_to_file(filename, filename + '.pred.json')
# #     metrics = json.loads(
# #         os.popen(
# #             'python /root/baidu/datasets/rc/dureader_robust-data/evaluate.py %s %s'
# #             % (filename, filename + '.pred.json')
# #         ).read().strip()
# #     )
# #     return metrics
#
#
# # class Evaluator(keras.callbacks.Callback):
# #     """评估和保存模型
# #     """
# #     def __init__(self):
# #         self.best_val_f1 = 0.
# #
# #     def on_epoch_end(self, epoch, logs=None):
# #         metrics = evaluate(
# #             '/root/baidu/datasets/rc/dureader_robust-data/dev.json'
# #         )
# #         if metrics['F1'] >= self.best_val_f1:
# #             self.best_val_f1 = metrics['F1']
# #             model.save_weights('best_model.weights')
# #         metrics['BEST F1'] = self.best_val_f1
# #         print(metrics)
#
#
# if __name__ == '__main__':
#
#     train_generator = data_generator(train_data, batch_size)
#     # evaluator = Evaluator()
#     #
#     # model.fit_generator(
#     #     train_generator.forfit(),
#     #     steps_per_epoch=len(train_generator),
#     #     epochs=epochs,
#     #     callbacks=[evaluator]
#     # )
#
#
#     # model.load_weights('best_model.weights')
#     # predict_to_file('/root/baidu/datasets/rc/dureader_robust-test1/test1.json', 'rc_pred.json')