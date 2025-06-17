#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import pandas as pd
####################################
####################Funcs###########

def flatten_traits(attributes):
    trait_map = {}
    counts = {}

    # First pass: count trait_type occurrences
    for attr in attributes:
        if "trait_type" in attr and "value" in attr:
            tt = attr["trait_type"].strip()
            counts[tt] = counts.get(tt, 0) + 1

    # If 'attribute' appears more than once, disambiguate
    disambiguate = counts.get("attribute", 0) > 1

    attribute_count = 1
    for attr in attributes:
        if "trait_type" not in attr or "value" not in attr:
            continue

        trait_type = attr["trait_type"].strip()
        value = attr["value"].strip()

        if disambiguate and trait_type.lower() == "attribute":
            trait_map[f"attribute{attribute_count}"] = value.lstrip()
            attribute_count += 1
        else:
            trait_map[trait_type] = value

    return trait_map


def fetch_collection_metadata(contract_address, ALCHEMY_API_KEY, output = False, path = None):
    BASE_URL = f"https://eth-mainnet.g.alchemy.com/nft/v3/{ALCHEMY_API_KEY}"
    all_nfts = []
    collection_name = None
    page_key = None
    count_inner = 0
    while True:
        url = f"{BASE_URL}/getNFTsForContract"
        params = {
            "contractAddress": contract_address,
            "withMetadata": "true",
            "pageKey": page_key,
            "pageSize": 100
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"❌ Error fetching data for {contract_address}: {response.status_code}")
            break

        data = response.json()
        nfts = data.get("nfts", [])
        for nft in nfts:
            meta = nft['raw']['metadata']
            try:
                attributes = meta.get("attributes", [])
                flat_traits = flatten_traits(attributes)
                row = {
                    "tokenId": nft["tokenId"],
#                     'address': nft['contract']['address'],
#                     'tokenType': nft['tokenType'],
#                     'name': nft['contract']['name'],
                    **flat_traits
                }
                all_nfts.append(row)
                if collection_name == None:
                    collection_name = nft['contract']['name'] + '_Adress_' + nft['contract']['address']
            except:
                pass
        
        page_key = data.get("pageKey")
        count_inner +=1
        if page_key != None:
            print('Page ' + str(count_inner) + ', page number ' + str(page_key))
        
        if not page_key:
            break

    df = pd.DataFrame(all_nfts).drop_duplicates(keep = 'first').set_index('tokenId')
    if output:
        if not df.empty:
            filename = '/' + collection_name.replace('/','|') + '_metadata.csv'
            print(f"✅ Saved {len(df)} NFTs in {filename}")
        else:
            print('No tokens found!')
        
    return collection_name, df


# In[ ]:




