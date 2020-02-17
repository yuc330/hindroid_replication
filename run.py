import numpy as np
import json
from src import etl

if __name__ == "__main__":
    #parse configuration
    train = json.load('config/data-params.json')
    sitemap = train['sitemap']
    train_outpath = train['outpath']
    max_app = train['max_app']

    #get data
    urls = np.random.choice(etl.get_app_urls(sitemap), max_app) #only get a portion of apps
    etl.get_smali_code(urls, train_outpath)
    etl.clean_disk(train_outpath)
    
    #feature extraction
    apps = os.listdir(train_outpath)
    df = etl.extract_simple_feat(apps)
    
    #parse configuration for test
    test = json.load('config/test-params.json')
    test_outpath = test['outpath']
    max_app = test['max_app']

    #get data for test
    urls = np.random.choice(etl.get_app_urls(sitemap), max_app) #only get a portion of apps
    etl.get_smali_code(urls, test_outpath)
    etl.clean_disk(test_outpath)
    
    #feature extraction for test
    apps = os.listdir(test_outpath)
    df2 = etl.extract_simple_feat(apps)
    
    #training and testing
    pre = etl.cat_package()
    fn_lr = etl.fn_LR(df, df2, pre)
    fn_rf = etl.fn_RF(df, df2, pre)
    fn_gbt = etl.fn_GBT(df, df2, pre)
    