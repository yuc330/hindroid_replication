import numpy as np
import warnings
import sys
import json
from src.ingestion import *
from src.baseline import *
from src.matrix import *
from src.model import *

def load_params(file):
        with open(file) as file:
            params = json.load(file)
        return params
    
def main(targets):
    warnings.filterwarnings("ignore")
    data_params = 'config/data-params.json'
    test_params = 'config/test-params.json'

    # make the clean target
    if 'clean' in targets:
        shutil.rmtree('data',ignore_errors = True)
        shutil.rmtree('output',ignore_errors = True)

    # make the data target
    if 'download' in targets:
        params = load_params(data_params)
        sitemap = params['sitemap']
        outpath = params['outpath']
        subpath = params['subpath']
        cat = params['categories']
        num = params['num']

        #download app
        urls = get_app_urls(sitemap,cat,num)
        print('start downloading...')
        download_apk(urls, outpath, subpath)
        print('finish downloading')

        #keep smali
        print('keeping only smali files...')
        clean_disk(outpath)
        print('finish cleaning disk')

    if 'baseline' in targets:
        if not os.path.exists('output'):
            os.mkdir('output')
        params = load_params(data_params)
        outpath = params['outpath']
        mal_path = params["malware"]
        mal_num = params["mal_num"]
        
        #get app paths
        print('retrieving app paths...')
        benign_paths = get_benign_paths(outpath, cat='analysis')
        malware_paths = get_malware_paths(mal_path, mal_num)
        print('app paths retrieved')
        
        #turn to smali strings
        print('retrieving smali files...')
        benign_smalis = [smalis_from_paths(get_smali_paths(p)) for p in benign_paths]
        malware_smalis = [smalis_from_paths(get_smali_paths(p)) for p in malware_paths]
        smalis, y = get_Xy(benign_smalis, malware_smalis)
        apis = smalis.apply(smali2apis, axis = 1)
        print('smali files retrieved')
        
        #start EDA and baseline model
        df_benign = extract_simple_feat(benign_smalis, 0)
        df_malware = extract_simple_feat(malware_smalis, 1)
        df = pd.concat([df_benign, df_malware])
        df_wona = df[df['num_api']!=0]
        df_wona.describe().to_csv(os.path.join('output', 'EDA.txt'))
        print('basic stats saved to output directory')
        baseline_model(df_wona)

    if 'model' in targets:
        if not os.path.exists('output'):
            os.mkdir('output')
        params = load_params(data_params)
        outpath = params['outpath']
        mal_path = params["malware"]
        mal_num = params["mal_num"]
        
        #get app paths
        print('retrieving app paths...')
        benign_paths = get_benign_paths(outpath, cat='analysis')
        malware_paths = get_malware_paths(mal_path, mal_num)
        print('app paths retrieved')
        
        #turn to smali strings
        print('retrieving smali files...')
        benign_smalis = [smalis_from_paths(get_smali_paths(p)) for p in benign_paths]
        malware_smalis = [smalis_from_paths(get_smali_paths(p)) for p in malware_paths]
        smalis, y = get_Xy(benign_smalis, malware_smalis)
        print('smali files retrieved')
        
        
        #train models
        kernel_models(smalis, y)
        

    # make the test target
    if 'test-project' in targets:
        if not os.path.exists('output'):
            os.mkdir('output')
        
        params = load_params(test_params)
        sitemap = params['sitemap']
        outpath = params['outpath']
        subpath = params['subpath']
        cat = params['categories']
        num = params['num']
        mal_path = params["malware"]
        mal_num = params["mal_num"]

        #download app
        benign_urls = get_app_urls(sitemap,cat,num)
        print('start downloading...')
        #download_apk(benign_urls, outpath, subpath)
        print('finish downloading')

        #keep smali
        print('keeping only smali files...')
        #clean_disk(outpath)
        print('finish cleaning disk')
        
        #get app paths
        print('retrieving app paths...')
        benign_paths = get_benign_paths(outpath, cat=subpath)
        malware_paths = get_malware_paths(mal_path, mal_num)
        print('app paths retrieved')
        
        #turn to smali strings
        print('retrieving smali files...')
        benign_smalis = [smalis_from_paths(get_smali_paths(p)) for p in benign_paths]
        malware_smalis = [smalis_from_paths(get_smali_paths(p)) for p in malware_paths]
        smalis, y = get_Xy(benign_smalis, malware_smalis)
        apis = smalis.apply(smali2apis, axis = 1)
        print('smali files retrieved')
        
        #start EDA and baseline model
        df_benign = extract_simple_feat(benign_smalis, 0)
        df_malware = extract_simple_feat(malware_smalis, 1)
        df = pd.concat([df_benign, df_malware])
        df_wona = df[df['num_api']!=0]
        df_wona.describe().to_csv(os.path.join('output', 'EDA.txt'))
        print('basic stats saved to output directory')
        baseline_model(df_wona)
        
        #train models
        kernel_models(smalis, y)

if __name__ == "__main__":
    targets = sys.argv[1:]
    main(targets)
    