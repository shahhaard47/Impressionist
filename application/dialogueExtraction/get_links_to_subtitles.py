"""
Get links to Friends episodes 

From http://www.livesinabox.com/friends/scripts.shtml

Haard @ Impressionist
"""


import os

CONTENT_DIR = "../../contentData/"
# don't run this script from anywhere else or if CONTENT_DIR is not at above location
if (not os.path.isdir(CONTENT_DIR)):
    print("Using relative paths. Please run this script from inside application/dialogueExtraction/ OR make sure "+CONTENT_DIR+" exists.")
    exit()

import sys
import re
from transcript_to_vtt import getFriendsDialogueDichotomy, addCharNames
from bs4 import BeautifulSoup
import requests

def getFriendsTranscriptsLinks(
    linkHome="http://www.livesinabox.com/friends/",
    linkEpisodes="scripts.shtml",
    season=None, # means all seasons
    episode=None # means all episodes
):
    """Gets links for `season` and `episode` for Friends from `livesinabox.com/friends`
    """
    linkEpisodes = linkHome + "scripts.shtml"
    page = requests.get(linkEpisodes) # try the following
    soup = BeautifulSoup(page.content, 'html5lib')

    links_with_tags = soup.find_all('li')

    episode_details = [] # info tuples (str link, int seasonNum, int episodeNum, str episodeTitle)
    couldntParse = [] # tuples (str tag, str error)
    for ii, tag in enumerate(links_with_tags):
        strtag = str(tag)
        text = tag.get_text()
        tmp = text.split(":") # splitting `episode ###: The one with...`
        
        # if (len(tmp) is 2):  
        if "Episode" in tmp[0] or "Epsiode" in tmp[0] or "Episdoe" in tmp[0]:
            if (len(tmp) >= 2):
                tmp[1] = " ".join(tmp[1:])
            else:
                couldntParse.append((strtag), "Found episode but splits to less than 2. Skipping...")
                continue
        else:
            couldntParse.append((strtag, "Couldn't parse tag.get_text(). Skipping...", "; tag.get_text() =", tag.get_text()))
            continue

        episodeStr = tmp[0]
        episodeStr = episodeStr.split() # splitting `episode ###` into two
        if (len(episodeStr) is not 2): 
            couldntParse.append((strtag, "Expected episodeStr (`episode ###`) to split into 2. Skipping..."))
            continue
        
        # get seasonNum and episodeNum
        episodeStr = episodeStr[1]
        if (len(episodeStr) is 3): # for seasons 1-9 (Friends)
            seasonNum = episodeStr[0]
            episodeNum = episodeStr[1:]
        elif (len(episodeStr) is 4): # if season is 10
            seasonNum = episodeStr[:2]
            episodeNum = episodeStr[2:]
        else:
            couldntParse.append((strtag, "Unable to parse episodeNum (#### or ###). Skipping..."))
            continue

        # get epiodeTitle
        episodeTitle = tmp[1]
        episodeTitle = episodeTitle.strip()
        episodeTitle = " ".join(episodeTitle.split())
        
        # get link
        link = re.findall(r'(?:href=\")(.*html?)(?=\">)', str(tag))
        if len(link) is 1: 
            link = link[0]
        else:
            couldntParse.append((strtag, "Unable to find link. Skipping..."))
            continue
        
        seasonNum = int(seasonNum)
        episodeNum = int(episodeNum)
        info = (linkHome + link, seasonNum, episodeNum, episodeTitle)
        if season is None: episode_details.append(info)
        else:
            if season is seasonNum:
                if episode is None or episode is episodeNum:
                    episode_details.append(info)
    return episode_details, couldntParse

def _checkAndCreateFolder(folderPath, verbose=False):
    """Create folder if doesn't exist"""
    if (not os.path.isdir(folderPath)):
        if verbose: print("Creating:", folderPath)
        os.makedirs(folderPath)

