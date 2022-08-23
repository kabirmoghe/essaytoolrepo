from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import httplib2
import googleapiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload,MediaFileUpload
import os
import time

# def getStudents():

# 	scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

# 	creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

# 	client = gspread.authorize(creds)

# 	#os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/kabirmoghe/Desktop/essayApp/creds.json'
# 	os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'creds.json'
# 	drive = googleapiclient.discovery.build('drive','v3')

# 	service = drive.files().list(fields='files(id, name, mimeType, parents)').execute()['files']

# 	driveInfo = pd.DataFrame(service)

# 	driveInfo = driveInfo[(driveInfo["parents"].isnull() == False)]
# 	driveInfo["parents"] = driveInfo["parents"].apply(lambda val: val[0])

# 	students = list(driveInfo[driveInfo["parents"] == '1EncvaZIVEUXKWWbqq0-0JrcH2abJwV-g']['name'])

# 	return students

def getStudents():

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'creds.json'
    drive = googleapiclient.discovery.build('drive','v3')

    service = drive.files().list(fields='files(id, name, mimeType, parents)', pageSize=1000).execute()['files']

    driveInfo = pd.DataFrame(service)

    driveInfo = driveInfo[(driveInfo["parents"].isnull() == False)]
    driveInfo["parents"] = driveInfo["parents"].apply(lambda val: val[0])

#1EncvaZIVEUXKWWbqq0-0JrcH2abJwV-g -OLD

    students = dict(driveInfo[driveInfo["parents"] == '11Gd7KQQLMLZAuzD87ab3Gb1t8TvP11ZZ'][['name','id']].values)  

    essayTypes={}
    
    for student in students:

        studentDf = driveInfo[driveInfo["parents"] == students[student]]
        essayOnlyStudentDf = studentDf[(studentDf["name"] != "Administrative") & (studentDf["name"] != "Supplements")]        
                
        essays = list(essayOnlyStudentDf["name"])
        
        if "Supplements" in studentDf["name"].values:
            [essays.append(essay) for essay in list(driveInfo[driveInfo["parents"] == studentDf[studentDf["name"] == "Supplements"]["id"].values[0]]['name'])]

        essayTypes[student] = essays
    
    return list(students.keys()), essayTypes

