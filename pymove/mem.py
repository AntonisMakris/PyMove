import re
import os
import psutil
import pwd
import pandas as pd
import numpy as np
import json
import resource

def get_proc_info():
    UID = 1

    regex = re.compile(r'.+kernel-(.+)\.json')
    port_regex = re.compile(r'port=(\d+)')
    
    pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]

    # memory info from psutil.Process
    df_mem = []

    for pid in pids:
        try:
            ret = open(os.path.join('/proc', pid, 'cmdline'), 'rb').read()
            ret_str = ret.decode('utf-8')
        except IOError:  # proc has already terminated
            continue

        # jupyter notebook processes
        if len(ret_str) > 0 and ('jupyter' in ret_str or 'ipython' in ret_str) and 'kernel' in ret_str:
            # kernel
            kernel_ID = re.sub(regex, r'\1', ret_str)[0:-1]
            #kernel_ID = filter(lambda x: x in string.printable, kernel_ID)

            # memory
            process = psutil.Process(int(pid))
            mem = process.memory_info()[0] / float(1e9)

            # user name for pid
            for ln in open('/proc/{0}/status'.format(int(pid))):
                if ln.startswith('Uid:'):
                    uid = int(ln.split()[UID])
                    uname = pwd.getpwuid(uid).pw_name

            # user, pid, memory, kernel_ID
            df_mem.append([uname, pid, mem, kernel_ID])

    df_mem = pd.DataFrame(df_mem)
    df_mem.columns = ['user', 'pid', 'memory_GB', 'kernel_ID']
    return df_mem

def get_session_info(sessions_str):
    sessions = json.loads(sessions_str)
    df_nb = []
    kernels = []
    for sess in sessions:
        kernel_ID = sess['kernel']['id']
        if kernel_ID not in kernels:
            notebook_path = sess['notebook']['path']
            df_nb.append([kernel_ID, notebook_path])
            kernels.append(kernel_ID)

    df_nb = pd.DataFrame(df_nb)
    df_nb.columns = ['kernel_ID', 'notebook_path']
    return df_nb

def stats(sessions_str):
    df_mem = get_proc_info()
    df_nb = get_session_info(sessions_str)

    # joining tables
    df = pd.merge(df_nb, df_mem, on=['kernel_ID'], how='right')
    df = df.sort_values('memory_GB', ascending=False)
    del(df_mem)
    del(df_nb)
    return df.reset_index(drop=True)

def mem():
    mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    return mem # used memory in MB

def reduce_mem_usage_automatic(df):
    start_mem = df.memory_usage().sum() / 1024**2
    print('Memory usage of dataframe is {:.2f} MB'.format(start_mem))

    for col in df.columns:
        col_type = df[col].dtype
        if str(col_type) == 'int':
            c_min = df[col].min()
            c_max = df[col].max()
            if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                df[col] = df[col].astype(np.int8)
            elif c_min > np.iinfo(np.uint8).min and c_max < np.iinfo(np.uint8).max:
                df[col] = df[col].astype(np.uint8)
            elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                df[col] = df[col].astype(np.int16)
            elif c_min > np.iinfo(np.uint16).min and c_max < np.iinfo(np.uint16).max:
                df[col] = df[col].astype(np.uint16)
            elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                df[col] = df[col].astype(np.int32)
            elif c_min > np.iinfo(np.uint32).min and c_max < np.iinfo(np.uint32).max:
                df[col] = df[col].astype(np.uint32)                    
            elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                df[col] = df[col].astype(np.int64)
            elif c_min > np.iinfo(np.uint64).min and c_max < np.iinfo(np.uint64).max:
                df[col] = df[col].astype(np.uint64)
        elif col_type == np.float:
            c_min = df[col].min()
            c_max = df[col].max()
            if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                df[col] = df[col].astype(np.float16)
            elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                df[col] = df[col].astype(np.float32)
            else:
                df[col] = df[col].astype(np.float64)

    end_mem = df.memory_usage().sum() / 1024**2
    print('Memory usage after optimization is: {:.2f} MB'.format(end_mem))
    print('Decreased by {:.1f}%'.format(100 * (start_mem - end_mem) / start_mem))