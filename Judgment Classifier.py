#!/usr/bin/env python
# coding: utf-8

# 使用套件
import os
import re
import pandas as pd
import numpy as np
from itertools import compress

# 人工標記結果
manual_label_df = pd.read_excel(r'C:\Users\ASUS VivoBook\Desktop\計算與法律分析\Final_Project\判決標註.xlsx', sheet_name = '工作表1') # read all sheets
manual_label_id = list(manual_label_df['檔案編號'])
manual_filename = ['verdict_' + str('{:03}'.format(x)) + '.txt' for x in sorted(manual_label_id)]

# 建立自動判決結果dataframe
dict2df = {'verdict':manual_filename,
          '判決書案號':list(manual_label_df['判決書案號']),
           '駁回_Auto':None,'駁回_Manual':manual_label_df['駁回'],
           '原告引用法條_Auto':None,'法官判決法條_Auto':None,
           '原告引用法條_Manual':manual_label_df['原告引用法條'],
           '法官判決法條_Manual':manual_label_df['法官判決法條'],
           '駁回_Diff':None,'原告引用法條_Diff':None,'法官判決法條_Diff':None
          }
label_df = pd.DataFrame.from_dict(dict2df)
label_df = label_df.set_index(['verdict'])

# 讀去判決書
def read_verdict(entry):
    os.chdir(r'C:\Users\ASUS VivoBook\Desktop\計算與法律分析\Final_Project\All_Verdicts')
    f = open(entry, 'r', encoding = 'utf-8-sig')
    txt = f.readlines()
    txt = [re.sub('\n', '', x) for x in txt]
    txt = [x for x in txt if x != '']
    return txt

# 著作權法第88條項目提取
def case_detection(txt):
    c23_regex = re.compile(r'著作權法(第\d+條)?(、)?第(88|八十八)條(第)?(1|一)?(項)?(、)?(第)?(2|二)(項)?(、)?(或)?(第)?(3|三)項')
    c2_regex = re.compile(r'著作權法(第\d+條)?(、)?第(88|八十八)條第(1|一)?(項)?(、)?(第)?(2|二)項')
    c3_regex = re.compile(r'著作權法(第\d+條)?(、)?第(88|八十八)條第(1|一)?(項)?(、)?(第)?(3|三)項')
    cX_regex = re.compile(r'著作權法(第\d+條)?(、)?第(88|八十八)條(\S+)?')
    if bool(c23_regex.search(txt)) == True:
        return 4
    elif bool(c2_regex.search(txt)) == True:
        return 2
    elif bool(c3_regex.search(txt)) == True:
        return 3
    else:
        return 99

def fill_dataframe(classify_, colname, filename):
    if 4 in classify_:
        label_df.loc[filename,colname] = 4
    elif 3 in classify_:
        label_df.loc[filename,colname] = 3
    elif 2 in classify_:
        label_df.loc[filename,colname] = 2        
    elif 99 in classify_:
        label_df.loc[filename,colname] = 99       
    elif classify_ == []:
        label_df.loc[filename,colname] = 99  

