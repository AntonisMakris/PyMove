import numpy as np
import pandas as pd
import time
from scipy.interpolate import interp1d
from tqdm import tqdm_notebook as tqdm
from pymove import utils as ut
from pymove import gridutils

"""main labels """
dic_labels = {"id" : 'id', 'lat' : 'lat', 'lon' : 'lon', 'datetime' : 'datetime'}

dic_features_label = {'tid' : 'tid', 'dist_to_prev' : 'dist_to_prev', "dist_to_next" : 'dist_to_next', 'dist_prev_to_next' : 'dist_prev_to_next', 
                    'time_to_prev' : 'time_to_prev', 'time_to_next' : 'time_to_next', 'speed_to_prev': 'speed_to_prev', 'speed_to_next': 'speed_to_next',
                    'period': 'period', 'day': 'day', 'index_grid_lat': 'index_grid_lat', 'index_grid_lon' : 'index_grid_lon',
                    'situation':'situation'}

def format_labels(df_, current_id, current_lat, current_lon, current_datetime):
    """ 
    Format the labels for the PyRoad lib pattern 
        labels output = lat, lon and datatime
    """ 
    dic_labels['id'] = current_id
    dic_labels['lon'] = current_lon
    dic_labels['lat'] = current_lat
    dic_labels['datetime'] = current_datetime
    return dic_labels


def compress_segment_stop_to_point(df_, label_segment = 'segment_stop', label_stop = 'stop', point_mean = 'default', drop_moves=True):        
    
    """ compreess a segment to point setting lat_mean e lon_mean to each segment"""
    try:
            
        if (label_segment in df_) & (label_stop in df_):
            #start_time = time.time()

            print("...setting mean to lat and lon...")
            df_['lat_mean'] = -1.0
            df_['lon_mean'] = -1.0


            if drop_moves is False:
                df_.at[df_[df_[label_stop] == False].index, 'lat_mean'] = np.NaN
                df_.at[df_[df_[label_stop] == False].index, 'lon_mean'] = np.NaN
            else:
                print('...move segments will be dropped...')


            print("...get only segments stop...")
            segments = df_[df_[label_stop] == True][label_segment].unique()
            
            sum_size_id = 0
            df_size = df_[df_[label_stop] == True].shape[0]
            curr_perc_int = -1
            start_time = time.time()

            for idx in tqdm(segments):
                filter_ = (df_[label_segment] == idx)
                
                size_id = df_[filter_].shape[0]
                # veirify se o filter is None
                if(size_id > 1):
                    # get first and last point of each stop segment
                    ind_start = df_[filter_].iloc[[0]].index
                    ind_end = df_[filter_].iloc[[-1]].index
                    
                    # default: point  
                    if point_mean == 'default':
                        #print('...Lat and lon are defined based on point that repeats most within the segment')
                        p = df_[filter_].groupby(['lat', 'lon'], as_index=False).agg({'id':'count'}).sort_values(['id']).tail(1)                     
                        df_.at[ind_start, 'lat_mean'] = p.iloc[0,0]
                        df_.at[ind_start, 'lon_mean'] = p.iloc[0,1]    
                        df_.at[ind_end, 'lat_mean'] = p.iloc[0,0]
                        df_.at[ind_end, 'lon_mean'] = p.iloc[0,1] 
                    
                    elif point_mean == 'centroid':
                        #print('...Lat and lon are defined by centroid of the all points into segment')
                        # set lat and lon mean to first_point and last points to each segment
                        df_.at[ind_start, 'lat_mean'] = df_.loc[filter_]['lat'].mean()
                        df_.at[ind_start, 'lon_mean'] = df_.loc[filter_]['lon'].mean()     
                        df_.at[ind_end, 'lat_mean'] = df_.loc[filter_]['lat'].mean()
                        df_.at[ind_end, 'lon_mean'] = df_.loc[filter_]['lon'].mean()   
                else:
                    print('There are segments with only one point: {}'.format(idx))
                
                sum_size_id  += size_id
                curr_perc_int, est_time_str = ut.progress_update(sum_size_id, df_size, start_time, curr_perc_int, step_perc=5)
            
            shape_before = df_.shape[0]

            # filter points to drop
            filter_drop = (df_['lat_mean'] == -1.0) & (df_['lon_mean'] == -1.0)
            shape_drop = df_[filter_drop].shape[0]

            if shape_drop > 0:
                print("...Dropping {} points...".format(shape_drop))
                df_.drop(df_[filter_drop].index, inplace=True)

            print("...Shape_before: {}\n...Current shape: {}".format(shape_before,df_.shape[0]))
            print('...Compression time: {:.3f} seconds'.format((time.time() - start_time)))
            print('-----------------------------------------------------\n')
        else:
            print('{} or {} is not in dataframe'.format(label_stop, label_segment))
    except Exception as e:
        raise e

def compress_segment_stop_to_point_optimizer(df_, label_segment = 'segment_stop', label_stop = 'stop', point_mean = 'default', drop_moves=True):        
    
    """ compreess a segment to point setting lat_mean e lon_mean to each segment"""
    try:
            
        if (label_segment in df_) & (label_stop in df_):
            #start_time = time.time()

            print("...setting mean to lat and lon...")
            #df_['lat_mean'] = -1.0
            #df_['lon_mean'] = -1.0

            lat_mean = np.full(df_.shape[0], -1.0, dtype=np.float32)
            lon_mean = np.full(df_.shape[0], -1.0, dtype=np.float32)

            if drop_moves is False:
                lat_mean[df_[df_[label_stop] == False].index] = np.NaN
                lon_mean[df_[df_[label_stop] == False].index] = np.NaN
            else:
                print('...move segments will be dropped...')

            sum_size_id = 0
            df_size = df_[df_[label_stop] == True].shape[0]
            curr_perc_int = -1
            start_time = time.time()
            
            print("...get only segments stop...")
            segments = df_[df_[label_stop] == True][label_segment].unique()
            for idx in tqdm(segments):
                filter_ = (df_[label_segment] == idx)
                
                size_id = df_[filter_].shape[0]
                # veirify se o filter is None
                if(size_id > 1):
                    # get first and last point of each stop segment
                    ind_start = df_[filter_].iloc[[0]].index
                    ind_end = df_[filter_].iloc[[-1]].index

                    if point_mean == 'default':
                        #print('...Lat and lon are defined based on point that repeats most within the segment')
                        p = df_[filter_].groupby(['lat', 'lon'], as_index=False).agg({'id':'count'}).sort_values(['id']).tail(1)                     
                        lat_mean[ind_start] = p.iloc[0,0]
                        lon_mean[ind_start] = p.iloc[0,1] 
                        lat_mean[ind_end] = p.iloc[0,0]
                        lon_mean[ind_end] = p.iloc[0,1] 
                        
                    elif point_mean == 'centroid':
                        #print('...Lat and lon are defined by centroid of the all points into segment')
                        # set lat and lon mean to first_point and last points to each segment
                        lat_mean[ind_start] = df_.loc[filter_]['lat'].mean()
                        lon_mean[ind_start] = df_.loc[filter_]['lon'].mean() 
                        lat_mean[ind_end] = df_.loc[filter_]['lat'].mean()
                        lon_mean[ind_end] = df_.loc[filter_]['lon'].mean() 
                else:
                    print('There are segments with only one point: {}'.format(idx))
                
                sum_size_id  += size_id
                curr_perc_int, est_time_str = ut.progress_update(sum_size_id, df_size, start_time, curr_perc_int, step_perc=10)
            
            df_['lat_mean'] = lat_mean
            df_['lon_mean'] = lon_mean
            del lat_mean
            del lon_mean

            shape_before = df_.shape[0]
            # filter points to drop
            filter_drop = (df_['lat_mean'] == -1.0) & (df_['lon_mean'] == -1.0)
            shape_drop = df_[filter_drop].shape[0]

            if shape_drop > 0:
                print("...Dropping {} points...".format(shape_drop))
                df_.drop(df_[filter_drop].index, inplace=True)

            print("...Shape_before: {}\n...Current shape: {}".format(shape_before,df_.shape[0]))
            print('...Compression time: {:.3f} seconds'.format((time.time() - start_time)))
            print('-----------------------------------------------------\n')
        else:
            print('{} or {} is not in dataframe'.format(label_stop, label_segment))
    except Exception as e:
        raise e

