import pandas as pd
from googleapiclient.discovery import build
import streamlit as st
import datetime
import plotly.express as px
import mysql.connector
import isodate

# Api connection details
Api_Key = "AIzaSyDTcodc_UrO3gRXodqa6sWZp7FBV4tGktw"
Api_Name = "youtube"
Api_Version = "v3"

def Api_connect():
    youtube = build(Api_Name, Api_Version, developerKey=Api_Key)
    return youtube

#Getting channels details
def get_channel_info(youtube, channel_id):
    request = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        id=channel_id)
    response = request.execute()

    data = []
    for i in response["items"]:
        data.append({"Channel_Name": i["snippet"]["title"],
            "Channel_Id": i["id"],
            "Subscribers": i["statistics"]["subscriberCount"],
            "Views": i["statistics"]["viewCount"],
            "Total_videos": i["statistics"]["videoCount"],
            "Channel_description": i["snippet"]["description"],
            "Playlist_Id": i["contentDetails"]["relatedPlaylists"]["uploads"]})
    return data

#Getting video ids
def get_video_ids(youtube, channel_id):
    video_ids = []
    response = youtube.channels().list(
        id=channel_id,
        part='contentDetails' ).execute()
    playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    next_page_token = None

    while True:
        response = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token).execute()

        for item in response['items']:
            video_ids.append(item['snippet']['resourceId']['videoId'])

        next_page_token = response.get('nextPageToken')

        if not next_page_token:
            break

    return video_ids

#Function to parse ISO 8601 duration to HH:MM:SS format
# Duration Format change
def duration_to_seconds(Duration):
     duration = isodate.parse_duration(Duration)
     hours = duration.days * 24 + duration.seconds // 3600
     minutes = (duration.seconds % 3600) // 60
     seconds = duration.seconds % 60
     total_seconds = hours * 3600 + minutes * 60 + seconds
     return total_seconds

#Getting video details
def get_Video_Details(youtube, video_ids):
    Video_data = []

    for video_id in video_ids:
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id)
        response = request.execute()

        for item in response["items"]:
            publish_date_str = item['snippet']['publishedAt']
            publish_date = datetime.datetime.strptime(publish_date_str, '%Y-%m-%dT%H:%M:%SZ')
            formatted_publish_date = publish_date.strftime('%Y-%m-%d %H:%M:%S')

            data = {'Channel_Name': item['snippet']['channelTitle'],
                'channel_Id': item['snippet']['channelId'],
                'Video_Id': item['id'],
                'Title': item['snippet']['title'],
                'Tags': item['snippet'].get('tags'),
                'Thumbnail': item['snippet']['thumbnails']['default']['url'],
                'Description': item['snippet'].get('description'),
                'Publishdate': formatted_publish_date,
                'Duration': duration_to_seconds(item['contentDetails'].get('duration')),
                'Views': item['statistics'].get('viewCount'),
                'Likes': item['statistics'].get('likeCount'),
                'Comments': item['statistics'].get('commentCount'),
                'Favorite_count': item['statistics'].get('favoriteCount'),
                'Definition': item['contentDetails']['definition'],
                'Caption_Status': item['contentDetails']['caption']}
            Video_data.append(data)
    return Video_data

#Getting comment details
def get_comment_Details(youtube, video_ids):
    Comment_data = []
    try:
        for video_id in video_ids:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=50)
            response = request.execute()

            for item in response['items']:
                publish_date_str = item['snippet']['topLevelComment']['snippet']['publishedAt']
                publish_date = datetime.datetime.strptime(publish_date_str, '%Y-%m-%dT%H:%M:%SZ')
                formatted_publish_date = publish_date.strftime('%Y-%m-%d %H:%M:%S')
                data = {'Comment_id': item['snippet']['topLevelComment']['id'],
                    'Video_id': item['snippet']['topLevelComment']['snippet']['videoId'],
                    'Comment_text': item['snippet']['topLevelComment']['snippet']['textDisplay'],
                    'Comment_Author': item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                    'Comment_Published':  formatted_publish_date}
                Comment_data.append(data)
    except Exception as e:
        print("Error retrieving comments:", e)
    return Comment_data

#Getting playlist details
def get_playlist_details(youtube, channel_id):
    next_page_token = None
    All_data = []
    while True:
        request = youtube.playlists().list(
            part='snippet,contentDetails',
            channelId=channel_id,
            maxResults=50,
            pageToken=next_page_token)
        response = request.execute()

        for item in response['items']:
            data = {'Playlist_Id': item['id'],
                'Title': item['snippet']['title'],
                'Channel_Id': item['snippet']['channelId'],
                'Channel_Name': item['snippet']['channelTitle'],
                'PublishedAt': item['snippet']['publishedAt'],
                'Video_count': item['contentDetails']['itemCount']}
            All_data.append(data)

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return All_data

