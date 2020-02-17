import requests
import re
import glob, os, shutil
import gzip
import subprocess
import numpy as np
from bs4 import BeautifulSoup

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier,GradientBoostingClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import confusion_matrix

#Part3.1 Create sample of android apps

def get_submap_xmls(sitemap): #get a list of submap xmls from sitemap
    resp = requests.get(sitemap)
    data = resp.content
    soup = BeautifulSoup(data, 'xml')
    loc_list = soup.find_all('loc') 
    xml_lst = []
    for link in loc_list:
        xml_lst += [link.get_text()]
    return xml_lst

def category(xml_lst): #get a list of category
    cat = [] 
    for xml in xml_lst:
        cat += [re.search('(?<=sitemaps\/)(.*)(?=\-\d)|(?<=sitemaps\/)(.*)(?=\.xml)',xml).groups()[1]]
    return [i for i in category if i] #remove none value

def sample_from_cat(categories): #choose the first submap of each category
    apps = []
    for c in categories:
        url = 'https://apkpure.com/sitemaps/{}.xml.gz'.format(c)
        try:
            r = requests.get(url)
        except:
            url = 'https://apkpure.com/sitemaps/{}.xml.gz'.format(c+'-1')
            r = requests.get(url)
    
        data = gzip.decompress(r.content)
        apps.append(data)
    return apps

#TODO: categories selection
def get_app_urls(sitemap): #get all app urls of our sample
    xmls = get_submap_xmls(sitemap)
    categories = category(xmls)
    samples = sample_from_cat(categories)
    apps = []
    for sample in samples:
        soup = bs4.BeautifulSoup(sample ,features = 'lxml')
        
         #find all urls stored in loc, which also return image:loc
        loc_urls = soup.find_all(re.compile('loc'))
        lst = [] #list of url for apps
        for i in loc_urls:
            if re.match('<loc>', str(i)): #select only <loc>
                lst += [re.search('(?<=<loc>)(.*)(?=<\/loc>)', str(i)).group()]
        apps += lst
    return apps

#part3.2 Download and decompile apk files

def get_download_page(app_link): #get download page of an app
    app_name = app_link.split('/')[-1]
    if not os.path.exists(outpath+'/'):
        os.mkdir(outpath+'/')
    r = requests.get(app_link)
    app_page = bs4.BeautifulSoup(r.text)
    
    #find download page
    download_page_l = app_path + app_page.find('div', attrs={"class":"down"}).a['href']
    return download_page_l

def download_apk(download_page_link, app_link, outpath): #download the apk file
    app_name = app_link.split('/')[-1]
    r_download = requests.get(download_page_link)
    download_page = bs4.BeautifulSoup(r_download.text)
    
    #get download link
    download_link = download_page.find('div',attrs = {"class":"fast-download-box fast-bottom"}).a['href']
    r = requests.get(download_link)
    apkfile = r.content
    
    #download an save in outpath directory
    path = os.path.join(outpath +'/', app_name +".apk")
    with open(path, 'wb') as f:
            f.write(apkfile)

def decompile(app_link, outpath): #decompile apk files and remove .apk
    app_name = app_link.split('/')[-1]
    subprocess.call(['cd', outpath]) 
    name = os.path.join(outpath+'/', link.split('/')[-1]+".apk") 
    subprocess.call(['apktool', 'd', name])
    if os.path.exists(name +".apk"): #delete apkfiles
        os.remove(name +".apk")

def get_smali_code(app_urls, outpath): #download and decompile all application urls
    for url in app_urls:
        page = get_download_page(url)
        download_apk(page, url, outpath)
        decompile(url, outpath)

#part3.3 organize disk

def clean_app_folder(app_path): #remove anything that is not smali
    subs = os.listdir(app_path)
    for s in subs:
        if s not in ['smali', 'AndroidManifest.xml']:
            path = app_path+'/'+s
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.isfile(path):
                os.remove(path)

def clean_disk(outpath): #run through all the app files
    apps = os.listdir(outpath)
    for app in apps:
        clean_app_folder(app)
        
        
#extract feature

def get_smali_paths(app_path): #create a list of smali file paths from app path
    smalis = []
    for d, dirs, files in os.walk(app_path + '/smali/'):
        for file in files:
            if file.endswith('smali'):
                smalis.append(os.path.join(d, file))
    return smalis

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
    return re.findall('(invoke-.*?)\\n', block)

def invoke_type(api):
    return re.search('(invoke-\w+)(?:\/range)? {.*},', api)[1]

def package(api):
    return re.search('invoke-.*? {.*?}. (\[*[ZBSCFIJD]|\[*L[\w\/$-]+;)->', api)[1]

#different abstraction to reduce time of for loops below
def num_api(smalis):
    total = 0
    apis = []
    for smali in smalis:
        api = find_apis(smali)
        total += len(api)
        apis += api
    return total, len(set(apis)) #return total apis and unique apis
        
def num_method(smalis):
    total = 0
    blocks = []
    for smali in smalis:
        block = find_blocks(smali)
        total += len(block)
        blocks += block
    return total, len(set(blocks)) #return total methods and unique methods

def most_used_package(smalis):
    package = {}
    for smali in smalis:
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
    return most_used #return mostly used package

def extract_simple_feat(apps):
    num_apis = []
    unique_apis = []
    num_methods = []
    unique_methods = []
    most_used_package = []
    for app in apps: #extract features
        smalis = etl.smalis_from_paths(etl.get_smali_paths('data/'+app))
        n, u = etl.num_api(smalis)
        num_apis.append(n)
        unique_apis.append(u)
        n, u = etl.num_method(smalis)
        num_methods.append(n)
        unique_methods.append(u)
        most_used_package.append(etl.most_used_package(smalis))
        
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

def cat_package():
    cat_feat = ['most_used_package']
    cat_trans = Pipeline(steps=[
        ('onehot', OneHotEncoder())
        ])
    return ColumnTransformer(transformers=[('cat', cat_trans,cat_feat)])

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