def create_or_update_move_stop_by_dist_time(df_, label_id='id', dist_radius=30, time_radius=900):
    try:
        start_time = time.time()
        label_segment_stop = 'segment_stop'
        trajutils.segment_traj_by_max_dist(df_, label_id=label_id, max_dist_between_adj_points=dist_radius, label_segment=label_segment_stop)
        
        if(label_segment_stop in df_):
            #update dist, time and speed using segment_stop
            trajutils.create_update_dist_time_speed_features(df_, label_id=label_segment_stop)     
            
            print('Create or update stop as True or False')
            print('...Creating stop features as True or False using {} to time in seconds'.format(time_radius))
            df_['stop'] = False
            df_agg_tid = df_.groupby(by=label_segment_stop).agg({'time_to_prev':'sum'}).query('time_to_prev > '+str(time_radius)).index
            idx = df_[df_[label_segment_stop].isin(df_agg_tid)].index
            df_.at[idx, 'stop'] = True
            print(df_['stop'].value_counts())
            print('\nTotal Time: {:.2f} seconds'.format((time.time() - start_time)))
            print('-----------------------------------------------------\n')
    except Exception as e:
        raise e

def show_trajectories_info(df_, dic_labels=dic_labels):
    """
        show dataset information from dataframe, this is number of rows, datetime interval, and bounding box 
    """
    try:
        print('\n======================= INFORMATION ABOUT DATASET =======================\n')
        print('Number of Points: {}\n'.format(df_.shape[0]))
        if dic_labels['id'] in df_:
            print('Number of IDs objects: {}\n'.format(df_[dic_labels['id']].nunique()))
        if dic_features_label['tid'] in df_:
            print('Number of TIDs trajectory: {}\n'.format(df_[dic_features_label['tid']].nunique()))
        if dic_labels['datetime'] in df_:
            print('Start Date:{}     End Date:{}\n'.format(df_[dic_labels['datetime']].min(), df_[dic_labels['datetime']].max()))
        if dic_labels['lat'] and dic_labels['lon'] in df_:
            print('Bounding Box:{}\n'.format(get_bbox(df_, dic_labels))) # bbox return =  Lat_min , Long_min, Lat_max, Long_max) 
        if dic_features_label['time_to_prev'] in df_:            
            print('Gap time MAX:{}     Gap time MIN:{}\n'.format(round(df_[dic_features_label['time_to_prev']].max(),3), round(df_[dic_features_label['time_to_prev']].min(), 3)))
        if dic_features_label['speed_to_prev'] in df_:            
            print('Speed MAX:{}    Speed MIN:{}\n'.format(round(df_[dic_features_label['speed_to_prev']].max(), 3), round(df_[dic_features_label['speed_to_prev']].min(), 3))) 
        if dic_features_label['dist_to_prev'] in df_:            
            print('Distance MAX:{}    Distance MIN:{}\n'.format(round(df_[dic_features_label['dist_to_prev']].max(),3), round(df_[dic_features_label['dist_to_prev']].min(), 3))) 
            
        print('\n=========================================================================\n')
    except Exception as e:
        raise e    

def get_bbox(df_, dic_labels=dic_labels):
    """
    A bounding box (usually shortened to bbox) is an area defined by two longitudes and two latitudes, where:
    Latitude is a decimal number between -90.0 and 90.0. Longitude is a decimal number between -180.0 and 180.0.
    They usually follow the standard format of: 
    bbox = left,bottom,right,top 
    bbox = min Longitude , min Latitude , max Longitude , max Latitude 
    """
    try:
        return (df_[dic_labels['lat']].min(), df_[dic_labels['lon']].min(), df_[dic_labels['lat']].max(), df_[dic_labels['lon']].max())
    except Exception as e:
        raise e

def bbox_split(bbox, number_grids):
    """
        split bound box in N grids of the same size
    """
    lat_min = bbox[0]
    lon_min = bbox[1]
    lat_max = bbox[2]
    lon_max = bbox[3]
    
    const_lat =  abs(abs(lat_max) - abs(lat_min))/number_grids
    const_lon =  abs(abs(lon_max) - abs(lon_min))/number_grids
    print('const_lat: {}\nconst_lon: {}'.format(const_lat, const_lon))

    df = pd.DataFrame(columns=['lat_min', 'lon_min', 'lat_max', 'lon_max'])
    for i in range(number_grids):
        df = df.append({'lat_min':lat_min, 'lon_min': lon_min + (const_lon * i), 'lat_max': lat_max, 'lon_max':lon_min + (const_lon * (i + 1))}, ignore_index=True)
    return df

def filter_bbox(df_, bbox, filter_out=False, dic_labels=dic_labels, inplace=False):
    """
    Filter bounding box.
    Example: 
        filter_bbox(df_, [-3.90, -38.67, -3.68, -38.38]) -> Fortaleza
            lat_down =  bbox[0], lon_left =  bbox[1], lat_up = bbox[2], lon_right = bbox[3]
    """
    try:
        filter_ = (df_[dic_labels['lat']] >=  bbox[0]) & (df_[dic_labels['lat']] <= bbox[2]) & (df_[dic_labels['lon']] >= bbox[1]) & (df_[dic_labels['lon']] <= bbox[3])
        if filter_out:
            filter_ = ~filter_

        if inplace:
            df_.drop( index=df_[ ~filter_ ].index, inplace=True )
            return df_
        else:
            return df_.loc[ filter_ ]
    except Exception as e: 
            raise e

def filter_by_datetime(df_, startDatetime=None, endDatetime=None, dic_labels=dic_labels, filter_out=False):
    
    try:
        if startDatetime is not None and endDatetime is not None:
            filter_ = (df_[dic_labels['datetime']] > startDatetime) & (df_[dic_labels['datetime']] <= endDatetime)
        elif endDatetime is not None:
            filter_ = (df_[dic_labels['datetime']] <= endDatetime)
        else:
            filter_ = (df_[dic_labels['datetime']] > startDatetime)
        
        if filter_out:
            filter_ = ~filter_
        
        return df_[filter_]

    except Exception as e:
        raise e

def filter_by_label(df_, value, label_name, filter_out=False):
    try:
        filter_ = (df_[label_name] == value)

        if filter_out:
            filter_ = ~filter_
        
        return df_[filter_]
    
    except Exception as e:
        raise e

def filter_by_id(df_, id_=None, label_id=dic_labels['id'], filter_out=False):
    """
        filter dataset from id
    """
    return filter_by_label(df_, id_, label_id, filter_out)

def filter_by_tid(df_, tid_=None, label_tid=dic_features_label['tid'], filter_out=False):
    """
        filter dataset from id
    """
    return filter_by_label(df_, tid_, label_tid, filter_out)

def filter_jumps(df_, jump_coefficient=3.0, threshold = 1, filter_out=False):
    
    if df_.index.name is not None:
        print('...Reset index for filtering\n')
        df_.reset_index(inplace=True)
    
    if dic_features_label['dist_to_prev'] in df_ and dic_features_label['dist_to_next'] and dic_features_label['dist_prev_to_next'] in df_:
        filter_ = (df_[dic_features_label['dist_to_next']] > threshold) & (df_[dic_features_label['dist_to_prev']] > threshold) & (df_[dic_features_label['dist_prev_to_next']] > threshold) & \
        (jump_coefficient * df_[dic_features_label['dist_prev_to_next']] < df_[dic_features_label['dist_to_next']]) & \
        (jump_coefficient * df_[dic_features_label['dist_prev_to_next']] < df_[dic_features_label['dist_to_prev']])  

        if filter_out:
            filter_ = ~filter_

        print('...Filtring jumps \n')
        return df_[filter_]
    
    else:
        print('...Distances features were not created')
        return df_

def lon2XSpherical(lon):
    """
    From Longitude to X EPSG:3857 WGS 84 / Pseudo-Mercator
    https://epsg.io/transform
    @param longitude in degrees
    @return X offset from your original position in meters.
    -38.501597 -> -4285978.17
    """
    return 6378137 * np.radians(lon)

def lat2YSpherical(lat):
    """
    From Latitude to Y EPSG:3857 WGS 84 / Pseudo-Mercator
    @param latitude in degrees
    @return Y offset from your original position in meters.
    -3.797864 -> -423086.22
    """
    return 6378137 * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2.0))

def x2LonSpherical(x):
    """
    From X to Longitude.
    -4285978.17 -> -38.501597
    """
    return np.degrees(x / 6378137.0)

def y2LatSpherical(y):
    """
    From Y to Longitude.
    -423086.22 -> -3.797864 
    """
    return np.degrees(np.arctan(np.sinh(y / 6378137.0)))

