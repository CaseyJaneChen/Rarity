import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
from scipy.stats.distributions import chi2

class rarity():
    def __init__(self, metadata, padding = True, save_output = False, path = './', name = 'Collection', 
                 plotting = True, plt_xaxis='Geometric', plt_yaxis='Harmonic', ind_sig = 0.99, save_graph = False):
        self.metadata_raw = metadata
        self.padding = padding
        self.save_output = save_output
        self.path = path
        self.name = name.replace('/','|') # / in name disturbs path to save data or plots
        self.plotting = plotting 
        self.plt_xaxis = plt_xaxis
        self.plt_yaxis = plt_yaxis
        self.ind_sig = ind_sig
        self.save_graph = [save_graph if plotting else False][0]

        # record padding situation originally        
        self.original_padding = ['Originally not padded' if metadata.isna().sum().sum() > 0 else 'Originally padded'][0]
        # insert padding if padding
        self.metadata = [metadata.fillna('None') if padding else metadata][0]
        # sometimes incomplete freq columns found in data and need removal
        attr_list = [c for c in self.metadata.columns.tolist() if '_count' not in c] 
        attr_list.sort()
        self.metadata = self.metadata[attr_list] 
        
    def run(self):
        # compute attributes prob matrix        
        self.attribute2prob()
        # compute all rarity metrics
        self.rarity_metrics_calc()
        # indpendent test 1
        self.traitIndepend()
        # indpendent test 2
        self.traitCramersV()
        # plot graph
        if self.plotting:
            self.plot_rarity()
    
    def attribute2prob(self):
        metadata_temp = self.metadata.copy()
        attr_list = metadata_temp.columns.tolist()
        for attr_ in attr_list:
            temp = pd.DataFrame(metadata_temp[attr_].value_counts(dropna = True)/len(metadata_temp)).reset_index()
            temp.rename({'count': attr_ + '_count'},axis='columns',inplace = True)
            metadata_temp = metadata_temp.merge(temp, on = attr_, how = 'left')
        self.attr_prob = metadata_temp[[c for c in metadata_temp.columns.tolist() if '_count' in c]]
        if self.save_output:
            self.attr_prob.to_csv(self.path + '/' + self.name + '_trait_freq_dist.csv')
            print('Trait frequency matrix exported!')
            
    def rarity_metrics_calc(self):
        attr_prob = self.attr_prob.copy()
        rarity_metrics = pd.DataFrame(index = attr_prob.index)
        rarity_metrics['Harmonic_value'] = attr_prob.count(axis=1)/((attr_prob**(-1)).sum(axis=1))
        rarity_metrics['Geometric_value'] = (attr_prob.prod(axis=1))**(1/attr_prob.count(axis=1))
        rarity_metrics['Arithmetic_value'] = attr_prob.sum(axis=1)/attr_prob.count(axis=1)
        rarity_metrics['max-min'] = attr_prob.max(axis=1) - attr_prob.min(axis=1)
        
        metadata = self.metadata.copy()
        attr_value_count = pd.Series({d + '_count': len(metadata[d].value_counts()) for d in metadata.columns.tolist()})
        rarity_metrics['TN_Harmonic_value'] = attr_value_count.sum()/(attr_value_count/(attr_prob*len(attr_prob))).sum(axis=1)
        rarity_metrics['TN_Geometric_value'] = np.exp((np.log(attr_prob*len(attr_prob))*attr_value_count).sum(axis=1)*(1/attr_value_count.sum()))
        rarity_metrics['TN_Arithmetic_value'] = (attr_value_count*(attr_prob*len(attr_prob))).sum(axis=1)/attr_value_count.sum()
        
        for c in ['Harmonic','Geometric','Arithmetic']:
            for d in ['', 'TN_']:
                rarity_metrics[d + c + '_score'] = (rarity_metrics[d + c + '_value'] - rarity_metrics[d + c + '_value'].min())/(rarity_metrics[d + c + '_value'].max() - rarity_metrics[d + c + '_value'].min())
                rarity_metrics[d + c + '_rank'] = rarity_metrics[d + c + '_score'].rank(method='max',na_option='bottom',ascending=True)
        
        self.rarity_metrics = rarity_metrics
        if self.save_output:
            self.rarity_metrics.to_csv(self.path + '/' + self.name + '_rarity_metrics.csv')
            print('Rarity metrics exported!')
            
    def traitIndepend(self):
        metadata = self.metadata.copy()
        attr_list = metadata.columns.tolist()
        independ = pd.DataFrame(columns = attr_list, index = attr_list)
        total_pair = 0
        ind_pair = 0
        for i, trait_ in enumerate(attr_list[0:-1]):
            for trait_col_ in attr_list[(i+1):]:
                total_pair += 1
                temp = pd.crosstab(metadata[trait_], metadata[trait_col_])
                indpdTest = stats.chi2_contingency(temp)
                independ.loc[trait_,trait_col_] = str(int(np.round(indpdTest[0],0)))
                independ.loc[trait_col_,trait_] = str(int(np.round(chi2.ppf(self.ind_sig, df = indpdTest[2]),0)))
                if indpdTest[0] > chi2.ppf(self.ind_sig, df = indpdTest[2]):
                    independ.loc[trait_,trait_col_] = independ.loc[trait_,trait_col_]  + '*'
                else:
                    ind_pair += 1
        ind_pair_result = {'No of independent trait pairs (ITP)': ind_pair, 
                           'No of total trait pairs (TTP)': total_pair, 
                           'ITP/TTP': ind_pair/total_pair}
        
        self.independ = independ
        if self.save_output:
            self.independ.to_csv(self.path + '/' + self.name + '_independent_test_result.csv')
            print('Trait independent test result exported!')
        
        self.ind_pair_result = ind_pair_result
        print(self.ind_pair_result)
        
    def traitCramersV(self):
        metadata = self.metadata.copy()
        attr_list = metadata.columns.tolist()
        cramersV = pd.DataFrame(columns = attr_list, index = attr_list)

        for i, trait_ in enumerate(attr_list[0:-1]):
            for trait_col_ in attr_list[(i+1):]:
                temp = pd.crosstab(metadata[trait_], metadata[trait_col_])
                crmVtest = stats.chi2_contingency(temp)
                N = np.sum(np.sum(temp))
                minimum_dimension = min(temp.shape)-1
                cramersV.loc[trait_,trait_col_] = np.round(np.sqrt((crmVtest[0]/N) / minimum_dimension),4)
        self.cramersV = cramersV
        if self.save_output:
            self.cramersV.to_csv(self.path + '/' + self.name + '_cramersV_result.csv')
            print('CramersV test result exported!')

    def plot_rarity(self):
        metadata = self.metadata.copy()
        rarity_metrics = self.rarity_metrics.copy()
        
        figure,axs = plt.subplots(2,figsize = (4.4,6.6))
        axs[0].scatter(np.arange(len(rarity_metrics)),rarity_metrics['max-min'],s=1)
        axs[0].set_ylim([-.1,1.1])
        axs[0].set_xlabel('Token ID')
        axs[0].set_ylabel('Maximum - Minimum')
        axs[1].scatter(rarity_metrics[self.plt_xaxis + '_rank'],rarity_metrics[self.plt_yaxis + '_rank'],s=.5)
        axs[1].plot([0,len(rarity_metrics)],[0,len(rarity_metrics)],color='r')
        axs[1].set_xlabel(self.plt_xaxis + ' Rank')
        axs[1].set_ylabel(self.plt_yaxis + ' Rank')
        ind_pair_d = ['Independent trait pairs' if self.ind_pair_result['ITP/TTP'] >=.9 else 'Dependent trait pairs'][0]
        axs[0].set_title(self.name +"\n(" + str(int(len(metadata))) + " tokens, " + str(int(len(metadata.columns.tolist()))) + " traits)\n" + ind_pair_d + '\n')
        figure.tight_layout(h_pad=1, w_pad=1)
        if self.save_graph:
            plt.savefig(self.path + '/' + self.name + '_rarity_ranks_comparison.png')
            print('Graph exported!')
        figure.show()

