import numpy as np
import json
from src import etl

if __name__ == "__main__":
    #parse configuration
    train = json.load('config/data-params.json')
    sitemap = train['sitemap']
    train_outpath = train['outpath']
    num = train['num']
    cat = train['categories']

    #get data
    apps = etl.get_app_urls(sitemap, cat, num) #only get a portion of apps
    etl.download_apk(apps[:num], train_outpath, cat[0])
    etl.download_apk(apps[num:], train_outpath, cat[1])
    etl.clean_disk(train_outpath)
    
    #feature extraction
    df1 = etl.extract_simple_feat(os.listdir(train_outpath+'/'+cat[0]))
    df2 = etl.extract_simple_feat(os.listdir(train_outpath+'/'+cat[1]))
    app_df = pd.concat([df1,df2])
    
    #parse configuration for test
    test = json.load('config/test-params.json')
    test_outpath = test['outpath']
    tnum = test['num']

    #get data for test
    apps = etl.get_app_urls(sitemap, cat, tnum) #only get a portion of apps
    etl.download_apk(apps[:tnum], test_outpath, cat[0])
    etl.download_apk(apps[tnum:], test_outpath, cat[1])
    etl.clean_disk(test_outpath)
    
    #feature extraction
    df1 = etl.extract_simple_feat(os.listdir(test_outpath+'/'+cats[1]))
    df2 = etl.extract_simple_feat(os.listdir(test_outpath+'/'+cats[2]))
    test_df = pd.concat([df1,df2])
    
    #training and testing
    pre = etl.cat_package(app_df)
    fn_lr = etl.fn_LR(app_df, test_df, pre)
    fn_rf = etl.fn_RF(app_df, test_df, pre)
    fn_gbt = etl.fn_GBT(app_df, test_df, pre)
    