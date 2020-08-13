import csv
import json
import math
import os
import random
import requests
import numpy as np
from matplotlib import cm
from matplotlib import axes
import matplotlib.pyplot as plt
from sympy.integrals.rubi.utility_function import Null
from snownlp import sentiment, SnowNLP

'''* * * * *'''
'''PART I: 爬取树洞信息'''
'''* * * * *'''

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
                  '63.0.3239.108 Safari/537.36'}


def createDir():
    isExists = os.path.exists('thuhole_ana')
    if not isExists:
        os.makedirs('thuhole_ana')
    isExists2 = os.path.exists('thuhole_ana/holes')
    if not isExists2:
        os.makedirs('thuhole_ana/holes')
    isExists3 = os.path.exists('thuhole_ana/comments')
    if not isExists3:
        os.makedirs('thuhole_ana/comments')


def getSingleHole(pid):
    res = requests.get('爬虫API不公布')
    # tokenId必须在全局变量中设置好，请检查当前tokenId是否可用
    res.encoding = 'utf-8'
    if res.status_code == 200:
        f = open('thuhole_ana/holes/' + str(pid) + '.json', 'w', encoding='utf-8')
        f.write(res.text)
        f.close()
    else:
        return
    res2 = requests.get('爬虫API不公布')
    res2.encoding = 'utf-8'
    if res2.status_code == 200:
        f2 = open('thuhole_ana/comments/' + str(pid) + '.json', 'w', encoding='utf-8')
        f2.write(res2.text)
        f2.close()
    else:
        return
    print(str(pid) + 'done')


def getRaw():
    # 判断文件夹是否存在
    createDir()
    for num in range(1, 37500):
        getSingleHole(num)
    # 理论上上述代码运行需约10h
    # 实际运行时是分为不同的段多脚本同时运行
    # 所用数据说明：截止2020年8月3日17时，包含1-37499的树洞和评论


'''爬取原始数据部分，请勿重复使用该脚本'''
# getRaw()
'''爬取原始数据结束'''

'''* * * * *'''
'''PART II: 消息的预处理（数据部分）'''
'''* * * * *'''

dealtDataList = []


def dealTag(tag):
    # 没tag 0；性 1；政治 2；nsfw 3；其他 4
    if tag == Null or len(tag) == 0:
        return 0
    if tag == '性相关' or tag == '性话题':
        return 1
    if tag == '政治相关' or tag == '政治话题':
        return 2
    if tag == 'NSFW':
        return 3
    return 4


def getCited(content):
    for newt in range(len(content)):
        if content[newt] == '#':
            total = 0
            for j in range(newt + 1, len(content)):
                if content[j].isdigit():
                    total *= 10
                    total += int(content[j])
                else:
                    break
            if total < len(dealtDataList) - 1:
                dealtDataList[total - 1][3] += 1
    return


