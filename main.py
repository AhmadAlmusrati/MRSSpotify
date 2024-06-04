#   First I import all of the required packages that I need for the project.
import os
import pylast
import time
import webbrowser
import sqlite3
import random

#   This is how the program connects to the last.fm website 
key = os.path.join(os.path.expanduser("~"), ".session_key")
network = pylast.LastFMNetwork("a2e244b572b6028c0a82608b2d72885e", "585f3d6428dae988e941da614f7d62f1",)
skg = pylast.SessionKeyGenerator(network)
url = skg.get_web_auth_url()

#   Gets the username of the user to access their account information, this is also where the program asks you to authenticate its access to your account.
username = input("Please enter your Last.FM username here: ")
print(f"Please authorize this script to access your account: {url}\n")

webbrowser.open(url)

while True:
    try:
        session_key = skg.get_web_auth_session_key(url)
        with open(key, "w") as f:
            f.write(session_key)
        break
    except pylast.WSError:
        time.sleep(1)

#   Creation of the session key (required to do literally anything here).
network.session_key = session_key
print(network.session_key)
user = pylast.User(username, network)
exit = False

def InputIntoSongDB(raw):
    #   Connecting to the Database
    num = 0
    sqliteConnection = sqlite3.connect("userdata.db")
    cursor = sqliteConnection.cursor()
    data = cursor.execute("SELECT * FROM TopSongs;")
    #   Checks to see if there is already pre-existing data in the database
    for row in data:
        num = num + 1
    #   If there is it will delete the data
    if num > 0:
        deletequery = f"DELETE FROM TopSongs;"
        cursor.execute(deletequery)
    #   And then insert the new data into the database.
    for i in range(0, len(raw)):
        position = i
        name = raw[i][1]
        artist = raw[i][0].replace("(","",1)
        query = f"INSERT INTO TopSongs VALUES ({position}, {name}, {artist});"
        cursor.execute(query)
    sqliteConnection.commit()
    sqliteConnection.close()

def InputIntoTagDB(raw):
    #   Connecting to the Database
    num = 0
    sqliteConnection = sqlite3.connect("userdata.db")
    cursor = sqliteConnection.cursor()
    data = cursor.execute("SELECT * FROM TopTags;")
    #   Checks to see if there is already pre-existing data in the database
    for row in data:
        num = num + 1
    #   If there is it will delete the data
    if num > 0:
        deletequery = f"DELETE FROM TopTags;"
        cursor.execute(deletequery)
    #   And then insert the new data into the database.
    for i in range(0, 10):
        position = i
        name = raw[i][0]
        weight = raw[i][1]
        query = f"INSERT INTO TopTags VALUES ({position}, '{name}', {weight});"
        cursor.execute(query)
    sqliteConnection.commit()
    sqliteConnection.close()

def GetPlaylistFromSongs():
    #   Connects to the database
    sqliteConnection = sqlite3.connect("userdata.db")
    cursor = sqliteConnection.cursor()
    cursor.execute("SELECT * FROM TopSongs")
    data = cursor.fetchall()
    playlist = []
    #   Loops until there are 30 songs in the playlist
    while len(playlist) < 30:
        for i in range(0, len(data)):
            songName = data[i][1]
            artistName = data[i][2]
            #   This gets a track similar to the track inputted.
            track = network.get_track(artist= str(artistName), title= str(songName))
            similarTracks = track.get_similar(limit = 30)
            #   Some Tracks may not have any similar tracks in the website (they may be too niche).
            try:
                #   Selecting a random track
                newTrack = similarTracks[random.randint(0,len(similarTracks))]
                #   Checking if the track already exists in the playlist
                if newTrack in playlist:
                    pass
                else:
                    playlist.append(newTrack)
            except:
                pass
    #   This prints out the playlist for the user to access.
    print("Here is a playlist based on your top 10 songs:")
    for j in range (0, len(playlist)):
        print(playlist[j][0])