# 著作權法第88條項目分類
def Classify(filename):
    current_verdict = read_verdict(filename)
    # dissmiss detection
    main_rex = re.compile('^主文')
    main_txt = [current_verdict[i] for i, x in enumerate(current_verdict) if main_rex.search(x) != None]
    rex1 = re.compile(r'(應?(連帶)?給付)(周年利率|週年利率|年息|年利率)?(百分之五|百分之5|5％|5%)?')
    if bool(rex1.search(main_txt[0])) == True:
        label_df.loc[filename,'駁回_Auto'] = 0
    else:
        label_df.loc[filename,'駁回_Auto'] = 1

    # 提取著作權法第88條相關條文
    rex88 = re.compile(r'著作權法(第\d+條)?(、)?(第\d+項)?(、)?第(88|八十八)(、\d+-\d)?(、\d+){0,2}?條(第)?(1|一|2|二|3|三)?(項)?(及)?((、)?第(2|二)項)?((、)?第(3|三)項)?((、)?(2|二)項)?((、)?(3|三)項)?')
    filter1 = [current_verdict[i] for i, x in enumerate(current_verdict) if rex88.search(x) != None]
    filter1
    # 原告引用法條
    copyright88 = [filter1[i] for i, x in enumerate(filter1) if re.search(r'(原告|被告|被上訴人|上訴人|被害人|公司)', x) != None]
    copyright88 = [copyright88[i] for i, x in enumerate(copyright88) if not bool(re.search(r'(二造|爭點|抗辯|\?|\？|定有明文)', x)) == True]
    plaintiff = [copyright88[i] for i, x in enumerate(copyright88) if bool(re.search('請求(原告|被告|被害人|上訴人|被上訴人)?(等連帶負損害賠償責任)?', x)) == True]
    # 法官判決法條
    court = [copyright88[i] for i, x in enumerate(copyright88) if bool(re.search('(為有理由|即有理由|洵屬正當|即非不合|核屬正當|應予准許|核屬合法適當|核屬有據|於法有據|即無不合)(，)?(應予准許)?', x)) == True]
    court_ = [x for x in court if x in plaintiff]
    plaintiff_ = [x for x in plaintiff if x not in court_]
    plaintiff_classify = list(set([case_detection(x) for x in plaintiff_]))
    court_classify = list(set([case_detection(x) for x in court_]))
     
    # 填入dataframe
    fill_dataframe(plaintiff_classify, '原告引用法條_Auto', filename)
    fill_dataframe(court_classify, '法官判決法條_Auto', filename)
    
    # 判斷分類對錯
    if label_df.loc[filename, '駁回_Auto'] != label_df.loc[filename, '駁回_Manual']:
        label_df.loc[filename, '駁回_Diff'] = 1
    else:
        label_df.loc[filename, '原告引用法條_Diff'] = 0
    
    if label_df.loc[filename, '原告引用法條_Auto'] != label_df.loc[filename, '原告引用法條_Manual']:
        label_df.loc[filename, '原告引用法條_Diff'] = 1
    else:
        label_df.loc[filename, '原告引用法條_Diff'] = 0
    
    if label_df.loc[filename, '法官判決法條_Auto'] != label_df.loc[filename, '法官判決法條_Manual']:
        label_df.loc[filename, '法官判決法條_Diff'] = 1
    else:
        label_df.loc[filename, '法官判決法條_Diff'] = 0

def Copyright_88_Classifier(filename_lst):
    # 將挑選判決進行分類並填入表格
    for filename in filename_lst:
        Classify(filename)
    
    
    # 結果分析    
    dismiss_wrong = label_df.loc[label_df['駁回_Diff'] == 1,:]
    
    all_wrong = label_df.loc[label_df.loc[:,['原告引用法條_Diff','法官判決法條_Diff']].sum(axis = 1) == 2,:]
    tmp = label_df.loc[label_df['原告引用法條_Diff'] == 1,:]
    plaintiff_wrong = tmp.loc[[ind for ind in list(tmp.index) if ind not in list(all_wrong.index)],:] 
    tmp = label_df.loc[label_df['法官判決法條_Diff'] == 1,:]
    court_wrong = tmp.loc[[ind for ind in list(tmp.index) if ind not in list(all_wrong.index)],:] 
    all_right = label_df.loc[label_df.loc[:,['原告引用法條_Diff','法官判決法條_Diff']].sum(axis = 1) == 0,:]
    summary_dict = {'Case':['僅原告引用法條分錯', '僅法官判決法條分錯','皆分錯','皆分對','總和'],
                  'amount':None,'proportion':None}
    summary_df = pd.DataFrame.from_dict(summary_dict)
    summary_df = summary_df.set_index(['Case'])

    summary_df.iloc[0,0:2] = [len(plaintiff_wrong), len(plaintiff_wrong)/len(label_df)]
    summary_df.iloc[1,0:2] = [len(court_wrong), len(court_wrong)/len(label_df)]
    summary_df.iloc[2,0:2] = [len(all_wrong), len(all_wrong)/len(label_df)]
    summary_df.iloc[3,0:2] = [len(all_right), len(all_right)/len(label_df)]
    summary_df.iloc[4,0:2] = summary_df.iloc[0:4,].sum(axis = 0)
    summary_df
    return label_df, summary_df, dismiss_wrong

label_df, summary_df, dismiss = Copyright_88_Classifier(manual_filename)