def dealSingleHole(pid):
    fp = open('thuhole_ana/holes/' + str(pid) + '.json', 'r', encoding='utf8')
    json_data = json.load(fp)
    # dealtItem: code, likenum, reply, cited, tag, textLength
    # , withPic, timeDate, timeMod, pid
    dealtItem = [1, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    dealtItem[9] = pid
    if json_data['code'] == 0:
        dealtItem[0] = 0
        dealtItem[1] = json_data['data']['likenum']
        dealtItem[2] = json_data['data']['reply']
        dealtItem[4] = dealTag(json_data['data']['tag'])
        dealtItem[5] = len(json_data['data']['text'])
        # 有pic时withPic是1
        if len(json_data['data']['url']) > 0:
            dealtItem[6] = 1
        # 时间戳以6月16日4点为起始，分别对一日秒数
        dealtItem[7] = int(((json_data['data']['timestamp']) - 1592251200) / 86400)
        dealtItem[8] = ((json_data['data']['timestamp']) - 1592251200) % 86400
        getCited(json_data['data']['text'])
    dealtDataList.append(dealtItem)
    fp.close()
    return


'''在PART II中执行的代码'''
# for i in range(1, 37500):
#     dealSingleHole(i)
#     print(i)
# fileRaw = open('thuhole_ana/raw.txt', 'w')
# fileRaw.write(str(dealtDataList))
'''预处理结束'''

'''* * * * *'''
'''PART III: 单变量分析'''
'''* * * * *'''

# 之前的数据处理

unDeleted = []


def savedJudge(arr):
    if arr[0] == 0:
        return True
    else:
        return False


# 抽取已被删除树洞的信息并重新整合
def dealWithDeleted():
    fileRaw = open('thuhole_ana/raw.txt', 'r')
    jsonRaw = json.load(fileRaw)
    deletedList = []
    for i in range(0, 37499):
        if not savedJudge(jsonRaw[i]):
            # 删除对象的时间戳由其前后两个对象的时间戳平均而成
            jsonRaw[i][7] = int((jsonRaw[i - 1][7] + jsonRaw[i + 1][7]) / 2)
            jsonRaw[i][8] = int((jsonRaw[i - 1][8] + jsonRaw[i + 1][8]) / 2)
            deletedList.append([jsonRaw[i][3], jsonRaw[i][7], jsonRaw[i][8], jsonRaw[i][9]])
    fileDel = open('thuhole_ana/analysisDeleted/rawDeleted.txt', 'w')
    fileDel.write(str(deletedList))
    fileDel.close()
    afterDeleted = list(filter(savedJudge, jsonRaw))
    for j in range(0, len(afterDeleted)):
        afterDeleted[j].pop(0)
        if afterDeleted[j][0] < 0:
            afterDeleted[j][0] = 0
    fileExist = open('thuhole_ana/analysisExisted/rawExisted.txt', 'w')
    fileExist.write(str(afterDeleted))
    fileExist.close()
    return afterDeleted


def analysisDeleted():
    fileDel = open('thuhole_ana/analysisDeleted/rawDeleted.txt', 'r')
    jsonDel = json.load(fileDel)
    # analysis cited numbers of the deleted hole
    plt.cla()
    citedStatic = []
    for i in range(0, len(jsonDel)):
        citedStatic.append(jsonDel[i][0])
    bins = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5]
    cited, _, _ = plt.hist(np.array(citedStatic),
                           bins, color='#e0e0f6')
    plt.xlabel('cited number')
    plt.ylabel('sum of holes')
    plt.plot([x - 0.5 for x in bins[1:]], cited, color='palevioletred')
    plt.title("Cited numbers of the deleted hole")
    plt.savefig('thuhole_ana/analysisDeleted/关注数直方图.png')
    # analysis date of the deleted hole
    plt.cla()
    dateStatic = []
    for i in range(0, len(jsonDel)):
        dateStatic.append(jsonDel[i][1])
    bins2 = range(0, 51, 5)
    date, _, _ = plt.hist(np.array(dateStatic),
                          bins2, color='#e0e0f6')
    plt.xlabel('days after the hole is created')
    plt.ylabel('sum of holes')
    plt.plot([x - 2.5 for x in bins2[1:]], date, color='palevioletred')
    plt.title("Numbers of days since created of the deleted hole")
    plt.savefig('thuhole_ana/analysisDeleted/日期直方图.png')
    # analysis time numbers of the deleted hole
    plt.cla()
    timeStatic = []
    for i in range(0, len(jsonDel)):
        timeStatic.append(jsonDel[i][2])
    bins3 = range(0, 86401, 7200)
    time, _, _ = plt.hist(np.array(timeStatic),
                          bins3, color='#e0e0f6')
    plt.xlabel('clock of the day started from 4:00am UTC+8 (sec)')
    plt.ylabel('sum of holes')
    plt.plot([x - 3600 for x in bins3[1:]], time, color='palevioletred')
    plt.title("Time interval of the deleted hole")
    plt.savefig('thuhole_ana/analysisDeleted/时间直方图.png')
    # analysis serial number of the deleted hole
    plt.cla()
    serialStatic = []
    for i in range(0, len(jsonDel)):
        serialStatic.append(jsonDel[i][2])
    bins4 = range(0, 37501, 2380)
    serial, _, _ = plt.hist(np.array(serialStatic),
                            bins4, color='#e0e0f6')
    plt.xlabel('serial number of the hole')
    plt.ylabel('sum of holes')
    plt.plot([x - 1190 for x in bins4[1:]], serial, color='palevioletred')
    plt.title("Serial number of the deleted hole")
    plt.savefig('thuhole_ana/analysisDeleted/序列直方图.png')
    plt.cla()
    return


# dealtItem: likenum, reply, cited, tag, textLength
# , withPic, timeDate, timeMod, pid

