import pandas as pd
import requests
import os
from scipy.stats import ks_2samp
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
from scipy.stats.distributions import chi2

import warnings
warnings.filterwarnings('ignore')

path = os.getcwd()


## pull name and attribute data on a particular NFT collection
contract_address = '0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D'
ALCHEMY_API_KEY = "YOUR ALCHMEY API KEY HERE"

from Func_download_metadata import fetch_collection_metadata # %run Func_download_metadata.ipynb

collection_name, metadata = fetch_collection_metadata(contract_address, ALCHEMY_API_KEY, output = True, path = path)

# import metadata from local drive 
collection_name, contract_address = 'BoredApeYachtClub', '0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D'
# collection_name, contract_address = 'Doodles', '0x8a90cab2b38dba80c64b7734e58ee1db38b8992e'
# collection_name, contract_address = 'PudgyPenguins', '0xbd3531da5cf5857e7cfaa92426877b022e612cf8' #PudgyPenguins
metadata  = pd.read_csv(path + '/' + collection_name + '_Address_' + contract_address + '_metadata.csv',index_col=0)

# run rarity functions
from Func_rarity import rarity # %run Func_rarity.ipynb

rc = rarity(metadata, padding = True, save_output = False, path = path, name = collection_name, 
            plotting = True, plt_xaxis='Harmonic', plt_yaxis='Geometric', ind_sig = 0.99, save_graph = False)

rc.run()


rc.attr_prob

rc.rarity_metrics

rc.independ

rc.cramersV

rc.ind_pair_result