#My SQL Connection
mysql_host = "localhost"
mysql_user = "root"
mysql_password = "Raj$1006"
mysql_database = "youtubedata"
mysql_port = "3306"

#Connection to MySQL database
def connect_to_mysql():
    try:
        conn = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            port=mysql_port)
        print("Connected to MySQL database successfully")
        return conn
    except mysql.connector.Error as e:
        print("Error connecting to MySQL database:", e)
        return None

# Function to create tables in MySQL
def create_tables(conn):
    cursor = conn.cursor()

    # Table creation queries
    #Channels Table
    channel_table_query = """CREATE TABLE IF NOT EXISTS channel_data (
        Channel_Name VARCHAR(255),
        Channel_Id VARCHAR(255) NOT NULL,
        Subscribers INT,
        Views INT,
        Total_videos INT,
        Channel_description TEXT,
        Playlist_Id VARCHAR(255),
        PRIMARY KEY(Channel_Id))"""
    
    #Videos Table
    video_table_query = """CREATE TABLE IF NOT EXISTS video_data (
        Channel_Name VARCHAR(255),
        Channel_Id VARCHAR(255),
        Video_Id VARCHAR(255),
        Title VARCHAR(255),
        Tags TEXT,
        Thumbnail TEXT,
        Description TEXT,
        Publishdate DATETIME,
        Duration INT,
        Views INT,
        Likes INT,
        Comments INT,
        Favorite_count INT,
        Definition VARCHAR(255),
        Caption_Status VARCHAR(255),
        PRIMARY KEY(Video_Id))"""
    
    #Comments Table
    comment_table_query = """CREATE TABLE IF NOT EXISTS comment_data (
        Comment_id VARCHAR(255),
        Video_id VARCHAR(255),
        Comment_text TEXT,
        Comment_Author VARCHAR(255),
        Comment_Published DATETIME,
        PRIMARY KEY (Comment_id))"""
    
    #Playlists Table
    playlist_table_query = """CREATE TABLE IF NOT EXISTS playlist_data (
        Playlist_Id VARCHAR(255),
        Title VARCHAR(255),
        Channel_Id VARCHAR(255),
        Channel_Name VARCHAR(255),
        PublishedAt DATETIME,
        Video_count INT)"""
    
    try:
        cursor.execute(channel_table_query)
        cursor.execute(video_table_query)
        cursor.execute(comment_table_query)
        cursor.execute(playlist_table_query)

        conn.commit()
        print("Tables created successfully in MySQL")
    except mysql.connector.Error as e:
        print("Error creating tables in MySQL:", e)
        conn.rollback()
    finally:
        cursor.close()

# Test the functions
conn = connect_to_mysql()
if conn is not None:
    create_tables(conn)
    conn.close()

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Raj$1006",
    database="youtubedata",
    port="3306")

