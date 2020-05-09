import pandas as pd 
import matplotlib.pyplot as plt

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import time

print('Starting up ...')

# initialize main variables
stats = {}
sleep_duration = 2
nap_duration = 0.5

# initialize login credentials
email_cred = 'YOUR_USERNAME_OR_EMAIL'
pass_cred = 'YOUR_PASSWORD'

# start webdriver
options = Options()
options.headless = True
driver = webdriver.Chrome('/usr/bin/chromedriver', options=options)

driver.get('https://medium.com/me/stats')

print('Setting login method ...')

# choose twitter
WebDriverWait(driver, 10).until(
    lambda driver: driver.find_element_by_xpath('//*[@data-action="twitter-auth"]')).click()

print("Logging in ...")

# fill out login form
username = WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath('//*[@id="username_or_email"]'))
password = WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath('//*[@id="password"]'))
login = WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath('//*[@id="allow"]'))

time.sleep(sleep_duration)
username.clear()
username.send_keys(email_cred)

time.sleep(nap_duration)
password.clear()
password.send_keys(pass_cred)

time.sleep(nap_duration)
login.click()

print("Authenticated succesfully!")

time.sleep(sleep_duration)

print("Parsing Medium stats ...")

# get stats table
stats_table = WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath('/html/body/div[1]/div[2]/div/div[3]/div/div[4]/table'))

time.sleep(sleep_duration)

# scroll a couple of times to make sure the whole table is rendered
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(nap_duration)
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(nap_duration)

current_year = 0
# loop through table rows retrieving the data and adding it to our stats dictionary
for row in stats_table.find_elements_by_tag_name('tr'):
    if (len(row.get_attribute('class')) > 0):
        if ('sortableTable-row--dateBucket' in row.get_attribute('class')): # when encountering a year row
            for cell in row.find_elements_by_tag_name('td'):
                current_year = cell.text
                stats[current_year] = []
        elif ('js-statsTableRow' in row.get_attribute('class')): # when encountering a story
            td_idx = 1
            story = {}
            for cell in row.find_elements_by_tag_name('td'):
                if td_idx == 1: story['title'] = cell.text
                elif td_idx == 2: story['views'] = cell.find_elements_by_class_name('sortableTable-value')[0].get_attribute("innerHTML")
                elif td_idx == 3: story['reads'] = cell.find_elements_by_class_name('sortableTable-value')[0].get_attribute("innerHTML")
                elif td_idx == 4: story['ratio'] = cell.text
                elif td_idx == 5: story['fans'] = cell.find_elements_by_class_name('sortableTable-value')[0].get_attribute("innerHTML")
                td_idx += 1
            stats[current_year].append(story)

# calculate the total number of views
total_views = 0
for year in stats.keys():
    for story in stats[year]:
        total_views += int(story['views'])

print('Total Number of Views: %s' % (total_views))

print('Processing and plotting data ...')

# create a list of dataframes for each year
df_yearly = []
for year in stats.keys():
    # create dataframe
    tmp_df = pd.DataFrame(stats[year])
    # add 'year' column to dataframe
    tmp_df['year'] = year
    df_yearly.append(tmp_df)

# combine all yearly dataframes into one dataframe
df = pd.concat(df_yearly)
# reverse dataframe so that oldest story has the smallest index
df = df.iloc[::-1]
# reset index to remove overlapping indices across dataframes
df.reset_index(drop=True, inplace=True)

# convert numeric data types to float
df['views'] = df['views'].astype(float)
df['reads'] = df['reads'].astype(float)
df['fans'] = df['fans'].astype(float)

# add cumulative sum columns to the dataframe
df['views_cumsum'] = df['views'].cumsum()
df['reads_cumsum'] = df['reads'].cumsum()
df['fans_cumsum'] = df['fans'].cumsum()

# set up our plots
fig, axes = plt.subplots(nrows=2, ncols=3)
df['views_cumsum'].plot(ax=axes[0,0], title='Views Over Time', c='blue', grid=True).set(ylabel='# of Views')
df['reads_cumsum'].plot(ax=axes[0,1], title='Reads Over Time', c='green', grid=True).set(ylabel='# of Reads')
df['fans_cumsum'].plot(ax=axes[0,2], title='Fans Over Time', c='red', grid=True).set(ylabel='# of Fans')
df[['reads', 'fans']].plot(ax=axes[1,0], title='Reads/Fans by Story', kind='bar', stacked=True, grid=True).legend(['# of Reads', '# of Fans'])
df[['reads_cumsum', 'fans_cumsum']].plot.area(ax=axes[1,1], title='Views/Fans Over Time', grid=True).legend(['# of Reads', '# of Fans'])
df.groupby('year')['views'].sum().plot.bar(ax=axes[1,2], x='year', y='views', title='Yearly Views', grid=True)

# set subplot style
plt.tight_layout(pad=1.5)

plt.show()