def _getFilesFrom(folderPath, extension="all", verbose=False):
    """returns list of files from `folderPath` 
    example: _getFileFrom(/folder/name, extension='.csv')
    """
    files = os.listdir(folderPath)
    # files = [os.path.join(folderPath, f) for f in files] # don't return full paths
    newFiles = [] # return this
    if extension is "all": return files
    else:
        for f in files:
            _, fext = os.path.splitext(f)
            if fext == extension: newFiles.append(f)
        return newFiles

def _writeDiagsToCSV(tuplesList, fileName, delim=","):
    print("_writeDiagsToCSV not implemented yet")



def createContentDirsFriends(season=2, episode=None, folderPath=None, transcriptLink=None, extractCharacters=False, saveTranscriptToCSV=False, verbose=False):
    """Create folders inside contentData folder
    TODO: add a loop to do all seasons
    `extractCharacters`

    if `folderPath` and `transcriptLink` contain value
        - don't need to create seasona and episode folders
            - they will be created using path
        - transcript link will be used to get char names
    """
    # Create Friends home directory
    friendsDir = os.path.join(CONTENT_DIR, "tvShows/Friends")
    _checkAndCreateFolder(friendsDir)

    if (folderPath is not None and transcriptLink is not None):
        print(folderPath)
        print(transcriptLink)

        episodes = [(folderPath, transcriptLink)]
    else:
        # initialize directories inside Friends
        episodes, couldntParse = getFriendsTranscriptsLinks(season=season, episode=episode)
        print("------------Couldn't parse------------")
        for c in couldntParse: print(c)
        print("--------------------------------------")
        assert (len(episodes) is not 0), "no episodes were extracted"

        seasonNum = episodes[0][1]
        if (seasonNum < 10): seasonNum = "0" + str(seasonNum)
        seasonDir = os.path.join(friendsDir, seasonNum)
        # create folder for season 02
        _checkAndCreateFolder(seasonDir)
    
    for ep in episodes:

        if (folderPath is not None and transcriptLink is not None):
            fullEpisodeFolderName, link = ep
        else:
            num = str(ep[2]) + "-"
            name = ep[3]
            name = "-".join(name.split(" "))
            episodeFolderName = num+name
            # remove any \' from name
            episodeFolderName = episodeFolderName.replace("'", "")
            # FIXME: replace dots in name like "Ross-and-rachel...You-Know"
            fullEpisodeFolderName = os.path.join(seasonDir, episodeFolderName)
            if ("'" in fullEpisodeFolderName):
                print("apostrophe in path. not supported yet. please change names")
                continue
            print(fullEpisodeFolderName)
            # _checkAndCreateFolder(fullEpisodeFolderName)
            link = ep[0]
            
        if (extractCharacters):
            # get transcript and character name pairs
            print("----------------------------------------------------------------------------")
            print("**Extracting characters for :", fullEpisodeFolderName)
            print("**FROM: ", link)
            print("----------------------------------------------------------------------------")

            transcriptPairs = getFriendsDialogueDichotomy(link)
            
            if (saveTranscriptToCSV):
                csvFileName =  "transcript.csv"
                fullcsvFileName = os.path.join(fullEpisodeFolderName, csvFileName)
                print("Writing transcriptPairs to CSV file:", fullcsvFileName)
                _writeDiagsToCSV(transcriptPairs, fullcsvFileName, delim=",")
            
            vttFiles = _getFilesFrom(fullEpisodeFolderName, extension=".vtt")
            fullInputSubsPath = ""
            fullOutputSubsPath = ""
            if (len(vttFiles) == 1): # there's only .vtt file (must be from netflix subs)
                subs = vttFiles[0]
                fullInputSubsPath = os.path.join(fullEpisodeFolderName, subs)
                if ("netflix_subs" in subs):
                    outSubs = subs.replace("netflix_subs", "labeled_subs")
                    fullOutputSubsPath = os.path.join(fullEpisodeFolderName, outSubs)
            elif (len(vttFiles) > 1):
                # rename old one
                for f in vttFiles:
                    if "netflix_subs" in f:
                        fullInputSubsPath = os.path.join(fullEpisodeFolderName, f)
                        outSubs = f.replace("netflix_subs", "labeled_subs")
                        fullOutputSubsPath = os.path.join(fullEpisodeFolderName, outSubs)
                    elif "labeled_subs" in f:
                        num = 1
                        while (num < 11):
                            old = f.replace("labeled_subs", str(num)+"-old_labeled")
                            fullOld = os.path.join(fullEpisodeFolderName, old)
                            if not (os.path.exists(fullOld)): 
                                # rename f_full -> fullOld
                                f_full = os.path.join(fullEpisodeFolderName, f)
                                os.rename(f_full, fullOld)
                                break
                            num += 1
            
            if fullInputSubsPath != "" and fullOutputSubsPath != "":
                print("getting charNames....")
                addCharNames(transcriptPairs, fullInputSubsPath, fullOutputSubsPath, verbose=True, detailedVerbose=False,
                             interactive=True, interactiveResolve=False, specialInitialMaxNotMatchedBeforeMovingOn=250)
            else:
                print("netflix_subs_...vtt file not found. Moving on.")


