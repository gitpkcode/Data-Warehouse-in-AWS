import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

# DROP TABLES

staging_events_table_drop = "DROP TABLE IF EXISTS staging_events;"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs;"
songplay_table_drop = "DROP TABLE IF EXISTS songplays;"
user_table_drop = "DROP TABLE IF EXISTS users;"
song_table_drop = "DROP TABLE IF EXISTS songs;"
artist_table_drop = "DROP TABLE IF EXISTS artists;"
time_table_drop = "DROP TABLE IF EXISTS time;"

# CREATE TABLES

staging_events_table_create = ("""CREATE TABLE IF NOT EXISTS staging_events (
                                    artist text, 
                                    auth text, 
                                    firstName text, 
                                    gender text, 
                                    ItemInSession text,
                                    lastName text, 
                                    length float8, 
                                    level text, 
                                    location text, 
                                    method text,
                                    page text, 
                                    registration text, 
                                    sessionId int, 
                                    song text, 
                                    status int,
                                    ts BIGINT, 
                                    userAgent text, 
                                    userId int);
                            """)

staging_songs_table_create = ("""CREATE TABLE IF NOT EXISTS staging_songs( 
                                    num_songs text,
                                    artist_id text,
                                    artist_name varchar(max),
                                    artist_latitude numeric,
                                    artist_longitude numeric,
                                    artist_location text,
                                    song_id text,
                                    title text,
                                    duration float8,
                                    year int );
                              """)
                            

songplay_table_create = ("""CREATE TABLE IF NOT EXISTS songplays (
                            songplay_id INT IDENTITY(0,1) PRIMARY KEY,
                            start_time BIGINT NOT NULL,
                            user_id INT NOT NULL,
                            level VARCHAR,
                            song_id VARCHAR,
                            artist_id VARCHAR,
                            session_id INT,
                            location VARCHAR,
                            user_agent VARCHAR);
                        """)

user_table_create = ("""CREATE TABLE IF NOT EXISTS users (
                        user_id INT PRIMARY KEY,
                        first_name VARCHAR(100),
                        last_name VARCHAR(100),
                        gender VARCHAR(1),
                        level VARCHAR(8));
                    """)

song_table_create = ("""CREATE TABLE IF NOT EXISTS songs (
                        song_id VARCHAR(32) PRIMARY KEY,
                        title VARCHAR(1024),
                        artist_id VARCHAR(32),
                        year INT,
                        duration double precision);
                    """)

artist_table_create = ("""CREATE TABLE IF NOT EXISTS artists (
                          artist_id VARCHAR(32) PRIMARY KEY,
                          name VARCHAR(64),
                          location VARCHAR(256),
                          latitude VARCHAR(32),
                          longitude VARCHAR(32));
                       """)

time_table_create = ("""CREATE TABLE IF NOT EXISTS time (
                        start_time BIGINT,
                        hour INT,
                        day INT,
                        week INT,
                        month INT,
                        year INT,
                        weekday INT);
                    """)

# STAGING TABLES

staging_events_copy = ("""
                        copy staging_events
                        from {}
                        iam_role {}
                        region 'us-west-2'
                        json {};
                    """).format(config['S3']['LOG_DATA'], config['IAM_ROLE']['ARN'],config['S3']['LOG_JSONPATH'])

staging_songs_copy = ("""
                        copy staging_songs
                        from {}
                        iam_role {}
                        region 'us-west-2'
                        JSON 'auto' ;
                    """).format(config['S3']['SONG_DATA'], config['IAM_ROLE']['ARN'])



# FINAL TABLES

songplay_table_insert = ("""INSERT INTO songplays (start_time,user_id,level,song_id,artist_id,session_id,location,user_agent)
                            SELECT se.ts,
                            se.userId,
                            se.level,
                            ss.song_id,
                            ss.artist_id,
                            se.sessionId,
                            se.location,
                            se.userAgent
                            FROM staging_events se JOIN staging_songs ss ON
                            se.artist=ss.artist_name AND
                            se.song=ss.title AND
                            se.length=ss.duration
                            WHERE se.page='NextSong';
                        """)

user_table_insert = ("""INSERT INTO users (user_id, first_name, last_name, gender, level)
                        SELECT DISTINCT
                        se.userId,
                        se.firstName,
                        se.lastName,
                        se.gender,
                        se.level
                        FROM staging_events se
                        WHERE se.page='NextSong';
                    """)

song_table_insert = (""" INSERT INTO songs (song_id, title, artist_id, year, duration)
                        SELECT DISTINCT
                        ss.song_id,
                        ss.title,
                        ss.artist_id,
                        ss.year,
                        ss.duration
                        FROM staging_songs ss;
                    """)

artist_table_insert = ("""INSERT INTO artists (artist_id, name, location, latitude, longitude)
                            SELECT DISTINCT 
                            ss.artist_id,
                            ss.artist_name,
                            se.location,
                            ss.artist_latitude,
                            ss.artist_longitude
                            FROM staging_events se JOIN staging_songs ss
                            ON se.artist=ss.artist_name AND
                            se.song=ss.title AND
                            se.length=ss.duration;
                        """)

time_table_insert = ("""INSERT INTO time (start_time, hour, day, week, month, year, weekday)
                        SELECT DISTINCT 
                        ts,
                        EXTRACT(HOUR FROM start_time) AS hour,
                        EXTRACT(DAY FROM start_time) AS day,
                        EXTRACT(WEEK FROM start_time) AS week,
                        EXTRACT(MONTH FROM start_time) AS month,
                        EXTRACT(YEAR FROM start_time) AS year,
                        EXTRACT(DOW FROM start_time) AS weekday
                        FROM (SELECT DISTINCT '1970-01-01'::date + ts/1000 * interval '1 second' as start_time, ts
                        FROM staging_events);
                    """)

# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create,
                        songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop,
                      songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert,
                        song_table_insert, artist_table_insert, time_table_insert]
