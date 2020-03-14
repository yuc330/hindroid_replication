import re
import glob, os, shutil
import gzip
import numpy as np

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier,GradientBoostingClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import confusion_matrix

#extract feature

def get_smali_paths(app_path): #create a list of smali file paths from app path
    smalis = []
    for d, dirs, files in os.walk(app_path + '/smali/'):
        for file in files:
            if file.endswith('smali'):
                smalis.append(os.path.join(d, file))
    return smalis

def smalis_from_paths(paths): #create list of smali texts from list of paths
    return [open(p, 'r').read() for p in paths]

def find_blocks(smali):
    return re.findall( '\.method([\S\s]*?)\.end method', smali)

def find_apis(block):
    return re.findall('invoke-\w+ {.*}, (.*?)\\(', block)

def invoke_type(api):
    return re.search('(invoke-\w+)(?:\/range)? {.*},', api)[1]

def package(api):
    return re.search('(\[*[ZBSCFIJD]|\[*L[\w\/$-]+;)->', api)[1]

def basic_stats(smalis):
    total_a = 0
    apis = []
    
    total_b = 0
    blocks = []
    
    package = {}
    for smali in smalis:
        api = find_apis(smali)
        total_a += len(api)
        apis += api
        
        block = find_blocks(smali)
        total_b += len(block)
        blocks += block
        
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
        



def extract_simple_feat(apps, path):
    num_apis = []
    unique_apis = []
    num_methods = []
    unique_methods = []
    most_used_package = []
    for app in apps: #extract features
        smalis = smalis_from_paths(get_smali_paths(path+app))
        na, ua, nb, ub, mp = basic_stats(smalis)
        num_apis.append(na)
        unique_apis.append(ua)
        num_methods.append(nb)
        unique_methods.append(ub)
        most_used_package.append(mp)
        
    df = pd.DataFrame({
        'apps':apps,
        'num_api':num_apis,
        'unique_api':unique_apis,
        'num_method':num_methods,
        'unique_method':unique_methods,
        'most_used_package':most_used_package,
        'malware': [0]*len(most_used_package)
    })
    return df[df['apps']!='.DS_Store']

#model training

def cat_package(X):
    imp = SimpleImputer(missing_values=np.nan, strategy='mean')
    imp2 = SimpleImputer(missing_values=np.NaN, strategy='mean')

    cat_feat = ['most_used_package']
    cat_trans = Pipeline(steps=[
        ('onehot', OneHotEncoder())
        ])

    imp_feat = [i for i in X.columns.values if i != 'dating']
    imp_trans = Pipeline(steps=[
        ('impute1', imp),
        ('impute2', imp2),
        ])

    return ColumnTransformer(transformers=[('cat', cat_trans,cat_feat), ('imp', imp_trans,imp_feat)])

def fn_LR(df_train, df_test, pre):
    X = df_train.drop('malware', 1)
    y = df_train.malware
    pipe = Pipeline(steps=[('preprocessor', pre),
                       ('clf', LogisticRegression())
                       ])
    pipe.fit(X,y)
    X_te = df_train.drop('malware', 1)
    y_te = df_train.malware
    y_pred = pipe.predict(X_te)
    tn, fp, fn, tp = confusion_matrix(y_te, y_pred).ravel()
    return fn/(tn+fp+fn+tp)

def fn_RF(df_train, df_test, pre):
    X = df_train.drop('malware', 1)
    y = df_train.malware
    pipe = Pipeline(steps=[('preprocessor', pre),
                       ('clf', RandomForestClassifier(max_depth=2, random_state=0))
                       ])
    pipe.fit(X,y)
    X_te = df_train.drop('malware', 1)
    y_te = df_train.malware
    y_pred = pipe.predict(X_te)
    tn, fp, fn, tp = confusion_matrix(y_te, y_pred).ravel()
    return fn/(tn+fp+fn+tp)

def fn_GBT(df_train, df_test, pre):
    X = df_train.drop('malware', 1)
    y = df_train.malware
    pipe = Pipeline(steps=[('preprocessor', pre),
                       ('clf', GradientBoostingClassifier())
                       ])
    pipe.fit(X,y)
    X_te = df_train.drop('malware', 1)
    y_te = df_train.malware
    y_pred = pipe.predict(X_te)
    tn, fp, fn, tp = confusion_matrix(y_te, y_pred).ravel()
    return fn/(tn+fp+fn+tp)