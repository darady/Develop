import streamlit as st
import pandas as pd
from io import StringIO
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import numpy as np
from io import BytesIO
import math
from pathlib import Path
import altair as alt
from datetime import datetime, timedelta
import requests

# from streamlit_tags import st_tags, st_tags_sidebar

st.sidebar.title('Naver place data analysis')

st.sidebar.divider()
st.sidebar.write('### Choose a ranking data file')
ranking_file = st.sidebar.file_uploader('', key='ranking_file')

st.sidebar.write('### Choose a save data file')
save_file = st.sidebar.file_uploader('', key='save_file')

def backupData(ranking_df, save_df):
    if not os.path.exists('backup'):
        os.makedirs('backup')
    
    if (ranking_df is not None):
        ranking_df.to_csv('backup/ranking.csv', index = False)
    
    if (save_df is not None):
        save_df.to_csv('backup/save.csv', index = False)

backup_ranking_path = 'https://raw.githubusercontent.com/darady/Develop/main/backup/ranking.csv'
backup_save_path = 'https://raw.githubusercontent.com/darady/Develop/main/backup/save.csv'

@st.cache_data
def initRankingDf(ranking_file):
    ranking_df = None
    if ranking_file is not None:
        ranking_df = pd.read_csv(ranking_file)

        itemList = []
        for index in range(len(ranking_df.columns)):
            itemList.append(ranking_df.columns[index])

        itemDf = pd.DataFrame(columns=itemList)
        itemDf.loc[0] = itemList

        ranking_df = pd.concat([itemDf, ranking_df], ignore_index=True)
    else:
        ranking_df = pd.read_csv(backup_ranking_path)
    return ranking_df

@st.cache_data
def initSaveDf(save_file):
    save_df = None
    if save_file is not None:
        save_df = pd.read_csv(save_file)

        itemList = []
        for index in range(len(save_df.columns)):
            itemList.append(save_df.columns[index])

        itemDf = pd.DataFrame(columns=itemList)
        itemDf.loc[0] = itemList

        save_df = pd.concat([itemDf, save_df], ignore_index=True)
    else:
        save_df = pd.read_csv(backup_save_path)

    return save_df

ranking_df = initRankingDf(ranking_file)
save_df = initSaveDf(save_file)

def isna(x):
    return x != x

#N사_플레이스 순위 체크,	그룹	검색어	매칭값	플레이스명	메모	등록일	07-12	07-11	07-10	07-09
#-----	, 선재안남	서울용산맛집	https://m.place.naver.com/restaurant/1235024042/home	안남 신용산점		2024-06-26 12:14:46	-	170위	188위	185위

class RankingData:
    def __init__(self, key, group, searchWord, matchingValue, placeName, dateList, rankingList, saveList, blogList, visitList):
        self.key = key
        self.group = group
        self.searchWord = searchWord
        self.matchingValue = matchingValue
        self.placeName = placeName
        self.dateList = dateList
        self.rankingList = rankingList
        self.saveList = saveList
        self.blogList = blogList
        self.visitList = visitList