def downloadFiles(driveInfo, students, name, essayType):

    begin = time.time()

    print("Setting Up")

    # STUDENT SPECIFIC

    studentFolders = driveInfo[driveInfo["parents"] == students[name]]
    studentFolders = studentFolders[studentFolders["name"] != "Administrative"]

    if "Supplements" in studentFolders['name'].values:
        suppFolders = driveInfo[driveInfo["parents"] == studentFolders[studentFolders["name"] == "Supplements"]["id"].values[0]]
        studentFolders = pd.concat([studentFolders[studentFolders["name"] != "Supplements"], suppFolders])

    folderId = studentFolders[studentFolders["name"] == essayType]["id"].iloc[0]
    docsDf = driveInfo[driveInfo['parents'] == folderId]

    docsDf = docsDf[docsDf["name"].str.contains("Draft")]

    if len(docsDf) == 0:
        return False
    else:

        docIds = list(docsDf['id'])
        docNames = list(docsDf['name'])

        # Makes parent directory for student

        print("Creating Directories")

        if name not in os.listdir():
            os.mkdir(name)

            os.mkdir("{}/{}".format(name, essayType))

        else:
            if essayType not in os.listdir(name):
                os.mkdir("{}/{}".format(name, essayType))

        # Docs

        print("Creating Docs")

        docStart = time.time()

        currentDocs = os.listdir("{}/{}".format(name, essayType))
        currentDocs = [doc.split('.docx')[0] for doc in currentDocs]     

        toSkip = []

        for i in range(len(docIds)):

            docName = docNames[i]

            if docName not in currentDocs:

                print("Downloading {}".format(docName))

                doc = drive.files().export_media(fileId = docIds[i], mimeType = "application/vnd.openxmlformats-officedocument.wordprocessingml.document").execute()

                with open("{}/{}/{}.docx".format(name, essayType, docName), "wb") as f:
                    f.write(doc)
            else:

                print("Skipping {}".format(docName))

                toSkip.append(i)

        docEnd = time.time()

        print("Docs Time: {}".format(round(docEnd-docStart, 1)))

        # Insights

    #     print("Creating insights")

    #     insightsStart = time.time()

        # sheet = df[df["mimeType"] == "application/vnd.google-apps.spreadsheet"]

        # sheetName = list(sheet['name'])[0]

        # # sheets = df[df["mimeType"] == "application/vnd.google-apps.spreadsheet"]

        # #sheetNames = list(sheets['name'])

        # # currentSheets = os.listdir("{}/Sheets".format(name))
        # # currentSheets = [sheet.split('.csv')[0] for sheet in currentSheets]                      

        # # for sheetName in sheetNames:

        # #     if sheetName not in currentSheets:

        # #         sheet = client.open(sheetName).sheet1

        # #         print("Downloading {}".format(sheetName))

        # #         df = pd.DataFrame(sheet.get_all_records())

        # #         df.to_csv("{}/Sheets/{}.csv".format(name, sheetName))
        # #     else:
        # #         print("Skipping {}".format(sheetName))

        # sheet = client.open(sheetName).sheet1
        # print("Downloading {}".format(sheetName))
        # df = pd.DataFrame(sheet.get_all_records())
        # df.to_csv("{}/Sheets/{}.csv".format(name, sheetName))

    #     draftNums = [int(name.split()[-1].split('#')[-1]) for name in docNames]

    #     commentTallies = []
    #     subs = []

    #     for i in range(len(docIds)):

    #         docId = docIds[i]

    #         # commentList = drive.comments().list(fileId=docId,fields='comments', pageSize=999).execute() 

    #         # comments = []

    #         # for comment in commentList.get('comments'):         
    #         #     comments.append(comment['content'])

    #         comments = []

    #         hasNext = True
    #         token = ""

    #         while hasNext:

    #             commentDict = drive.comments().list(fileId=docId,fields='nextPageToken, comments', pageSize=100, pageToken=token).execute()   

    #             for comment in commentDict.get('comments'):         
    #                 comments.append(comment['content'])

    #             if 'nextPageToken' in commentDict.keys():
    #                 token = commentDict["nextPageToken"]
    #             else:
    #                 hasNext = False

    #         admi = 0 
    #         mech = 0 
    #         stru = 0
    #         idea = 0
    #         sati = 0
    #         date = ''

    #         for comment in comments:
    #             if "[Administrative Comment]" in comment or "[AC]" in comment:
    #                 admi += 1
    #             elif "[Mechanical Comment]" in comment or "[MC]" in comment:
    #                 mech += 1
    #             elif "[Structural Comment]" in comment or "[SC]" in comment:
    #                 stru += 1
    #             elif "[Ideational Comment]" in comment or "[IC]" in comment:
    #                 idea += 1
    #             elif "[Self Eval]" in comment or "[Self-Eval]" in comment or "[Submission Info]" in comment:

    #                 date = comment.split("Submission Date:")[-1].split("Date of Submission:")[-1].replace(u'\xa0', '')
    #                 strSati = comment.split("Satisfaction:")[1].split("\n")[0].strip()

    #                 if strSati == '':
    #                     sati = 0.0
    #                 else:
    #                     sati = float(strSati)

    #         total = admi+mech+stru+idea

    #         commentTallies.append([total, admi, mech, stru, idea, sati, date])


    #     print(commentTallies)

    #     commentDf = pd.DataFrame(commentTallies, columns=["Total Tallies","Administrative Tallies", "Mechanical Tallies", "Structural Tallies", "Ideational Tallies", "Satisfaction Level", "Submission Date"])
    #     commentDf["Draft Number"] = draftNums

    #     #print(range(len(draftNums)))

    #     commentDf["Shared Drafts"] = range(1, len(draftNums)+1)
    #     commentDf["Student Name"] = name
    #     commentDf["Total Words"] = 0
    #     commentDf["Essay Type"] = "College Essay"
    #     commentDf["Comments/Words"] = commentDf["Total Tallies"]

    #     commentDf = commentDf.sort_values(by="Draft Number").reindex(columns=["Student Name","Essay Type","Draft Number","Total Tallies","Total Words","Comments/Words","Satisfaction Level", "Administrative Tallies", "Mechanical Tallies", "Ideational Tallies", "Structural Tallies", "Submission Date","Shared Drafts"]).reset_index(drop=True)

    #     drafts = len(commentDf)
    #     comments = commentDf["Total Tallies"].sum()
    #     words = commentDf["Total Words"].sum()
    #     administrative = commentDf["Administrative Tallies"].sum()
    #     mechanical = commentDf["Mechanical Tallies"].sum()
    #     ideational = commentDf["Ideational Tallies"].sum()
    #     structural = commentDf["Structural Tallies"].sum()
    #     submission = commentDf["Submission Date"].iloc[-1]

    #     drafts_total = commentDf["Draft Number"].iloc[-1]

    #     insightsEnd = time.time()

    #     print("Insights Time: {}".format(round(insightsEnd-insightsStart, 1)))

        print("Finished Connecting and Downloading")

        end = time.time()

        total = round(end-begin, 1)

        print("Total: {} seconds".format(total))

        return True
