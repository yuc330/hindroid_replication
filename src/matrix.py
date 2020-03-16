import numpy as np
import json
import os
import re
import pandas as pd
import scipy.sparse
from sklearn.preprocessing import MultiLabelBinarizer

def get_Xy(cat1, cat2, y_col = 'malware'):
    """
    given two lists of lists of smali files, each for different category, return a dataframe for smali files and a list of labels

    Args:
        cat1: first category of smali data with label 0
        cat2: second category of smali data with label 1
        y_col: column name for labels, default malware
        
    """
    df1 = pd.DataFrame(cat1)
    df1[y_col] = 0
    df2 = pd.DataFrame(cat2)
    df2[y_col] = 1
    all_df = pd.concat([df1, df2])
    smalis = all_df.drop(y_col,1)
    y = all_df[y_col]
    return smalis, y

# functions for A
def find_apis(block):
    """
    find all apis in the block

    Args:
        block - string of smali to look for api
        
    """
    return re.findall('invoke-\w+ {.*}, (.*?)\\(', block)

def smali2apis(row):
    """
    output a set of unique apis of an app given series of smali files

    Args:
        row - series of smali files
        
    """
    smalis = '\n'.join(row.dropna())
    return set(find_apis(smalis))

def construct_A(apis):
    """
    construct A matrix

    Args:
        apis - a series of set of apis, each set representing the apis for an app
        
    """
    mlb = MultiLabelBinarizer(sparse_output = True)
    A = mlb.fit_transform(apis)
    return A, mlb.classes_

def construct_A_test(apis, classes):
    """
    construct A matrix for testing set

    Args:
        apis - a series of set of apis, each set representing the apis for an app
        classes - apis to check for in this series
        
    """
    mlb = MultiLabelBinarizer(sparse_output = True, classes = classes)
    A = mlb.fit_transform(apis)
    return A

# functions for B
def find_blocks(smali):
    """
    find all code blocks in a smali file

    Args:
        smali - string of smali to check for code blocks
        
    """
    return re.findall( '\.method([\S\s]*?)\.end method', smali)

def smali2blocks(row):
    """
    find all code blocks given a series of smali files

    Args:
       row - series of smali files 
        
    """
    smali = '\n'.join(row.dropna())
    return list(set(find_blocks(smali)))


def construct_B(smalis):
    """
    construct B matrix

    Args:
        smalis - dataframe of smali files
        
    """
    B_dict = {}
    def block2apis(block):
        """
        helper method to find all apis in a block and update dictionary B_dict

        Args:
            block - string of block to find apis and update B_dict
            
        """
        apis = set(re.findall('invoke-\w+ {.*}, (.*?)\\(', block))
        for api in apis:
            if api not in B_dict.keys():
                B_dict[api] = apis
            else:
                B_dict[api] = B_dict[api].union(apis)
            
    blocks = smalis.apply(smali2blocks, axis = 1).explode() #get a series of blocks
    blocks.dropna().apply(block2apis) #update B_dict
    mlb = MultiLabelBinarizer(sparse_output = True)
    return mlb.fit_transform(B_dict.values())

#functions for P
def package(api):
    """
    find the package of an api

    Args:
        api - string of api
        
    """
    return re.search('(\[*[ZBSCFIJD]|\[*L[\w\/$-]+;)->', api)[1]

def construct_P(apis):
    """
    construct P matrix

    Args:
        apis - a series of set of apis
        
    """
    api_df = pd.DataFrame({'api':apis}).dropna()
    api_df['package'] = api_df.api.apply(package)
    P_dict = api_df.groupby('package')['api'].apply(set).to_dict()
    api_df['same_package_apis'] = api_df['package'].apply(lambda x: P_dict[x])
    P_series = api_df.drop('package',axis=1).set_index('api')['same_package_apis']
    mlb = MultiLabelBinarizer(sparse_output = True)
    return mlb.fit_transform(P_series)

# construct all

def construct_matrices(app_smalis, test_app_smalis = None):
    """
    construct matrices A, A_test, B, and P

    Args:
        app_smalis - list of list of smali files to construct from
        test_app_smalis - list of list of testing smali fils to construct A_test, default none
        
    """
    smalis = pd.DataFrame(app_smalis)
    apis = smalis.apply(smali2apis, axis = 1)
    A, all_apis = construct_A(apis)
    if not(test_app_smalis is None):
        test_smalis = pd.DataFrame(test_app_smalis)
        test_apis = test_smalis.apply(smali2apis, axis = 1)
        A_test = construct_A_test(test_apis, all_apis)
    else:
        A_test = None
    B = construct_B(smalis)
    P = construct_P(all_apis)
    return A, A_test, B, P

def save_matrix_to_file(mat, path):
    """
    save a matrix as a sparse one to file

    Args:
        mat - matrix to save
        path - path of matrix to save
        
    """
    sparse = scipy.sparse.csc_matrix(mat)
    scipy.sparse.save_npz(path, sparse)