@st.cache_data
def parseRankingDf(ranking_df):
    resultList = list()
    dataIndex = 0

    for index in range(len(ranking_df.index)):
        if (len(ranking_df.index) <= index):
            break

        rawData = ranking_df[dataIndex:dataIndex+5]

        dateList = list()
        rankingList = list()
        saveList = list()
        blogList = list()
        visitList = list()

        if len(rawData.index) <= 1:
            break

        for idx in range(len(rawData.columns)):
            if idx+7 >= len(rawData.columns):
                continue
            
            dateStr = rawData.iloc[0, idx+7]
            rankingStr = rawData.iloc[1, idx+7]
            saveStr = rawData.iloc[2, idx+7]
            blogStr = rawData.iloc[3, idx+7]
            visitStr = rawData.iloc[4, idx+7]

            if rankingStr == 'nan' or rankingStr is None or isna(rankingStr) or rankingStr == '-':
                rankingStr = '-1'
                dataStr = '-'
            rankingStr = re.sub('위','', rankingStr)

            if saveStr == 'nan' or saveStr is None or isna(saveStr) or saveStr == '-':
                saveStr = '-1'
            saveStr = re.sub('\+','', saveStr)
            saveStr = re.sub(',','', saveStr)

            if blogStr == 'nan' or blogStr is None or isna(blogStr) or blogStr == '-':
                blogStr = '-1'
            blogStr = re.sub('블 ','', blogStr)
            blogStr = re.sub(',','', blogStr)
            blogStr = re.sub('개','', blogStr)

            if visitStr == 'nan' or visitStr is None or isna(visitStr) or visitStr == '-':
                visitStr = '-1'
            visitStr = re.sub('방 ','', visitStr)
            visitStr = re.sub(',','', visitStr)
            visitStr = re.sub('개','', visitStr)

            #rawData.iloc[1, 2]

            dateList.append(dateStr)
            rankingList.append(int(rankingStr))

            try:
                saveList.append(int(saveStr))
            except Exception as e:
                saveList.append(-1)
            
            try:
                blogList.append(int(blogStr))
            except Exception as e:
                blogList.append(-1)

            try:
                visitList.append(int(visitStr))
            except Exception as e:
                visitList.append(-1)
            
            #saveList.append(int(saveStr))
            #blogList.append(int(blogStr))
            #visitList.append(int(visitStr))

        rankingData = RankingData(rawData.iloc[1, 6], rawData.iloc[1, 1], rawData.iloc[1, 2]
                                  , rawData.iloc[1, 3], rawData.iloc[1, 4], dateList, rankingList, saveList, blogList, visitList)
        resultList.append(rankingData)

        dataIndex += 6
    return resultList

# rankingDataList = parseRankingDf(ranking_df)

