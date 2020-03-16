import re
import glob, os, shutil
import gzip
import numpy as np
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier,GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split
from src.model import compute_metrics


#extract feature

def get_smali_paths(app_path): #create a list of smali file paths from app path
    """
    with an app path, retrieve all of its smali file paths within a list
    
    Args:
       app_path - the path of app 
       
    """
    smalis = []
    for d, dirs, files in os.walk(app_path + '/smali/'):
        for file in files:
            if file.endswith('smali'):
                smalis.append(os.path.join(d, file))
    return smalis

def smalis_from_paths(paths): 
    """
    with a list of smali file paths, return all of its file content as a list of string
    
    Args:
        paths - the paths of smali files
        
    """
    return [open(p, 'r').read() for p in paths]

def find_blocks(smali):
    """
    find all code blocks and return them as a list given a smali string
    
    Args:
        smali - string of smali codes
        
    """
    return re.findall( '\.method([\S\s]*?)\.end method', smali)

def find_apis(smali):
    """
    find all api calls and return them as a list given a smali string
    
    Args:
        smali - string of smali codes
        
    """
    return re.findall('invoke-\w+ {.*}, (.*?)\\(', smali)

def invoke_type(api):
    """
    find the invoke type of an api call
    
    Args:
        api - string of api call
        
    """
    return re.search('(invoke-\w+)(?:\/range)? {.*},', api)[1]

def package(api):
    """
    find the package used of an api call
    
    Args:
        api - string of api call
        
    """
    return re.search('(\[*[ZBSCFIJD]|\[*L[\w\/$-]+;)->', api)[1]

def basic_stats(smalis):
    """
    given a list of smali files, output the basic stats of the app
    
    Args:
        smalis - list of all the smali files of an app
        
    """
    total_a = 0
    apis = []
    
    total_b = 0
    blocks = []
    
    package = {}
    for smali in smalis:
        #calculate number of apis
        api = find_apis(smali)
        total_a += len(api)
        apis += api
        
        #calculate number of code blocks
        block = find_blocks(smali)
        total_b += len(block)
        blocks += block
        
        #find package
        ps = re.findall('invoke-.*? {.*?}. (\[*[ZBSCFIJD]|\[*L[\w\/$-]+;)->', smali)
        for p in ps:
            if p in package.keys():
                package[p] += 1
            else:
                package[p] = 1
    try:
        most_used = max(package, key=package.get)
    except:
        most_used = np.nan
   
    #return total apis and unique apis, total methods and unique methods, return mostly used package
    return total_a, len(set(apis)), total_b, len(set(blocks)), most_used
        



def extract_simple_feat(smalis, y, y_col = 'malware'):
    """
    given a dataframe of smali files of apps, output dataframe of the simple features of app
    
    Args:
        smalis - dataframe of smali files, in which each row is an app
        y - the label of this set of apps
        y_col - the column name for label, default malware
        
    """
    num_apis = []
    unique_apis = []
    num_methods = []
    unique_methods = []
    most_used_package = []
    for app in smalis: #extract features
        na, ua, nb, ub, mp = basic_stats(app)
        num_apis.append(na)
        unique_apis.append(ua)
        num_methods.append(nb)
        unique_methods.append(ub)
        most_used_package.append(mp)
        
    df = pd.DataFrame({
        'num_api':num_apis,
        'unique_api':unique_apis,
        'num_method':num_methods,
        'unique_method':unique_methods,
        'most_used_package':most_used_package,
         y_col: [y]*len(most_used_package)
    })
    return df

#model training

def preprocess(X):
    """
    provide the column transformer for the dataframe of simple features
    
    Args:
        X - dataframe of the apps w/ simple feature to create column transformer
        
    """
    cat_feat = ['most_used_package']
    cat_trans = Pipeline(steps=[
        ('onehot', OneHotEncoder(handle_unknown = 'ignore'))
        ])

    num_trans = Pipeline(steps = [('standard_scalar',StandardScaler())])
    num_feat = ['num_method','num_api']

    return ColumnTransformer(transformers=[('cat', cat_trans,cat_feat), ('num', num_trans, num_feat)])

