
import datetime
import boto3
now = datetime.datetime.now()
strTime = now.strftime("%Y-%m-%d %H:%M:%S")

try:
    import io
    from io import StringIO
    import os
    import stanza
    import time
    import docx
    import pandas as pd
    import modDriveConnect
    import clear

    def stringifyAndProcess(doc, nlp, studentName, essayType):

        print("Creating compact string...")

        properDoc = docx.Document("{}/{}/{}".format(studentName, essayType, doc))

        docParas = [p.text.strip() for p in properDoc.paragraphs if (p.text!= "" and not p.text.isspace())]

        docText = ""

        for i in range(len(docParas)):

            docText+=docParas[i]+" (New paragraph begins). "    

        print("Processing '{}'".format(doc))
        processedDoc = nlp(docText)

        paraSents = []

        docSents = []

        for sent in processedDoc.sentences:

            s = sent.text

            if s=="(New paragraph begins).":
                docSents.append(paraSents)
                paraSents = []
            elif "(New paragraph begins)." in s:

                split = s.split('(New paragraph begins).')

                sent = stanzaNLP(split[0]).sentences[0]

                paraSents.append(sent)
                docSents.append(paraSents)
                paraSents = []

            else:
                paraSents.append(sent)

        return docSents

    # NEW AND IMPROVED SENTENCE FUNCTIONS

    def idSentence(strProcessed):
    #     print("--")
        strTree = str(strProcessed.constituency).replace('(, ,)', '').replace("  ", " ")
    #     print(strProcessed.text)
    #     print(strTree)
        
    #     print(list(sent))
    #     print("--")
        
    #     processedSent = stanzaNLP(sent)
        
    #     tree = processedSent.sentences[0].constituency
    #     strTree = str(tree)
        
        simpleCount = strTree.count("(S")
        coordCount = strTree.count("(:") + strTree.count("(CC for) (S")+strTree.count("(CC and) (S")+strTree.count("(CC nor) (S")+strTree.count("(CC but) (S") + strTree.count("(CC or) (S")+strTree.count("(CC yes) (S")+strTree.count("(CC so) (S")
        depCount = strTree.count("(SBAR ")

    #     print(simpleCount)
    #     print(coordCount)
    #     print(depCount)
        
        if simpleCount >= 1 and coordCount == 0 and depCount == 0 and len(strProcessed.text.split()) > 1:
    #         print("Simple")
            return "Simple"
        elif simpleCount >= 3 and coordCount >= 1 and depCount == 0:
    #         print("Compound")
            return "Compound"
        elif simpleCount >=1 and coordCount == 0 and depCount >= 1:
    #         print("Complex")
            return "Complex"
        elif simpleCount >= 3 and coordCount >= 1 and depCount >= 1:
    #         print("Compound-Complex")
            return "Compound-Complex"
        else:
            
    #         print("Fragment")
            return "Fragment"

    def docSentence(processedDocInfo, index):

        print("Analyzing sentence information...")

        categories = {"Fragment":"#DF8CE3", "Simple":"#8CCBE3", "Compound":"#8CE397", "Complex":"#E3D78C", "Compound-Complex":"#E3938C"}

        allSentInfo = []
        justSentList = []

    #     for i in range(len(processedDocsInfo)):

        index += 1

    #     doc = processedDocsInfo[i]

        docSentInfo = []
        justColors = []
        justSentences = []

        for para in processedDocInfo:

            paraSentInfo = []
            paraSents = []

            for s in para:

                txt = s.text
                sType = idSentence(s)

                paraSentInfo.append([txt,categories[sType]])
                justColors.append(sType)
                paraSents.append(txt)

            docSentInfo.append(paraSentInfo)
            justSentences.append(paraSents)

        typeTally = {}

        for color in justColors:

            if type(color) == str:
                if color not in typeTally:
                    typeTally[color] = 1
                else:
                    typeTally[color] = typeTally[color]+1

    #         print(typeTally)


        typeInfo = []

        for sType in categories:

            color = categories[sType]

            # print(sType)

            if sType not in typeTally:
                typeTally[sType] = 0

            typeInfo.append([sType, color, typeTally[sType]])


        indivSentInfo = [docSentInfo, index, typeInfo]
    #     justSentList.append(justSentences)

        print("Done with sentence analysis")

        return indivSentInfo, justSentences, index

    def readStudentSentInfo(name, essay):

        bucketName = 'essaytool'
        fileName = "{}_{}_all.csv".format(name, essay)

        client = boto3.client('s3')

        csv_obj = client.get_object(Bucket=bucketName, Key=fileName)
        body = csv_obj['Body']
        csv_string = body.read().decode('utf-8')

        retrievedData = pd.read_csv(StringIO(csv_string), index_col = 0)   

        listData = retrievedData.values.tolist()
        finalSentInfo = []

        for docInfo in listData:

            docSentInfo = []

            for item in docInfo:
                if type(item) == str:
                    docSentInfo.append(eval(item))
                else:
                    docSentInfo.append(item)

            finalSentInfo.append(docSentInfo)

        # SENTS

        fileName = "{}_{}_sents.csv".format(name, essay)

        client = boto3.client('s3')

        csv_obj = client.get_object(Bucket=bucketName, Key=fileName)
        body = csv_obj['Body']
        csv_string = body.read().decode('utf-8')

        retrievedData = pd.read_csv(StringIO(csv_string), index_col = 0)   

        listData = retrievedData.values.tolist()
        justSentInfo = []

        for docInfo in listData:

            docSentInfo = []

            for item in docInfo:
                if type(item) == str:
                    docSentInfo.append(eval(item))
                else:
                    docSentInfo.append(item)

            justSentInfo.append(docSentInfo)

        return finalSentInfo, justSentInfo

    def produceStudentSentInfo():

        start = time.time()

        studentNames, essayTypes = modDriveConnect.getStudents()

        stanzaNLP = stanza.Pipeline('en', use_gpu=False, processors='tokenize,pos,constituency')

        client = boto3.client('s3')

        for studentName in studentNames:
            for essayType in essayTypes[studentName]:

                try:

                    print("--")
                    print("Student: {}".format(studentName))

                    modDriveConnect.downloadFiles(studentName, essayType)

                    docs = os.listdir("{}/{}".format(studentName, essayType))

                    numForDraft = {}

                    draftNums = [int(doc.split(".")[0].split()[-1].split("#")[-1]) for doc in docs]

                    for i in range(len(docs)):
                        doc = docs[i]
                        numForDraft[doc] = draftNums[i]

                    docs = [pair[0] for pair in sorted(numForDraft.items(),key=lambda item: item[1], reverse=False)]
                    draftNums = sorted(draftNums)

                    actualNumDocs = len(docs)

                    print("Getting S3 doc info...")

                    try: 
                        bucketInfo, bucketSents = readStudentSentInfo(studentName, essayType)

                        s3Docs = len(bucketInfo) # The number of "DocInfos" for the first returned object from the method

                        index = s3Docs-actualNumDocs

                        if len(docs) > 0 and index < 0:
                            docs = docs[index:]

                            nextIndex = bucketInfo[-1][1]

                            for doc in docs:

                                processedSentInfo = stringifyAndProcess(doc, stanzaNLP, studentName, essayType)
                                allSentenceInfo, sentList, nextIndex = docSentence(processedSentInfo, nextIndex)

                                bucketInfo.append(allSentenceInfo)
                                bucketSents.append(sentList)

                                allDf = pd.DataFrame(bucketInfo)
                                sentDf = pd.DataFrame(bucketSents)

                                fileName = "{}_{}_all.csv".format(studentName, essayType)
                                bucketName = 'essaytool'

                                csv_buffer = StringIO()
                                allDf.to_csv(csv_buffer)

                                response = client.put_object(Body = csv_buffer.getvalue(), Bucket = bucketName, Key = fileName)

                                fileName = "{}_{}_sents.csv".format(studentName, essayType)

                                csv_buffer = StringIO()
                                sentDf.to_csv(csv_buffer)

                                response = client.put_object(Body = csv_buffer.getvalue(), Bucket = bucketName, Key = fileName)
                        else:
                            print("No new information")
                    except:
                        print("No Information in bucket")

                        nextIndex = 0

                        for doc in docs:

                            processedSentInfo = stringifyAndProcess(doc, stanzaNLP, studentName, essayType)

                            if nextIndex > 0:

    #                             print("Not first draft")

                                bucketInfo, bucketSents = readStudentSentInfo(studentName, essayType)                

                                allSentenceInfo, sentList, nextIndex = docSentence(processedSentInfo, nextIndex)  

                                bucketInfo.append(allSentenceInfo)
                                bucketSents.append(sentList)    

                                allDf = pd.DataFrame(bucketInfo)
                                sentDf = pd.DataFrame(bucketSents)

                            else:

    #                             print("First draft")

                                allSentenceInfo, sentList, nextIndex = docSentence(processedSentInfo, nextIndex)  

                                allDf = pd.DataFrame([allSentenceInfo])

                                sentDf = pd.DataFrame([sentList]) 

                            fileName = "{}_{}_all.csv".format(studentName, essayType)
                            bucketName = 'essaytool'

                            csv_buffer = StringIO()
                            allDf.to_csv(csv_buffer)

                            response = client.put_object(Body = csv_buffer.getvalue(), Bucket = bucketName, Key = fileName)

                            fileName = "{}_{}_sents.csv".format(studentName, essayType)

                            csv_buffer = StringIO()
                            sentDf.to_csv(csv_buffer)

                            response = client.put_object(Body = csv_buffer.getvalue(), Bucket = bucketName, Key = fileName)                    

                except Exception as e:
                    print(e)

        endTime = time.time()-start 

        print("Took {}s".format(endTime))
        
        clear.clear()

        # Open the file in append & read mode ('a+')
        with open("logs.txt", "a+") as f:
            # Move read cursor to the start of file.
            f.seek(0)
            # If file is not empty then append '\n'
            data = f.read(100)
        
            if len(data) > 0 :
                f.write("\n")
            # Append text at the end of file
            f.write("Ran at {} (took {}s)".format(strTime, endTime))

        client.put_object(Body = open('logs.txt', 'rb'), Bucket = 'essaytool', Key = 'logs.txt')

    if __name__ == '__main__':
        produceStudentSentInfo()

except Exception as e:
    
    client = boto3.client('s3')

    # Open the file in append & read mode ('a+')
    with open("errors.txt", "a+") as f:
        # Move read cursor to the start of file.
        f.seek(0)
        # If file is not empty then append '\n'
        data = f.read(100)

        if len(data) > 0 :
            f.write("\n")
        # Append text at the end of file
        f.write("Ran at {}: {}".format(strTime,e))

    client.put_object(Body = open('errors.txt', 'rb'), Bucket = 'essaytool', Key = 'errors.txt')