if ranking_df is not None:
    rankingDataList = parseRankingDf(ranking_df)

    placeNameList = list()
    for index in range(len(rankingDataList)):
        placeName = rankingDataList[index].placeName

        if isna(placeName):
            continue
        
        placeNameList.append(placeName)

    placeNameList = list(set(placeNameList))
    st.write('# 플레이스 순위 정보')

    selctedPlaceName = st.selectbox(
        "플레이스 선택",
        placeNameList
    )

    rankingDatas = list()
    rankingKewards = list()

    #make ranking chart
    st.write('#### 키워드 랭킹')

    rankingChartDf = pd.DataFrame()

    for index in range(len(rankingDataList)):
        if (selctedPlaceName == rankingDataList[index].placeName):
            searchWord = rankingDataList[index].searchWord
            dateList = rankingDataList[index].dateList

            rankingList = rankingDataList[index].rankingList
            saveList = rankingDataList[index].saveList
            blogList = rankingDataList[index].blogList
            visitList = rankingDataList[index].visitList
            
            beforeSaveData = -1
            for idx in range(len(rankingList)):
                currentDate = dateList[idx]

                if beforeSaveData < 0:
                    beforeSaveData = saveList[idx]
                
                if saveList[idx] < 0:
                    saveList[idx] = beforeSaveData

                if rankingList[idx] >= 0:
                    itemDf = pd.DataFrame({'keyword' : [ searchWord ],
                            'date' : [ currentDate ],
                            'ranking' : [ rankingList[idx] ],
                            'save' : [ saveList[idx] ],
                            'gap' : [ beforeSaveData - saveList[idx] ],
                            'blog' : [ blogList[idx] ],
                            'visit' : [ visitList[idx] ]})
                    rankingChartDf = pd.concat([rankingChartDf, itemDf], ignore_index=True)

                    beforeSaveData = saveList[idx]
    #         keyword    keyword2
    # date     ranking      1
    # date2       2         2

    #       키워드          날짜    랭킹
    # 0     움복산맛집       5-12    1
    # 1     성수맛집        5-12    2
    # 1     성수맛집        5-13    1

    #rankingChartDf

    highlight = alt.selection_point(on='pointerover', fields=['keyword'], nearest=True)

    #Create a common chart object
    chart = alt.Chart(rankingChartDf).encode(
        alt.Color("keyword").legend(None)
    ).properties(width=800, height=350)

    # Draw the line
    line = chart.mark_line().encode(
        x="date:T",
        y=alt.Y('ranking:Q').sort('descending'),
        size=alt.condition(~highlight, alt.value(1), alt.value(2))
    )

    # Use the `argmax` aggregate to limit the dataset to the final value
    label = chart.encode(
        x='max(date):T',
        y=alt.Y('ranking:Q').aggregate(argmax='date'),
        text='keyword'
    )

    # Create a text label
    text = label.mark_text(align='left', dx=4, fontSize=10)

    # Create a circle annotation
    # circle = label.mark_circle()
    circle = label.mark_circle().encode(
        opacity=alt.value(0)
    ).add_params(
        highlight
    )  
    
    # Draw the chart with all the layers combined
    line + circle + text


    #save chart
    st.write('#### 네이버 저장하기')

    highlight = alt.selection_point(on='pointerover', fields=['keyword'], nearest=True)

    # Create a common chart object
    chart = alt.Chart(rankingChartDf).encode(
        alt.Color("keyword").legend(None)
    ).properties(width=800, height=350)

    # Draw the line
    line = chart.mark_line().encode(
        x="date:T",
        y="save:Q",
        size=alt.condition(~highlight, alt.value(1), alt.value(3))
    )

    # Use the `argmax` aggregate to limit the dataset to the final value
    label = chart.encode(
        x='max(date):T',
        y=alt.Y('save:Q').aggregate(argmax='date'),
        text='keyword'
    )

    # Create a text label
    text = label.mark_text(align='left', dx=4)

    # Create a circle annotation
    # circle = label.mark_circle()
    circle = label.mark_circle().encode(
        opacity=alt.value(0)
    ).add_params(
        highlight
    )  
    
    # Draw the chart with all the layers combined
    line + circle + text

    # Create a common chart object
    chart = alt.Chart(rankingChartDf).encode(
        alt.Color("keyword").legend(None)
    ).properties(width=800, height=350)

    # Draw the line
    line = chart.mark_bar().encode(
        x="date:T",
        y="gap:Q"
    )

    # Use the `argmax` aggregate to limit the dataset to the final value
    label = chart.encode(
        x='max(date):T',
        y=alt.Y('gap:Q').aggregate(argmax='date'),
        text='keyword'
    )

    # Create a text label
    text = label.mark_text(align='left', dx=4)

    # Create a circle annotation
    # circle = label.mark_circle()
    circle = label.mark_circle().encode(
        opacity=alt.value(0)
    ).add_params(
        highlight
    )  
    
    # Draw the chart with all the layers combined
    line + circle + text

    #blog chart
    st.write('#### 블로그')

    highlight = alt.selection_point(on='pointerover', fields=['keyword'], nearest=True)

    # Create a common chart object
    chart = alt.Chart(rankingChartDf).encode(
        alt.Color("keyword").legend(None)
    ).properties(width=800, height=350)

    # Draw the line
    line = chart.mark_line().encode(
        x="date:T",
        y="blog:Q",
        size=alt.condition(~highlight, alt.value(1), alt.value(3))
    )

    # Use the `argmax` aggregate to limit the dataset to the final value
    label = chart.encode(
        x='max(date):T',
        y=alt.Y('blog:Q').aggregate(argmax='date'),
        text='keyword'
    )

    # Create a text label
    text = label.mark_text(align='left', dx=4)

    # Create a circle annotation
    # circle = label.mark_circle()
    circle = label.mark_circle().encode(
        opacity=alt.value(0)
    ).add_params(
        highlight
    )  
    
    # Draw the chart with all the layers combined
    line + circle + text

    #visit chart
    st.write('#### 방문자 리뷰')

    highlight = alt.selection_point(on='pointerover', fields=['keyword'], nearest=True)

    # Create a common chart object
    chart = alt.Chart(rankingChartDf).encode(
        alt.Color("keyword").legend(None)
    ).properties(width=800, height=350)

    # Draw the line
    line = chart.mark_line().encode(
        x="date:T",
        y="visit:Q",
        size=alt.condition(~highlight, alt.value(1), alt.value(3))
    )

    # Use the `argmax` aggregate to limit the dataset to the final value
    label = chart.encode(
        x='max(date):T',
        y=alt.Y('visit:Q').aggregate(argmax='date'),
        text='keyword'
    )

    # Create a text label
    text = label.mark_text(align='left', dx=4)

    # Create a circle annotation
    # circle = label.mark_circle()
    circle = label.mark_circle().encode(
        opacity=alt.value(0)
    ).add_params(
        highlight
    )  
    
    # Draw the chart with all the layers combined
    line + circle + text