def getOfficeTranscriptPairsFromDir(directory, delim=';'):
    """Get tuples of transcripts (CHARNAME, dialogue)
    """
    transcript = "csvTranscript.csv"
    # check existence of transcript
    metaFile = os.path.join(directory, transcript)
    if not os.path.exists(metaFile): 
        print(transcript, " not found")
        return []
    
    pairs = []
    with open(metaFile, 'r') as file:
        for line in file:
            line = line.strip()
            pairs.append(tuple(line.split(delim)))

    return pairs

def getNetflixSubsVTT(directory):
    files = _getFilesFrom(directory, extension='.vtt')
    netflix_sub = ''    
    for file in files:
        if "netflix_subs_" in file:
            netflix_sub = file
            return os.path.join(directory, netflix_sub)
    return ''

if __name__ == "__main__":
    # support office
    # season 1 not supported: 
    # season 2 not supported: 1, 11
    if (len(sys.argv) < 3):
        print("Usage: python ", sys.argv[0], "<season|episode> <directory> [--interactive]")
        print("--interactive also turns on verbose")
        exit()
    choice = sys.argv[1]
    directory = sys.argv[2]
    intResolve = False
    if (len(sys.argv) == 4):
        if sys.argv[3] == "--interactive":
            intResolve = True
    if (choice == 'season'):
        all_episodes = sorted(os.listdir(directory))
        all_episodes = [os.path.join(directory, ep) for ep in all_episodes]
    elif (choice == 'episode'):
        all_episodes = [directory]
    for episodeDir in all_episodes:
        if not os.path.isdir(episodeDir): continue
        pairs = getOfficeTranscriptPairsFromDir(episodeDir)

        fullInputSubs = getNetflixSubsVTT(episodeDir)
        if fullInputSubs == '':
            print("error getting netflix_subs_ file")
            exit()
        fullOutputSubs = fullInputSubs.replace('netflix_subs_', 'labeled_subs_')
        print("---------------------------------")
        print("input subs:", fullInputSubs)
        # print(fullOutputSubs)
        addCharNames(pairs, fullInputSubs, fullOutputSubs, verbose=intResolve, detailedVerbose=False, interactive=True, interactiveResolve=intResolve)

    # support friends episodes
    # episodeNum = None
    # folderPath = None
    # transcriptLink = None
    # if (len(sys.argv) == 2): episodeNum = int(sys.argv[1])
    # elif (len(sys.argv) == 3): # args folder and link
    #     episodeNum = None
    #     folderPath = sys.argv[1]
    #     transcriptLink = sys.argv[2]
    # createContentDirsFriends(season=2, episode=episodeNum, folderPath=folderPath, transcriptLink=transcriptLink,  extractCharacters=True, saveTranscriptToCSV=False, verbose=True)

    
    
    
    
    
    
    
            


