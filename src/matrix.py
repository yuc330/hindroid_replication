import numpy as np
import json
import os
import re
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer

# functions for A
def find_apis(block):
    return re.findall('invoke-\w+ {.*}, (.*?)\\(', block)

def smali2apis(row):
    smalis = '\n'.join(row.dropna())
    return set(find_apis(smalis))

def construct_A(apis):
    mlb = MultiLabelBinarizer()
    A = mlb.fit_transform(apis)
    return A, mlb.classes_

# functions for B
def find_blocks(smali):
    return re.findall( '\.method([\S\s]*?)\.end method', smali)

def smali2blocks(row):
    smalis = '\n'.join(row.dropna())
    return list(set(find_blocks(smalis)))

def block2apis(block):
    apis = set(re.findall('invoke-\w+ {.*}, (.*?)\\(', block))
    for api in apis:
        if api not in B_dict.keys():
            B_dict[api] = apis
        else:
            B_dict[api] = B_dict[api].union(apis)
            
def construct_B(smalis):
    B_dict = {}
    blocks = smalis.apply(smali2blocks, axis = 1).explode().reset_index().iloc[:,1]
    blocks.dropna().apply(block2apis)
    mlb = MultiLabelBinarizer()
    return mlb.fit_transform(B_dict)

#functions for P
def package(api):
    return re.search('(\[*[ZBSCFIJD]|\[*L[\w\/$-]+;)->', api)[1]

def construct_P(apis):
    api_df = pd.DataFrame({'api':apis}).dropna()
    api_df['package'] = api_df.api.apply(package)
    P_dict = api_df.groupby('package')['api'].apply(set).to_dict()
    mlb = MultiLabelBinarizer()
    return mlb.fit_transform(P_dict)

# construct all

def construct_matrices():
    smalis = pd.DataFrame(app_smalis)
    apis = smalis.apply(smali2apis, axis = 1)
    A, all_apis = construct_A(apis)
    B = construct_B(smalis)
    P = construct_P(all_apis)
    return A, B, P