def result_LR(df_train, df_test, pre, y_column = 'malware'):
    """
    output the testing confusion matrix after feeding simple features into logistic regression models
    
    Args:
        df_train - dataframe for training set
        df_test - dataframe for test set
        pre - column transformer
        y_column - the column name of labels, default malware
        
    """
    X = df_train.drop(y_column, 1)
    y = df_train[y_column]
    pipe = Pipeline(steps=[('preprocessor', pre),
                       ('clf', LogisticRegression())
                       ])
    pipe.fit(X,y)
    X_te = df_test.drop(y_column, 1)
    y_te = df_test[y_column]
    y_pred = pipe.predict(X_te)
    tn, fp, fn, tp = confusion_matrix(y_te, y_pred).ravel()
    return tn, fp, fn, tp

def result_RF(df_train, df_test, pre, y_column = 'malware'):
    """
    output the testing confusion matrix after feeding simple features into random forest models
    
    Args:
        df_train - dataframe for training set
        df_test - dataframe for test set
        pre - column transformer
        y_column - the column name of labels, default malware
        
    """
    X = df_train.drop(y_column, 1)
    y = df_train[y_column]
    pipe = Pipeline(steps=[('preprocessor', pre),
                       ('clf', RandomForestClassifier(max_depth=2, random_state=0))
                       ])
    pipe.fit(X,y)
    X_te = df_test.drop(y_column, 1)
    y_te = df_test[y_column]
    y_pred = pipe.predict(X_te)
    tn, fp, fn, tp = confusion_matrix(y_te, y_pred).ravel()
    return tn, fp, fn, tp

def result_GBT(df_train, df_test, pre, y_column = 'malware'):
    """
    output the testing confusion matrix after feeding simple features into gradient boost classifier models
    
    Args:
        df_train - dataframe for training set
        df_test - dataframe for test set
        pre - column transformer
        y_column - the column name of labels, default malware
        
    """
    X = df_train.drop(y_column, 1)
    y = df_train[y_column]
    pipe = Pipeline(steps=[('preprocessor', pre),
                       ('clf', GradientBoostingClassifier())
                       ])
    pipe.fit(X,y)
    X_te = df_test.drop(y_column, 1)
    y_te = df_test[y_column]
    y_pred = pipe.predict(X_te)
    tn, fp, fn, tp = confusion_matrix(y_te, y_pred).ravel()
    return tn, fp, fn, tp

def save_baseline_result(lr, rf, gbt):
    """
    given results of the baseline models, save them to file
    
    Args:
        lr - test result of logistic regression
        rf - test result of random forest
        gbt - test result of gradient boost classifier
        
    """
    baseline_result = pd.DataFrame([lr, rf, gbt], columns=['tn', 'fp', 'fn', 'tp', 'acc', 'fnr'], index = np.array(['logistic regression', 'random forest', 'gradient boost']))
    baseline_result.to_csv(os.path.join('output', 'baseline_result.txt'))
    
def baseline_model(df, y_col = 'malware', test_size=0.33):
    """
    the whole process of training baseline model to saveing the result to file
    
    Args:
        df - dataframe of simple features
        y_col - column name for labels, default malware
        test_size - test size for train-test split, default 0.33
        
    """
    X = df.drop(y_col, 1)
    y = df[y_col]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, shuffle=True)
    print('preprocessing data...')
    pre = preprocess(X_train)

    df_train = X_train.assign(malware = y_train)
    df_test = X_test.assign(malware= y_test)
    
    print('start training baseline models...')
    result_lr = result_LR(df_train, df_test, pre)
    lr = compute_metrics(list(result_lr))

    result_rf = result_RF(df_train, df_test, pre)
    rf = compute_metrics(list(result_rf))

    result_gbt = result_GBT(df_train, df_test, pre)
    gbt = compute_metrics(list(result_gbt))
    print('finish training baseline models')

    baseline_result = pd.DataFrame([lr, rf, gbt], columns=['tn', 'fp', 'fn', 'tp', 'acc', 'fnr'], index = np.array(['logistic regression', 'random forest', 'gradient boost']))
    save_baseline_result(lr, rf, gbt)
    print('baseline test result saved to output directory')
