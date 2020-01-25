import requests
import re
import glob, os
import gzip
import subprocess
from bs4 import BeautifulSoup

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
    subprocess.call(['apktool', 'd', app_name +".apk"])
    if os.path.exists(app_name +".apk"): #delete apkfiles
        os.remove(app_name +".apk")

def get_smali_code(app_urls, outpath): #download and decompile all application urls
    for url in app_urls:
        page = get_download_page(url)
        download_apk(page, url, outpath)
        decompile(url, outpath)

#part3.3 organize disk

def clean_app_folder(app_path):
    subs = os.listdir(app_path)
    for s in subs:
        if s not in ['smali', 'AndroidManifest.xml']:
            if os.path.isdir(s):
                os.rmdir(s)
            elif os.path.isfile(s):
                os.remove(s)

def clean_disk(outpath):
    apps = os.listdir(outpath)
    for app in apps:
        clean_app_folder(app)