def haversine(lat1, lon1, lat2, lon2, to_radians=True, earth_radius=6371):
    
    """
    Vectorized haversine function: https://stackoverflow.com/questions/43577086/pandas-calculate-haversine-distance-within-each-group-of-rows
    About distance between two points: https://janakiev.com/blog/gps-points-distance-python/
    Calculate the great circle distance between two points on the earth (specified in decimal degrees or in radians).
    All (lat, lon) coordinates must have numeric dtypes and be of equal length.
    Result in meters. Use 3956 in earth radius for miles
    """
    try:
        # convert sinfle points to array
        """if type(lat1) is not np.ndarray:
            print('...Converting lat1 in np.ndarray')
            lat1 = np.array(lat1)
        if type(lon1) is not np.ndarray:
            print('...Converting lon1 in np.ndarray')
            lon1 = np.array(lon1)
        if type(lat2) is not np.ndarray:
            print('...Converting lat2 in np.ndarray')
            lat2 = np.array(lat2)
        if type(lon2) is not np.ndarray:
            print('...Converting lat1 in np.ndarray')
            lon2 = np.array(lon2)
"""
        if to_radians:
            lat1, lon1, lat2, lon2 = np.radians([lat1, lon1, lat2, lon2])
            a = np.sin((lat2-lat1)/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2-lon1)/2.0)**2
        #return earth_radius * 2 * np.arcsin(np.sqrt(a)) * 1000  # result in meters (* 1000)
        return 2 * 1000 * earth_radius * np.arctan2(a ** 0.5, (1-a) ** 0.5)
        #np.arctan2(np.sqrt(a), np.sqrt(1-a)) 

    except Exception as e:
        print('\nError Haverside fuction')
        print('lat1:{}\nlon1:{}\nlat2:{}\nlon2:{}'.format(lat1, lon1, lat2, lon2))
        print('type(lat1) = {}\ntype(lon1)= {}\ntype(lat2) = {}\ntype(lon2)= {}\n'.format(type(lat1), type(lon1), type(lat2), type(lon2)))
        raise e

def create_update_tid_based_on_id_datatime(df_, dic_labels=dic_labels, str_format="%Y%m%d%H", sort=True):
    """
        Create or update trajectory id  
            Exampĺe: ID = M00001 and datetime = 2019-04-28 00:00:56  -> tid = M000012019042800
    """
    try:
        print('\nCreating or updating tid feature...\n')
        if sort is True:
            print('...Sorting by {} and {} to increase performance\n'.format(dic_labels['id'], dic_labels['datetime']))
            df_.sort_values([dic_labels['id'], dic_labels['datetime']], inplace=True)

        df_[dic_features_label['tid']] = df_[dic_labels['id']].astype(str) + df_[dic_labels['datetime']].dt.strftime(str_format)  
        #%.dt.date.astype(str)        
        print('\n...tid feature was created...\n')      
    except Exception as e:
        raise e

def create_update_date_features(df_, dic_labels=dic_labels):
    try:
        print('Creating date features...')
        if dic_labels['datetime'] in df_:
            df_['date'] = df_[dic_labels['datetime']].dt.date
            print('..Date features was created...\n')
    except Exception as e:
        raise e
    
def create_update_hour_features(df_, dic_labels=dic_labels):    
    try:
        print('\nCreating or updating a feature for hour...\n')
        if dic_labels['datetime'] in df_:
            df_['hour'] = df_[dic_labels['datetime']].dt.hour
            print('...Hour feature was created...\n')
    except Exception as e:
        raise e

def create_update_datetime_in_format_cyclical(df_, label_datetime = 'datetime'):
    try:
        #https://ianlondon.github.io/blog/encoding-cyclical-features-24hour-time/
        #https://www.avanwyk.com/encoding-cyclical-features-for-deep-learning/
        print('Encoding cyclical continuous features - 24-hour time')
        if label_datetime in df_:
            hours = df_[label_datetime].dt.hour
            df_['hour_sin'] = np.sin(2 * np.pi * hours/23.0)
            df_['hour_cos'] = np.cos(2 * np.pi * hours/23.0)
            print('...hour_sin and  hour_cos features were created...\n')
    except Exception as e:
        raise e

def create_update_day_of_the_week_features(df_, dic_labels=dic_labels):
    """
        Create or update a feature day of the week from datatime
            Exampĺe: datetime = 2019-04-28 00:00:56  -> day = Sunday
    """
    try:
        print('\nCreating or updating day of the week feature...\n')
        df_[dic_features_label['day']] = df_[dic_labels['datetime']].dt.day_name()
        print('...the day of the week feature was created...\n')
    except Exception as e:
        raise e

def create_update_weekend_features(df_, label_date='datetime', create_day_of_week=False):
    try:
        create_update_day_of_the_week_features(df_)
        print('Creating or updating a feature for weekend\n')
        if 'day' in df_:
            index_fds = df_[(df_['day'] == 'Saturday') | (df_['day'] == 'Sunday')].index
            df_['weekend'] = 0
            df_.at[index_fds, 'weekend'] = 1
            print('...Weekend was set as 1 or 0...\n')         
            if ~create_day_of_week:
                print('...dropping colum day\n')
                del df_['day']
    except Exception as e:
        raise e

def create_update_time_of_day_features(df_, dic_labels=dic_labels):
    """
        Create a feature time of day or period from datatime
            Examples: 
                datetime1 = 2019-04-28 02:00:56 -> period = early morning
                datetime2 = 2019-04-28 08:00:56 -> period = morning
                datetime3 = 2019-04-28 14:00:56 -> period = afternoon
                datetime4 = 2019-04-28 20:00:56 -> period = evening
    """
    try:
        print('\nCreating or updating period feature\n...early morning from 0H to 6H\n...morning from 6H to 12H\n...afternoon from 12H to 18H\n...evening from 18H to 24H')
        conditions =   [(df_[dic_labels['datetime']].dt.hour >= 0) & (df_[dic_labels['datetime']].dt.hour < 6), 
                        (df_[dic_labels['datetime']].dt.hour >= 6) & (df_[dic_labels['datetime']].dt.hour < 12),
                        (df_[dic_labels['datetime']].dt.hour >= 12) & (df_[dic_labels['datetime']].dt.hour < 18),  
                        (df_[dic_labels['datetime']].dt.hour >= 18) & (df_[dic_labels['datetime']].dt.hour < 24)]
        choices = ['early morning', 'morning', 'afternoon', 'evening']
        df_[dic_features_label['period']] = np.select(conditions, choices, 'undefined')      
        print('...the period of day feature was created')
    except Exception as e:
        raise e

def create_update_dist_features(df_, label_id=dic_labels['id'], dic_labels=dic_labels, label_dtype = np.float64, sort=True):
    """
        Create three distance in meters to an GPS point P (lat, lon)
            Example:
                P to P.next = 2 meters
                P to P.previous = 1 meter
                P.previous to P.next = 1 meters
    """
    try:
        print('\nCreating or updating distance features in meters...\n')
        start_time = time.time()

        if sort is True:
            print('...Sorting by {} and {} to increase performance\n'.format(label_id, dic_labels['datetime']))
            df_.sort_values([label_id, dic_labels['datetime']], inplace=True)

        if df_.index.name is None:
            print('...Set {} as index to increase attribution performance\n'.format(label_id))
            df_.set_index(label_id, inplace=True)
        
        """ create ou update columns"""
        df_[dic_features_label['dist_to_prev']] = label_dtype(-1.0)
        df_[dic_features_label['dist_to_next']] = label_dtype(-1.0)
        df_[dic_features_label['dist_prev_to_next']]= label_dtype(-1.0)

        ids = df_.index.unique()
        df_size = df_.shape[0]
        curr_perc_int = -1
        start_time = time.time()
        deltatime_str = ''
        sum_size_id = 0
        size_id = 0
        for idx in ids:
            curr_lat = df_.at[idx, dic_labels['lat']]
            curr_lon = df_.at[idx, dic_labels['lon']]

            size_id = curr_lat.size
            
            if size_id <= 1:
                print('...id:{}, must have at least 2 GPS points\n'.format(idx))
                #df_.at[idx, dic_features_label['dist_to_next']] = np.nan
                df_.at[idx, dic_features_label['dist_to_prev']] = np.nan
                #df_.at[idx, dic_features_label['dist_prev_to_next']] = np.nan    
                
            else:
                prev_lat = ut.shift(curr_lat, 1)
                prev_lon = ut.shift(curr_lon, 1)
                # compute distance from previous to current point
                df_.at[idx, dic_features_label['dist_to_prev']] = haversine(prev_lat, prev_lon, curr_lat, curr_lon)
                
                next_lat = ut.shift(curr_lat, -1)
                next_lon = ut.shift(curr_lon, -1)
                # compute distance to next point
                df_.at[idx, dic_features_label['dist_to_next']] = haversine(curr_lat, curr_lon, next_lat, next_lon)
                
                # using pandas shift in a large dataset: 7min 21s
                # using numpy shift above: 33.6 s

                # use distance from previous to next
                df_.at[idx, dic_features_label['dist_prev_to_next']] = haversine(prev_lat, prev_lon, next_lat, next_lon)
                
                sum_size_id += size_id
                curr_perc_int, est_time_str = ut.progress_update(sum_size_id, df_size, start_time, curr_perc_int, step_perc=20)
        df_.reset_index(inplace=True)
        print('...Reset index\n')
        print('..Total Time: {}'.format((time.time() - start_time)))
    except Exception as e:
        print('label_id:{}\nidx:{}\nsize_id:{}\nsum_size_id:{}'.format(label_id, idx, size_id, sum_size_id))
        raise e