# Function to insert channel details into MySQL database
def insert_channel_info_to_mysql(conn, channel_info):
    cursor = conn.cursor()
    try:
        for info in channel_info:
            
            insert_query = """INSERT INTO channel_data (Channel_Name, Channel_Id, Subscribers, Views, Total_videos, Channel_description, Playlist_Id) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                       
            cursor.execute(insert_query, (info["Channel_Name"], info["Channel_Id"], info["Subscribers"], info["Views"], info["Total_videos"], info["Channel_description"], info["Playlist_Id"]))
        
        conn.commit()
        return "Success"
    except mysql.connector.Error as e:
        return "Duplicate"
        conn.rollback()
    finally:
        cursor.close()

# Function to insert video data into MySQL database
def insert_video_data_to_mysql(conn, video_data):
    cursor = conn.cursor()
    try:
        for data in video_data:
            tags = data.get('Tags', [])
            if not isinstance(tags, list):
                tags = [tags]  
            tags = [tag for tag in tags if tag is not None]
            insert_query = """
            INSERT INTO Video_data (Channel_Name, Channel_Id, Video_Id, Title, Tags, Thumbnail, Description, Publishdate, Duration, Views, Likes, Comments, Favorite_count, Definition, Caption_Status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            # Execute the query with data from the video_data list
            cursor.execute(insert_query, (data['Channel_Name'],
                data['channel_Id'],
                data['Video_Id'],
                data['Title'],
                ",".join(tags),  
                data['Thumbnail'],
                data.get('Description', ''),
                data['Publishdate'],
                data['Duration'],
                data['Views'],
                data.get('Likes', 0),  
                data.get('Comments', 0),  
                data.get('Favorite_count', 0),  
                data['Definition'],
                data['Caption_Status']))
            
        # Commit the changes to the database
        conn.commit()
        print("Video data inserted into MySQL successfully!")
    except mysql.connector.Error as e:
        print("Error inserting video data into MySQL:", e)
        conn.rollback()
    finally:
        cursor.close()


# Function to insert comment data into MySQL database
def insert_comment_data_to_mysql(conn, comment_data):
    cursor = conn.cursor()
    try:
        for data in comment_data:
            insert_query = """INSERT INTO comment_data (Comment_id, Video_id, Comment_text, Comment_Author, Comment_Published) 
            VALUES (%s, %s, %s, %s, %s)"""
           
            cursor.execute(insert_query, (data['Comment_id'],
                data['Video_id'],
                data['Comment_text'],
                data['Comment_Author'],
                data['Comment_Published']))
        
        # Commit the changes to the database
        conn.commit()
        print("Comment data inserted into MySQL successfully!")
    except mysql.connector.Error as e:
        print("Error inserting comment data into MySQL:", e)
        conn.rollback()
    finally:
        cursor.close()

# Function to insert playlist data into MySQL database
def insert_playlist_data_to_mysql(conn, playlist_data):
    cursor = conn.cursor()
    try:
        for data in playlist_data:
            insert_query = """INSERT INTO playlist_data (Playlist_Id, Title, Channel_Id, Channel_Name, PublishedAt, Video_count) 
            VALUES (%s, %s, %s, %s, %s, %s)"""
          
            cursor.execute(insert_query, (data['Playlist_Id'],
                data['Title'],
                data['Channel_Id'],
                data['Channel_Name'],
                data['PublishedAt'].replace("T", " ").replace("Z", " "),
                data['Video_count']))
        
        # Commit the changes to the database
        conn.commit()
        print("Playlist data inserted into MySQL successfully!")
    except mysql.connector.Error as e:
        print("Error inserting playlist data into MySQL:", e)
        conn.rollback()
    finally:
        cursor.close()

#Streamlit
st.title(":blue[Channel Data Collection]")
st.write("This Data collection zone can collect data by using channel id  and gives all the channel details,playlist details,comment details and video details")
                    
youtube = Api_connect()

channel_id_input_placeholder = 'channel_id_input'
channel_id = st.text_input('Enter the Channel ID', key=channel_id_input_placeholder)

if len(channel_id)>0:
    
    if st.button("Upload Data"):
        # Retrieving data from YouTube API
        playlist_data = get_playlist_details(youtube, channel_id)
        Video_data = get_video_ids(youtube,channel_id)
        comment_data = get_comment_Details(youtube, Video_data)
        video2 = get_Video_Details(youtube,Video_data)
        channel_data = get_channel_info(youtube, channel_id)

        # Establishing connection to MySQL database
        conn = connect_to_mysql()

        # Creating tables if they don't exist
        if conn is not None:
            create_tables(conn)

            # Inserting data into MySQL tables
            result = insert_channel_info_to_mysql(conn, channel_data)
            if result == "Success":
                insert_video_data_to_mysql(conn, video2)
                insert_comment_data_to_mysql(conn, comment_data)
                insert_playlist_data_to_mysql(conn, playlist_data)
                st.write("Data migrated to MySQL successfully!")
            else:
                st.write("Duplicate Data")

            # Closing the MySQL connection
            conn.close()

# MySQL connection configuration
mysql_host = "localhost"
mysql_user = "root"
mysql_password = "Raj$1006"
mysql_database = "youtubedata"
mysql_port = "3306"

# Function to connect to MySQL database
def connect_to_mysql():
    try:
        conn = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            port=mysql_port
        )
        print("Connected to MySQL database successfully")
        return conn
    except mysql.connector.Error as e:
        print("Error connecting to MySQL database:", e)
        return None


def execute_query(query):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Raj$1006",
        database="youtubedata",
        port="3306"
    )
    cursor = mydb.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    mydb.close()
    return data