def analysisExisted():
    fileDel = open('thuhole_ana/analysisExisted/rawExisted.txt', 'r')
    jsonDel = json.load(fileDel)
    fileDel.close()

    # analysis date of the hole
    plt.cla()
    dateStatic = []
    dateTags = [[], [], [], []]
    for i in range(0, len(jsonDel)):
        dateStatic.append(jsonDel[i][6])
        if jsonDel[i][3] > 0:
            dateTags[jsonDel[i][3] - 1].append(jsonDel[i][6])
    bins2 = range(1, 50, 1)
    # plt.subplot(2, 2, 3)
    date, _, _ = plt.hist(np.array(dateStatic),
                          bins2, color='#e0e0f6')
    plt.xlabel('days after the hole is created')
    plt.ylabel('sum of holes')
    plt.plot([x - 0.5 for x in bins2[1:]], date, color='palevioletred')
    plt.title("Numbers of holes each day")

    # tag proportion of each date
    dateTagsResult = [[], [], [], []]
    for i in range(0, 4):
        dateTagsResult[i], _, _ = plt.hist(np.array(dateTags[i]), bins2,
                                           color='#ffffff')
    for i in range(0, 4):
        for j in range(len(dateTagsResult[0])):
            if date[j] == 0:
                dateTagsResult[i][j] = 0
            else:
                dateTagsResult[i][j] /= date[j]
    colorArray = ['orange', 'RoyalBlue', 'BlueViolet', 'LightCoral']
    labelArray = ['Sexual', 'Political', 'NSFW', 'Others']
    # plt.subplot(2, 2, 1)
    for i in range(0, 4):
        plt.plot(bins2[2:], dateTagsResult[i][1:], label=labelArray[i], color=colorArray[i])
        plt.legend(loc='upper left')
    plt.xlabel('proportion of different tags (since the second day after created)')
    plt.ylabel('proportion of holes of the tag each day')
    plt.title("Proportion of different tags each day")

    # analysis time numbers of the deleted hole
    # plt.subplot(2, 2, 4)
    timeStatic = []
    timeTags = [[], [], [], []]
    for i in range(0, len(jsonDel)):
        timeStatic.append(jsonDel[i][7])
        if jsonDel[i][3] > 0:
            timeTags[jsonDel[i][3] - 1].append(jsonDel[i][7])
    bins3 = range(0, 86401, 3600)
    time, _, _ = plt.hist(np.array(timeStatic),
                          bins3, color='#e0e0f6')
    plt.xlabel('clock of the day started from 4:00am UTC+8 (sec)')
    plt.ylabel('sum of holes')
    plt.plot([x - 1800 for x in bins3[1:]], time, color='palevioletred')
    plt.title("Time interval of the hole")

    # tag proportion of each time interval
    timeTagsResult = [[], [], [], []]
    for i in range(0, 4):
        timeTagsResult[i], _, _ = plt.hist(np.array(timeTags[i]), bins3,
                                           color='#ffffff')
    for i in range(0, 4):
        for j in range(len(timeTagsResult[0])):
            if date[j] == 0:
                timeTagsResult[i][j] = 0
            else:
                timeTagsResult[i][j] /= time[j]
    # plt.subplot(2, 2, 2)
    colorArray = ['orange', 'RoyalBlue', 'BlueViolet', 'LightCoral']
    labelArray = ['Sexual', 'Political', 'NSFW', 'Others']
    for i in range(0, 4):
        plt.plot(bins3[1:], timeTagsResult[i], label=labelArray[i], color=colorArray[i])
        plt.legend(loc='upper left')
    plt.xlabel('clock of the day started from 4:00am UTC+8 (sec)')
    plt.ylabel('proportion of holes of the tag each day')
    plt.title("Proportion of different tags each time interval")
    # plt.show()

    # analysis liking numbers of the hole
    plt.cla()
    likeStatic = []
    replyStatic = []
    citedStatic = []
    for i in range(0, len(jsonDel)):
        if jsonDel[i][0] >= 0:
            likeStatic.append(jsonDel[i][0])
        else:
            likeStatic.append(0)
        replyStatic.append(jsonDel[i][1])
        citedStatic.append(jsonDel[i][2])
    likeStatic.sort(reverse=True)
    likeAvg, likeMed = np.mean(likeStatic), np.median(likeStatic)
    replyStatic.sort(reverse=True)
    replyAvg, replyMed = np.mean(replyStatic), np.median(replyStatic)
    citedStatic.sort(reverse=True)
    citedAvg, citedMed = np.mean(citedStatic), np.median(citedStatic)
    for i in range(len(likeStatic)):
        likeStatic[i] = math.log(likeStatic[i] + 1)
        replyStatic[i] = math.log(replyStatic[i] + 1)
        citedStatic[i] = math.log(citedStatic[i] + 1)
    plt.subplot(2, 2, 1)
    plt.xlabel('number of the holes in this sort of order')
    plt.ylabel('ln(x+1), x refers to the amount')
    plt.plot(replyStatic, color='RoyalBlue',
             label='reply mean: ' + str(round(replyAvg, 1)) +
                   ' median: ' + str(round(replyMed, 1)))
    plt.legend(loc='upper right')
    plt.plot(likeStatic, color='gold',
             label='likes  mean: ' + str(round(likeAvg, 1)) +
                   ' median: ' + str(round(likeMed, 1)))
    plt.legend(loc='upper right')
    plt.plot(citedStatic, color='BlueViolet',
             label='cited mean: ' + str(round(citedAvg, 1)) +
                   ' median: ' + str(round(citedMed, 1)))
    plt.legend(loc='upper right')
    plt.title("Interaction data distribution of the hole")
    plt.savefig('thuhole_ana/analysisExisted/喜好数散点图.png')

    # analysis text length and whether with picture or not of the hole
    withPicLength, withPicPid = [], []
    noPicLength, noPicPid = [], []
    for i in range(0, len(jsonDel)):
        if jsonDel[i][5] == 1:
            if jsonDel[i][4] < 1500:
                withPicLength.append(jsonDel[i][4])
                withPicPid.append(jsonDel[i][8])
        else:
            if jsonDel[i][4] < 1500:
                noPicLength.append(jsonDel[i][4])
                noPicPid.append(jsonDel[i][8])
    withAvg, withMed = np.mean(withPicLength), np.median(withPicLength)
    noAvg, noMed = np.mean(noPicLength), np.median(noPicLength)
    plt.subplot(2, 2, 2)
    plt.scatter(noPicPid, noPicLength, 1, color='CornflowerBlue', alpha=0.8,
                label='without a picture mean: ' + str(round(noAvg, 1)) + ' median: ' + str(round(noMed, 1)))
    plt.legend(loc='upper right')
    plt.scatter(withPicPid, withPicLength, 1, color='Orchid', alpha=0.8,
                label='with a picture mean: ' + str(round(withAvg, 1)) + ' median: ' + str(round(withMed, 1)))
    plt.legend(loc='upper right')
    plt.xlabel('number of the hole')
    plt.ylabel('length of the text \n (over 1500 ones are excluded)')
    plt.title("Text length of the hole")

    return