def create_update_dist_time_speed_features(df_, label_id=dic_labels['id'], dic_labels=dic_labels, label_dtype = np.float64, sort=True):
    """
    Firstly, create three distance to an GPS point P (lat, lon)
    After, create two feature to time between two P: time to previous and time to next 
    Lastly, create two feature to speed using time and distance features
    Example:
        dist_to_prev =  248.33 meters, dist_to_prev 536.57 meters
        time_to_prev = 60 seconds, time_prev = 60.0 seconds
        speed_to_prev = 4.13 m/s, speed_prev = 8.94 m/s.
    """
    try:
        print('Creating or updating distance, time and speed features in meters by seconds') 
        start_time = time.time()

        if sort is True:
            print('...Sorting by {} and {} to increase performance'.format(label_id, dic_labels['datetime']))
            df_.sort_values([label_id, dic_labels['datetime']], inplace=True)
            #time_sort = time.time()

        if df_.index.name is None:
            print('...Set {} as index to a higher peformance'.format(label_id))
            df_.set_index(label_id, inplace=True)
           # time_index = time.time()

        """create new feature to time"""
        df_[dic_features_label['dist_to_prev']] = label_dtype(-1.0)

        """create new feature to time"""
        #df_[dic_features_label['time_to_next']] = label_dtype(-1.0)
        df_[dic_features_label['time_to_prev']] = label_dtype(-1.0)

        """create new feature to speed"""
        #df_[dic_features_label['speed_to_next']] = label_dtype(-1.0)
        df_[dic_features_label['speed_to_prev']] = label_dtype(-1.0)

        ids = df_.index.unique()
        df_size = df_.shape[0]
        curr_perc_int = -1
        sum_size_id = 0
        size_id = 0

        for idx in ids:
            curr_lat = df_.at[idx, dic_labels['lat']]
            curr_lon = df_.at[idx, dic_labels['lon']]

            size_id = curr_lat.size
            
            if size_id <= 1:
                df_.at[idx, dic_features_label['dist_to_prev']] = np.nan 
                df_.at[idx, dic_features_label['time_to_prev']] = np.nan
                df_.at[idx, dic_features_label['speed_to_prev']] = np.nan   
            else:
                prev_lat = ut.shift(curr_lat, 1)
                prev_lon = ut.shift(curr_lon, 1)
                # compute distance from previous to current point
                df_.at[idx, dic_features_label['dist_to_prev']] = haversine(prev_lat, prev_lon, curr_lat, curr_lon)
                
                
            #""" if data is numpy array, then it is a datetime object with size <= 1"""
            #if type(df_.at[idx, dic_labels['datetime']]) is not np.ndarray:
                #size_id = 1
                #print('...id:{}, must have at least 2 GPS points\n'.format(idx))
                #df_.at[idx, dic_features_label['time_to_prev']] = np.nan
                #df_.at[idx, dic_features_label['speed_to_prev']] = np.nan   
            #else:
                #"""time_to_prev = current_datetime - prev_datetime 
                #the time_delta must be in nanosecond, then we multiplie by 10-⁹ to tranform in seconds """
                #size_id = df_.at[idx, dic_labels['datetime']].size

                time_ = df_.at[idx, dic_labels['datetime']].astype(label_dtype)
                time_prev = (time_ - ut.shift(time_, 1))*(10**-9)
                df_.at[idx, dic_features_label['time_to_prev']] = time_prev

                """ set time_to_next"""
                #time_next = (ut.shift(time_, -1) - time_)*(10**-9)
                #df_.at[idx, dic_features_label['time_to_next']] = time_next
                
                "set Speed features"
                df_.at[idx, dic_features_label['speed_to_prev']] = df_.at[idx, dic_features_label['dist_to_prev']] / (time_prev)  # unit: m/s
                #df_.at[idx, dic_features_label['speed_to_next']] = df_.at[idx, dic_features_label['dist_to_next']] / (time_next)  # unit: m/s


                #ut.change_df_feature_values_using_filter(df_, id_, 'delta_time', filter_points, delta_times)
                #ut.change_df_feature_values_using_filter(df_, id_, 'delta_dist', filter_points, delta_dists)
                #ut.change_df_feature_values_using_filter(df_, id_, 'speed', filter_points, speeds)

                sum_size_id  += size_id
                curr_perc_int, est_time_str = ut.progress_update(sum_size_id , df_size, start_time, curr_perc_int, step_perc=20)
        print('...Reset index...')
        df_.reset_index(inplace=True)
        print('\nTotal Time: {:.2f} seconds'.format((time.time() - start_time)))
        print('-----------------------------------------------------\n')
    except Exception as e:
        print('label_id:{}\nidx:{}\nsize_id:{}\nsum_size_id:{}'.format(label_id, idx, size_id, sum_size_id ))
        raise e

def create_update_move_and_stop_by_radius(df_, radius=0, target_label='dist_to_prev', new_label=dic_features_label['situation']):
    
    try:
        print('\nCreating or updating features MOVE and STOPS...\n')
        conditions = (df_[target_label] > radius), (df_[target_label] <= radius)
        choices = ['move', 'stop']

        df_[new_label] = np.select(conditions, choices, np.nan)      
        print('\n....There are {} stops to this parameters\n'.format(df_[df_[new_label] == 'stop'].shape[0]))
    except Exception as e:
        raise e

def create_update_index_grid_feature(df_, dic_grid=None, dic_labels=dic_labels, label_dtype=np.int64, sort=True):
    print('\nCreating or updating index of the grid feature..\n')
    try:
        if dic_grid is not None:
            if sort:
                df_.sort_values([dic_labels['id'], dic_labels['datetime']], inplace=True)

            lat_, lon_ = gridutils.point_to_index_grid(df_[dic_labels['lat'] ], df_[dic_labels['lon'] ], dic_grid)
            df_[dic_features_label['index_grid_lat']] = label_dtype(lat_)
            df_[dic_features_label['index_grid_lon']] = label_dtype(lon_)   
        else:
            print('... inform a grid virtual dictionary\n')
    except Exception as e:
        raise e

def clean_duplicates(df_, subset=None, keep='first', inplace=False, sort=True, return_idx=False):
    """
    Return DataFrame with duplicate rows removed, optionally only considering certain columns.
    """
    print('\nRemove rows duplicates by subset')
    if sort is True:
        print('...Sorting by {} and {} to increase performance\n'.format(dic_labels['id'], dic_labels['datetime']))
        df_.sort_values([dic_labels['id'], dic_labels['datetime']], inplace=True)
    
    idx = df_.duplicated(subset=subset )
    tam_drop = df_[idx].shape[0] 

    if tam_drop > 0:
        df_.drop_duplicates(subset, keep, inplace)
        print('...There are {} GPS points duplicated'.format(tam_drop))
    else:
        print('...There are no GPS points duplicated')

    if return_idx:
        return return_idx

def clean_consecutive_duplicates(df_, subset=None, keep='first', inplace=False):
    """
        Return DataFrame with consecutive duplicated rows removed, considering a subset
        
        Ex:
            clean_consecutive_duplicates(df, subset=['lat', 'lon'])
    """
    if keep == 'first':
        n = 1
    else:
        n = -1
        
    if subset is None:
        filter_ = (df_.shift(n) != df_).any(axis=1)
    else:
        filter_ = (df_[subset].shift(n) != df_[subset]).any(axis=1)

    if inplace:
        df_.drop( index=df_[~filter_].index, inplace=True )
        return df_
    else:
        return df_.loc[ filter_ ]