st.title(":orange[Queries and their Result]")
question = st.selectbox("Select Your Question To Display The Query",
                        ("What are the names of all the videos and their corresponding channels?",
                        "Which channels have the most number of videos, and how many videos do they have?",
                        "What are the top 10 most viewed videos and their respective channels?",
                        "How many comments were made on each video, and what are their corresponding video names?",
                        "Which videos have the highest number of likes, and what are their corresponding channel names?",
                        "What is the total number of likes for each video, and what are their corresponding video names?",
                        "What is the total number of views for each channel, and what are their corresponding channel names?",
                        "What are the names of all the channels that have published videos in the year 2022?",
                        "What is the average duration of all videos in each channel, and what are their corresponding channel names?",
                        "Which videos have the highest number of comments, and what are their corresponding channel names?"),
                        )

#QUESTION 1
if question == "What are the names of all the videos and their corresponding channels?":
     query = """SELECT c.Channel_Name, v.Title 
        FROM channel_data AS c 
        JOIN video_data AS v 
        ON c.Channel_Id = v.Channel_Id;"""
     result = execute_query(query)
     df1 = pd.DataFrame(result, columns=["Channel_Name","Title"])
     st.dataframe(df1,hide_index=True)

#QUESTION 2
elif question == "Which channels have the most number of videos, and how many videos do they have?":
        query = """SELECT Channel_Name, Total_videos 
            FROM channel_data
            ORDER BY Total_videos DESC;"""
        result = execute_query(query)
        df2 = pd.DataFrame(result, columns=["Channel_Name", "Total_videos"])
        st.dataframe(df2,hide_index=True)

        fig = px.bar(df2, x='Channel_Name', y='Total_videos', title='Channels with Most Videos',
                 labels={'Total_videos': 'Number of Videos', 'Channel_Name': 'Channel'})

    # Update layout
        fig.update_layout(xaxis_title='Channel', yaxis_title='Number of Videos')

        # Display the chart using Streamlit
        st.title(":grey[Visualization:]")
        st.plotly_chart(fig)

#QUESTION 3
elif question == "What are the top 10 most viewed videos and their respective channels?":
        query = """select Channel_Name,Title,Views from video_data
                order by Views desc limit 10;"""             
        result = execute_query(query)
        df3 = pd.DataFrame(result, columns=["Channel_Name", "Title","Views"])
        st.dataframe(df3,hide_index=True)

        fig = px.bar(df3, x='Channel_Name', y='Views', text='Title', title='Top 10 Most Viewed Videos by Channel')
        fig.update_traces(textposition='outside')
        fig.update_layout(xaxis_title='Channel Name', yaxis_title='Views')
        # st.write("Visualization:")
        st.title(":grey[Visualization:]")
        st.plotly_chart(fig)

#QUESTION 4
elif question == "How many comments were made on each video, and what are their corresponding video names?" :
        query = """Select c.Channel_Name, v.comments,v.Title from channel_data as c join video_data as v on c.Channel_ID=v.Channel_ID;"""
        result = execute_query(query)
        df4 = pd.DataFrame(result, columns=["Channel_Name", "Comments","Title"])
        st.dataframe(df4,hide_index=True)

        fig = px.bar(df4, x='Title', y='Comments', color='Channel_Name', title='Number of Comments on Each Video')
        fig.update_layout(xaxis_title='Video Title', yaxis_title='Number of Comments', legend_title='Channel Name')
        st.title(":grey[Visualization:]")
        st.plotly_chart(fig)

#QUESTION 5
elif question == "Which videos have the highest number of likes, and what are their corresponding channel names?" :
        query = """select c.Channel_Name,v.Title,v.Likes from channel_data as c join video_data as v on c.Channel_ID=v.Channel_ID
                order by v.Likes desc;"""         
        result = execute_query(query)
        df5 = pd.DataFrame(result, columns=["Channel_Name", "Title","Likes"])
        st.dataframe(df5,hide_index=True)

        fig = px.bar(df5, x='Title', y='Likes', color='Channel_Name', title='Number of Likes on Each Video')
        fig.update_layout(xaxis_title='Video Title', yaxis_title='Number of Likes', legend_title='Channel Name')
        st.title(":grey[Visualization:]")
        # st.write("Visualization:")
        st.plotly_chart(fig)

#QUESTION 6
elif question == "What is the total number of likes for each video, and what are their corresponding video names?" :
        query = """SELECT Title, SUM(Likes) AS Total_Likes
                FROM video_data
                GROUP BY Title
                ORDER BY Total_Likes DESC;"""
        result = execute_query(query)
        df6 = pd.DataFrame(result, columns=[ "Title","Likes"])
        st.dataframe(df6,hide_index=True)

        fig = px.bar(df6, x='Title', y='Likes', title='Total Number of Likes for Each Video')
        fig.update_layout(xaxis_title='Video Title', yaxis_title='Total Number of Likes')
        # st.write("Visualization:")
        st.title(":grey[Visualization:]")
        st.plotly_chart(fig)

