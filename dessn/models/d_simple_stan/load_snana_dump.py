# -*- coding: utf-8 -*-
"""
Created on Thu Sep 15 12:42:49 2016

@author: shint1
"""
import numpy as np
import pandas as pd
import os
import inspect


if __name__ == "__main__":
    file = os.path.abspath(inspect.stack()[0][1])
    dir_name = os.path.dirname(file)
    data_dir = os.path.abspath(dir_name + "/data")

    dump_file = os.path.abspath(data_dir + "/SHINTON_SPEC_SALT2.DUMP")
    dataframe = pd.read_csv(dump_file, sep='\s+', skiprows=1, comment="#")

    supernovae = dataframe.to_records()
    supernovae = supernovae.astype(np.float32)
    np.save(data_dir + "/SHINTON_SPEC_SALT2.npy", supernovae)
    print("Conversion done")