def clean_NaN_values(df_, axis=0, how='any', thresh=None, subset=None, inplace=True):
    #df.isna().sum()
    df_.dropna(axis=axis, how=how, thresh=thresh, subset=None, inplace=inplace)
         
def clean_gps_jumps_by_distance(df_, label_id=dic_labels['id'], jump_coefficient=3.0, threshold = 1, dic_labels=dic_labels, label_dtype=np.float64, sum_drop=0):

    create_update_dist_features(df_, label_id, dic_labels, label_dtype=label_dtype)

    try:
        print('\nCleaning gps jumps by distance to jump_coefficient {}...\n'.format(jump_coefficient))
        df_jumps = filter_jumps(df_, jump_coefficient, threshold)
        rows_to_drop = df_jumps.shape[0]

        if rows_to_drop > 0:
            print('...Dropping {} rows of gps points\n'.format(rows_to_drop))
            shape_before = df_.shape[0]
            df_.drop(index=df_jumps.index, inplace=True)
            sum_drop = sum_drop + rows_to_drop
            print('...Rows before: {}, Rows after:{}, Sum drop:{}\n'.format(shape_before, df_.shape[0], sum_drop))
            clean_gps_jumps_by_distance(df_, label_id, jump_coefficient, threshold, dic_labels, label_dtype, sum_drop)  
        else:
            print('{} GPS points were dropped'.format(sum_drop))    

    except Exception as e:
       raise e

def clean_gps_nearby_points_by_distances(df_, label_id=dic_labels['id'], dic_labels=dic_labels, radius_area=10.0, label_dtype=np.float64):

    create_update_dist_features(df_, label_id, dic_labels, label_dtype)
    try:
        print('\nCleaning gps points from radius of {} meters\n'.format(radius_area))
        if df_.index.name is not None:
            print('...Reset index for filtering\n')
            df_.reset_index(inplace=True)
    
        if dic_features_label['dist_to_prev'] in df_:
            filter_nearby_points = (df_[dic_features_label['dist_to_prev']] <= radius_area)

            idx = df_[filter_nearby_points].index
            print('...There are {} gps points to drop\n'.format(idx.shape[0]))
            if idx.shape[0] > 0:
                print('...Dropping {} gps points\n'.format(idx.shape[0]))
                shape_before = df_.shape[0]
                df_.drop(index=idx, inplace=True)
                print('...Rows before: {}, Rows after:{}\n'.format(shape_before, df_.shape[0]))
                clean_gps_nearby_points_by_distances(df_, label_id, dic_labels, radius_area, label_dtype)
        else:
            print('...{} is not in the dataframe'.format(dic_features_label['dist_to_prev']))
    except Exception as e:
       raise e

def clean_gps_nearby_points_by_speed(df_, label_id=dic_labels['id'], dic_labels=dic_labels, speed_radius=0.0, label_dtype=np.float64):

    create_update_dist_time_speed_features(df_, label_id, dic_labels, label_dtype)
    try:
        print('\nCleaning gps points using {} speed radius\n'.format(speed_radius))
        if df_.index.name is not None:
            print('...Reset index for filtering\n')
            df_.reset_index(inplace=True)
    
        if dic_features_label['speed_to_prev'] in df_:
            filter_nearby_points = (df_[dic_features_label['speed_to_prev']] <= speed_radius)

            idx = df_[filter_nearby_points].index
            print('...There are {} gps points to drop\n'.format(idx.shape[0]))
            if idx.shape[0] > 0:
                print('...Dropping {} gps points\n'.format(idx.shape[0]))
                shape_before = df_.shape[0]
                df_.drop(index=idx, inplace=True)
                print('...Rows before: {}, Rows after:{}\n'.format(shape_before, df_.shape[0]))
                clean_gps_nearby_points_by_speed(df_, label_id, dic_labels, speed_radius, label_dtype)
        else:
            print('...{} is not in the dataframe'.format(dic_features_label['dist_to_prev']))
    except Exception as e:
       raise e

def clean_gps_speed_max_radius(df_, label_id=dic_labels['id'], dic_labels=dic_labels, speed_max=50.0, label_dtype=np.float64):

    create_update_dist_time_speed_features(df_, label_id, dic_labels=dic_labels, label_dtype=label_dtype)

    print('\nClean gps points with speed max > {} meters by seconds'.format(speed_max))

    if dic_features_label['speed_to_prev'] in df_:
        filter_ = (df_[dic_features_label['speed_to_prev']] > speed_max) | (df_[dic_features_label['speed_to_next']] > speed_max)
    
        idx = df_[filter_].index
    
        print('...There {} gps points with speed_max > {}\n'.format(idx.shape[0], speed_max))
        if idx.shape[0] > 0:
            print('...Dropping {} rows of jumps by speed max\n'.format(idx.shape[0]))
            shape_before = df_.shape[0]
            df_.drop(index=idx, inplace=True)
            print('...Rows before: {}, Rows after:{}\n'.format(shape_before, df_.shape[0]))
            clean_gps_speed_max_radius(df_, label_id, dic_labels, speed_max, label_dtype)

def clean_id_by_time_max(df_, label_id = 'id', time_max = 3600, return_idx=True):
    print('\nClean gps points with time max by id < {} seconds'.format(time_max))
    if 'time_to_prev' in df_:
        df_id_drop = df_.groupby([label_id], as_index=False).agg({'time_to_prev':'sum'}).query('time_to_prev < {}'.format(time_max))
        print("...Ids total: {}\nIds to drop:{}".format(df_[label_id].nunique(),df_id_drop[label_id].nunique()))
        if df_id_drop.shape[0] > 0:
            before_drop = df_.shape[0]
            idx = df_[df_[label_id].isin(df_id_drop[label_id])].index
            df_.drop(idx, inplace=True)
            print("...Rows before drop: {}\n Rows after drop: {}".format(before_drop, df_.shape[0]))
            if(return_idx):
                return idx

def clean_traj_with_few_points(df_, label_tid=dic_features_label['tid'], dic_labels=dic_labels, min_points_per_trajectory=2, label_dtype=np.float64):

    if df_.index.name is not None:
        print('\n...Reset index for filtering\n')
        df_.reset_index(inplace=True)

    df_count_tid = df_.groupby(by= label_tid).size()
    tids_with_few_points = df_count_tid[ df_count_tid < min_points_per_trajectory ].index
    idx = df_[ df_[label_tid].isin(tids_with_few_points) ].index
    
    print('\n...There are {} ids with few points'.format(tids_with_few_points.shape[0])) 
    shape_before_drop = df_.shape
    if idx.shape[0] > 0:
        print('\n...Tids before drop: {}'.format(df_[label_tid].unique().shape[0]))
        df_.drop(index=idx, inplace=True)
        print('\n...Tids after drop: {}'.format(df_[label_tid].unique().shape[0]))
        print('\n...Shape - before drop: {} - after drop: {}'.format(shape_before_drop, df_.shape))
        create_update_dist_time_speed_features(df_, label_tid, dic_labels, label_dtype)      

def clean_traj_short_and_few_points_(df_,  label_id=dic_features_label['tid'], dic_labels=dic_labels, min_trajectory_distance=100, min_points_per_trajectory=2, label_dtype=np.float64):
    # remove_tids_with_few_points must be performed before updating features, because 
    # those features only can be computed with at least 2 points per trajactories
    print('\nRemove short trajectories...')
    clean_traj_with_few_points(df_, label_id, dic_labels, min_points_per_trajectory, label_dtype)
    
    create_update_dist_time_speed_features(df_, label_id, dic_labels, label_dtype)

    if df_.index.name is not None:
        print('reseting index')
        df_.reset_index(inplace=True)
        
    print('\n...Dropping unnecessary trajectories...')
    df_agg_tid = df_.groupby(by=label_id).agg({dic_features_label['dist_to_prev']:'sum'})
    filter_ = (df_agg_tid[dic_features_label['dist_to_prev']] < min_trajectory_distance)    
    tid_selection = df_agg_tid[ filter_ ].index
    # Whether each element in the DataFrame is contained in values.
    idx = df_[ df_[label_id].isin(tid_selection) ].index
    print('\n...short trajectories and trajectories with a minimum distance ({}): {}'.format(df_agg_tid.shape[0], min_trajectory_distance))
    print('\n...There are {} tid do drop'.format(tid_selection.shape[0]))
    shape_before_drop = df_.shape

    if idx.shape[0] > 0:
        tids_before_drop = df_[label_id].unique().shape[0]
        df_.drop(index=idx, inplace=True)
        print('\n...Tids - before drop: {} - after drop: {}'.format(tids_before_drop, df_[label_id].unique().shape[0]))
        print('\n...Shape - before drop: {} - after drop: {}'.format(shape_before_drop, df_.shape))
        clean_traj_short_and_few_points_(df_, dic_labels, min_trajectory_distance, min_points_per_trajectory, label_dtype)    