#QUESTION 7
elif question == "What is the total number of views for each channel, and what are their corresponding channel names?" :
        query = """select Channel_Name,views from channel_data order by views desc;"""        
        result = execute_query(query)
        df7 = pd.DataFrame(result, columns=[ "Channel_Name","views"])
        st.dataframe(df7,hide_index=True)

        fig = px.bar(df7, x='Channel_Name', y='views', title='Total Number of Views for Each Channel')
        fig.update_layout(xaxis_title='Channel Name', yaxis_title='Total Number of Views')
        # st.write("Visualization:")
        st.title(":grey[Visualization:]")
        st.plotly_chart(fig)

#QUESTION 8
elif question == "What are the names of all the channels that have published videos in the year 2022?" :
        query = """select Channel_Name from video_data
                where EXTRACT(YEAR FROM Publishdate) = 2022;"""        
        result = execute_query(query)
        df8 = pd.DataFrame(result, columns=[ "Channel_Name"])
        st.dataframe(df8,hide_index=True)

        fig = px.histogram(df8, x='Channel_Name', title='Channels that Published Videos in 2022')
        fig.update_layout(xaxis_title='Channel Name', yaxis_title='Frequency')
        # st.write("Visualization:")
        st.title(":grey[Visualization:]")
        st.plotly_chart(fig)

#QUESTION 9
elif question == "What is the average duration of all videos in each channel, and what are their corresponding channel names?" :
        query = """SELECT c.Channel_Name, AVG(v.Duration) AS Avg_Duration
                FROM channel_data c
                JOIN video_data v ON c.Channel_Id = v.Channel_Id
                GROUP BY c.Channel_Name;"""                
        result = execute_query(query)
        df9 = pd.DataFrame(result, columns=[ "Channel_Name","Avg_Duration"])
        st.dataframe(df9,hide_index=True)

        fig = px.bar(df9, x='Channel_Name', y='Avg_Duration', title='Average Duration of Videos in Each Channel')
        fig.update_layout(xaxis_title='Channel Name', yaxis_title='Average Duration')
        # st.write("Visualization:")
        st.title(":grey[Visualization:]")
        st.plotly_chart(fig)

#QUESTION 10
elif question == "Which videos have the highest number of comments, and what are their corresponding channel names?" :
        query = """SELECT c.Channel_Name, v.Title, COUNT(co.Comment_Id) AS Num_Comments
                FROM channel_data c
                JOIN video_data v ON c.Channel_Id = v.Channel_Id
                LEFT JOIN comment_data co ON v.Video_Id = co.Video_Id
                GROUP BY c.Channel_Name, v.Title
                ORDER BY Num_Comments DESC
                LIMIT 10;"""        
        result = execute_query(query)
        df10 = pd.DataFrame(result, columns=[ "Channel_Name","Title","Num_Comments"])
        st.dataframe(df10,hide_index=True)

        fig = px.bar(df10, x='Title', y='Num_Comments', color='Channel_Name', title='Videos with the Highest Number of Comments')
        fig.update_layout(xaxis_title='Video Title', yaxis_title='Number of Comments', legend_title='Channel Name')
        # st.write("Visualization:")
        st.title(":grey[Visualization:]")
        st.plotly_chart(fig)

#Youtube channel IDs

# My coding dairy - "UC_-Sg3dW0yIathaX7-RtJMQ"
# Gokul M - "UCImOs9CgQWVYHR3BgIsP9Gw"
# Balachandra - "UCEdNYjOHEiwA1kiPoI5igKw"
# Surendar Manoj - "UCF-DSCW_s3SUafgpt7-QtzA"
# Saraswathi - "UCEKXZbTmSNxl-r7MGYiQ1SQ"
# Be Positive Tamizha - "UCLcYzaJ9s6dEHRyZvm6vfqQ"
# Govt Exam Aspirant - "UCXeF1eZCihpE-zPx0AzmwVw"
# Kanthi Kalyan - "UC0Ti-l8IQKalQai2EXQs_pg"
# Kulkarni Academy Of Mechanical Engineering - "UCr_KAKlfAStAojEwQm4QHMQ"
# Aravindh Shanmugam - "UCnIc3nO0w-64NaMoe30ysxg"
  