'''在PART III中执行的代码'''
# III-1 分离被删除文章和未被删除树洞
# dealWithDeleted()
# III-2 分析被删除树洞
# analysisDeleted()
# III-3 分析未删除树洞的单一变量分布
# analysisExisted()
'''单变量分析结束'''

'''* * * * *'''
'''PART IV: 多变量分析'''
'''* * * * *'''


# dealtItem: likenum, reply, cited, tag, textLength
# , withPic, timeDate, timeMod, pid
# 事先预设：likenum, reply cited均表示互动，除了专门研究互动种类，没有必要分开处理
# tag为部分内容打上了标签，对于这一部分内容可以绕开文字先行分析
# 文字长度和是否有图片和互动的关系也值得研究

def analysisTagRelated():
    file = open('thuhole_ana/analysisExisted/rawExisted.txt', 'r')
    jsonFile = json.load(file)
    file.close()
    likeTags = [[], [], [], []]
    replyTags = [[], [], [], []]
    for i in range(0, len(jsonFile)):
        if jsonFile[i][3] > 0:
            likeTags[jsonFile[i][3] - 1].append(math.log(jsonFile[i][0] + 1 + (jsonFile[i][3] - 2) / 20))
            replyTags[jsonFile[i][3] - 1].append(math.log(jsonFile[i][1] + 1 + (jsonFile[i][3] - 2) / 20))
    colorArray = ['orange', 'Indigo', 'red', 'DarkGreen']
    labelArray = ['Sexual', 'Political', 'NSFW', 'Others']
    markers = ['.', ',', '^', 's']
    for i in range(0, 4):
        plt.scatter(likeTags[i], replyTags[i], 3,
                    label=labelArray[i], color=colorArray[i], marker=markers[i])
        plt.legend(loc='upper left')
    plt.xlabel('ln(x+1), x refers to the liking numbers of this hole')
    plt.ylabel('ln(y+1), y refers to the reply numbers of this hole')
    plt.title("Likes and reply numbers of the hole with tags")

    # analysis text length and whether with picture or not of the hole
    withPicLength, withPicInteraction = [], []
    noPicLength, noPicInteraction = [], []
    for i in range(0, len(jsonFile)):
        if jsonFile[i][5] == 1:
            withPicLength.append(math.log(jsonFile[i][4] + 1))
            withPicInteraction.append(math.log(jsonFile[i][0] + jsonFile[i][1] + jsonFile[i][2] + 1))
        else:
            noPicLength.append(math.log(jsonFile[i][4] + 1.05 + jsonFile[i][8] / 200000))
            noPicInteraction.append(math.log(jsonFile[i][0] + jsonFile[i][1] + jsonFile[i][2] + 1.05))
    plt.scatter(noPicLength, noPicInteraction, 1, color='CornflowerBlue', label='without a picture')
    plt.legend(loc='upper right')
    plt.scatter(withPicLength, withPicInteraction, 1, color='Orchid', label='with a picture')
    plt.legend(loc='upper right')
    plt.xlabel('ln(x+1), x refers to the text length of the hole')
    plt.ylabel('ln(y+1), y refers to total interaction numbers of this hole\n (likes + reply + cited)')
    plt.title("Relationship between interaction and text length")
    plt.savefig('thuhole_ana/analysisExisted/树洞字数长度与评论数的关系.png')

    return