#N사_플레이스 저장 체크	검색어	매칭값	플레이스명	메모	등록일	07-01	06-24
#-----	성수우동	https://m.place.naver.com/restaurant/1268725018/home?entry=pl	니카이 우동		2024-06-24 13:41:56	15,000+	14,000+
class SaveData:
    def __init__(self, key, searchWord, matchingValue, placeName, dateList, saveList, blogNumList, visitNumList):
        self.key = key
        self.searchWord = searchWord
        self.matchingValue = matchingValue
        self.placeName = placeName
        self.dateList = dateList
        self.saveList = saveList
        self.blogNumList = blogNumList
        self.visitNumList = visitNumList


@st.cache_data
def parseSaveDf(save_df):
    resultList = list()
    dataIndex = 0

    # itemList = []
    # for index in range(len(save_df.columns)):
    #     itemList.append(save_df.columns[index])

    # itemDf = pd.DataFrame(columns=itemList)
    # itemDf.loc[0] = itemList

    # save_df = pd.concat([itemDf, save_df], ignore_index=True)

    for index in range(len(save_df.index)):
        if (len(save_df.index) <= index):
            break

        rawData = save_df[dataIndex:dataIndex+4]

        dateList = list()
        saveList = list()
        blogList = list()
        visitList = list()

        if len(rawData.index) <= 1:
            break

        for idx in range(len(rawData.columns)):
            if idx+7 >= len(rawData.columns):
                continue
            
            dateStr = rawData.iloc[0, idx+7]
            saveStr = rawData.iloc[1, idx+7]
            blogStr = rawData.iloc[2, idx+7]
            visitStr = rawData.iloc[3, idx+7]

            if saveStr == 'nan' or saveStr is None or isna(saveStr) or saveStr == '-':
                saveStr = '-1'
                dataStr = '-'
            saveStr = re.sub('\+','', saveStr)
            saveStr = re.sub(',','', saveStr)

            if blogStr == 'nan' or blogStr is None or isna(blogStr) or blogStr == '-':
                blogStr = '-1'
            blogStr = re.sub('블 ','', blogStr)
            blogStr = re.sub(',','', blogStr)
            blogStr = re.sub('개','', blogStr)

            if visitStr == 'nan' or visitStr is None or isna(visitStr) or visitStr == '-':
                visitStr = '-1'
            visitStr = re.sub('방 ','', visitStr)
            visitStr = re.sub(',','', visitStr)
            visitStr = re.sub('개','', visitStr)

            dateList.append(dateStr)
            saveList.append(int(saveStr))

            try:
                blogList.append(int(blogStr))
            except Exception as e:
                blogList.append(-1)

            try:
                visitList.append(int(visitStr))
            except Exception as e:
                visitList.append(-1)
        
        saveData = SaveData(rawData.iloc[1, 6], rawData.iloc[1, 2], rawData.iloc[1, 3]
                                  , rawData.iloc[1, 4], dateList, saveList, blogList, visitList)
        resultList.append(saveData)

        dataIndex += 5
    return resultList

