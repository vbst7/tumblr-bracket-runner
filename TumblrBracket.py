from datetime import timedelta
from tumblr import Content, Tumblr
from typing import Self
import pytumblr
import sys

def load_datafile(filename):
    #takes a file and returns it as an array, where each index contains each line from the file
    try:

        with open(filename,'r') as f:
            A = []
            for line in f:
                #remove the newline. This is important for the keys
                A.append(line.replace('\n',''))
        return A
    except FileNotFoundError:
        print(f"Error: No such file '{filename}'")
        quit()

def matchupRound(rSheet,keys,name,top):
    tumblr = Tumblr(
    name,
    keys[0],
    keys[1],
    keys[2],
    keys[3],
    )
    #saves rSheet as a list
    sheet = load_datafile(rSheet)
    sH = sheet[0].split(",") #sheet heading

    #bring back real commas
    i = 0
    while (i < 4):
        sH[i] = sH[i].replace("|",",")
        i+=1

    states = {
        "image" : False, #True iff you are using images and want them to be side by side
        "video" : False, #True iff you are using videos and want them embedded
        "artist" : False, #True iff you are using the tag cell as the artist cell
        "titles" : False, #True iff you want titles to be displayed in text as well as in the poll options
                    #titles will be displayed even if this is false, if video is true
        "postState" : "draft",
        "defExpiry" : 7
    }
    robin = False
    topDown = False
    
    if len(sH) > 4:
        try:
            states["defExpiry"] = float(sH[4])
        except ValueError:
            states["defExpiry"] = 7
        if len(sH) >= 6:
            for char in sH[5]:
                if (char == "A"):
                    states["artist"] = True
                elif (char == "I"):
                    states["image"] = True
                elif (char == "V"):
                    states["video"] = True
                elif (char == "T"):
                    states["titles"] = True
                elif (char == "Q"):
                    states["postState"] = "queue"
                elif (char == "R"):
                    robin = True
                elif (char == "D"):
                    topDown = True
    if (robin == True):
        roundRobinMatch(tumblr, sheet, sH, states)
    elif(topDown == True):
        bottom = top + 1
        while (bottom < len(sheet)):
            genMatch(top, bottom, tumblr, sheet, sH, states)
            top +=2
            bottom+=2
    else:
        bottom = len(sheet)-top #index of the bottom of sheet
        #goes thru the top half of the list
        while (top < bottom):
            genMatch(top, bottom, tumblr, sheet, sH, states)
            top +=1
            bottom-=1

def roundRobinMatch(tumblr, sheet, sH, states):
    round = 1
    i = 1
    usedOpps = {0}
    while (round <= len(sheet)):
        while (i in usedOpps and i < len(sheet)-1):
            i += 1
        if (i >= len(sheet)-1):
            round += 1
            i = 1
            usedOpps = {0}
        opp = round - i
        if (opp < 0):
            opp += len(sheet)
        usedOpps.add(opp)
        if (opp != i and opp != 0 and opp < len(sheet)):
            genMatch(i, opp, tumblr, sheet, sH, states)
        i += 1

def roundRobinStats(name,pytum,sheet,newSheet):
    round = 1
    i = 1
    usedOpps = {0}
    while (round <= len(sheet)):
        while (i in usedOpps and i < len(sheet)-1):
            i += 1
        if (i >= len(sheet)-1):
            round += 1
            i = 1
            usedOpps = {0}
        opp = round - i
        if (opp < 0):
            opp += len(sheet)
        usedOpps.add(opp)
        if (opp != i and opp != 0 and opp < len(sheet)):
            results(name,pytum,i,opp,sheet,newSheet)
        i += 1