def analysisTimeRelated():
    file = open('thuhole_ana/analysisExisted/rawExisted.txt', 'r')
    jsonFile = json.load(file)
    file.close()
    likeNumDate, likeNumClock = [], []
    replyDate, replyClock = [], []
    for i in range(0, 24):
        likeNumClock.append([])
        replyClock.append([])
    for j in range(0, 48):
        replyDate.append([])
        likeNumDate.append([])
    for k in range(len(jsonFile)):
        likeNumDate[jsonFile[k][6] - 1].append(jsonFile[k][0])
        replyDate[jsonFile[k][6] - 1].append(jsonFile[k][1])
        likeNumClock[int(jsonFile[k][7] / 3600)].append(jsonFile[k][0])
        replyClock[int(jsonFile[k][7] / 3600)].append(jsonFile[k][1])
    likeNumClock.extend(likeNumClock[:21])
    likeNumClock = likeNumClock[21:]
    replyClock.extend(replyClock[:21])
    replyClock = replyClock[21:]
    flierprops = {'marker': 'o', 'markerfacecolor': 'red', 'color': 'black'}
    medianprops = {'linestyle': '--', 'color': 'orange'}
    plt.figure()
    plt.subplot(3, 1, 2)
    plt.boxplot(x=likeNumDate, patch_artist=True, showmeans=True, showfliers=False,
                boxprops={'color': 'black', 'facecolor': 'lightskyblue'}, flierprops=flierprops,
                meanprops={'marker': 'D', 'markerfacecolor': 'indianred'}, medianprops=medianprops)
    plt.title('Likes divided by date')
    plt.subplot(3, 1, 3)
    plt.boxplot(x=replyDate, patch_artist=True, showmeans=True, showfliers=False,
                boxprops={'color': 'black', 'facecolor': 'Deepskyblue'}, flierprops=flierprops,
                meanprops={'marker': 'D', 'markerfacecolor': 'indianred'}, medianprops=medianprops)
    plt.title('Replies divided by date')
    plt.subplot(3, 2, 1)
    plt.boxplot(x=likeNumClock, patch_artist=True, showmeans=True, showfliers=False,
                boxprops={'color': 'black', 'facecolor': 'violet'}, flierprops=flierprops,
                meanprops={'marker': 'D', 'markerfacecolor': 'indianred'}, medianprops=medianprops)
    plt.title('Likes divided by clock')
    plt.subplot(3, 2, 2)
    plt.boxplot(x=replyClock, patch_artist=True, showmeans=True, showfliers=False,
                boxprops={'color': 'black', 'facecolor': 'darkviolet'}, flierprops=flierprops,
                meanprops={'marker': 'D', 'markerfacecolor': 'indianred'}, medianprops=medianprops)
    plt.title('Replies divided by clock')
    plt.suptitle('Box-plot analysis on relationship \n'
                 'between likes or replies and time division by date or clock')
    plt.show()


def preAnalysisReplyTime():
    replyTime = []
    for i in range(1, 37500):
        print(i)
        fp = open('thuhole_ana/comments/' + str(i) + '.json', 'r', encoding='utf8')
        json_data = json.load(fp)
        fh = open('thuhole_ana/holes/' + str(i) + '.json', 'r', encoding='utf8')
        json_hole = json.load(fh)
        dealtItem = []
        if json_data['code'] == 0:
            originTime = json_hole['data']['timestamp']
            for j in json_data['data']:
                dealtItem.append(j['timestamp'] - originTime)
            replyTime.append(dealtItem)
        fp.close()
        fh.close()
    fr = open('thuhole_ana/analysisExisted/commentTime.json', 'w', encoding='utf8')
    fr.write(str(replyTime))
    fr.close()


'''在PART IV中执行的代码'''
# IV-1 tag和字符串长度关系的研究
# analysisTagRelated()
# IV-2 互动关系的时域研究
# analysisTimeRelated()
# IV-3 回复时间的预处理
# preAnalysisReplyTime()
'''多变量分析结束'''

'''* * * * *'''
'''PART V: 情感倾向训练与分析'''
'''* * * * *'''


# 情感倾向训练标准：
# 娱乐性质为正向，争论性质为负向
# 玩梗为正向，钓鱼为负向
# 干货（选课测评等）为正向，冲塔为负向
# 专业比较为负向，左和右的讨论均为负向

def extractHole():
    holeText = []
    for i in range(1, 37500):
        print(i)
        fp = open('thuhole_ana/holes/' + str(i) + '.json', 'r', encoding='utf8')
        json_data = json.load(fp)
        if json_data['code'] != 1:
            holeText.append(json_data['data']['text'].replace('\n', ''))
    fr = open('thuhole_ana/analysisExisted/textHole.txt', 'w', encoding='utf8')
    fr.write(json.dumps(holeText))


def getTrainer():
    fr = open('thuhole_ana/analysisExisted/textHole.txt', 'r', encoding='utf-8')
    json_data = json.load(fr)
    fw = open('thuhole_ana/analysisExisted/testHole.csv', 'a+', encoding='utf-8')
    for i in range(1122, 1500):
        rand = i * 25 + random.randint(0, 25)
        print(str(rand) + ':' + json_data[rand])
        inp = input('情感倾向：')
        if inp == '-1':
            break
        if inp == '0' or inp == '1':
            fw.write('\"' + json_data[rand].replace('\"', '') + '\", ' + str(inp) + '\n')
    fw.close()