if save_df is not None:
    saveDataList = parseSaveDf(save_df)

    placeNameList = list()
    for index in range(len(saveDataList)):
        placeName = saveDataList[index].placeName

        if isna(placeName):
            continue
        
        placeNameList.append(placeName)

    placeNameList = list(set(placeNameList))

    st.write('# Save data')

    selctedPlaceName = st.selectbox(
        "Select Place name",
        placeNameList
    )

    saveDatas = list()
    saveKewards = list()

    saveChartDf = pd.DataFrame()

    # # N사_플레이스 저장 체크_전체_20240704.csv
    # date = re.sub('N사_플레이스 저장 체크_전체_','', save_file.name)
    # date = re.sub('.csv','', date)

    # # st.write(date)

    # date = datetime.strptime(date, '%Y%m%d')
    
    # st.write(date)
    # datesData = list()
    # for index in range(len(rankingDataList[0].rankingList)):
    #     datesData.append(date+timedelta(days=index))
    # rankingChartDf['date'] = datesData

    # for index in range(len(rankingDataList)):
    #     if (selctedPlaceName == rankingDataList[index].placeName):
    #         rankingChartDf[rankingDataList[index].searchWord] = rankingDataList[index].rankingList

    for index in range(len(saveDataList)):
        if (selctedPlaceName == saveDataList[index].placeName):
            searchWord = saveDataList[index].searchWord
            saveList = saveDataList[index].saveList
            dateList = saveDataList[index].dateList
            
            beforeSaveData = -1
            for idx in range(len(saveList)):
                if saveList[idx] >= 0:

                    currentDate = datetime.strptime(dateList[idx], '%m-%d')
                    if beforeSaveData < 0:
                        beforeSaveData = saveList[idx]

                    itemDf = pd.DataFrame({'keyword' : [ searchWord ],
                            'date' : [ currentDate ],
                            'save' : [ saveList[idx] ],
                            'gap' : [ beforeSaveData - saveList[idx] ]})
                    saveChartDf = pd.concat([saveChartDf, itemDf], ignore_index=True)

                    beforeSaveData = saveList[idx]
    # saveChartDf

    highlight = alt.selection_point(on='pointerover', fields=['keyword'], nearest=True)

    # Create a common chart object
    chart = alt.Chart(saveChartDf).encode(
        alt.Color("keyword").legend(None)
    ).properties(width=800, height=350)

    # Draw the line
    line = chart.mark_line().encode(
        x="date:T",
        y="save:Q",
        size=alt.condition(~highlight, alt.value(1), alt.value(3))
    )

    # Use the `argmax` aggregate to limit the dataset to the final value
    label = chart.encode(
        x='max(date):T',
        y=alt.Y('save:Q').aggregate(argmax='date'),
        text='keyword'
    )

    # Create a text label
    text = label.mark_text(align='left', dx=4)

    # Create a circle annotation
    # circle = label.mark_circle()
    circle = label.mark_circle().encode(
        opacity=alt.value(0)
    ).add_params(
        highlight
    )  
    
    # Draw the chart with all the layers combined
    line + circle + text

    # Create a common chart object
    chart = alt.Chart(saveChartDf).encode(
        alt.Color("keyword").legend(None)
    ).properties(width=800, height=350)

    # Draw the line
    line = chart.mark_bar().encode(
        x="date:T",
        y="gap:Q"
    )

    # Use the `argmax` aggregate to limit the dataset to the final value
    label = chart.encode(
        x='max(date):T',
        y=alt.Y('gap:Q').aggregate(argmax='date'),
        text='keyword'
    )

    # Create a text label
    text = label.mark_text(align='left', dx=4)

    # Create a circle annotation
    # circle = label.mark_circle()
    circle = label.mark_circle().encode(
        opacity=alt.value(0)
    ).add_params(
        highlight
    )  
    
    # Draw the chart with all the layers combined
    line + circle + text

backup_button = st.sidebar.button('Backup')
if backup_button:
    backupData(ranking_df, save_df)

# make ranking grape



# get select box data

# ranking_df.shape

# get selected data





#data 


# ranking_df
# save_df


# data_urls = ranking_df[0:1]

# data_urls

# data_urls = ranking_df[3:4]

# data_urls





# if uploaded_file is not None:
#     resultDf = initResulttDf(df)

# if uploaded_file is not None:
#     st.write('## ' + uploaded_file.name + ' raw data')
#     df
# else:
#     st.write('## Choose a CSV file')
#     'no data'

# st.sidebar.divider()
# st.sidebar.write('### Blogdex data crawling')

# @st.cache_data
# def getBlogdexData(df):
#     data_urls = df['계정URL']
#     # st.write(data_urls.count())
#     progress_bar = st.sidebar.progress(0)

#     co = Options()
#     co.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
#     driver = webdriver.Chrome(options=co)

#     for idx in range(data_urls.count()):
#         data_url = data_urls[idx]