def genMatch(top, bottom, tumblr, sheet, sH, states):
    #generate serial number
    serial = (str)(hex(top-1)) + "v" + (str)(hex(bottom-1))

    #makes post with a poll pitting the highest seeded remaining contender vs the lowest seeded remaining contender
    s1 = sheet[top].split(",")
    s2 = sheet[bottom].split(",")

    #bring back all the real commas and newlines and music notes
    i=0
    while (i < 4 and i < len(s1)):
        s1[i] = s1[i].replace("|",",").replace("MUSIC","♪").replace("\\n","\n")
        i+=1
    i = 0
    while (i < 4 and i < len(s2)):
        s2[i] = s2[i].replace("|",",").replace("MUSIC","♪").replace("\\n","\n")
        i+=1
    
    #sets expiry to the value of the cell in column E for the top seed's row.
    # If this is not a number, then use the default
    if len(s1) > 4:
        try:
            expiry = float(s1[4])
        except ValueError:
            expiry = states["defExpiry"]
    else: expiry = states["defExpiry"]

    pollIndex = 0 #what number block the poll is
    
    #create the text contents of the post 
    contents = Content()
    if (sH[0]):
        if (len(s1) > 5 and s1[5]):
            contents.heading(s1[5])
        else:
            contents.heading(sH[0])
        pollIndex += 1
    if (sH[3]):
        contents.text(content = sH[3])
        pollIndex += 1

    #Poll contents, differs depending on whether the tag cell is an artist cell
    if (states["artist"]):
        options = [s1[0]+" - " + s1[1], s2[0]+" - " + s2[1],"Show results"]
    else:
        options = [s1[0], s2[0],"Show results"]

    contents.poll(
                sH[2],
                options,
                expire_after=timedelta(days=(expiry)),
            )



    if (states["image"]): 
        contents.blocks.append({"type": "image","media":[{"type": "image/jpeg","url": s1[3],}]})
        contents.blocks.append({"type": "image","media":[{"type": "image/jpeg","url": s2[3],}]})
    elif (states["video"]):
        if (len(s1[3]) > 0): 
            contents.blocks.append({"type": "video","url": s1[3],})
        if (len(s2[3]) > 0): 
            contents.blocks.append({"type": "video","url": s2[3],})

    #Text contents
    if (states["titles"]):
        contents.text(content = s1[0] + s1[2])
        contents.text(content = s2[0] + s2[2])

    display = []
    i = 0
    while (i < pollIndex):
        display.append({"blocks": [i]}) #the header and top message (if they exist)
        i+=1

    if (states["image"]):
        display.append({"blocks": [pollIndex+1,pollIndex+2]}) #two images
        if (states["titles"]):
            display.append({"blocks": [pollIndex+3]}) #text 1
            display.append({"blocks": [pollIndex+4]}) #text 2  
        display.append({"blocks": [pollIndex]}) #poll itself
    else:
        display.append({"blocks": [pollIndex]}) #poll itself
        display.append({"blocks": [pollIndex+3]}) #text 1
        display.append({"blocks": [pollIndex+1]}) #video 1
        display.append({"blocks": [pollIndex+4]}) #text 2  
        display.append({"blocks": [pollIndex+2]}) #video 2
    
    #add the display format to the content
    contents._rows = {"type" : "rows", "display": display}

    #create the tumblr post, with the serial number
    tumblr.post(
            content=(contents),
                state=states["postState"],
                tags=[sH[1], s1[1], s2[1], s1[0].replace(",","‚"), s2[0].replace(",","‚"), serial]
                )
    print(s1[0] + " vs " + s2[0])

def getPoll(blogname,id,tumblr):
    """
    :param blogname: name of the blog the poll is hosted on
    :param id: id of the post containing the post of itnerest
    :tumblr: pytumblr object  
    """
    #gets content from the post with the linked id
    url = '/v2/blog/{}/posts/{}'.format(blogname,id)
    get = tumblr.send_api_request("get", url, {}, [], True)
    con = get.get("content")
    uuid = -1
    #gets the client id and answers from the poll
    for block in con:
        if block.get("type") == 'poll':
            uuid = block.get("client_id")
            ans = block.get("answers")
            break
    #if the given post does not have a poll
    if (uuid == -1):
        return [-1,-1]

    #gets vote count from the poll
    url = '/v2/polls/{}/{}/{}/results'.format(blogname,id,uuid)
    return (ans,tumblr.send_api_request("get", url, {}, [], True).get("results"))