def trainEmotion():
    fn = open('thuhole_ana/analysisExisted/neg.', 'a+', encoding='utf-8')
    fp = open('thuhole_ana/analysisExisted/pos.', 'a+', encoding='utf-8')
    f = csv.reader(open('thuhole_ana/analysisExisted/备份.csv', 'r', encoding='utf-8'))
    for i in f:
        if i[1] == ' 0' or i[1] == ' -1':
            fn.write(i[0].replace('\n', '') + '\n')
        if i[1] == ' 1':
            fp.write(i[0].replace('\n', '') + '\n')
    fn.close()
    fp.close()
    sentiment.train('venv/Lib/site-packages/snownlp/sentiment/neg.txt',
                    'venv/Lib/site-packages/snownlp/sentiment/pos.txt')
    sentiment.save('venv/Lib/site-packages/snownlp/sentiment/sentiment.marshal2')


def testEmotion():
    f = csv.reader(open('thuhole_ana/analysisExisted/testHole.csv', 'r', encoding='utf-8'))
    pp, pn, np_, nn = 0, 0, 0, 0
    for i in f:
        q = SnowNLP(i[0])
        if i[1] == '  1':
            if q.sentiments > 0.5:
                pp += 1
            else:
                pn += 1
        if i[1] == '  -1':
            if q.sentiments > 0.5:
                np_ += 1
            else:
                nn += 1
    print(pp, pn, np_, nn)


def getHoleEmotion():
    fr = open('thuhole_ana/analysisExisted/textHole.txt', 'r', encoding='utf-8')
    json_data = json.load(fr)
    emotionResult = []
    for i in json_data:
        print(i)
        if len(i) <= 1:
            emotionResult.append(-1)
        elif i[0] == '捞':
            emotionResult.append(-1)
        else:
            q = SnowNLP(i)
            emotionResult.append(q.sentiments)
    print(emotionResult)


# dealtItem: likenum, reply, cited, tag, textLength
# , withPic, timeDate, timeMod, pid

def analysisHoleEmotion():
    fr = open('thuhole_ana/analysisExisted/holeEmotion.txt', 'r', encoding='utf-8')
    json_data = json.load(fr)
    ft = open('thuhole_ana/analysisExisted/rawExisted.txt', 'r', encoding='utf-8')
    json_data2 = json.load(ft)
    emotion = []
    wholeInfo = []
    for i in range(len(json_data)):
        if json_data[i] != -1:
            emotion.append(json_data[i])
            wholeInfo.append(json_data2[i])
    matrix = np.transpose(np.array(wholeInfo))
    plt.scatter(matrix[8], emotion, .1)
    plt.xlabel('number of the hole')
    plt.ylabel('sentiment of the hole\n 0 means negative, 1 means positive')
    plt.title('Sentiment distribution of holes \n(trained by 814 negative and 856 positive annotated hole texts)')
    # plt.show()

    plt.cla()
    newLike, newReply = [], []
    likeEmotion, replyEmotion = [], []
    for i in range(len(emotion)):
        if matrix[0][i] < 50:
            newLike.append(matrix[0][i])
            likeEmotion.append(emotion[i])
        if matrix[1][i] < 50:
            newReply.append(matrix[1][i])
            replyEmotion.append(emotion[i])
    plt.subplot(2, 1, 1)
    plt.title('Relationship between sentiment and likes number\n(those with over 50 replies are neglected)')
    plt.scatter(likeEmotion, newLike, .4, color='lightskyblue')
    plt.subplot(2, 1, 2)
    plt.title('Relationship between sentiment and reply number\n(those with over 50 replies are neglected)')
    plt.scatter(replyEmotion, newReply, .4, color='steelblue')
    # plt.show()

    plt.cla()
    emotionDate, emotionClock, emotionTag = [], [], [[], [], [], []]
    for i in range(0, 24):
        emotionClock.append([])
    for i in range(0, 48):
        emotionDate.append([])
    for i in range(len(emotion)):
        emotionDate[matrix[6][i] - 1].append(emotion[i])
        emotionClock[(4 + matrix[7][i]) % 24].append(emotion[i])
        if matrix[3][i] > 0:
            emotionTag[matrix[3][i] - 1].append(emotion[i])
    flierprops = {'marker': 'o', 'markerfacecolor': 'red', 'color': 'black'}
    medianprops = {'linestyle': '--', 'color': 'yellow'}
    plt.subplot(2, 1, 2)
    plt.boxplot(x=emotionDate, patch_artist=True, showmeans=True, showfliers=False,
                boxprops={'color': 'black', 'facecolor': 'lightskyblue'}, flierprops=flierprops,
                meanprops={'marker': 'D', 'markerfacecolor': 'indianred'}, medianprops=medianprops)
    plt.title('Sentiment distribution of holes by date')
    plt.subplot(2, 2, 1)
    plt.boxplot(x=emotionClock, patch_artist=True, showmeans=True, showfliers=False,
                boxprops={'color': 'black', 'facecolor': 'Steelblue'}, flierprops=flierprops,
                meanprops={'marker': 'D', 'markerfacecolor': 'indianred'}, medianprops=medianprops)
    plt.title('Sentiment distribution of holes by clock')
    plt.subplot(2, 2, 2)
    plt.boxplot(x=emotionTag, labels=['sexual', 'political', 'NSFW', 'others'],
                patch_artist=True, showmeans=True, showfliers=False,
                boxprops={'color': 'black', 'facecolor': 'royalblue'}, flierprops=flierprops,
                meanprops={'marker': 'D', 'markerfacecolor': 'indianred'}, medianprops=medianprops)
    plt.title('Sentiment distribution of holes by tag')
    plt.suptitle('Sentiment distribution of holes by clock, tag and date\n 0 means negative, 1 means positive')
    # plt.show()