def segment_traj_by_dist_time_speed(df_, label_id=dic_labels['id'], max_dist_between_adj_points=3000, max_time_between_adj_points=7200,
                      max_speed_between_adj_points=50.0, label_segment='tid_part'):
    """ segment trajectory based on threshold for each ID object"""
    """
    index_name is the current id.
    label_new_id is the new splitted id.
    time, dist, speeed features must be updated after split.
    """
        
    print('Split trajectories')
    print('...max_time_between_adj_points:', max_time_between_adj_points)
    print('...max_dist_between_adj_points:', max_dist_between_adj_points)
    print('...max_speed:', max_speed_between_adj_points)
    
    try:
        if df_.index.name is None:
            print('...setting {} as index'.format(label_id))
            df_.set_index(label_id, inplace=True)

        curr_tid = 0
        if label_segment not in df_:
            df_[label_segment] = curr_tid

        ids = df_.index.unique()
        count = 0
        df_size = df_.shape[0]
        curr_perc_int = -1
        start_time = time.time()

        for idx in ids:
            curr_tid += 1
            
            filter_ = (df_.at[idx, dic_features_label['time_to_prev']] > max_time_between_adj_points) | \
                        (df_.at[idx, dic_features_label['dist_to_prev']] > max_dist_between_adj_points) | \
                        (df_.at[idx, dic_features_label['speed_to_prev']] > max_speed_between_adj_points)        

            """ check if object have only one point to be removed """
            if filter_.shape == ():
                print('id: {} has not point to split'.format(id))
                df_.at[idx, label_segment] = curr_tid
                count+=1
            else:
                tids = np.empty(filter_.shape[0], dtype=np.int64)
                tids.fill(curr_tid)
                for i, has_problem in enumerate(filter_):
                    if has_problem:
                        curr_tid += 1
                        tids[i:] = curr_tid
                count += tids.shape[0]
                df_.at[idx, label_segment] = tids
            
            curr_perc_int, est_time_str = ut.progress_update(count, df_size, start_time, curr_perc_int, step_perc=20)

        if label_id == label_segment:
            df_.reset_index(drop=True, inplace=True)
            print('... label_id = label_segment, then reseting and drop index')
        else:
            df_.reset_index(inplace=True)
            print('... Reseting index')
        print('\nTotal Time: {:.2f} seconds'.format((time.time() - start_time)))
        print('------------------------------------------\n')
        #if drop_single_points:
         #   shape_before_drop = df_.shape
         #   idx = df_[ df_[label_segment] == -1 ].index
          #  if idx.shape[0] > 0:
           #     print('...Drop Trajectory with a unique GPS point\n')
            #    ids_before_drop = df_[label_id].unique().shape[0]
             #   df_.drop(index=idx, inplace=True)
              #  print('...Object - before drop: {} - after drop: {}'.format(ids_before_drop, df_[label_id].unique().shape[0]))
               # print('...Shape - before drop: {} - after drop: {}'.format(shape_before_drop, df_.shape))
            #else:
             #   print('...No trajs with only one point.', df_.shape)
    except Exception as e:
        print('label_id:{}\nidx:{}\n'.format(label_id, idx))
        raise e

def segment_traj_by_max_dist(df_, label_id=dic_labels['id'],  max_dist_between_adj_points=3000, label_segment='tid_dist'):
    """ Index_name is the current id.
    label_new_id is the new splitted id.
    Speed features must be updated after split.
    """     
    print('Split trajectories by max distance between adjacent points:', max_dist_between_adj_points) 
    try:
        if df_.index.name is None:
            print('...setting {} as index'.format(label_id))
            df_.set_index(label_id, inplace=True)

        curr_tid = 0
        if label_segment not in df_:
            df_[label_segment] = curr_tid

        ids = df_.index.unique()
        count = 0
        df_size = df_.shape[0]
        curr_perc_int = -1
        start_time = time.time()

        for idx in ids:            
            """ increment index to trajectory"""
            curr_tid += 1

            """ filter dist max"""
            dist = (df_.at[idx, dic_features_label['dist_to_prev']] > max_dist_between_adj_points)                      
            """ check if object have more than one point to split"""
            if dist.shape == ():   
                print('id: {} has not point to split'.format(idx))
                df_.at[idx, label_segment] = curr_tid
                count+=1
            else: 
                tids = np.empty(dist.shape[0], dtype=np.int64)
                tids.fill(curr_tid)
                for i, has_problem in enumerate(dist):
                    if has_problem:
                        curr_tid += 1
                        tids[i:] = curr_tid
                count += tids.shape[0]
                df_.at[idx, label_segment] = tids

            curr_perc_int, est_time_str = ut.progress_update(count, df_size, start_time, curr_perc_int, step_perc=20)

        if label_id == label_segment:
            df_.reset_index(drop=True, inplace=True)
            print('... label_id = label_new_id, then reseting and drop index')
        else:
            df_.reset_index(inplace=True)
            print('... Reseting index')
        print('\nTotal Time: {:.2f} seconds'.format((time.time() - start_time)))
        print('------------------------------------------\n') 
    except Exception as e:
        print('label_id:{}\nidx:{}\n'.format(label_id, idx))
        raise e

def segment_traj_by_max_time(df_, label_id=dic_labels['id'], max_time_between_adj_points=900.0, label_segment='tid_time'):
    """
    index_name is the current id.
    label_new_id is the new splitted id.
    Speed features must be updated after split.
    """     
    print('Split trajectories by max_time_between_adj_points:', max_time_between_adj_points) 
    try:
        if df_.index.name is None:
            print('...setting {} as index'.format(label_id))
            df_.set_index(label_id, inplace=True)

        curr_tid = 0
        if label_segment not in df_:
            df_[label_segment] = curr_tid

        ids = df_.index.unique()
        count = 0
        df_size = df_.shape[0]
        curr_perc_int = -1
        start_time = time.time()

        for idx in ids:            
            """ increment index to trajectory"""
            curr_tid += 1

            """ filter time max"""
            times = (df_.at[idx, dic_features_label['time_to_prev']] > max_time_between_adj_points)        
                     
            """ check if object have only one point to be removed """
            if times.shape == ():
                print('id: {} has not point to split'.format(id))
                df_.at[idx, label_segment] = curr_tid
                count+=1
            else: 
                tids = np.empty(times.shape[0], dtype=np.int64)
                tids.fill(curr_tid)
                for i, has_problem in enumerate(times):
                    if has_problem:
                        curr_tid += 1
                        tids[i:] = curr_tid
                count += tids.shape[0]
                df_.at[idx, label_segment] = tids

            curr_perc_int, est_time_str = ut.progress_update(count, df_size, start_time, curr_perc_int, step_perc=20)

        if label_id == label_segment:
            df_.reset_index(drop=True, inplace=True)
            print('... label_id = label_new_id, then reseting and drop index')
        else:
            df_.reset_index(inplace=True)
            print('... Reseting index')
        print('\nTotal Time: {:.2f} seconds'.format((time.time() - start_time)))
        print('------------------------------------------\n')      
        #if drop_single_points:
         #   shape_before_drop = df_.shape
          #  idx = df_[ df_[label_segment] == -1 ].index
           # if idx.shape[0] > 0:
            #    print('...Drop Trajectory with a unique GPS point\n')
             #   ids_before_drop = df_[label_id].unique().shape[0]
              #  df_.drop(index=idx, inplace=True)
               # print('...Object - before drop: {} - after drop: {}'.format(ids_before_drop, df_[label_id].unique().shape[0]))
               # print('...Shape - before drop: {} - after drop: {}'.format(shape_before_drop, df_.shape))
            #else:
             #   print('...No trajs with only one point.', df_.shape)

    except Exception as e:
        print('label_id:{}\nidx:{}\n'.format(label_id, idx))
        raise e