def getResults(rSheet,keys,name,newSheet,robin):
    sheet = load_datafile(rSheet)

    sH = sheet[0].split(",")
    topDown = False
    if len(sH) >= 6:
            for char in sH[5]:
                if (char == "D"):
                    topDown = True

    with open(newSheet, "w") as file:
        file.write("Winning %,Top Votes,Bottom Votes,Show Results Votes,"+sheet[0])

    #makes tumblr object with keys
    pytum = pytumblr.TumblrRestClient(
    keys[0],
    keys[1],
    keys[2],
    keys[3]
    )
    
    #go thru sheet
    if (robin == True):
        roundRobinStats(name,pytum,sheet,newSheet)
    elif(topDown == True):
        top = 1
        bottom = top + 1
        while (bottom < len(sheet)):
            results(name,pytum,top,bottom,sheet,newSheet)
            top +=2
            bottom+=2
    else:
        top = 1
        bottom = len(sheet)-top #index of the bottom of sheet
        #goes thru the top half of the list
        while (top < bottom):
            results(name,pytum,top,bottom,sheet,newSheet)
            top +=1
            bottom-=1


def results(name,pytum,top,bottom,sheet,newSheet):
    #generate serial number
    serial = (str)(hex(top-1)) + "v" + (str)(hex(bottom-1))

    winner = 0

    #check that poll post exists
    post = pytum.posts(blogname = name, tag=serial,limit=1)['posts']   

    if (len(post) == 0): #if the post does not exist
        winner = -1
    else:
        ident = post[0]['id']
        answers,poll = getPoll(name,ident,pytum)

        results = []
        for res in poll:
            results.append(poll[res])
        #if result 1 > result 2, winner = top, opposite situation: winner = bottom
        if (results[0] == -1): #there was no poll in the post
            winner = -1
        elif (results[0] > results[1]):
            winner = top
        elif (results[0] < results[1]):
            winner = bottom
        else:
            print("Warning! Matchup : " + sheet[top].split(',')[0] + " vs " + sheet[bottom].split(',')[0] + " is a tie! (position: " + (str)(top+1) + ")")
        #make sure results has at least 3 memebrs
        while (len(results) < 3):
            results.append("No option")


    #append to new csv: Show Results %, % result 1, result 2, result 3 (show results), winner (all comma-seperated)   
    with open(newSheet, "a") as file:
        if (winner == -1):#error getting results
            file.write("\nPOST MISSING: " +sheet[top].split(',')[0] +" vs " +sheet[bottom].split(',')[0] + " Could not get results")
            return
        elif (winner == 0):#tied match
            file.write("\n50,"+(str)(results[0])+","+(str)(results[1])+","+(str)(results[2])+",TIED MATCH: "+ sheet[top].split(',')[0] + " vs " + sheet[bottom].split(',')[0])
        else:
            totalVotes = results[0]+results[1]
            percent = round((100 * max(results[0],results[1])/totalVotes),2)
            file.write('\n'+(str)(percent) + "," +(str)(results[0])+","+(str)(results[1])+","+(str)(results[2])+","+sheet[winner])
        if (answers[0].get('answer_text').startswith(sheet[top].split(',')[0]) == False or answers[1].get('answer_text').startswith(sheet[bottom].split(',')[0]) == False):
            #top option doesn't begin with the top seeded competitor OR second option doesn't begin with the bottom seeded competitor
            file.write(",Matchup Error! Position: " + (str)(top+1))
            print("Warning! Matchup : " + sheet[top].split(',')[0] + " vs " + sheet[bottom].split(',')[0] + " may have innacurate vote totals, as the poll option's results was different from the name of the seeded option. (position: " + (str)(top+1) + ")")
            print("Top option in poll was: " + answers[0].get('answer_text'))
            print("Bottom option in poll was: " + answers[1].get('answer_text'))

def main():
    #reads blog name, csv file name, and file of OAuth keys from command line
    name = lower(sys.argv[1])
    sourceFile = sys.argv[2]
    keys = load_datafile(sys.argv[3])
    top = 1

    if (len(sys.argv) >= 5):
        try:
            top = int(sys.argv[4])
            matchupRound(sourceFile,keys,name,top)
            return
        except ValueError:
            outFile = sys.argv[4]
        if (len(sys.argv) >= 6):
            try:
                top = int(sys.argv[4])
            except ValueError:
                top = 1
        getResults(sourceFile,keys,name,outFile,False)


    else:
        matchupRound(sourceFile,keys,name,1)

# the main guard, calls the main() function only if you run this program as a stand-alone program
if __name__ == "__main__":
    main()