#         #https://m.blog.naver.com/hyooo88_
#         #https://m.blog.naver.com/PostList.naver?blogId=greatting_&tab=1
#         #https://oiuio.tistory.com/, http://blog.naver.com/grkcolour
#         # data_url = data_url.sub('https://m.blog.naver.com/','')
#         # data_url = data_url.sub('https://','')
#         # data_url = data_url.sub('&tab=1','')
#         # data_url = data_url.sub('/','')
        
#         data_url = re.sub('https://m.blog.naver.com/','', data_url)
#         data_url = re.sub('http://m.blog.naver.com/','', data_url)
#         data_url = re.sub('https://blog.naver.com/','', data_url)
#         data_url = re.sub('http://blog.naver.com/','', data_url)
#         data_url = re.sub('https://','', data_url)
#         data_url = re.sub('&tab=1','', data_url)
#         data_url = re.sub('PostList.naver\?blogId=','', data_url)
#         data_url = re.sub('/','', data_url)

#         # data_url

#         url = "https://blogdex.space/blog-index/" + data_url
#         driver.get(url)

#         driver.implicitly_wait(10)

#         try:
#             div_1 = driver.find_element(By.XPATH, "//*[@id='__next']/div[1]/main/div/div[2]/div[1]/div[2]/div[1]/div[3]/div[1]/div/div/p")
#             div_2 = driver.find_element(By.XPATH, "//*[@id='__next']/div[1]/main/div/div[2]/div[1]/div[2]/div[1]/div[3]/div[2]/div/div/p")
#             div_3 = driver.find_element(By.XPATH, "//*[@id='__next']/div[1]/main/div/div[2]/div[1]/div[2]/div[1]/div[3]/div[3]/div/div/p")
#             div_4 = driver.find_element(By.XPATH, "//*[@id='__next']/div[1]/main/div/div[2]/div[1]/div[2]/div[3]/div[1]/div/div")
#             div_5 = driver.find_element(By.XPATH, "//*[@id='__next']/div[1]/main/div/div[2]/div[1]/div[2]/div[7]/div/div[1]/p")                                                       

#             df.loc[int(idx), '주제지수'] = div_1.text
#             df.loc[int(idx), '종합지수'] = div_2.text
#             df.loc[int(idx), '최고지수'] = div_3.text
#             df.loc[int(idx), '총구독자'] = div_4.text
#             df.loc[int(idx), '최적화수치'] = div_5.text
#         except Exception as e:
#             print(e)
               
#         progress_bar.progress(int((idx + 1) * 100 / data_urls.count()))
#     driver.quit()
#     return df


# st.divider()
# st.write('## Result data')

# if 'completeData' not in st.session_state:
#     st.session_state['completeData'] = 0

# if st.session_state['completeData'] == 1:
#     resultDf = st.session_state['resultDf']
#     resultDf
# else:
#     start_button = st.sidebar.button('start')
#     if start_button:
#         resultDf = getBlogdexData(resultDf)
#         st.session_state['completeData'] = 1
#         st.session_state['resultDf'] = resultDf
#         resultDf
#     else:
#         'no data'
  
# st.divider()
# st.write('## Save result data')

# def to_excel(df):
#     output = BytesIO()
#     writer = pd.ExcelWriter(output, engine='xlsxwriter')
#     df.to_excel(writer, index=False, sheet_name='Sheet1')
#     workbook = writer.book
#     worksheet = writer.sheets['Sheet1']
#     format1 = workbook.add_format({'num_format': '0.00'}) 
#     worksheet.set_column('A:A', None, format1)  
#     writer.close()
#     processed_data = output.getvalue()
#     return processed_data

# col1, col2 = st.columns(2)

# downlaod_filename = 'download file name'
# if uploaded_file is not None:
#     downlaod_filename = uploaded_file.name
#     downlaod_filename = re.sub('리뷰어','', downlaod_filename)
#     downlaod_filename = re.sub('.csv','.xlsx', downlaod_filename)

# with col1:
#     downlaod_filename = st.text_input(
#         "downloadfile name",
#         downlaod_filename,
#         key="",
#     )

# with col2:
#     if resultDf is not 'no data':
#         download_button = st.download_button('Download file', to_excel(resultDf), file_name = downlaod_filename)