def segment_traj_by_max_speed(df_, label_id=dic_labels['id'], max_speed_between_adj_points=50.0, label_segment='tid_speed'):
    """ Index_name is the current id.
    label_new_id is the new splitted id.
    Speed features must be updated after split.
    """     
    print('Split trajectories by max_speed_between_adj_points:', max_speed_between_adj_points) 
    try:
        if df_.index.name is None:
            print('...setting {} as index'.format(label_id))
            df_.set_index(label_id, inplace=True)

        curr_tid = 0
        if label_segment not in df_:
            df_[label_segment] = curr_tid

        ids = df_.index.unique()
        count = 0
        df_size = df_.shape[0]
        curr_perc_int = -1
        start_time = time.time()

        for idx in ids:            
            """ increment index to trajectory"""
            curr_tid += 1

            """ filter speed max"""
            speed = (df_.at[idx, dic_features_label['speed_to_prev']] > max_speed_between_adj_points)        
            """ check if object have only one point to be removed """
            if speed.shape == ():
                print('id: {} has not point to split'.format(id))
                df_.at[idx, label_segment] = curr_tid
                count+=1
            else: 
                tids = np.empty(speed.shape[0], dtype=np.int64)
                tids.fill(curr_tid)
                for i, has_problem in enumerate(speed):
                    if has_problem:
                        curr_tid += 1
                        tids[i:] = curr_tid
                count += tids.shape[0]
                df_.at[idx, label_segment] = tids

            curr_perc_int, est_time_str = ut.progress_update(count, df_size, start_time, curr_perc_int, step_perc=20)

        if label_id == label_segment:
            df_.reset_index(drop=True, inplace=True)
            print('... label_id = label_new_id, then reseting and drop index')
        else:
            df_.reset_index(inplace=True)
            print('... Reseting index')
        print('\nTotal Time: {:.2f} seconds'.format((time.time() - start_time)))
        print('------------------------------------------\n')
       
        #if drop_single_points:
         #   shape_before_drop = df_.shape
          #  idx = df_[df_[label_segment] == -1].index
           # if idx.shape[0] > 0:
            #    print('...Drop Trajectory with a unique GPS point\n')
             #   ids_before_drop = df_[label_id].unique().shape[0]
              #  df_.drop(index=idx, inplace=True)
               # print('...Object - before drop: {} - after drop: {}'.format(ids_before_drop, df_[label_id].unique().shape[0]))
               # print('...Shape - before drop: {} - after drop: {}'.format(shape_before_drop, df_.shape))
                #create_update_dist_time_speed_features(df_, label_segment, dic_labels)
            #else:
                #print('...No trajs with only one point.', df_.shape)

    except Exception as e:
        print('label_id:{}\nidx:{}\n'.format(label_id, idx))
        raise e

def transform_speed_from_ms_to_kmh(df_, label_speed=dic_features_label['speed_to_prev'], new_label = None):
    """ transform speed """
    try:
        df_[label_speed] = df_[label_speed].transform(lambda row: row*3.6)
        if new_label is not None:
            df_.rename(columns = {label_speed: new_label}, inplace=True) 
    except Exception as e: 
        raise e
   
def transform_speed_from_kmh_to_ms(df_, label_speed=dic_features_label['speed_to_prev'], new_label = None):
    try:
        df_[label_speed] = df_[label_speed].transform(lambda row: row/3.6)
        if new_label is not None:
            df_.rename(columns = {label_speed: new_label}, inplace=True) 
    except Exception as e: 
        raise e

def transform_dist_from_meters_to_kilometers(df_, label_distance=dic_features_label['dist_to_prev'], new_label=None):
    """ transform distances """
    try:
        df_[label_distance] = df_[label_distance].transform(lambda row: row/1000)
        if new_label is not None:
            df_.rename(columns = {label_distance: new_label}, inplace=True) 
    except Exception as e: 
        raise e

def transform_dist_from_to_kilometers_to_meters(df_, label_distance=dic_features_label['dist_to_prev'], new_label=None):
    try:
        df_[label_distance] = df_[label_distance].transform(lambda row: row*1000)
        if new_label is not None:
            df_.rename(columns = {label_distance: new_label}, inplace=True) 
    except Exception as e: 
        raise e

def transform_time_from_seconds_to_minutes(df_, label_time=dic_features_label['time_to_prev'], new_label=None):
    """ transform time """
    try:
        df_[label_time] = df_[label_time].transform(lambda row: row/60.0)
        if new_label is not None:
            df_.rename(columns = {label_time: new_label}, inplace=True) 
    except Exception as e: 
        raise e 

def transform_time_from_minute_to_seconds(df_, label_time=dic_features_label['time_to_prev'], new_label=None):
    try:
        df_[label_time] = df_[label_time].apply(lambda row: row*60.0)
        if new_label is not None:
            df_.rename(columns = {label_time: new_label}, inplace=True) 
    except Exception as e: 
        raise e 

def transform_time_from_minute_to_hours(df_, label_time=dic_features_label['time_to_prev'], new_label=None):
    try:
        df_[label_time] = df_[label_time].apply(lambda row: row/60.0)
        if new_label is not None:
            df_.rename(columns = {label_time: new_label}, inplace=True) 
    except Exception as e: 
        raise e  

def transform_time_from_hours_to_minute(df_, label_time=dic_features_label['time_to_prev'], new_label=None):
    try:
        df_[label_time] = df_[label_time].apply(lambda row: row*60.0)
        if new_label is not None:
            df_.rename(columns = {label_time: new_label}, inplace=True) 
    except Exception as e:
        raise e

def transform_time_from_seconds_to_hours(df_, label_time=dic_features_label['time_to_prev'], new_label=None):
    try:
        df_[label_time] = df_[label_time].apply(lambda row: row/3600.0)
        if new_label is not None:
            df_.rename(columns = {label_time: new_label}, inplace=True) 
    except Exception as e:
        raise e

def transform_time_from_hours_to_seconds(df_, label_time=dic_features_label['time_to_prev'], new_label=None):
    try:
        df_[label_time] = df_[label_time].apply(lambda row: row*3600.0)
        if new_label is not None:
            df_.rename(columns = {label_time: new_label}, inplace=True) 
    except Exception as e:
        raise e

def check_time_dist(df, index_name='tid', tids=None, max_dist_between_adj_points=5000, max_time_between_adj_points=900, max_speed=30):
    """ Fuction to solve problems after Map-matching"""
    try:
        if df.index.name is not None:
            print('reseting index...')
            df.reset_index(inplace=True)
        
        if tids is None:
            tids = df[index_name].unique()
        
        size = df.shape[0]
        if df.index.name is None:
            print('creating index...')
            df.set_index(index_name, inplace=True)        
        
        count = 0
        curr_perc_int = -1
        start_time = time.time()
        size_id = 0
        print('checking ascending distance and time...')
        for tid in tids:
            filter_ = (df.at[tid,'isNode'] != 1)

            # be sure that distances are in ascending order
            dists = df.at[tid, 'distFromTrajStartToCurrPoint'][filter_]
            assert np.all(dists[:-1] < dists[1:]), 'distance feature is not in ascending order'
            
            # be sure that times are in ascending order
            times = df.at[tid, 'time'][filter_].astype(np.float64)
            assert np.all(times[:-1] < times[1:]), 'time feature is not in ascending order'
            
            size_id = 1 if filter_.shape == () else filter_.shape[0]
            count += size_id
            curr_perc_int, est_time_str = ut.progress_update(count, size, start_time, curr_perc_int, step_perc=20)
            

        count = 0
        curr_perc_int = -1
        start_time = time.time()
        size_id = 0
        print('checking delta_times, delta_dists and speeds...')
        for tid in tids:
            filter_ = (df.at[tid,'isNode'] != 1)

            dists = df.at[tid, 'distFromTrajStartToCurrPoint'][filter_]
            delta_dists = (ut.shift(dists, -1) - dists)[:-1]   # do not use last element (np.nan)
                          
            assert np.all(delta_dists <= max_dist_between_adj_points), \
                          'delta_dists must be <= {}'.format(max_dist_between_adj_points)
            
            times = df.at[tid, 'time'][filter_].astype(np.float64)
            delta_times = ((ut.shift(times, -1) - times) / 1000.0)[:-1] # do not use last element (np.nan)
                          
            assert np.all(delta_times <= max_time_between_adj_points), \
                          'delta_times must be <= {}'.format(max_time_between_adj_points)
            
            assert np.all(delta_times > 0), 'delta_times must be > 0'

            assert np.all(delta_dists > 0), 'delta_dists must be > 0'
            
            speeds = delta_dists / delta_times
            assert np.all(speeds <= max_speed), 'speeds > {}'.format(max_speed)
            
            size_id = 1 if filter_.shape == () else filter_.shape[0]
            count += size_id
            curr_perc_int, est_time_str = ut.progress_update(count, size, start_time, curr_perc_int, step_perc=20)
            

        df.reset_index(inplace=True)
    
    except Exception as e:
        print('{}: {} - size: {}'.format(index_name, tid, size_id))
        raise e
        
