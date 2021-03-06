"""
--------------------------------------------------------------------------------
nets_prec/NEOFAC_A/mean-R2: -0.1478
nets_prec/NEOFAC_O/mean-R2: -0.1461
nets_prec/NEOFAC_C/mean-R2: -0.1680
nets_prec/NEOFAC_N/mean-R2: -0.1546
nets_prec/NEOFAC_E/mean-R2: -0.1475
--------------------------------------------------------------------------------
nets_cov/NEOFAC_A/mean-R2: -0.1763
nets_cov/NEOFAC_O/mean-R2: -0.1573
nets_cov/NEOFAC_C/mean-R2: -0.1611
nets_cov/NEOFAC_N/mean-R2: -0.1774
nets_cov/NEOFAC_E/mean-R2: -0.1396
--------------------------------------------------------------------------------
regs_prec/NEOFAC_A/mean-R2: -0.1803
regs_prec/NEOFAC_O/mean-R2: -0.1852
regs_prec/NEOFAC_C/mean-R2: -0.1822
regs_prec/NEOFAC_N/mean-R2: -0.1981
regs_prec/NEOFAC_E/mean-R2: -0.1956
--------------------------------------------------------------------------------
regs_cov/NEOFAC_A/mean-R2: -0.1762
regs_cov/NEOFAC_O/mean-R2: -0.1852
regs_cov/NEOFAC_C/mean-R2: -0.1897
regs_cov/NEOFAC_N/mean-R2: -0.1854
regs_cov/NEOFAC_E/mean-R2: -0.2075

"""

import glob
import numpy as np
import nibabel as nib
import pandas
from nilearn.image import concat_imgs
from sklearn.preprocessing import StandardScaler

# gather the data
mask_file = nib.load('grey10_icbm_3mm_bin.nii.gz')


for cur_ana in ['nets_prec', 'nets_cov', 'regs_prec', 'regs_cov']:
    print('-' * 80)
    cur_paths = glob.glob('*_%s.npy' % cur_ana)

    sub_ids = np.array([int(p.split('_')[0]) for p in cur_paths])

    beh = pandas.read_csv('unrestricted_behavior.csv')
    neo_inds = np.array(['Compl' in col for col in beh.columns.values])
    # neo_inds = np.array(['WM_' in col for col in beh.columns.values])
    # neo_inds = np.array(['NEOFAC_' in col for col in beh.columns.values])
    # thing
    
    print('Predicting %i columns...' % neo_inds.sum())
    contrast_names = list(beh.columns.values[neo_inds])

    # map HCP big 5 to subject dump list
    hcp_to_dump_inds = []
    for cur_id in sub_ids:
        ind = np.where(beh.values[:, 0] == cur_id)[0]
        assert len(ind) == 1
        hcp_to_dump_inds.append(ind[0])
    hcp_to_dump_inds = np.array(hcp_to_dump_inds)

    beh_scores = np.array(beh.values[hcp_to_dump_inds][:, neo_inds], dtype=np.float64)
    beh_titles = np.array(beh.columns[neo_inds])


    # predict
    FS_brain = []
    idx = np.triu_indices(20, 1)
    for item in cur_paths:
        item_data = np.load(item)
        FS_brain.append(item_data[idx])
    FS_brain = np.array(FS_brain)
    FS_brain = StandardScaler().fit_transform(FS_brain)

    for i_beh in range(5):
        scores = beh_scores[:, i_beh]
        title = beh_titles[i_beh]

        from sklearn.cross_validation import cross_val_score, ShuffleSplit
        from sklearn.linear_model import Lasso

        clf = Lasso(alpha=1.0)
        scores = StandardScaler().fit_transform(scores)

        coefs = []
        r2_list = []
        folder = ShuffleSplit(n=len(scores), n_iter=500, test_size=0.1)
        for train, test in folder:
            clf.fit(X=FS_brain[train], y=scores[train])
            r2 = clf.score(FS_brain[test], scores[test])
            r2_list.append(r2)
        mean_r2 = np.mean(r2_list)
        print('%s/%s/mean-R2: %.4f' % (cur_ana, title, mean_r2))


