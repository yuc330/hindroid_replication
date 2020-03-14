import requests
import re
import glob, os, shutil
import gzip
import subprocess
import numpy as np
from bs4 import BeautifulSoup


#Part3.1 Create sample of android apps

def get_submap_xmls(sitemap):
    resp = requests.get(sitemap)
    soup = BeautifulSoup(resp.content, 'xml')
    url = soup.find_all('loc') 
    result = []
    for link in url:
        result += [link.get_text()]
    return result
#extract categories list
def category(link_lst):
    result = [] 
    for xml in link_lst:
        result += [re.search('(?<=sitemaps\/)(.*)(?=\-\d)|(?<=sitemaps\/)(.*)(?=\.xml)',xml).groups()[1]]
    return [i for i in result if i] 


#get all the gz files from each categories
def sample_from_cat(categories): 
    soups = []
    for c in categories:
        url = 'https://apkpure.com/sitemaps/{}.xml.gz'.format(c)
        try:
            r = requests.get(url)
        except:
            url = 'https://apkpure.com/sitemaps/{}.xml.gz'.format(c+'-1')
            r = requests.get(url)
        #decompress the gz file and parse xml
        data = gzip.decompress(r.content)
        soup = BeautifulSoup(data,features = 'lxml')
        soups.append(soup)
    return soups
def get_app_urls(sitemap,cat,number):
    xmls = get_submap_xmls(sitemap)
    
    if cat == 'all':
        categories = category(xmls)
    elif type(cat) == int:
        categories = random.choices(category(xmls), k = cat)
    else:
        categories = cat
        
    soups = sample_from_cat(categories)
    apps = []
    for soup in soups:
        count = 0
        sp = soup.find_all(re.compile('loc')) 
        lst = [] 
        for i in sp:
            if re.match('<loc>', str(i)) and count < number:
                try:
                    lst += [re.search('(?<=<loc>)(https:\/\/apkpure.com\/.*?\/.*[a-zA-Z\d].*)(?=<\/loc>)', str(i)).group()] #find all urls storec in loc
                    count += 1
                except:
                    continue
        apps += lst
    return apps

#part3.2 Download and decompile apk files

def download_apk(app_urls, outpath, cat):
    if not os.path.exists(outpath):
        os.mkdir(outpath)
    if not os.path.exists(outpath + '/' + cat):
        os.mkdir(outpath + '/' + cat)

    for url in app_urls:
        download_link = url + '/download?from=details'
        r1 = requests.get(download_link)
        soup = BeautifulSoup(r1.text)
        try:
            download_link_file = soup.find('div',attrs = {"class":"fast-download-box fast-bottom"}).find('p',attrs = {'class':'down-click'}).find('a',href = True)['href']
        except:
            continue
        r2 = requests.get(download_link_file)
        apkfile = r2.content
        complete_name = os.path.join(outpath+'/'+cat+'/', url.split('/')[-1]+".apk")
        out_name = os.path.join(outpath+'/'+cat+'/', url.split('/')[-1])
        with open(complete_name, 'wb') as fh:
            fh.write(apkfile)
        subprocess.call(['apktool', 'd', outpath+'/'+cat+'/'+url.split('/')[-1]+".apk", '-o',out_name])

        
#part3.3 organize disk

def clean_app_folder(app_path):
    if '.DS_Store' not in app_path:
        if os.path.isdir(app_path):
            subs = os.listdir(app_path)
            for s in subs:
                if s not in ['smali', 'AndroidManifest.xml']:
                    path = app_path+'/'+s
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    elif os.path.isfile(path):
                        os.remove(path)
        else:
            os.remove(app_path)

def clean_disk(outpath):
    folders = os.listdir(outpath)
    for f in folders:
        if os.path.isdir(outpath+'/'+f):
            apps = os.listdir(outpath+'/'+f)
            for app in apps:
                clean_app_folder(outpath+'/'+f+'/'+app)
        else:
            os.remove(outpath+'/'+f)
        
        
#extract smalis

def get_smali_paths(app_path): #create a list of smali file paths from app path
    smalis = []
    for d, dirs, files in os.walk(app_path + '/smali/'):
        for file in files:
            if file.endswith('smali'):
                smalis.append(os.path.join(d, file))
    return smalis

def smalis_from_paths(paths): #create list of smali texts from list of paths
    return [open(p, 'r').read() for p in paths]