def fix_time_not_in_ascending_order_id(df, tid, index_name='tid'):
    if 'deleted' not in df:
        df['deleted'] = False
        
    if df.index.name is None:
        print('creating index...')
        df.set_index(index_name, inplace=True)
    
    filter_ = (df.at[tid,'isNode'] != 1) & (~df.at[tid,'deleted'])
    
    # be sure that distances are in ascending order
    dists = df.at[tid, 'distFromTrajStartToCurrPoint'][filter_]
    assert np.all(dists[:-1] <= dists[1:]), 'distance feature is not in ascending order'
    
    if filter_.shape == ():     # do not use trajectories with only 1 point.
        size_id = 1
        df.at[tid, 'deleted'] = True
    else:
        size_id = filter_.shape[0]
        times = df.at[tid, 'time'][filter_]
        idx_not_in_ascending_order = np.where(times[:-1] >= times[1:])[0] + 1

        if idx_not_in_ascending_order.shape[0] > 0:
            #print(tid, 'idx_not_in_ascending_order:', idx_not_in_ascending_order, 'times.shape', times.shape)

            ut.change_df_feature_values_using_filter_and_indexes(df, tid, 'deleted', filter_, idx_not_in_ascending_order, True)
            # equivalent of: df.at[tid, 'deleted'][filter_][idx_not_in_ascending_order] = True

            fix_time_not_in_ascending_order_id(df, tid, index_name=index_name)
    
    return size_id        
        
def fix_time_not_in_ascending_order_all(df, index_name='tid', drop_marked_to_delete=False):
    try:
        if df.index.name is not None:
            print('reseting index...')
            df.reset_index(inplace=True)
        
        print('dropping duplicate distances... shape before:', df.shape)
        df.drop_duplicates(subset=[index_name, 'isNode', 'distFromTrajStartToCurrPoint'], keep='first', inplace=True)
        print('shape after:', df.shape)
        
        print('sorting by id and distance...')
        df.sort_values(by=[index_name, 'distFromTrajStartToCurrPoint'], inplace=True)
        print('sorting done')
        
        tids = df[index_name].unique()
        df['deleted'] = False

        print('starting fix...')
        size = df.shape[0]
        count = 0
        curr_perc_int = -1
        start_time = time.time()
        for tid in tids:
            size_id = fix_time_not_in_ascending_order_id(df, tid, index_name)

            count += size_id
            curr_perc_int, est_time_str = ut.progress_update(count, size, start_time, curr_perc_int, step_perc=20)

        df.reset_index(inplace=True)
        idxs = df[ df['deleted'] ].index
        print('{} rows marked for deletion.'.format(idxs.shape[0]))

        if idxs.shape[0] > 0 and drop_marked_to_delete:
            print('shape before dropping: {}'.format(df.shape))
            df.drop(index=idxs, inplace=True )
            df.drop(labels='deleted', axis=1, inplace=True)
            print('shape after dropping: {}'.format(df.shape))
    
    except Exception as e:
        print('{}: {} - size: {}'.format(index_name, tid, size_id))
        raise e
       
def interpolate_add_deltatime_speed_features(df, label_id='tid', max_time_between_adj_points=900, 
                                             max_dist_between_adj_points=5000, max_speed=30):
    """
    interpolate distances (x) to find times (y).
    max_time_between_adj_points, max_dist_between_adj_points and max_speed are used only for verification.
    """
    if df.index.name is not None:
        print('reseting index...')
        df.reset_index(inplace=True)

    tids = df[label_id].unique()
    #tids = [2]

    if df.index.name is None:
        print('creating index...')
        df.set_index(label_id, inplace=True)

    drop_trajectories = []    
    size = df.shape[0]
    count = 0
    curr_perc_int = -1
    start_time = time.time()

    df['delta_time'] = np.nan
    df['speed'] = np.nan

    try:
        for tid in tids:
            filter_nodes = (df.at[tid,'isNode'] == 1)
            times = df.at[tid, 'time'][filter_nodes]
            size_id = 1 if filter_nodes.shape == () else filter_nodes.shape[0]
            count += size_id

            # y - time of snapped points
            y_ = df.at[tid,'time'][~filter_nodes]
            if y_.shape[0] < 2:
                #print('traj: {} - insuficient points ({}) for interpolation. adding to drop list...'.format(tid,  y_.shape[0]))
                drop_trajectories.append(tid)
                curr_perc_int, est_time_str = ut.progress_update(count, size, start_time, curr_perc_int, step_perc=20)
                continue

            assert np.all(y_[1:] >= y_[:-1]), 'time feature is not in ascending order'

            # x - distance from traj start to snapped points
            x_ = df.at[tid, 'distFromTrajStartToCurrPoint'][~filter_nodes]

            assert np.all(x_[1:] >= x_[:-1]), 'distance feature is not in ascending order'

            # remove duplicates in distances to avoid np.inf in future interpolation results
            idx_duplicates = np.where(x_[1:] == x_[:-1])[0]
            if idx_duplicates.shape[0] > 0:
                x_ = np.delete(x_, idx_duplicates)
                y_ = np.delete(y_, idx_duplicates)

            if y_.shape[0] < 2:
                #print('traj: {} - insuficient points ({}) for interpolation. adding to drop list...'.format(tid,  y_.shape[0]))
                drop_trajectories.append(tid)
                curr_perc_int, est_time_str = ut.progress_update(count, size, start_time, curr_perc_int, step_perc=20)
                continue

            # compute delta_time and distance between points
            #values = (ut.shift(df.at[tid, 'time'][filter_nodes].astype(np.float64), -1) - df.at[tid, 'time'][filter_nodes]) / 1000
            #ut.change_df_feature_values_using_filter(df, tid, 'delta_time', filter_nodes, values)
            delta_time = ( (ut.shift(y_.astype(np.float64), -1) - y_) / 1000.0 )[:-1]
            dist_curr_to_next = (ut.shift(x_, -1) - x_)[:-1]
            speed = (dist_curr_to_next / delta_time)[:-1]

            assert np.all(delta_time <= max_time_between_adj_points), 'delta_time between points cannot be more than {}'.format(max_time_between_adj_points)
            assert np.all(dist_curr_to_next <= max_dist_between_adj_points), 'distance between points cannot be more than {}'.format(max_dist_between_adj_points)
            assert np.all(speed <= max_speed), 'speed between points cannot be more than {}'.format(max_speed)   

            assert np.all(x_[1:] >= x_[:-1]), 'distance feature is not in ascending order'

            f_intp = interp1d(x_, y_, fill_value='extrapolate')

            x2_ = df.at[tid, 'distFromTrajStartToCurrPoint'][filter_nodes]
            assert np.all(x2_[1:] >= x2_[:-1]), 'distances in nodes are not in ascending order'

            intp_result = f_intp(x2_) #.astype(np.int64)
            assert np.all(intp_result[1:] >= intp_result[:-1]), 'resulting times are not in ascending order'

            assert ~np.isin(np.inf, intp_result), 'interpolation results with np.inf value(s)'

            # update time features for nodes. initially they are empty.
            values = intp_result.astype(np.int64)
            ut.change_df_feature_values_using_filter(df, tid, 'time', filter_nodes, values)

            # create delta_time feature
            values = (ut.shift(df.at[tid, 'time'][filter_nodes].astype(np.float64), -1) - df.at[tid, 'time'][filter_nodes]) / 1000
            ut.change_df_feature_values_using_filter(df, tid, 'delta_time', filter_nodes, values)

            # create speed feature
            values = df.at[tid, 'edgeDistance'][filter_nodes] / df.at[tid, 'delta_time'][filter_nodes]
            ut.change_df_feature_values_using_filter(df, tid, 'speed', filter_nodes, values)

            curr_perc_int, est_time_str = ut.progress_update(count, size, start_time, curr_perc_int, step_perc=20)
            
    except Exception as e:
        print('{}: {} - size: {} - count: {}'.format(label_id, tid, size_id, count))
        raise e
        
    print(count, size)
    print('we still need to drop {} trajectories with only 1 gps point'.format(len(drop_trajectories)))
    df.reset_index(inplace=True)
    idxs_drop = df[ df[label_id].isin(drop_trajectories) ].index.values
    print('dropping {} rows in {} trajectories with only 1 gps point'.format(idxs_drop.shape[0], 
            len(drop_trajectories)))
    if idxs_drop.shape[0] > 0:
        print('shape before dropping: {}'.format(df.shape))
        df.drop(index=idxs_drop, inplace=True )
        print('shape after dropping: {}'.format(df.shape))