'''在PART V中执行的代码'''
# V-1 文本提取
# extractHole()
# V-2 采药
# getTrainer()
# V-3 炼丹
# trainEmotion()
# V-4 测试炼丹成果
# testEmotion()
# V-5 获得树洞情感倾向
# getHoleEmotion()
# V-6 分析其他因素与树洞情感倾向的关系
# analysisHoleEmotion()
'''多变量分析结束'''

'''* * * * *'''
'''PART VI: 评论情感倾向与总体'''
'''* * * * *'''


def extractComment():
    commentText = []
    textPosition = -1
    for i in range(1, 37500):
        print(i)
        fp = open('thuhole_ana/comments/' + str(i) + '.json', 'r', encoding='utf8')
        json_data = json.load(fp)
        fp.close()
        if json_data['code'] != 1:
            for i in json_data['data']:
                textPosition = i['text'].find(']')
                commentText.append(i['text'][textPosition + 2:].replace('\n', ''))
    fr = open('thuhole_ana/analysisExisted/commentHole.txt', 'w', encoding='utf8')
    fr.write(json.dumps(commentText))


def getTrainer2():
    fr = open('thuhole_ana/analysisExisted/commentHole.txt', 'r', encoding='utf-8')
    json_data = json.load(fr)
    fr.close()
    fp = open('thuhole_ana/analysisExisted/pos2.txt', 'a+', encoding='utf-8')
    fn = open('thuhole_ana/analysisExisted/neg2.txt', 'a+', encoding='utf-8')
    print(len(json_data))
    for i in range(300, 681):
        rand = i * 300 + random.randint(0, 300)
        print(str(rand) + ':' + json_data[rand])
        inp = input('情感倾向：')
        resPos = json_data[rand].find(':')
        if inp == '-1':
            break
        if inp == '0':
            fn.write(json_data[rand][resPos + 2:] + '\n')
        elif inp == '1':
            fp.write(json_data[rand][resPos + 2:] + '\n')
    fp.close()
    fn.close()


def getCommentEmotion():
    commentText = []
    textPosition = -1
    pos = -1
    for i in range(1, 37500):
        print(i)
        fp = open('thuhole_ana/comments/' + str(i) + '.json', 'r', encoding='utf8')
        json_data = json.load(fp)
        fp.close()
        if json_data['code'] != 1:
            pos += 1
            commentText.append([])
            for j in json_data['data']:
                textPosition = j['text'].find(']')
                text = j['text'][textPosition + 1:].replace('\n', '')
                if len(text) < 2:
                    commentText[pos].append(-1)
                else:
                    q = SnowNLP(str(text))
                    commentText[pos].append(q.sentiments)
    fr = open('thuhole_ana/analysisExisted/commentSentiment.txt', 'w', encoding='utf8')
    fr.write(json.dumps(commentText))


