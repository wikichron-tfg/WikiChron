#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
   stats.py

   Descp:

   Created on: 14-nov-2017

   Copyright 2017-2018 Abel 'Akronix' Serrano Juste <akronix5@gmail.com>
"""

import pandas as pd
import numpy as np
import math
import datetime as d
from dateutil.relativedelta import relativedelta
import time

def calculate_index_all_months(data):
    monthly_data = data.groupby(pd.Grouper(key='timestamp', freq='MS'))
    index = monthly_data.size().index
    return index



# Users


###### General helper functions ######

def set_category_name(list_of_series, list_of_names):
    '''
    Set the name to be given to each pd series.
    '''
    for i in range(len(list_of_series)):
        list_of_series[i].name = list_of_names[i]

def get_accum_number_of_edits_until_each_month(data, index):
    '''
    Returns a pd DataFrame with the suitable shape for calculating the metrics:
    one row contains the contributor_id, timestamp and nEdits -- cumulative number of edits done until the given timestamp
    '''
    df = data.groupby(['contributor_id']).apply(lambda x: x.groupby(pd.Grouper(key='timestamp', freq='MS')).size().to_frame('nEdits').reindex(index, fill_value=0).cumsum()).reset_index()
    return df

def get_monthly_number_of_edits(data, index):
    '''
    Adds a new column to the pd DataFrame given in data:
    one row contains the contributor_id, timestamp and monthly_nEdits -- monthly number of edits by the user
    '''
    cond = (data['contributor_id'] == data['contributor_id'].shift())
    data['monthly_nEdits'] = np.where(cond, data['nEdits'] - data['nEdits'].shift(), data['nEdits'])

def filter_df(data, condition, index):
    '''
    Filter the df in data, according to the given condition.
    Return a pd Series, with index = time index of the wiki, and data = number of users that fullfill the condition.
    '''
    users = data[condition]
    series = pd.Series(users.groupby(['timestamp']).size(), index).fillna(0)

    if index is not None:
        series = series.reindex(index, fill_value=0)
    return series

def filter_anonymous(data):
    '''
    Erase anonymous users from the DataFrame in data
    '''
    data = data[data['contributor_name'] != 'Anonymous']
    return data

def calcultate_relative_proportion(list_of_category_series, list_of_column_names):
    '''
    Calculate the relative number of the data in each pd Series given in the list_of_category_series parameter.
    Return a pd DataFrame in which:
    -index = time index of the wiki.
    -A column per category with its relative proportion regarding the total in the month is computed.
    '''
    df = pd.concat(list_of_category_series, axis = 1)
    df['total'] = df[list_of_column_names].sum(axis=1)
    
    for i in range(len(list_of_column_names)):
        df[str(list_of_column_names[i])] = (df[str(list_of_column_names[i])]/df['total'])*100
    
    return df

def generate_list_of_dataframes(list_of_series, list_of_names):
    '''
    Return a list of pd DataFrames from the given list_of_series, using as column names the given list_of_names.
    '''
    list_of_dfs = []
    
    for i in range(len(list_of_names)):
        list_of_dfs.append(list_of_series[i].to_frame(str(list_of_names[i])))
    
    return list_of_dfs

#### Helper Factoid metrics ####

def merge_dataframes(data, df1):
    '''
    Filter data so that it only contains rows for the edits done by the editors in the timestamps specified in df1.
    '''
    return (df1.reset_index()[["contributor_id", "timestamp"]].merge(data.reset_index(), on=["contributor_id", "timestamp"], how="inner"))

def calculate_added_factoids_by_editor_category(frame):
    '''
    Calculate the monthly number of added factoids by an editor category.
    Parameter:
    -frame: filtered wiki csv that only contains rows for the edits done by a particular editor category.
    '''
    frame['factoids'] = frame['factoids'].apply(str).apply(lambda x: x.split(',')).apply(set)
    frame['added_factoids'] = frame.groupby('page_id').factoids.diff().fillna(frame.factoids)
    frame['number_added_factoids'] = frame['added_factoids'].apply(len)
    frame = frame.groupby(pd.Grouper(key='timestamp', freq='MS'))['number_added_factoids'].sum()

    return frame

def calculate_deleted_factoids_by_editor_category(frame):
    '''
    Calculate the monthly number of deleted factoids by an editor category.
    Parameter:
    -frame: filtered wiki csv that only contains rows for the edits done by a particular editor category.
    '''
    frame['factoids'] = frame['factoids'].apply(str).apply(lambda x: x.split(',')).apply(set)
    frame['factoids_history'] = pd.concat([pd.Series([set()]), frame['factoids'][:-1]]).reset_index(drop=True)
    frame['deleted_factoids'] = frame['factoids_history'] - frame['factoids']
    idx = frame.groupby('contributor_id').head(1).index
    frame.loc[idx, 'deleted_factoids'] = frame.loc[idx, 'deleted_factoids'].apply(lambda x: set())
    frame.drop('factoids_history', axis=1, inplace=True)
    frame['number_deleted_factoids'] = frame['deleted_factoids'].apply(len)

    frame = frame.groupby(pd.Grouper(key='timestamp', freq='MS'))['number_deleted_factoids'].sum()

    return frame

#### Helper users active ####

def users_active_more_than_x_editions(data, index, x):
    monthly_edits = data.groupby([pd.Grouper(key='timestamp', freq='MS'), 'contributor_name']).size()
    monthly_edits_filtered = monthly_edits[monthly_edits > x].to_frame(name='pages_edited').reset_index()
    series = monthly_edits_filtered.groupby(pd.Grouper(key='timestamp', freq='MS')).size()
    if index is not None:
        series = series.reindex(index, fill_value=0)
    return series

#### Helper metric 2 ####

def add_x_months(data, months):
    return data['timestamp'].apply(lambda x: x + relativedelta(months = +months))

'''def displace_x_months_per_user(data, months):
    return data.shift(months)'''

def current_streak_x_or_y_months_in_a_row(mothly, index, z, y, type):
    mothly['add_months'] = add_x_months(mothly, z)
    lista = ['contributor_id']
    lista.append('add_months')
    if y > 0:
      mothly['add_y_months'] = add_x_months(mothly, y)
      lista.append('add_y_months')
    group_users = mothly[lista].groupby(['contributor_id'])
    displace_z_month = group_users['add_months'].shift(z)
    mothly['displace'] = displace_z_month
    if y > 0:
      displace_y_month = group_users['add_y_months'].shift(y)
      mothly['displace_y_month']= displace_y_month
      current_streak = mothly[(mothly['displace'] == mothly['timestamp']) & (mothly['displace_y_month'] != mothly['timestamp'])]
    elif z == 1:
      current_streak = mothly[mothly['displace'] != mothly['timestamp']]
    elif z == 6:
      current_streak = mothly[mothly['displace'] == mothly['timestamp']]
	 
    if type == 'users':
      series = current_streak.groupby(pd.Grouper(key = 'timestamp', freq = 'MS')).size()
    elif type == 'edits':
      series = current_streak.groupby(pd.Grouper(key = 'timestamp', freq = 'MS'))['size'].sum()
    elif type == 'factoids':
      series = current_streak.groupby(['timestamp'])['number_of_factoids'].sum()

    if index is not None:
        series = series.reindex(index, fill_value=0)
    return series

def edition_concrete(data, index, pagType):
    filterData = data[data['page_ns'] == pagType]
    series = filterData.groupby([pd.Grouper(key ='timestamp', freq='MS')]).size()
    if index is not None:
        series = series.reindex(index, fill_value=0)
    return series
def rest_edition(data, index, listP):
    filterData = data
    for i in listP:
        filterData= filterData[filterData['page_ns'] != i]
    series = filterData.groupby([pd.Grouper(key ='timestamp', freq='MS')]).size()
    if index is not None:
        series = series.reindex(index, fill_value=0)
    return series

#### Helpers Users by Tenure ####

def add_position_column_users_first_edit(data):
    '''
    Add a new column to data:
    position: indicates the number of months since the the user's first contribution in the wiki
    '''
    cond = data['nEdits'] == 0
    data['position'] = np.where(cond, 0, data.groupby([cond, 'contributor_id']).cumcount() + 1)

def generate_condition_users_first_edit(data, x, y):
    '''
    Create a condition that the users must fulfill in order to be included in one of the categories of the users by tenure metric.
    '''
    if y > 0:
        condition = ((data['position'] >= x) & (data['position'] <= y)) & (data['nEdits'] != data['nEdits'].shift())
    else:
        condition = (data['position'] > x) & (data['nEdits'] != data['nEdits'].shift())
    
    return condition

#### Helpers Users by the date of the last edit ####

def add_position_column_users_last_edit(data):
    '''
    Add a new column to data:
    position: indicates the number of months since the user's last contribution in the wikis
    '''
    cond = data['nEdits'] == 0
    data['position'] = np.where(cond, 0, data.groupby([cond, 'contributor_id', 'nEdits']).cumcount() + 1)
    
def generate_condition_users_last_edit(data, x):
    '''
    Create a condition that the users must fulfill in order to be included in one of the categories of the users by date of the last edit metric.
    '''
    if x != 6:
        condition = ((data['position'] == 1) & (data['position'].shift() == x)) & (data['contributor_id'] == data['contributor_id'].shift())
    
    else:
        condition = ((data['position'] == 1) & (data['position'].shift() > x)) & (data['contributor_id'] == data['contributor_id'].shift())

    return condition

#### Helper Active editors by Experience ####

def generate_condition_users_by_number_of_edits(data, x, y):
    '''
    Determine the group of users to be included in one of the categories of the Active editors by experience metric.
    '''
    if (y != 0) and (x > 0):
        condition = (data['medits'] > 0) & ((data['nEdits_until_previous_month'] >= x) & (data['nEdits_until_previous_month'] <= y))
    elif (y == 0) and (x == 0):
        condition = (data['nEdits_until_previous_month'] == -1)
    elif (y == 0) and (x > 0):
        condition = (data['medits'] > 0) & (data['nEdits_until_previous_month'] >= x)

    return condition

#### Helper metrics 9 and 10 ####

# this helper function gets the number of users that have edited a particular kind of page, specified by the parameter page_ns
def filter_users_pageNS(data, index, page_ns):
    data = filter_anonymous(data)
    edits_page = data[data['page_ns'] == page_ns]
    series = edits_page.groupby(pd.Grouper(key = 'timestamp', freq = 'MS'))['contributor_id'].nunique()
    if index is not None:
        series = series.reindex(index, fill_value=0)
    return series


#### Helper metrics Edits by editor experience ####

def sum_monthly_edits_by_users(data, index):
    '''
    Return a pd Series with the sum of the monthly number of edits, stored in the monthly_nEdits column in the pd DataFrame given in data
    '''
    data = data.groupby(pd.Grouper(key='timestamp', freq='MS'))['monthly_nEdits'].sum()

    if index is not None:
        series = series.reindex(index, fill_value=0)
    return series

###### Callable Functions ######

############################ New and Reincident users ###############################################################

def users_new(data, index):
    users = data.drop_duplicates('contributor_id')
    series = users.groupby(pd.Grouper(key='timestamp', freq='MS')).size()
    if index is not None:
        series = series.reindex(index, fill_value=0)
    return series

#users who make their second edition in the wiki (we want the count for this kind of users per month)
def users_reincident(data, index):
    data['test_duplicated'] = data['contributor_id'].duplicated()
    data = data[data['contributor_name'] != 'Anonymous']
    users_reincident = data[data['test_duplicated'] == True]
#determine in which month each user performed their second edition-> can be the same month as the first one
#1) get number of editions per month for every user
    users_reincident = users_reincident.groupby(['contributor_id', pd.Grouper(key='timestamp', freq='MS')]).size().to_frame('edits_count').reset_index()
#2) get the accum. number of edits per user each month
    users_reincident['accum_edit_count'] = users_reincident.groupby('contributor_id')['edits_count'].transform(lambda x: x.cumsum())
#3) drop rows in which the accum_edit_count is less than 2
    users_reincident = users_reincident[users_reincident['accum_edit_count'] > 1]
#4) now, we just want the first month in which the user became reincident: (drop_duplicates drops all rows but first, so as it is sorted, for sure we will keep the first month)
    users_reincident = users_reincident.drop_duplicates('contributor_id')
#5) group by timestamp and get the count of reincident users per month
    series = users_reincident.groupby(pd.Grouper(key='timestamp', freq='MS')).size()
    if index is not None:
        series = series.reindex(index, fill_value=0)
    return series


############################ METRIC 2 #################################################################################################

def current_streak(data, index):
    data = filter_anonymous(data)

    mothly = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('size').reset_index()

    this_month = current_streak_x_or_y_months_in_a_row(mothly, index, 1, 0, 'users')
    two_three_months = current_streak_x_or_y_months_in_a_row(mothly, index, 1, 3, 'users')
    four_six_months = current_streak_x_or_y_months_in_a_row(mothly, index, 3, 6, 'users')
    more_six = current_streak_x_or_y_months_in_a_row(mothly, index, 6, 0, 'users')
	
    set_category_name([this_month, two_three_months, four_six_months, more_six], ['1 month editing', 'Btw. 2 and 3 consecutive months', 'Btw. 4 and 6 consecutive months', 'More than 6 consecutive months'])
    
    return [this_month, two_three_months, four_six_months, more_six, 1]

def current_streak_only_mains(data, index):
    data = data[data['page_ns']==0]
    return current_streak(data, index)

def edits_by_current_streak(data, index):
    data = filter_anonymous(data)

    mothly = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('size').reset_index()
	
    this_month = current_streak_x_or_y_months_in_a_row(mothly, index, 1, 0, 'edits')
    two_three_months = current_streak_x_or_y_months_in_a_row(mothly, index, 1, 3, 'edits')
    four_six_months = current_streak_x_or_y_months_in_a_row(mothly, index, 3, 6, 'edits')
    more_six = current_streak_x_or_y_months_in_a_row(mothly, index, 6, 0, 'edits')
	
    set_category_name([this_month, two_three_months, four_six_months, more_six], ['1 month editing', 'Btw. 2 and 3 consecutive months', 'Btw. 4 and 6 consecutive months', 'More than 6 consecutive months'])
    
    return [this_month, two_three_months, four_six_months, more_six, 1]

def edits_by_current_streak_only_mains(data, index):
    data = data[data['page_ns']==0]
    return edits_by_current_streak(data, index)

def edition_on_type_pages(data, index):
    data=filter_anonymous(data)
    articles=edition_concrete(data, index, 0)
    talkPA=edition_concrete(data, index, 1)
    userP=edition_concrete(data, index, 2)
    talkPU=edition_concrete(data, index, 3)
    rest=rest_edition(data, index, [0,1,2,3])
    articles.name= 'Article pages'
    talkPA.name='Article talk pages'
    userP.name='User pages'
    talkPU.name='User talk pages'
    rest.name='Other pages'
    return [articles, talkPA, talkPU, userP, rest, 0]

def edition_on_type_pages_extends_rest(data, index):
    data=filter_anonymous(data)
    #filt=rest_edition(data,index,[0,1,2,3])
    file=edition_concrete(data,index,6)
    mediaWiki=edition_concrete(data,index,8)
    template=edition_concrete(data,index,10)
    category=edition_concrete(data,index,14)
    rest=rest_edition(data,index,[0,1,2,3,6,8,10,14])
    file.name= 'File pages'
    mediaWiki.name='Media wiki pages'
    template.name='Template pages'
    category.name='Category pages'
    rest.name='Other pages'
    return [file,mediaWiki,template,category,rest, 0]

############################ Users by tenure #################################################################################

def users_first_edit(data, index):
    '''Calculate the monthly number of users whose first edit was between 1 and 3, 4 and 6, 6 and 12, and more than 12 months ago
    '''
    data = filter_anonymous(data)
    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    
    mins = format_data.groupby('contributor_id')['timestamp'].transform('min')
    format_data['months'] = format_data['timestamp'].sub(mins).div(pd.Timedelta(1, 'M')).round().astype(int)
    
    this_month = users_new(data, index)
    one_three = pd.Series(format_data[(format_data['months'] >= 1) & (format_data['months'] <= 3)].groupby(['timestamp']).size(), index).fillna(0)
    four_six = pd.Series(format_data[(format_data['months'] >= 4) & (format_data['months'] <= 6)].groupby(['timestamp']).size(), index).fillna(0)
    six_twelve = pd.Series(format_data[(format_data['months'] >= 7) & (format_data['months'] <= 12)].groupby(['timestamp']).size(), index).fillna(0)
    more_twelve = pd.Series(format_data[format_data['months'] >= 13].groupby(['timestamp']).size(), index).fillna(0)

    this_month.name = 'New users'
    one_three.name = 'Btw. 1 and 3 months ago'
    four_six.name = 'Btw. 4 and 6 months ago'
    six_twelve.name = 'Btw. 6 and 12 months ago'
    more_twelve.name = 'More than 12 months ago'
    
    return [this_month, one_three, four_six, six_twelve, more_twelve, 1]

def users_first_edit_abs(data, index):
    '''Calculate the monthly percentage of users whose first edit was between 1 and 3, 4 and 6, 6 and 12, and more than 12 months ago
    '''
    data = filter_anonymous(data)
    monthly_total_users = data.groupby([pd.Grouper(key='timestamp', freq='MS'), 'contributor_id']).size().reset_index()
    monthly_total_users = monthly_total_users.groupby(pd.Grouper(key='timestamp', freq='MS')).size()
    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    
    mins = format_data.groupby('contributor_id')['timestamp'].transform('min')
    format_data['months'] = format_data['timestamp'].sub(mins).div(pd.Timedelta(1, 'M')).round().astype(int)
    
    this_month = (users_new(data, index) / monthly_total_users) * 100
    one_three = ((pd.Series(format_data[(format_data['months'] >= 1) & (format_data['months'] <= 3)].groupby(['timestamp']).size(), index).fillna(0)) / monthly_total_users) * 100
    four_six = ((pd.Series(format_data[(format_data['months'] >= 4) & (format_data['months'] <= 6)].groupby(['timestamp']).size(), index).fillna(0)) / monthly_total_users) * 100
    six_twelve = ((pd.Series(format_data[(format_data['months'] >= 7) & (format_data['months'] <= 12)].groupby(['timestamp']).size(), index).fillna(0)) / monthly_total_users) * 100
    more_twelve = ((pd.Series(format_data[format_data['months'] >= 13].groupby(['timestamp']).size(), index).fillna(0)) / monthly_total_users) * 100

    this_month.name = 'New users'
    one_three.name = 'Btw. 1 and 3 months ago'
    four_six.name = 'Btw. 4 and 6 months ago'
    six_twelve.name = 'Btw. 6 and 12 months ago'
    more_twelve.name = 'More than 12 months ago'
    
    return [this_month, one_three, four_six, six_twelve, more_twelve, 1]

############################ Users by the date of the last edit ###########################################################################

def users_last_edit(data, index):
    '''
    Get the monthly number of users whose last edit was less than 1, between 2 and 3, 4 and 6, and more than 6 months ago
    '''
    data = filter_anonymous(data)
    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    format_data['months'] = format_data.groupby('contributor_id')['timestamp'].diff().div(pd.Timedelta(days=30.44), fill_value=0).round().astype(int)

    new_users = users_new(data, index)
    one_month = pd.Series((format_data[format_data['months'] == 1]).groupby(['timestamp']).size(), index).fillna(0)
    two_three_months = pd.Series((format_data[(format_data['months'] == 2) | (format_data['months'] == 3)]).groupby(['timestamp']).size(), index).fillna(0)
    four_six_months = pd.Series((format_data[(format_data['months'] >= 4) & (format_data['months'] <= 6)]).groupby(['timestamp']).size(), index).fillna(0)
    more_six_months = pd.Series((format_data[format_data['months'] > 6]).groupby(['timestamp']).size(), index).fillna(0)

    new_users.name = 'New users'
    one_month.name = '1 month ago'
    two_three_months.name = 'Btw. 2 and 3 months ago'
    four_six_months.name = 'Btw. 4 and 6 months ago'
    more_six_months.name = 'More than six months ago'

    return [new_users, one_month, two_three_months, four_six_months, more_six_months, 1]

def users_last_edit_abs(data, index):
    '''
    Get the monthly percentage of users whose last edit was less than 1, between 2 and 3, 4 and 6, and more than 6 months ago
    '''
    data = filter_anonymous(data)
    monthly_total_users = data.groupby([pd.Grouper(key='timestamp', freq='MS'), 'contributor_id']).size().reset_index()
    monthly_total_users = monthly_total_users.groupby(pd.Grouper(key='timestamp', freq='MS')).size()
    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    format_data['months'] = format_data.groupby('contributor_id')['timestamp'].diff().div(pd.Timedelta(days=30.44), fill_value=0).round().astype(int)

    new_users = (users_new(data, index) / monthly_total_users) * 100
    one_month = ((pd.Series((format_data[format_data['months'] == 1]).groupby(['timestamp']).size(), index).fillna(0)) / monthly_total_users)*100
    two_three_months = ((pd.Series((format_data[(format_data['months'] == 2) | (format_data['months'] == 3)]).groupby(['timestamp']).size(), index).fillna(0)) / monthly_total_users)*100
    four_six_months = ((pd.Series((format_data[(format_data['months'] >= 4) & (format_data['months'] <= 6)]).groupby(['timestamp']).size(), index).fillna(0)) / monthly_total_users)*100
    more_six_months = ((pd.Series((format_data[format_data['months'] > 6]).groupby(['timestamp']).size(), index).fillna(0)) / monthly_total_users)*100

    new_users.name = 'New users'
    one_month.name = '1 month ago'
    two_three_months.name = 'Btw. 2 and 3 months ago'
    four_six_months.name = 'Btw. 4 and 6 months ago'
    more_six_months.name = 'More than six months ago'

    return [new_users, one_month, two_three_months, four_six_months, more_six_months, 1]

############################ Active editors by experience #####################################################################

def users_number_of_edits(data, index):
    '''
    Get the monthly number of users that belong to each category, in the Active editors by experience metric.
    '''
    data = filter_anonymous(data)
    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    format_data['nEdits'] = (format_data[['medits', 'contributor_id']].groupby(['contributor_id']))['medits'].cumsum()
    format_data['nEdits_until_previous_month'] = (format_data[['nEdits','contributor_id']].groupby(['contributor_id']))['nEdits'].shift().fillna(-1)

    new_users = users_new(data, index)
    one_four = pd.Series(format_data[generate_condition_users_by_number_of_edits(format_data, 1,4)].groupby(['timestamp']).size(), index).fillna(0)
    between_5_24 = pd.Series(format_data[generate_condition_users_by_number_of_edits(format_data,5,24)].groupby(['timestamp']).size(), index).fillna(0)
    between_25_99 = pd.Series(format_data[generate_condition_users_by_number_of_edits(format_data,25,99)].groupby(['timestamp']).size(), index).fillna(0)
    highEq_100 = pd.Series(format_data[generate_condition_users_by_number_of_edits(format_data,100,0)].groupby(['timestamp']).size(), index).fillna(0)

    new_users.name = 'New users'
    one_four.name = 'Btw. 1 and 4 edits'
    between_5_24.name = 'Btw. 5 and 24 edits'
    between_25_99.name = 'Btw. 25 and 99 edits'
    highEq_100.name = 'More than 99 edits'

    return [new_users, one_four, between_5_24, between_25_99, highEq_100, 1]

def users_number_of_edits_abs(data, index):
    '''
    Get the absolute proportion of users that belong to each category, in the Active editors by experience metric.
    '''
    users_num_edits = users_number_of_edits(data, index)

    list_of_category_names = ['new_users', 'one_four', '5_24', '25_99', 'highEq_100']
    list_of_categories = generate_list_of_dataframes(users_num_edits, list_of_category_names)
    df = calcultate_relative_proportion(list_of_categories, list_of_category_names)

    new_users = pd.Series(df['new_users'], index = index)
    one_four = pd.Series(df['one_four'], index = index)
    between_5_24 = pd.Series(df['5_24'], index = index)
    between_25_99 = pd.Series(df['25_99'], index = index)
    highEq_100 = pd.Series(df['highEq_100'], index = index)

    new_users.name = 'New users'
    one_four.name = 'Btw. 1 and 4 edits'
    between_5_24.name = 'Btw. 5 and 24 edits'
    between_25_99.name = 'Btw. 25 and 99 edits'
    highEq_100.name = 'More than 99 edits'
    
    return [new_users, one_four, between_5_24, between_25_99, highEq_100, 1]

############################ Active editors by namespace #####################################################################################

def users_article_page(data, index):
    '''
    Monthly number of users that have edited a main page
    '''
    return filter_users_pageNS(data, index, 0)

def users_articletalk_page(data, index):
    '''
    Monthly number of users that have edited an article talk page
    '''
    return filter_users_pageNS(data, index, 1)

def users_user_page(data, index):
    '''
    Monthly number of users that have edited a user page
    '''
    return filter_users_pageNS(data, index, 2)

def users_template_page(data, index):
    '''
    Monthly number of users that have edited a template page
    '''
    return filter_users_pageNS(data, index, 10)

def users_usertalk_page(data,index):
    '''
    Monthly number of users that have edited a talk page
    '''
    return filter_users_pageNS(data, index, 3)

def users_file_page(data, index):
    return filter_users_pageNS(data, index, 6)

def users_mediaWiki_page(data, index):
    return filter_users_pageNS(data, index, 8)

def users_category_page(data, index):
    return filter_users_pageNS(data, index, 14)

def users_other_page(data,index,dif):
    '''
    Monthly number of users that have edited the rest of relevant namespaces in the wiki
    '''
    if dif == 0:
        category_list = [-2, -1, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 110, 111]
    else:
        category_list = [-2, -1, 4, 5, 7, 9, 11, 12, 13, 15, 110, 111]
    aux = pd.DataFrame()
    aux['timestamp'] = index

    for i in range(len(category_list)):
        serie = filter_users_pageNS(data, index, category_list[i])
        serie = pd.DataFrame(serie).reset_index()
        aux['page_ns_' + str(category_list[i])] = serie['contributor_id']
    aux['final_result'] = aux.sum(axis=1)
    series = pd.Series(index=aux['timestamp'], data=aux['final_result'].values)
    return series

def users_in_namespaces(data, index):
    '''
    Get the monthly number of users that belong to each category in the Active editors in namespaces metric
    '''
    data = filter_anonymous(data)

    main_page = users_article_page(data, index)
    articletalk_page = users_articletalk_page(data, index)
    user_page = users_user_page(data, index)
    template_page = users_template_page(data, index)
    usertalk_page = users_usertalk_page(data,index)
    other_page = users_other_page(data,index,0)

    set_category_name([main_page, articletalk_page, user_page, template_page, usertalk_page, other_page], ['Article pages', 'Article talk pages', 'User pages', 'Template pages', 'User talk pages', 'Other pages'])

    return [main_page, articletalk_page, user_page, usertalk_page, template_page, other_page, 0]
	
def users_in_namespaces_extends(data, index):
    '''
    Get the monthly number of users that belong to each category in the Active editors in namespaces metric
    '''
    data = filter_anonymous(data)

    file = users_file_page(data, index)
    mediaWiki = users_mediaWiki_page(data, index)
    category = users_category_page(data, index)
    other_page = users_other_page(data,index,1)

    set_category_name([file,mediaWiki,category,other_page], ['File pages', 'Media wiki pages', 'Category pages','Other pages'])

    return [file, mediaWiki, category, other_page, 0]

############################ Edits by editor experience (absolute and relative) #########################################

def number_of_edits_by_experience(data, index):
    '''
    Get the monthly number of edits by each user category in the Active editors by experience metric
    '''
    data = filter_anonymous(data)
    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    format_data['nEdits'] = (format_data[['medits', 'contributor_id']].groupby(['contributor_id']))['medits'].cumsum()
    format_data['nEdits_until_previous_month'] = (format_data[['nEdits','contributor_id']].groupby(['contributor_id']))['nEdits'].shift().fillna(-1)
    
    new_users = format_data[generate_condition_users_by_number_of_edits(format_data, 0,0)]
    one_four = format_data[generate_condition_users_by_number_of_edits(format_data, 1,4)]
    between_5_24 = format_data[generate_condition_users_by_number_of_edits(format_data, 5,24)]
    between_25_99 = format_data[generate_condition_users_by_number_of_edits(format_data, 25,99)]
    highEq_100 = format_data[generate_condition_users_by_number_of_edits(format_data, 100,0)]

    new_users = new_users.groupby(['timestamp'])['medits'].sum().reindex(index).fillna(0)
    one_four = one_four.groupby(['timestamp'])['medits'].sum().reindex(index).fillna(0)
    between_5_24 = between_5_24.groupby(['timestamp'])['medits'].sum().reindex(index).fillna(0)
    between_25_99 = between_25_99.groupby(['timestamp'])['medits'].sum().reindex(index).fillna(0)
    highEq_100 = highEq_100.groupby(['timestamp'])['medits'].sum().reindex(index).fillna(0)

    new_users.name = "New users"
    one_four.name = "Btw. 1 and 4 edits"
    between_5_24.name = "Btw. 5 and 24 edits"
    between_25_99.name = "Btw. 24 and 99 edits"
    highEq_100.name = "More than 99 edits"

    return [new_users, one_four, between_5_24, between_25_99, highEq_100, 1]

def number_of_edits_by_experience_abs(data, index):
    '''
    Get the monthly proportion of edits done by each user category in the Active editors by experience metrics
    '''
    categories = number_of_edits_by_experience(data, index)

    data = filter_anonymous(data)
    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    format_data['nEdits'] = (format_data[['medits', 'contributor_id']].groupby(['contributor_id']))['medits'].cumsum()
    format_data['nEdits_until_previous_month'] = (format_data[['nEdits','contributor_id']].groupby(['contributor_id']))['nEdits'].shift().fillna(-1)
    monthly_total_edits = format_data.groupby(['timestamp'])['medits'].sum().reindex(index).fillna(0)

    edits_new_users = ((categories[0] / monthly_total_edits)*100).fillna(0)
    edits_beginners = ((categories[1] / monthly_total_edits)*100).fillna(0)
    edits_advanced = ((categories[2] / monthly_total_edits)*100).fillna(0)
    edits_experimented = ((categories[3] / monthly_total_edits)*100).fillna(0)
    edits_H_experimented = ((categories[4] / monthly_total_edits)*100).fillna(0)

    edits_new_users.name = "New users"
    edits_beginners.name = "Btw. 1 and 4 edits"
    edits_advanced.name = "Btw. 5 and 24 edits"
    edits_experimented.name = "Btw. 24 and 99 edits"
    edits_H_experimented.name = "More than 99 edits"

    return [edits_new_users, edits_beginners, edits_advanced, edits_experimented, edits_H_experimented, 1]

############################ Edits by editor's tenure #########################################

def number_of_edits_by_tenure(data, index):
    '''
    Get the monthly number of edits by each user category in the Users by tenure metric
    '''
    data = filter_anonymous(data)
    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    
    mins = format_data.groupby('contributor_id')['timestamp'].transform('min')
    format_data['months'] = format_data['timestamp'].sub(mins).div(pd.Timedelta(1, 'M')).round().astype(int)
    
    new_users = format_data[format_data['months'] == 0]
    one_three = format_data[(format_data['months'] >= 1) & (format_data['months'] <= 3)]
    four_six = format_data[(format_data['months'] >= 4) & (format_data['months'] <= 6)]
    six_twelve = format_data[(format_data['months'] >= 7) & (format_data['months'] <= 12)]
    more_twelve = format_data[format_data['months'] >= 13]

    new_users = new_users.groupby(['timestamp'])['medits'].sum().reindex(index).fillna(0)
    one_three = one_three.groupby(['timestamp'])['medits'].sum().reindex(index).fillna(0)
    four_six = four_six.groupby(['timestamp'])['medits'].sum().reindex(index).fillna(0)
    six_twelve = six_twelve.groupby(['timestamp'])['medits'].sum().reindex(index).fillna(0)
    more_twelve = more_twelve.groupby(['timestamp'])['medits'].sum().reindex(index).fillna(0)

    new_users.name = 'New users'
    one_three.name = 'Btw. 1 and 3 months ago'
    four_six.name = 'Btw. 4 and 6 months ago'
    six_twelve.name = 'Btw. 6 and 12 months ago'
    more_twelve.name = 'More than 12 months ago'
    
    return [new_users, one_three, four_six, six_twelve, more_twelve, 1]

def number_of_edits_by_tenure_abs(data, index):
    '''
    Get the monthly proportion of edits done by each user category in the Users by tenure metric
    '''
    categories = number_of_edits_by_tenure(data, index)

    data = filter_anonymous(data)
    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    monthly_total_edits = format_data.groupby(['timestamp'])['medits'].sum()

    new_users = (categories[0]/monthly_total_edits)*100
    one_three = (categories[1]/monthly_total_edits)*100
    four_six = (categories[2]/monthly_total_edits)*100
    six_twelve = (categories[3]/monthly_total_edits)*100
    more_twelve = (categories[4]/monthly_total_edits)*100

    new_users.name = 'New users'
    one_three.name = 'Btw. 1 and 3 months ago'
    four_six.name = 'Btw. 4 and 6 months ago'
    six_twelve.name = 'Btw. 6 and 12 months ago'
    more_twelve.name = 'More than 12 months ago'

    return [new_users, one_three, four_six, six_twelve, more_twelve, 1]

############################ Edits by editor's last edit date #########################################

def number_of_edits_by_last_edit(data, index):
    '''
    Get the monthly number of edits by each user category in the Users by the date of the last edit metric
    '''
    data = filter_anonymous(data)
    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    format_data['months'] = format_data.groupby('contributor_id')['timestamp'].diff().div(pd.Timedelta(days=30.44), fill_value=0).round().astype(int)

    new_users = (format_data[format_data['months'] == 0]).groupby(['timestamp'])['medits'].sum().reindex(index).fillna(0)
    one_month = (format_data[format_data['months'] == 1]).groupby(['timestamp'])['medits'].sum().reindex(index).fillna(0)
    two_three_months = (format_data[(format_data['months'] == 2) | (format_data['months'] == 3)]).groupby(['timestamp'])['medits'].sum().reindex(index).fillna(0)
    four_six_months = (format_data[(format_data['months'] >= 4) & (format_data['months'] <= 6)]).groupby(['timestamp'])['medits'].sum().reindex(index).fillna(0)
    more_six_months = (format_data[format_data['months'] > 6]).groupby(['timestamp'])['medits'].sum().reindex(index).fillna(0)

    new_users.name = 'New users'
    one_month.name = '1 month ago'
    two_three_months.name = 'Btw. 2 and 3 months ago'
    four_six_months.name = 'Btw. 4 and 6 months ago'
    more_six_months.name = 'More than six months ago'

    return [new_users, one_month, two_three_months, four_six_months, more_six_months, 1]

def number_of_edits_by_last_edit_abs(data, index):
    '''
    Get the monthly proportion of edits done by each user category in the Users by the date of the last edit metric
    '''
    categories = number_of_edits_by_last_edit(data, index)
    data = filter_anonymous(data)
    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    monthly_total_edits = format_data.groupby(['timestamp'])['medits'].sum()

    new_users = (categories[0] / monthly_total_edits) * 100
    one_month = (categories[1] / monthly_total_edits) * 100
    two_three_months = (categories[2] / monthly_total_edits) * 100
    four_six_months = (categories[3] / monthly_total_edits) * 100
    more_six_months = (categories[4] / monthly_total_edits) * 100

    new_users.name = 'New users'
    one_month.name = '1 month ago'
    two_three_months.name = 'Btw. 2 and 3 months ago'
    four_six_months.name = 'Btw. 4 and 6 months ago'
    more_six_months.name = 'More than six months ago'

    return [new_users, one_month, two_three_months, four_six_months, more_six_months, 1]

############################ Factoids by Active editors by experience #########################################
def url_by_months(data,index):
        data = filter_anonymous(data)
        data['edit_content']=data['edit_content'].apply(str)
        data['countI']=data['edit_content'].apply(lambda x:x.count('[['))
        data['countE']=data['edit_content'].apply(lambda x:x.count('[http'))
        data['countTotal']=data['countI'] + data['countE']
        series = data.groupby(pd.Grouper(key ='timestamp', freq='MS'))['countTotal'].sum()
        if index is not None:
            series= series.reindex(index, fill_value=0)
        return series

def pic_by_months(data, index):
    data = filter_anonymous(data)
    data['edit_content'] = data['edit_content'].apply(str)
    data['countJPG'] = data['edit_content'].apply(lambda x:x.count('.jpg'))
    data['countPNG'] = data['edit_content'].apply(lambda x:x.count('.png'))
    data['count'] = data['countJPG'] + data['countPNG']
    series = data.groupby(pd.Grouper(key ='timestamp', freq='MS'))['count'].sum()
    if index is not None:
        series= series.reindex(index, fill_value=0)
    return series
def difference_btw_external_and_internal_links(data,index):
        data = filter_anonymous(data)
        data['edit_content']=data['edit_content'].apply(str)
        dataExternal=data
        data['countI']=data['edit_content'].apply(lambda x:x.count('[['))
        dataExternal['countE']=data['edit_content'].apply(lambda x:x.count('[http'))
        internalBar=data.groupby(pd.Grouper(key ='timestamp', freq='MS'))['countI'].sum()
        externalBar = dataExternal.groupby(pd.Grouper(key ='timestamp', freq='MS'))['countE'].sum()
        internalBar.name='Internal link'
        externalBar.name='External link'
        return[internalBar, externalBar,1]
def added_factoids_by_active_editors_by_experience(data, index):
    '''
    Get the number of factoids added by users that belong to each category, in the Active editors by experience metric.
    '''
    data = filter_anonymous(data)
    data = data[data['page_ns'] == 0]
    data['timestamp'] = pd.to_datetime(data['timestamp']).dt.to_period('M').dt.to_timestamp()
    data['factoids'] = data['factoids'].apply(str).apply(lambda x: x.split(',')).apply(set)
    data['added_factoids'] = data.groupby('page_id').factoids.diff().fillna(data.factoids)
    data['number_added_factoids'] = data['added_factoids'].apply(len)

    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    format_data['number_added_factoids'] = (data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')])['number_added_factoids'].sum().reset_index())['number_added_factoids']
    format_data['nEdits'] = (format_data[['medits', 'contributor_id']].groupby(['contributor_id']))['medits'].cumsum()
    format_data['nEdits_until_previous_month'] = (format_data[['nEdits','contributor_id']].groupby(['contributor_id']))['nEdits'].shift().fillna(-1)

    new_users = format_data[generate_condition_users_by_number_of_edits(format_data, 0,0)]
    one_four = format_data[generate_condition_users_by_number_of_edits(format_data, 1,4)]
    between_5_24 = format_data[generate_condition_users_by_number_of_edits(format_data,5,24)]
    between_25_99 = format_data[generate_condition_users_by_number_of_edits(format_data,25,99)]
    highEq_100 = format_data[generate_condition_users_by_number_of_edits(format_data,100,0)]

    new_users_factoids = new_users.groupby(['timestamp'])['number_added_factoids'].sum().reindex(index).fillna(0)
    one_four_factoids = one_four.groupby(['timestamp'])['number_added_factoids'].sum().reindex(index).fillna(0)
    between_5_24_factoids = between_5_24.groupby(['timestamp'])['number_added_factoids'].sum().reindex(index).fillna(0)
    between_25_99_factoids = between_25_99.groupby(['timestamp'])['number_added_factoids'].sum().reindex(index).fillna(0)
    highEq_100_factoids = highEq_100.groupby(['timestamp'])['number_added_factoids'].sum().reindex(index).fillna(0)

    new_users_factoids.name = 'By new users'
    one_four_factoids.name = 'By users that have done btw. 1 and 4 edits'
    between_5_24_factoids.name = 'By users that have done btw. 5 and 24 edits'
    between_25_99_factoids.name = 'By users that have done btw. 25 and 99 edits'
    highEq_100_factoids.name = 'By users that have done more than 99 edits'

    return [new_users_factoids, one_four_factoids, between_5_24_factoids, between_25_99_factoids, highEq_100_factoids, 1]

def deleted_factoids_by_active_editors_by_experience(data, index):
    '''
    Get the average number of factoids deleted by users that belong to each category, in the Active editors by experience metric.
    '''
    data = filter_anonymous(data)
    data = data[data['page_ns'] == 0]
    data['timestamp'] = pd.to_datetime(data['timestamp']).dt.to_period('M').dt.to_timestamp()

    data['factoids'] = data['factoids'].apply(str).apply(lambda x: x.split(',')).apply(set)
    data['factoids_history'] = pd.concat([pd.Series([set()]), data['factoids'][:-1]]).reset_index(drop=True)
    data['deleted_factoids'] = data['factoids_history'] - data['factoids']
    idx = data.groupby('contributor_id').head(1).index
    data.loc[idx, 'deleted_factoids'] = data.loc[idx, 'deleted_factoids'].apply(lambda x: set())
    data.drop('factoids_history', axis=1, inplace=True)
    data['number_deleted_factoids'] = data['deleted_factoids'].str.len()

    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    format_data['number_deleted_factoids'] = (data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')])['number_deleted_factoids'].sum().reset_index())['number_deleted_factoids']
    format_data['nEdits'] = (format_data[['medits', 'contributor_id']].groupby(['contributor_id']))['medits'].cumsum()
    format_data['nEdits_until_previous_month'] = (format_data[['nEdits','contributor_id']].groupby(['contributor_id']))['nEdits'].shift().fillna(-1)

    new_users = format_data[generate_condition_users_by_number_of_edits(format_data, 0,0)]
    one_four = format_data[generate_condition_users_by_number_of_edits(format_data, 1,4)]
    between_5_24 = format_data[generate_condition_users_by_number_of_edits(format_data,5,24)]
    between_25_99 = format_data[generate_condition_users_by_number_of_edits(format_data,25,99)]
    highEq_100 = format_data[generate_condition_users_by_number_of_edits(format_data,100,0)]

    new_users_factoids = new_users.groupby(['timestamp'])['number_deleted_factoids'].sum().reindex(index).fillna(0)
    one_four_factoids = one_four.groupby(['timestamp'])['number_deleted_factoids'].sum().reindex(index).fillna(0)
    between_5_24_factoids = between_5_24.groupby(['timestamp'])['number_deleted_factoids'].sum().reindex(index).fillna(0)
    between_25_99_factoids = between_25_99.groupby(['timestamp'])['number_deleted_factoids'].sum().reindex(index).fillna(0)
    highEq_100_factoids = highEq_100.groupby(['timestamp'])['number_deleted_factoids'].sum().reindex(index).fillna(0)

    new_users_factoids.name = 'By new users'
    one_four_factoids.name = 'By users that have done btw. 1 and 4 edits'
    between_5_24_factoids.name = 'By users that have done btw. 5 and 24 edits'
    between_25_99_factoids.name = 'By users that have done btw. 25 and 99 edits'
    highEq_100_factoids.name = 'By users that have done more than 99 edits'

    return [new_users_factoids, one_four_factoids, between_5_24_factoids, between_25_99_factoids, highEq_100_factoids, 1]

############################ Factoids by Users by edit streak #########################################
def added_factoids_by_edit_streak(data, index):
    '''
    Get the number of factoids added by users that belong to each category, in the Users by edit streak.
    '''
    data = filter_anonymous(data)
    data = data[data['page_ns'] == 0]
    data['timestamp'] = pd.to_datetime(data['timestamp']).dt.to_period('M').dt.to_timestamp()
    data['factoids'] = data['factoids'].apply(str).apply(lambda x: x.split(',')).apply(set)
    data['added_factoids'] = data.groupby('page_id').factoids.diff().fillna(data.factoids)
    data['number_added_factoids'] = data['added_factoids'].apply(len)
	
    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    format_data['number_of_factoids'] = (data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')])['number_added_factoids'].sum().reset_index())['number_added_factoids']

    this_month = current_streak_x_or_y_months_in_a_row(format_data, index, 1, 0, 'factoids')
    two_three_months = current_streak_x_or_y_months_in_a_row(format_data, index, 1, 3, 'factoids')
    four_six_months = current_streak_x_or_y_months_in_a_row(format_data, index, 3, 6, 'factoids')
    more_six = current_streak_x_or_y_months_in_a_row(format_data, index, 6, 0, 'factoids')
	
    set_category_name([this_month, two_three_months, four_six_months, more_six], ['1 month editing', 'Btw. 2 and 3 consecutive months', 'Btw. 4 and 6 consecutive months', 'More than 6 consecutive months'])
    
    return [this_month, two_three_months, four_six_months, more_six, 1]
	
def deleted_factoids_by_edit_streak(data, index):
    '''
    Get the number of factoids deleted by users that belong to each category, in the Users by edit streak metric.
    '''
    data = filter_anonymous(data)
    data = data[data['page_ns'] == 0]
    data['timestamp'] = pd.to_datetime(data['timestamp']).dt.to_period('M').dt.to_timestamp()

    data['factoids'] = data['factoids'].apply(str).apply(lambda x: x.split(',')).apply(set)
    data['factoids_history'] = pd.concat([pd.Series([set()]), data['factoids'][:-1]]).reset_index(drop=True)
    data['deleted_factoids'] = data['factoids_history'] - data['factoids']
    idx = data.groupby('contributor_id').head(1).index
    data.loc[idx, 'deleted_factoids'] = data.loc[idx, 'deleted_factoids'].apply(lambda x: set())
    data.drop('factoids_history', axis=1, inplace=True)
    data['number_deleted_factoids'] = data['deleted_factoids'].str.len()
	
    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    format_data['number_of_factoids'] = (data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')])['number_deleted_factoids'].sum().reset_index())['number_deleted_factoids']

    this_month = current_streak_x_or_y_months_in_a_row(format_data, index, 1, 0, 'factoids')
    two_three_months = current_streak_x_or_y_months_in_a_row(format_data, index, 1, 3, 'factoids')
    four_six_months = current_streak_x_or_y_months_in_a_row(format_data, index, 3, 6, 'factoids')
    more_six = current_streak_x_or_y_months_in_a_row(format_data, index, 6, 0, 'factoids')
	
    set_category_name([this_month, two_three_months, four_six_months, more_six], ['1 month editing', 'Btw. 2 and 3 consecutive months', 'Btw. 4 and 6 consecutive months', 'More than 6 consecutive months'])
    
    return [this_month, two_three_months, four_six_months, more_six, 1]

############################ Factoids by Users by tenure #########################################

def added_factoids_by_tenure(data, index):
    '''
    Get the number of factoids added by users that belong to each category, in the Users by tenure metric.
    '''
    data = filter_anonymous(data)
    data = data[data['page_ns'] == 0]
    data['timestamp'] = pd.to_datetime(data['timestamp']).dt.to_period('M').dt.to_timestamp()
    data['factoids'] = data['factoids'].apply(str).apply(lambda x: x.split(',')).apply(set)
    data['added_factoids'] = data.groupby('page_id').factoids.diff().fillna(data.factoids)
    data['number_added_factoids'] = data['added_factoids'].apply(len)

    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    format_data['number_added_factoids'] = (data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')])['number_added_factoids'].sum().reset_index())['number_added_factoids']

    mins = format_data.groupby('contributor_id')['timestamp'].transform('min')
    format_data['months'] = format_data['timestamp'].sub(mins).div(pd.Timedelta(1, 'M')).round().astype(int)
    
    new_users = format_data[format_data['months'] == 0]
    one_three = format_data[(format_data['months'] >= 1) & (format_data['months'] <= 3)]
    four_six = format_data[(format_data['months'] >= 4) & (format_data['months'] <= 6)]
    six_twelve = format_data[(format_data['months'] >= 7) & (format_data['months'] <= 12)]
    more_twelve = format_data[format_data['months'] >= 13]

    new_users_factoids = new_users.groupby(['timestamp'])['number_added_factoids'].sum().reindex(index).fillna(0)
    one_three_factoids = one_three.groupby(['timestamp'])['number_added_factoids'].sum().reindex(index).fillna(0)
    four_six_factoids = four_six.groupby(['timestamp'])['number_added_factoids'].sum().reindex(index).fillna(0)
    six_twelve_factoids = six_twelve.groupby(['timestamp'])['number_added_factoids'].sum().reindex(index).fillna(0)
    more_twelve_factoids = more_twelve.groupby(['timestamp'])['number_added_factoids'].sum().reindex(index).fillna(0)

    new_users_factoids.name = 'By new users'
    one_three_factoids.name = 'By users first edit between 1 and 3 months ago'
    four_six_factoids.name = 'By users first edit between 4 and 6 months ago'
    six_twelve_factoids.name = 'By users first edit between 6 and 12 months ago'
    more_twelve_factoids.name = 'By users first edit more than 12 months ago'

    return [new_users_factoids, one_three_factoids, four_six_factoids, six_twelve_factoids, more_twelve_factoids, 1]

def deleted_factoids_by_tenure(data, index):
    '''
    Get the number of factoids deleted by users that belong to each category, in the Users by tenure metric.
    '''
    data = filter_anonymous(data)
    data = data[data['page_ns'] == 0]
    data['timestamp'] = pd.to_datetime(data['timestamp']).dt.to_period('M').dt.to_timestamp()

    data['factoids'] = data['factoids'].apply(str).apply(lambda x: x.split(',')).apply(set)
    data['factoids_history'] = pd.concat([pd.Series([set()]), data['factoids'][:-1]]).reset_index(drop=True)
    data['deleted_factoids'] = data['factoids_history'] - data['factoids']
    idx = data.groupby('contributor_id').head(1).index
    data.loc[idx, 'deleted_factoids'] = data.loc[idx, 'deleted_factoids'].apply(lambda x: set())
    data.drop('factoids_history', axis=1, inplace=True)
    data['number_deleted_factoids'] = data['deleted_factoids'].str.len()

    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    format_data['number_deleted_factoids'] = (data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')])['number_deleted_factoids'].sum().reset_index())['number_deleted_factoids']

    mins = format_data.groupby('contributor_id')['timestamp'].transform('min')
    format_data['months'] = format_data['timestamp'].sub(mins).div(pd.Timedelta(1, 'M')).round().astype(int)
    
    new_users = format_data[format_data['months'] == 0]
    one_three = format_data[(format_data['months'] >= 1) & (format_data['months'] <= 3)]
    four_six = format_data[(format_data['months'] >= 4) & (format_data['months'] <= 6)]
    six_twelve = format_data[(format_data['months'] >= 7) & (format_data['months'] <= 12)]
    more_twelve = format_data[format_data['months'] >= 13]

    new_users_factoids = new_users.groupby(['timestamp'])['number_deleted_factoids'].sum().reindex(index).fillna(0)
    one_three_factoids = one_three.groupby(['timestamp'])['number_deleted_factoids'].sum().reindex(index).fillna(0)
    four_six_factoids = four_six.groupby(['timestamp'])['number_deleted_factoids'].sum().reindex(index).fillna(0)
    six_twelve_factoids = six_twelve.groupby(['timestamp'])['number_deleted_factoids'].sum().reindex(index).fillna(0)
    more_twelve_factoids = more_twelve.groupby(['timestamp'])['number_deleted_factoids'].sum().reindex(index).fillna(0)

    new_users_factoids.name = 'By new users'
    one_three_factoids.name = 'By users first edit between 1 and 3 months ago'
    four_six_factoids.name = 'By users first edit between 4 and 6 months ago'
    six_twelve_factoids.name = 'By users first edit between 6 and 12 months ago'
    more_twelve_factoids.name = 'By users first edit more than 12 months ago'

    return [new_users_factoids, one_three_factoids, four_six_factoids, six_twelve_factoids, more_twelve_factoids, 1]

############################ Factoids by Users by date of the last edit #########################################

def added_factoids_by_date_of_last_edit(data, index):
    '''
    Get the number of factoids added by users that belong to each category, in the Users by the date of the last edit metric.
    '''
    data = filter_anonymous(data)
    data = data[data['page_ns'] == 0]
    data['timestamp'] = pd.to_datetime(data['timestamp']).dt.to_period('M').dt.to_timestamp()
    data['factoids'] = data['factoids'].apply(str).apply(lambda x: x.split(',')).apply(set)
    data['added_factoids'] = data.groupby('page_id').factoids.diff().fillna(data.factoids)
    data['number_added_factoids'] = data['added_factoids'].apply(len)

    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    format_data['number_added_factoids'] = (data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')])['number_added_factoids'].sum().reset_index())['number_added_factoids']
    format_data['months'] = format_data.groupby('contributor_id')['timestamp'].diff().div(pd.Timedelta(days=30.44), fill_value=0).round().astype(int)
    
    new_users = format_data[format_data['months'] == 0]
    one_month = format_data[format_data['months'] == 1]
    two_three_months = format_data[(format_data['months'] == 2) | (format_data['months'] == 3)]
    four_six_months = format_data[(format_data['months'] >= 4) & (format_data['months'] <= 6)]
    more_six_months = format_data[format_data['months'] > 6]

    new_users_factoids = new_users.groupby(['timestamp'])['number_added_factoids'].sum().reindex(index).fillna(0)
    one_month_factoids = one_month.groupby(['timestamp'])['number_added_factoids'].sum().reindex(index).fillna(0)
    two_three_months_factoids = two_three_months.groupby(['timestamp'])['number_added_factoids'].sum().reindex(index).fillna(0)
    four_six_months_factoids = four_six_months.groupby(['timestamp'])['number_added_factoids'].sum().reindex(index).fillna(0)
    more_six_months_factoids = more_six_months.groupby(['timestamp'])['number_added_factoids'].sum().reindex(index).fillna(0)

    new_users_factoids.name = 'By new users'
    one_month_factoids.name = 'By users last edit 1 month ago'
    two_three_months_factoids.name = 'By users last edit between 2 and 3 months ago'
    four_six_months_factoids.name = 'By users last edit between 4 and 6 months ago'
    more_six_months_factoids.name = 'By users last edit more than 6 months ago'

    return [new_users_factoids, one_month_factoids, two_three_months_factoids, four_six_months_factoids, more_six_months_factoids, 1]

def deleted_factoids_by_date_of_last_edit(data, index):
    '''
    Get the number of factoids deleted by users that belong to each category, in the Users by the date of the last edit metric.
    '''
    data = filter_anonymous(data)
    data = data[data['page_ns'] == 0]
    data['timestamp'] = pd.to_datetime(data['timestamp']).dt.to_period('M').dt.to_timestamp()

    data['factoids'] = data['factoids'].apply(str).apply(lambda x: x.split(',')).apply(set)
    data['factoids_history'] = pd.concat([pd.Series([set()]), data['factoids'][:-1]]).reset_index(drop=True)
    data['deleted_factoids'] = data['factoids_history'] - data['factoids']
    idx = data.groupby('contributor_id').head(1).index
    data.loc[idx, 'deleted_factoids'] = data.loc[idx, 'deleted_factoids'].apply(lambda x: set())
    data.drop('factoids_history', axis=1, inplace=True)
    data['number_deleted_factoids'] = data['deleted_factoids'].str.len()

    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    format_data['number_deleted_factoids'] = (data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')])['number_deleted_factoids'].sum().reset_index())['number_deleted_factoids']
    format_data['months'] = format_data.groupby('contributor_id')['timestamp'].diff().div(pd.Timedelta(days=30.44), fill_value=0).round().astype(int)
    
    new_users = format_data[format_data['months'] == 0]
    one_month = format_data[format_data['months'] == 1]
    two_three_months = format_data[(format_data['months'] == 2) | (format_data['months'] == 3)]
    four_six_months = format_data[(format_data['months'] >= 4) & (format_data['months'] <= 6)]
    more_six_months = format_data[format_data['months'] > 6]

    new_users_factoids = new_users.groupby(['timestamp'])['number_deleted_factoids'].sum().reindex(index).fillna(0)
    one_month_factoids = one_month.groupby(['timestamp'])['number_deleted_factoids'].sum().reindex(index).fillna(0)
    two_three_months_factoids = two_three_months.groupby(['timestamp'])['number_deleted_factoids'].sum().reindex(index).fillna(0)
    four_six_months_factoids = four_six_months.groupby(['timestamp'])['number_deleted_factoids'].sum().reindex(index).fillna(0)
    more_six_months_factoids = more_six_months.groupby(['timestamp'])['number_deleted_factoids'].sum().reindex(index).fillna(0)

    new_users_factoids.name = 'By new users'
    one_month_factoids.name = 'By users last edit 1 month ago'
    two_three_months_factoids.name = 'By users last edit between 2 and 3 months ago'
    four_six_months_factoids.name = 'By users last edit between 4 and 6 months ago'
    more_six_months_factoids.name = 'By users last edit more than 6 months ago'

    return [new_users_factoids, one_month_factoids, two_three_months_factoids, four_six_months_factoids, more_six_months_factoids, 1]


############################# HEATMAP METRICS ##############################################

def edit_distributions_across_editors(data, index):
    """
    Function which calculates the number X of editors making the same number of editions.
    it returns the months of the wiki, a list of the number of contributions until the maximum number,
    and at last, a matrix with the number of contributors doing the same number of contributions on each month.

    """
    users_registered = filter_anonymous(data)
    mothly = users_registered.groupby([pd.Grouper(key ='timestamp', freq='MS'),'contributor_id']).size()
    mothly = mothly.to_frame('num_contributions').reset_index()
    mothly.loc[mothly['num_contributions'] > 100, 'num_contributions'] = 100
    mothly = mothly.groupby([pd.Grouper(key ='timestamp', freq='MS'),'num_contributions']).size().to_frame('num_editors').reset_index()
    list_range = list(range(0, 111, 10))
    max_range = max(list_range)
    mothly['range'] = pd.cut(mothly['num_contributions'], bins = list_range, right = False).astype(str)
    months_range = mothly.groupby([pd.Grouper(key ='timestamp', freq='MS'), 'range'])['num_editors'].sum()
    graphs_list = [[0 for j in range(max_range)] for i in range(len(index))]
    before = pd.to_datetime(0)
    j = -1
    for i, v in months_range.iteritems(): 
        i = list(i)#lista con timestamp y bins
        current = i[0]#fecha
        p = i[1]# untervalo
        p = p.split(')')[0]
        p = p.split('[')[1]
        p = p.split(',')
        num_min = int(float(p[0]))
        num_max = int(float(p[1]))
        num_min = (num_min)
        num_max = (num_max-1)
        resta = current - before
        resta = int(resta / np.timedelta64(1, 'D'))
        if (resta > 31 and before != pd.to_datetime(0)):
            aux= int(resta / 31)
            j = j + aux
            resta = resta- (31 * aux)
        if (before != current):
            j = j +1
            before = current
        graphs_list[j][num_min:num_max+1] = [v for i in range(num_min,num_max+1)]
    wiki_by_metrics = np.transpose(graphs_list);
    return [index,list(range(0, 109)), wiki_by_metrics, 'Number of editors']

def bytes_difference_across_articles(data, index):
    data.set_index(data['timestamp'], inplace=True)
    users_registered = filter_anonymous(data)
    mains = users_registered[users_registered['page_ns'] == 0]
    order = mains.sort_index()
    group_by_page_id = order[['page_id', 'bytes']].groupby(['page_id'])
    #order = group_by_page_id.apply(lambda x: (x.bytes-x.bytes.shift()).fillna(x.bytes)).to_frame('dif')
    group = group_by_page_id['bytes'].shift()
    order['bytes1'] = group
    order['dif'] = order['bytes'] - order['bytes1']
    order['dif'] = order['dif'].fillna(order['bytes']).astype(int)
    order.loc[order['dif'] > 1000, 'dif'] = 1000
    order.loc[order['dif'] < -1000, 'dif'] = -1000
    #order['dif'] = order['dif'].apply(lambda x: int(x))
    #print(order[['bytes', 'bytes1', 'dif']])
    #order = order.reset_index()
    #max_dif_bytes = int(max(order['dif']))
    #min_dif_bytes = int(min(order['dif'])-1)
    #round_max = (max_dif_bytes+100)
    list_range = list(range(-1100, 1101, 100))
    min_range = min(list_range)
    max_range = max(list_range)
    order['range'] = pd.cut(order['dif'], bins = list_range, right = False).astype(str)
    #list_range = list(range(min_dif_bytes, round_max, 100))

    #order['range'] = pd.cut(order['dif'], bins = list_range).astype(str)
    months_range = order.groupby([pd.Grouper(key ='timestamp', freq='MS'), 'range']).size()
    #min_dif_bytes_a = abs(min_dif_bytes+1)
    #max_range = max_range + min_dif_bytes_a
    graphs_list = [[0 for j in range(min_range, max_range)] for i in range(len(index))]
    before = pd.to_datetime(0)
    j = -1
    for i, v in months_range.iteritems(): 
        i = list(i)#lsita con timestamp y bins
        current = i[0]#fecha
        p = i[1]# untervalo
        p = p.split(')')[0]
        p = p.split('[')[1]
        p = p.split(',')
        num_min = int(float(p[0]))
        num_max = int(float(p[1]))
        num_min = (num_min)
        num_max = (num_max)
        resta = current - before
        resta = int(resta / np.timedelta64(1, 'D'))
        if (resta > 31 and before != pd.to_datetime(0)):
            aux= int(resta / 31)
            j = j + aux
            resta = resta- (31 * aux)
        if (before != current):
            j = j +1
            before = current
        graphs_list[j][num_min:num_max] = [v for i in range(num_min,num_max)]
    wiki_by_metrics = np.transpose(graphs_list)
    return [index, list(range(-1100, 1099)), wiki_by_metrics, 'Number of articles']

def edition_on_pages(data, index):
    users_registered = filter_anonymous(data)
    groupTP=users_registered.groupby([pd.Grouper(key ='timestamp', freq='MS'),'page_id']).size().to_frame('ediciones').reset_index()
    maxEditors=max(groupTP['ediciones'])
    round_max = (maxEditors+5)
    list_range = list(range(0, round_max+1, 5))
    max_range = max(list_range)
    groupTP['range'] = pd.cut(groupTP['ediciones'], bins = list_range).astype(str)
    z = groupTP.groupby([pd.Grouper(key ='timestamp', freq='MS'), 'range']).size()
    graphs_list = [[0 for j in range(max_range+1)] for i in range(len(index))]
    before = pd.to_datetime(0)
    j = -1
    for i, v in z.iteritems(): 
        i = list(i)#lsita con timestamp y bins
        current = i[0]#fecha
        p = i[1]# untervalo
        p = p.split(']')[0]
        p = p.split('(')[1]
        p = p.split(',')
        num_min = int(float(p[0]))
        num_max = int(float(p[1]))
        num_min = (num_min+1)
        num_max = (num_max)
        resta = current - before
        resta = int(resta / np.timedelta64(1, 'D'))
        if (resta > 31 and before != pd.to_datetime(0)):
            aux= int(resta / 31)
            j = j + aux
            resta = resta- (31 * aux)
        if (before != current):
            j = j +1
            before = current
        graphs_list[j][num_min:num_max+1] = [v for i in range(num_min,num_max+1)]
    wiki_by_metrics = np.transpose(graphs_list);
    return [index,list(range(maxEditors)),wiki_by_metrics, 'Number of pages']

def mask_first(x):
    result = np.ones_like(x)
    result[0] = 0
    return result

def revision_on_pages(data, index):
    users_registered = filter_anonymous(data)
    #without_first_edition = users_registered.groupby([pd.Grouper(key ='timestamp', freq='MS'),'page_id']).apply(lambda x:x.iloc[1:,1:])
    groupTP = users_registered.groupby(['page_id'])['page_id'].transform(mask_first).astype(bool)
    without_first_edition = users_registered.loc[groupTP]
    z=without_first_edition.groupby([pd.Grouper(key ='timestamp', freq='MS'),'page_id']).size().to_frame('revisiones').reset_index()
    maxRevision= max(z['revisiones'])
    round_max = (maxRevision+5)
    list_range = list(range(0, round_max+1, 5))
    max_range = max(list_range)
    z['range'] = pd.cut(z['revisiones'], bins = list_range).astype(str)
    z = z.groupby([pd.Grouper(key ='timestamp', freq='MS'), 'range']).size()
    graphs_list = [[0 for j in range(max_range+1)] for i in range(len(index))]
    before = pd.to_datetime(0)
    j = -1
    for i, v in z.iteritems(): 
        i = list(i)#lsita con timestamp y bins
        current = i[0]#fecha
        p = i[1]# untervalo
        p = p.split(']')[0]
        p = p.split('(')[1]
        p = p.split(',')
        num_min = int(float(p[0]))
        num_max = int(float(p[1]))
        num_min = (num_min+1)
        num_max = (num_max)
        resta = current - before
        resta = int(resta / np.timedelta64(1, 'D'))
        if (resta > 31 and before != pd.to_datetime(0)):
            aux= int(resta / 31)
            j = j + aux
            resta = resta- (31 * aux)
        if (before != current):
            j = j +1
            before = current
        graphs_list[j][num_min:num_max+1] = [v for i in range(num_min,num_max+1)]
    wiki_by_metrics = np.transpose(graphs_list);
    return [index,list(range(maxRevision)),wiki_by_metrics, 'Number of pages']

def distribution_editors_between_articles_edited_each_month(data, index):
    users_registered = filter_anonymous(data)
    #main namespace
    users_registered = users_registered[users_registered['page_ns']==0]

    users_per_article = users_registered.groupby([pd.Grouper(key ='timestamp', freq='MS'),'page_id'])['contributor_id'].nunique().reset_index(name='editor_count')

    max_editors = max(users_per_article['editor_count'])

    z_articles_by_y_editors = users_per_article.groupby([pd.Grouper(key ='timestamp', freq='MS'),'editor_count']).size()


    #y parameter
    y_param = list(range(max_editors))

    #z parameter
    graphs_list = [[0 for j in range(max_editors+1)] for i in range(len(index))]
    anterior = pd.to_datetime(0)
    j = -1
    for i, v in z_articles_by_y_editors.iteritems():
        i = list(i)
        actual = i[0]
        num = i[1]
        resta = actual - anterior
        resta = int(resta / np.timedelta64(1, 'D'))
        while (resta > 31 and anterior != pd.to_datetime(0)):
            j = j+1
            resta = resta-31
        if (anterior != actual):
            j = j +1
            anterior = actual
        if(j <= len(index)):
            graphs_list[j][num] = v

    z_param = []
    for i in range(max_editors+1):
            row = [graphs_list[j].pop(0) for j in range(len(graphs_list))]
            z_param.append(row)  
    return [index,y_param,z_param, z_articles_by_y_editors, 'Number of articles']
    

########################### % Of edits by % of users (accumulated and monthly) ###########################################

	
def contributor_pctg_per_contributions_pctg(data, index):
    """
    Function which calculates which % of contributors has contributed
    in a 50%, 80%, 90% and 99% of the total wiki edits until each month.
    """

    data = filter_anonymous(data)
    format_data =data.groupby(['contributor_id']).apply(lambda x: x.groupby(pd.Grouper(key='timestamp', freq='MS')).size().to_frame('nEdits_cumulative').reindex(index, fill_value=0).cumsum()).reset_index()
    format_data['monthly_total_edits'] = format_data.groupby('timestamp')['nEdits_cumulative'].transform('sum')
    format_data['edits%'] = (format_data['nEdits_cumulative'] / format_data['monthly_total_edits']) * 100
    format_data = format_data.sort_values(['timestamp', 'edits%'], ascending=[True, False])
    format_data['edits%accum'] = format_data.groupby('timestamp')['edits%'].cumsum()
    format_data = format_data[format_data['edits%'] > 0]
    monthly_total_users = format_data.groupby('timestamp').size().reindex(index).fillna(0)
	
    p = [1 for j in range(1, len(format_data.index)+1)]
    format_data['count'] = p
    format_data['count_acum'] = format_data.groupby('timestamp')['count'].cumsum()

    category_50 = (format_data[format_data['edits%accum'] >= 50]).groupby('timestamp').head(1)
    category_50 = category_50.set_index(category_50['timestamp']).reindex(index).fillna(0)['count_acum']
    category_50= ((category_50 / monthly_total_users)*100).fillna(0)

    category_80 = (format_data[(format_data['edits%accum'] >=80)]).groupby('timestamp').head(1)
    category_80 = category_80.set_index(category_80['timestamp']).reindex(index).fillna(0)['count_acum']
    category_80 = ((category_80 / monthly_total_users)*100).fillna(0)

    category_90 = (format_data[(format_data['edits%accum'] >=90)]).groupby('timestamp').head(1)
    category_90 = category_90.set_index(category_90['timestamp']).reindex(index).fillna(0)['count_acum']
    category_90 = ((category_90 / monthly_total_users)*100).fillna(0)

    category_99 = (format_data[(format_data['edits%accum'] >=99)]).groupby('timestamp').head(1)
    category_99 = category_99.set_index(category_99['timestamp']).reindex(index).fillna(0)['count_acum']
    category_99 = ((category_99 / monthly_total_users)*100).fillna(0)
	
    category_rest = (format_data[(format_data['edits%accum'] > 99)]).groupby('timestamp').head(1)
    category_rest = category_rest.set_index(category_rest['timestamp']).reindex(index).fillna(0)['count_acum']
    category_rest = ((category_rest / monthly_total_users)*100).fillna(0)

    category_50.name = "50% of edits"
    category_80.name = "80% of edits"
    category_90.name = "90% of edits"
    category_99.name = "99% of edits"
    category_rest.name = "100% of edits"

    return[category_50, category_80, category_90, category_99, category_rest]
	
def contributor_pctg_per_contributions_pctg_per_month(data, index):

    data = filter_anonymous(data)
    #index = data.groupby(pd.Grouper(key='timestamp', freq='MS')).size().to_frame('months').index
    format_data = data.groupby(['contributor_id',pd.Grouper(key = 'timestamp', freq = 'MS')]).size().to_frame('medits').reset_index()
    format_data['monthly_total_edits'] = format_data.groupby('timestamp')['medits'].transform('sum')
    format_data['edits%'] = (format_data['medits'] / format_data['monthly_total_edits']) * 100
    format_data = format_data.sort_values(['timestamp', 'edits%'], ascending=[True, False])
    format_data['edits%accum'] = format_data.groupby('timestamp')['edits%'].cumsum()
    monthly_total_users = format_data.groupby('timestamp').size().reindex(index).fillna(0)

    p = [1 for j in range(1, len(format_data.index)+1)]
    format_data['count'] = p
    format_data['count_acum'] = format_data.groupby('timestamp')['count'].cumsum()

    category_50 = (format_data[format_data['edits%accum'] >= 50]).groupby('timestamp').head(1)
    category_50 = category_50.set_index(category_50['timestamp']).reindex(index).fillna(0)['count_acum']
    category_50= ((category_50 / monthly_total_users)*100).fillna(0)

    category_80 = (format_data[(format_data['edits%accum'] >=80)]).groupby('timestamp').head(1)
    category_80 = category_80.set_index(category_80['timestamp']).reindex(index).fillna(0)['count_acum']
    category_80 = ((category_80 / monthly_total_users)*100).fillna(0)

    category_90 = (format_data[(format_data['edits%accum'] >=90)]).groupby('timestamp').head(1)
    category_90 = category_90.set_index(category_90['timestamp']).reindex(index).fillna(0)['count_acum']
    category_90 = ((category_90 / monthly_total_users)*100).fillna(0)

    category_99 = (format_data[(format_data['edits%accum'] >=99)]).groupby('timestamp').head(1)
    category_99 = category_99.set_index(category_99['timestamp']).reindex(index).fillna(0)['count_acum']
    category_99 = ((category_99 / monthly_total_users)*100).fillna(0)
	
    category_rest = (format_data[(format_data['edits%accum'] > 99)]).groupby('timestamp').head(1)
    category_rest = category_rest.set_index(category_rest['timestamp']).reindex(index).fillna(0)['count_acum']
    category_rest = ((category_rest / monthly_total_users)*100).fillna(0)

    category_50.name = "50% of edits"
    category_80.name = "80% of edits"
    category_90.name = "90% of edits"
    category_99.name = "99% of edits"
    category_rest.name = "100% of edits"

    return[category_50, category_80, category_90, category_99, category_rest]