def GetPlaylistFromTags():
    #   Connects to the database
    totalWeight = 0
    sqliteConnection = sqlite3.connect("userdata.db")
    cursor = sqliteConnection.cursor()
    cursor.execute("SELECT * FROM TopTags")
    data = cursor.fetchall()
    playlist = []
    #   Gets the ratio of each genre required to make this a balanced list based on weight
    for j in range(0, len(data)):
        totalWeight = totalWeight + data[j][2]
    weightRatio =  30 / totalWeight
    #   Loops until there are 30 songs in the playlist
    while len(playlist) < 30:
        for i in range(0, len(data)):
            tagName = data[i][1]
            tagAdapted = pylast.Tag(tagName, network)
            weight = data[i][2]
            NOSongs = int(weightRatio * weight)
            #   Loops based on how many songs are needed from each genre.
            for k in range(0, NOSongs):
                track =  tagAdapted.get_top_tracks(limit = 10)
                print(track)
                try:
                    newTrack = track[random.randint(0, len(track))]
                    if newTrack in playlist:
                        pass
                    else:
                        playlist.append(newTrack)
                except:
                    pass
    print("Your playlist based off of your top tags is:")
    for l in range(0, len(playlist)):
        print(playlist[l][0])



#   This function requests a list of your top 10 songs of all time (since creating the last.fm account).
def TopSongsGetter(number):
    global rawdata
    songdata = user.get_top_tracks(limit= number)
    songs = str(songdata)
    rawdata = []
    songList = []
    rawSongData = songs.split("TopItem(item=pylast.Track")
    rawSongData.pop(0)
    for item in range(0,len(rawSongData)):
        splitSongList = rawSongData[item].split(",")
        Artistname = splitSongList[0].replace('(', '', 1)
        rawdata.append(splitSongList)
        songList.append(f"Song Name: {splitSongList[1]}, Artist Name: {Artistname}")
    return songList

#   This function requests a list of your top 100 songs and fetches the associated tags, then orders them based on their weight (frequency in the list) and then presents the top 10 tags.
def TopTagsGetter():
    #   Fetches the top 100 songs from your account
    songList = user.get_top_tracks(limit= 100)
    orderedTagList = []
    tagList = []
    #   Turns the song data into usable data for the API
    for i in range (0, len(songList)):
        songdata = songList[i]
        artistName = songdata[0].get_artist().get_name()
        songName = songdata[0].get_title()
        track = network.get_track(artist= str(artistName), title= str(songName))
        tags = track.get_top_tags(limit= 10)
        print(track)
        print(tags)
        #   This applies a weight variable to the listed tags.
        for j in range(0, len(tags)):
            tagdata = tags[j]
            tagName = tagdata[0].get_name()
            notInList = True
            for l in range(0, len(tagList)):
                if tagName == tagList[l][0]:
                    tagList[l][1] = tagList[l][1] + 1
                    notInList = False
            if notInList == True:
                tagList.append([tagName,1])

        print(tagList)
        #   This sorts through the code and finds the highest possible weight value in the 2D list.
        maximum = tagList[0][1]
        for m in range(0, len(tagList)):
            if maximum <= tagList[m][1]:
                maximum = tagList[m][1]
            else:
                pass
        #   Using the found maximum value, this now inserts the values of the list in descending order of weight.
        for n in range(0, maximum + 1):
            for o in range(0, len(tagList)):
                if tagList[o][1] == n:
                    orderedTagList.insert(0,tagList[o])
    return orderedTagList
    
        


#   Menu Code
while exit == False:
    menu = int(input("""
    =============================
    Welcome To The MRS System
    =============================
    Please select from below:
    1. Retrieve Top Songs
    2. Retrieve Top Tags
    3. Retrieve Recommended Songs Based on Top Songs
    4. Retrieve Recommended Songs Based on Top Tags
    5. Exit Program
    """))

    if menu == 1:
        #   Calls the top 10 songs function and presents it to the user
        songList = TopSongsGetter(10)
        print("Your Top 10 Songs according to Last.FM are:")
        for i in range(0, len(songList)):
            print(f"{i + 1}) {songList[i]}")
        InputIntoSongDB(rawdata)
    elif menu == 2:
        #   Calls the top 10 tags function and presents it to the user.
        tags = TopTagsGetter()
        #   Presenting the data to the user.
        print("Your Top 10 Tags according Last.FM are:")
        for p in range(0, 10):
            print(f"{p + 1}) {tags[p][0]}")
        InputIntoTagDB(tags)
    elif menu == 3:
        GetPlaylistFromSongs()
    elif menu == 4:
        GetPlaylistFromTags()
    elif menu == 5:
        #   Exit function
        exit = True
        print("Thank You for Using The MRS System.")