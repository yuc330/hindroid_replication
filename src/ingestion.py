import requests
import re
import glob, os, shutil
import gzip
import subprocess
import numpy as np
import random
from bs4 import BeautifulSoup
from multiprocessing import Pool


#Part3.1 Create sample of android apps

def get_submap_xmls(sitemap):
    """
    given the url of sitemap for android app, retrieve the urls of sub-sitemaps

    Args:
        sitemap - url of sitemap
        
    """
    resp = requests.get(sitemap)
    soup = BeautifulSoup(resp.content, 'xml')
    url = soup.find_all('loc') 
    result = []
    for link in url:
        result += [link.get_text()]
    return result

#extract categories list
def category(link_lst):
    """
    given a list of sub-sitemaps, retrieve all possible categories

    Args:
       link_lst - list of urls for sub-sitemaps 
        
    """
    result = [] 
    for xml in link_lst:
        result += [re.search('(?<=sitemaps\/)(.*)(?=\-\d)|(?<=sitemaps\/)(.*)(?=\.xml)',xml).groups()[1]]
    return [i for i in result if i] 


#get all the gz files from each categories
def sample_from_cat(categories): 
    """
    given a list of categories, retrieve all urls of apps in the categories

    Args:
        categories - list of categories
        
    """
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
    """
    create a list of app urls to download later

    Args:
        sitemap - url of the sitemap
        cat - categories to get app urls
        number - number of app urls to get for each category
        
    """
    xmls = get_submap_xmls(sitemap)
    
    if cat == 'all':
        categories = category(xmls) #retrieve urls for all categories
    elif type(cat) == int:
        categories = random.choices(category(xmls), k = cat) #retrieve urls for a number of categories randomly sampled
    else:
        categories = cat #a list of categories given
        
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
    """
    download and decompile apps given urls and paths

    Args:
        app_urls - a list of app urls to be downloaded from
        outpath - the path to store downloaded apps
        cat - the category, or subpath, that the apps are stored in outpath
        
    """
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
        #decompile apps
        subprocess.call(['apktool', 'd', outpath+'/'+cat+'/'+url.split('/')[-1]+".apk", '-o',out_name])

        
#part3.3 organize disk

def clean_app_folder(app_path):
    """
    remove all files except for smali files and AndroidManifest.xml in the folder

    Args:
        app_path - path of the folder to be cleaned
        
    """
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
    """
    remove all files except for smali files and AndroidManifest.xml in the app folders in the folder

    Args:
        outpath - path of the folder whose sub-app folders to be cleaned
        
    """
    folders = os.listdir(outpath)
    for f in folders:
        if os.path.isdir(outpath+'/'+f):
            apps = [outpath+'/'+f+'/'+a for a in os.listdir(outpath+'/'+f)]
            pool = Pool(os.cpu_count())                 
            pool.map(clean_app_folder, apps)
            pool.close()
  
        else:
            os.remove(outpath+'/'+f)
        
        
#extract smalis

def get_benign_paths(outpath, cat='analysis'):
    """
    get all the paths of apps in the sub-folder in outpath folder in a list

    Args:
        outpath - path where all data is stored
        cat - sub folder in outpath folder where app folders are stored, default analysis
        
    """
    paths = [outpath+'/'+cat+'/'+ d for d in os.listdir(outpath+'/'+cat)]
    
    #store mediate files
    if not os.path.exists('mediate'):
        os.mkdir('mediate')
    with open('mediate/benign_paths.txt', 'w') as f:
        for item in paths:
            f.write("%s\n" % item)
    return paths

def get_malware_paths(malware_path, num):
    """
    get a number of malware paths given the parent folder of the malwares

    Args:
        malware_path - parent folder of the malwares
        num - number of malwares to get
        
    """
    paths = []
    count = 0
    for d, dirs, files in os.walk(malware_path):
        for subd in dirs:
            if subd == 'smali' and count < num:
                paths.append(d)
                count += 1
            if count > num:
                break
                
    #store mediate files
    if not os.path.exists('mediate'):
        os.mkdir('mediate')
    with open('mediate/malware_paths.txt', 'w') as f:
        for item in paths:
            f.write("%s\n" % item)
    return paths

def get_all_paths_fromfile():
    """
    read all smalis paths already saved in mediate folder
    
    Args:
        none
        
    """
    with open('benign_paths.txt') as f:
        benign_paths = f.read().splitlines()
    with open('malware_paths.txt') as f:
        malware_paths = f.read().splitlines()
    return benign_paths, malware_paths