def analysisCommentTime():
    fe = open('thuhole_ana/analysisExisted/commentSentiment.txt', 'r', encoding='utf-8')
    emotion = json.load(fe)
    ft = open('thuhole_ana/analysisExisted/commentTime.json', 'r', encoding='utf-8')
    time = json.load(ft)
    fh = open('thuhole_ana/analysisExisted/holeEmotion.txt', 'r', encoding='utf-8')
    holeEmotion = json.load(fh)
    eList, tList = [], []
    for i in range(len(emotion)):
        if len(emotion[i]) > 1:
            for j in range(0,len(emotion[i]) - 1):
                if emotion[i][j] != -1 and time[i][j + 1] - time[i][j] < 500:
                    eList.append(emotion[i][j])
                    tList.append(time[i][j + 1] - time[i][j])
    lists = [eList, tList]
    print(np.corrcoef(lists))
    plt.subplot(2, 2, 1)
    plt.scatter(eList, tList, .01, color='lightskyblue')
    plt.title('Sentiments of comments and time gap with the next\n'
              '(corr = 0.017)')

    eList2, tList2 = [], []
    for i in range(len(emotion)):
        if len(emotion[i]) > 1:
            for j in range(1, len(emotion[i])):
                if emotion[i][j] != -1 and time[i][j] - time[i][j - 1] < 500:
                    eList2.append(emotion[i][j])
                    tList2.append(time[i][j] - time[i][j - 1])
    lists2 = [eList2, tList2]
    print(np.corrcoef(lists2))
    plt.subplot(2, 2, 2)
    plt.scatter(eList2, tList2, .01, color='deepskyblue')
    plt.title('Sentiments of comments and time gap with the previous\n'
              '(corr = 0.021)')

    holeDistri, timeDistri = [], []
    for i in range(len(holeEmotion)):
        if holeEmotion[i] >= 0 and len(time[i]) > 0:
            if time[i][0] < 500:
                holeDistri.append(holeEmotion[i])
                timeDistri.append(time[i][0])
    lists3 = [holeDistri, timeDistri]
    print(np.corrcoef(lists3))
    plt.subplot(2, 2, 3)
    plt.scatter(holeDistri, timeDistri, .01, color='royalblue')
    plt.title('Sentiments of holes and time gap with the first comment\n'
              '(corr = 0.033)')

    endSentiment = []
    for i in range(len(holeEmotion)):
        if len(time[i]) == 1:
            if time[i][-1] < 500 and emotion[i][-1] >= 0:
                endSentiment.append(emotion[i][-1])
        if len(time[i]) > 1:
            if time[i][-1] - time[i][-2] < 500 and emotion[i][-1] >= 0:
                endSentiment.append(emotion[i][-1])
    plt.subplot(2, 2, 4)
    plt.hist(endSentiment, [0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1], color='#e0e0f6')
    plt.title('Sentiment distribution of the last comment')

    plt.show()


def getAverageEmotion():
    fe = open('thuhole_ana/analysisExisted/commentSentiment.txt', 'r', encoding='utf-8')
    emotion = json.load(fe)
    averageEmotion = []
    for i in emotion:
        times = 0
        sum = 0
        for j in i:
            if j != -1:
                sum += j
                times += 1
        if times == 0:
            averageEmotion.append(-1)
        else:
            averageEmotion.append(sum / times)
    print(averageEmotion)


# dealtItem: likenum, reply, cited, tag, textLength
# , withPic, timeDate, timeMod, pid

def getMatrix():
    fh = open('thuhole_ana/analysisExisted/holeEmotion.txt', 'r', encoding='utf-8')
    json_hole = json.load(fh)
    ft = open('thuhole_ana/analysisExisted/rawExisted.txt', 'r', encoding='utf-8')
    json_total = json.load(ft)
    fc = open('thuhole_ana/analysisExisted/commentAverage.txt', 'r', encoding='utf-8')
    json_comment = json.load(fc)
    matrix = [[], [], [], [], [], [], [], [], [], [], []]
    for i in range(len(json_total)):
        if json_hole[i] != 0 and json_comment[i] != 0:
            for j in range(0, 9):
                matrix[j].append(json_total[i][j])
            matrix[9].append(json_hole[i])
            matrix[10].append(json_comment[i])
    fig = plt.figure()
    ax = fig.add_subplot(111)
    yLabel = ['Like', 'Reply', 'Cited', 'Tag', 'Text length',
              'Whether with a picture', 'Date', 'Clock', 'Pid', 'Hole sentiment', 'Comment sentiment']
    xLabel = ['Like', 'Reply', 'Cited', 'Tag', 'Text..',
              'Pic..', 'Date', 'Clock', 'Pid', 'Hole..', 'Comment..']
    ax.set_yticks(range(len(yLabel)))
    ax.set_yticklabels(yLabel)
    ax.set_xticks(range(len(xLabel)))
    ax.set_xticklabels(xLabel)
    # 作图并选择热图的颜色填充风格，这里选择hot
    raw = np.array(matrix)
    data = np.corrcoef(raw)
    im = ax.imshow(data, cmap=plt.cm.bone_r)
    plt.colorbar(im)
    plt.title("Correlation coefficient matrix of all parameters of the hole")
    plt.show()

    plt.cla()
    s, P = np.linalg.eig(data)
    print(s)
    plt.bar(['Like', 'Reply', 'Cited', 'Tag', 'Text length',
              'Whether \nwith a picture', 'Date', 'Clock',
             'Pid', 'Hole\n sentiment', 'Comment \nsentiment'],
            s, color='#e0e0f6')
    plt.title("Eigenvalues of each factor on the correlation coefficient matrix of all holes")
    plt.show()


# VI-1 提取
# extractComment()
# VI-2 加入到训练集中
# getTrainer2()
# VI-3 分析评论情感
# getCommentEmotion()
# VI-4 评论情况分析
# analysisCommentTime()
# VI-5 获取平均评论情感
# getAverageEmotion()
# VI-6 绘制相关系数矩阵并作特征值分解
# getMatrix()
