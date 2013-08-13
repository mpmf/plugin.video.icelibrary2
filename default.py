#!/usr/bin/python
#IceLibrary2
#With some code borrowed from Icefilms.info v1.0.10 - anarchintosh / daledude / westcoast13 2011-07-02

############################
### Imports		 ###
############################	

import urllib2, urllib, sys, os, re, random, copy, shutil
import xbmc,xbmcplugin,xbmcgui,xbmcaddon,xbmcvfs
import threading
import trace
import urlresolver
from urllib import quote_plus
from t0mm0.common.net import Net
from t0mm0.common.addon import Addon
net = Net()



ADDON_ID = 'plugin.video.icelibrary2'
ADDON = xbmcaddon.Addon(id=ADDON_ID)
selfAddon = ADDON
addon = Addon(ADDON_ID)
icepath = selfAddon.getAddonInfo('path')
sys.path.append( os.path.join( icepath, 'resources', 'lib' ) )
art = icepath+'/resources/art'

############################
### Enviornment		 ###
############################


#import jsunpack
#import debridroutines
from BeautifulSoup import BeautifulSoup, Tag, NavigableString
#import resolvers

datapath = addon.get_profile()
cookie_path = os.path.join(datapath, 'cookies')
if not os.path.exists(cookie_path):
	os.makedirs(cookie_path)
cookie_jar = os.path.join(cookie_path, "cookiejar.lwp")
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/537.36'
ACCEPT = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
DATA_PATH = os.path.join(xbmc.translatePath('special://profile/addon_data/' + ADDON_ID), '')

if ADDON.getSetting('movie_custom_directory') == "true":
	MOVIES_PATH = ADDON.getSetting('movie_directory')
else:
	MOVIES_PATH = os.path.join(xbmc.translatePath(DATA_PATH + 'movies'), '')

if ADDON.getSetting('tv_show_custom_directory') == "true":
	TV_SHOWS_PATH = ADDON.getSetting('tv_show_directory')
else:
	TV_SHOWS_PATH = os.path.join(xbmc.translatePath(DATA_PATH + 'tvshows'), '')






STREAM_URL = ""
MOVIES_DATA_PATH = os.path.join(xbmc.translatePath(DATA_PATH + 'movies_data'), '')
TV_SHOWS_DATA_PATH = os.path.join(xbmc.translatePath(DATA_PATH + 'tvshows_data'), '')
DOWNLOAD_PATH = os.path.join(xbmc.translatePath(DATA_PATH + 'download'), '')
ICEFILMS_URL = ADDON.getSetting('icefilms-url')
ICEFILMS_REFERRER = 'http://www.icefilms.info'
ICEFILMS_AJAX = ICEFILMS_URL + '/membersonly/components/com_iceplayer/video.phpAjaxResp.php'
EXCLUDE_PROBLEM_EPISODES = True
AZ_DIRECTORIES = ['1', 'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y', 'Z']
MOVIE_YEAR = int(ADDON.getSetting('movie_minimum_year'))
TV_SHOW_YEAR = int(ADDON.getSetting('tv_show_minimum_year'))
AUTO_BEST_QUALITY = True
AUTO_DVDRIP_QUALITY = True
AUTO_PLAY_MIRRORS = True
AUTO_PLAY_PARTS = False #Not yet implemented

if ADDON.getSetting('movie_hd_only') == "true":
	MOVIES_HD_ONLY = True
else:
	MOVIES_HD_ONLY = False

if ADDON.getSetting('auto_best_quality') == "true":
	AUTO_BEST_QUALITY = True
else:
	AUTO_BEST_QUALITY = False

if ADDON.getSetting('auto_dvdrip_quality') == "true":
	AUTO_DVDRIP_QUALITY = True
else:
	AUTO_DVDRIP_QUALITY = False

if ADDON.getSetting('auto_mirror') == "true":
	AUTO_PLAY_MIRRORS = True
else:
	AUTO_PLAY_MIRRORS = False


############################
### Database		 ###
############################

#try:
DB_NAME = ADDON.getSetting('database_mysql_name')
DB_USER = ADDON.getSetting('database_mysql_host_user')
DB_PASS = ADDON.getSetting('database_mysql_host_pass')
DB_ADDRESS = ADDON.getSetting('database_mysql_host')
if ADDON.getSetting('database_mysql')=='true':
	DB_NAME = ADDON.getSetting('database_mysql_name')
	DB_USER = ADDON.getSetting('database_mysql_user')
	DB_PASS = ADDON.getSetting('database_mysql_pass')
	DB_ADDRESS = ADDON.getSetting('database_mysql_host')
	DB_TYPE = 'mysql'
	print "Connecting to MySQL database " + DB_NAME + " ON " + DB_ADDRESS
	try:	
		import mysql.connector as database
		DBH = database.connect(DB_NAME, DB_USER, DB_PASS, DB_ADDRESS, buffered=True)
	except:
		import MySQLdb as database
		DBH=database.connect(host=DB_ADDRESS,user=DB_USER,passwd=DB_PASS,db=DB_NAME)

	DBC = DBH.cursor()
	DBC.execute("SELECT idVersion FROM version")
	row = DBC.fetchone()
	DB_VERSION = str(row[0])
	print "Database is version: " + DB_VERSION

else:
	try:
		from sqlite3 import dbapi2 as database
		print "Loading sqlite3 as DB engine"
	except:
		from pysqlite2 import dbapi2 as database
		print "Loading pysqlite2 as DB engine"
  	DB_TYPE = 'sqlite'
	DB_DIR = xbmc.translatePath("special://database")
	
	directoryListing = os.listdir(DB_DIR)
	for f in directoryListing:
		match = re.match(r'MyVideos(\d).\.db', f)
		if match:
			DB_NAME = match.group(0)
			pass 
	DB_FILE = os.path.join(xbmc.translatePath("special://database"), DB_NAME)
	print "Connecting to SQLite database " + DB_FILE	
	DBH = database.connect(DB_FILE)
	DBC = DBH.cursor()
	DBC.execute("SELECT idVersion FROM version")
	row = DBC.fetchone()
	DB_VERSION = str(row[0])
	print "Database is version: " + DB_VERSION


def initilizeDatabase():
	print "Initializing database"
	if DB_TYPE == 'mysql':
		DBC.execute("CREATE TABLE IF NOT EXISTS `ice_favorites` (`id` int(11) NOT NULL AUTO_INCREMENT, `name` varchar(255) DEFAULT NULL, `url` varchar(125) DEFAULT NULL, `new` tinyint(1) DEFAULT '1', PRIMARY KEY (`id`), UNIQUE KEY `url` (`url`) ) ENGINE=InnoDB AUTO_INCREMENT=237 DEFAULT  CHARSET=latin1")
	else:
		DBC.execute("CREATE TABLE IF NOT EXISTS ice_favorites (id INTEGER PRIMARY KEY, name TEXT UNIQUE, url TEXT UNIQUE, new INTEGER default 0)")
	DBH.commit()
	
###########################
### General functions 	###
###########################

def Notification(title, message):
	xbmc.executebuiltin("XBMC.Notification("+title+","+message+")")

def xbmcpath(path,filename):
     translatedpath = os.path.join(xbmc.translatePath( path ), ''+filename+'')
     return translatedpath

def Notify(typeq,title,message,times, line2='', line3=''):
     #simplified way to call notifications. common notifications here.
     if title == '':
          title='Icefilms Notification'
     if typeq == 'small' or typeq == 'Download Alert':
          if times == '':
               times='5000'
          smallicon=handle_file('smallicon')
          xbmc.executebuiltin("XBMC.Notification("+title+","+message+","+times+","+smallicon+")")
     elif typeq == 'big':
          dialog = xbmcgui.Dialog()
          dialog.ok(' '+title+' ', ' '+message+' ', line2, line3)
     elif typeq == 'megaalert1':
          ip = xbmc.getIPAddress()
          title='Megaupload Alert for IP '+ip
          message="Either you've reached your daily download limit\n or your IP is already downloading a file."
          dialog = xbmcgui.Dialog()
          dialog.ok(' '+title+' ', ' '+message+' ')
     elif typeq == 'megaalert2':
          ip = xbmc.getIPAddress()
          title='Megaupload Info for IP '+ip
          message="No problems! You have not reached your limit."
          dialog = xbmcgui.Dialog()
          dialog.ok(' '+title+' ', ' '+message+' ')
     else:
          dialog = xbmcgui.Dialog()
          dialog.ok(' '+title+' ', ' '+message+' ')

def handle_file(filename,getmode=''):
     #bad python code to add a get file routine.
     if filename == 'smallicon':
          return_file = xbmcpath(art,'smalltransparent2.png')
     elif filename == 'mirror':
          return_file = xbmcpath(datapath,'MirrorPageSource.txt')
     elif filename == 'homepage':
          return_file = xbmcpath(art,'homepage.png')
     elif filename == 'movies':
          return_file = xbmcpath(art,'movies.png')
     elif filename == 'music':
          return_file = xbmcpath(art,'music.png')
     elif filename == 'tvshows':
          return_file = xbmcpath(art,'tvshows.png')
     elif filename == 'movies_fav':
        return_file = xbmcpath(art,'movies_fav.png')
     elif filename == 'tvshows_fav':
        return_file = xbmcpath(art,'tvshows_fav.png')

     elif filename == 'other':
          return_file = xbmcpath(art,'other.png')
     elif filename == 'search':
          return_file = xbmcpath(art,'search.png')
     elif filename == 'standup':
          return_file = xbmcpath(art,'standup.png')
     elif filename == 'megapic':
          return_file = xbmcpath(art,'megaupload.png')
     elif filename == 'shared2pic':
          return_file = xbmcpath(art,'2shared.png')
     elif filename == 'rapidpic':
          return_file = xbmcpath(art,'rapidshare.png')
     elif filename == '180pic':
          return_file = xbmcpath(art,'180upload.png')
     elif filename == 'speedypic':
          return_file = xbmcpath(art,'speedyshare.png')
     elif filename == 'vihogpic':
          return_file = xbmcpath(art,'vidhog.png')
     elif filename == 'uploadorbpic':
          return_file = xbmcpath(art,'uploadorb.png')
     elif filename == 'sharebeespic':
          return_file = xbmcpath(art,'sharebees.png')
     elif filename == 'glumbopic':
          return_file = xbmcpath(art,'glumbo.png')
     elif filename == 'movreelpic':
          return_file = xbmcpath(art,'movreel.png')
     elif filename == 'jumbopic':
          return_file = xbmcpath(art,'jumbofiles.png')
     elif filename == 'billionpic':
          return_file = xbmcpath(art,'billion.png')
     elif filename == 'localpic':
          return_file = xbmcpath(art,'local_file.jpg')

     if getmode == '':
          return return_file
     if getmode == 'open':
          try:
               opened_return_file=openfile(return_file)
               return opened_return_file
          except:
               print 'opening failed'

def RemoveDirectory(dir):
	dialog = xbmcgui.Dialog()
	if dialog.yesno("Remove directory", "Do you want to remove directory?", dir):
		if os.path.exists(dir):
			pDialog = xbmcgui.DialogProgress()
			pDialog.create(' Removing directory...')
			pDialog.update(0, dir)	
			# TODO: implement this using xbmcvfs
			# shutil.rmtree(dir)
			pDialog.close()
			Notification("Directory removed", dir)
		else:
			Notification("Directory not found", "Can't delete what does not exist.")	
	
def GetURL(url, params = None, referrer = ICEFILMS_REFERRER, cookie = None, save_cookie = False, silent = False):
     print 'GetUrl: ' + url
     print 'params: ' + repr(params)
     print 'referrer: ' + repr(referrer)
     print 'cookie: ' + repr(cookie)
     print 'save_cookie: ' + repr(save_cookie)

     if params:
        req = urllib2.Request(url, params)
        # req.add_header('Content-type', 'application/x-www-form-urlencoded')
     else:
         req = urllib2.Request(url)

     req.add_header('User-Agent', USER_AGENT)
     req.add_header('Accept', ACCEPT)

     # as of 2011-06-02, IceFilms sources aren't displayed unless a valid referrer header is supplied:
     # http://forum.xbmc.org/showpost.php?p=810288&postcount=1146
     if referrer:
         req.add_header('Referer', referrer)

     if cookie:
         req.add_header('Cookie', cookie)

     # avoid Python >= 2.5 ternary operator for backwards compatibility
     # http://wiki.xbmc.org/index.php?title=Python_Development#Version
     try:
         response = urllib2.urlopen(req)
         body = response.read()

         if save_cookie:
             setcookie = response.info().get('Set-Cookie', None)
             print "Set-Cookie: %s" % repr(setcookie)
             if setcookie:
                 setcookie = re.search('([^=]+=[^=;]+)', setcookie).group(1)
                 body = body + '<cookie>' + setcookie + '</cookie>'
    
         response.close()

     except Exception, e:
         print '****** ERROR: %s' % e
         Notify('big','Error Requesting Site','An error has occured communicating with Icefilms', '', '', 'Check your connection and the Icefilms site.' )
         body = ''
         pass

     return body
	
def PassMovieFilter(year, hd_test):
	if MOVIES_HD_ONLY:
		if hd_test != "HD":
			return False
	if MOVIE_YEAR > year:		
		return False
	return True
	
def PassTVShowFilter(year):
	if TV_SHOW_YEAR > 1900:
		try:
			year = int(show_name[len(show_name)-5:len(show_name)-1])
		except:
			year = 0
		if year < TV_SHOW_YEAR:
			return False
	return True

def MysqlEscapeString(s):
	s = s.replace('\%', '\\\%')
	s = s.replace('\\', '\\\\')		
	s = s.replace("'", "\\'")
	s = "'" + s + "'"
	return s

def CreateRecentPlaylist():
	try:
		content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<smartplaylist type="episodes">
    <name>Recently Aired</name>
    <match>all</match>
    <rule field="airdate" operator="inthelast">3 weeks</rule>
    <order direction="descending">airdate</order>
</smartplaylist>'''
		playlist_file = os.path.join(xbmc.translatePath('special://profile'), 'playlists/video/RecentlyAired.xsp')
		print "Creating " + playlist_file
		file = open(playlist_file,'w')
		file.write(content)
		file.close()
		Notification("Success", "Playlist created: Recently Aired.")
	except:
		print "Error creating xsp file"
	
def CreateStreamFile(name, href, dir, remove_year, show_name=''):
	try:
		
		if len(show_name) > 0:
			show_name = show_name + ' '
		
		filename = CleanFileName(name, remove_year) + ".strm"
		path = os.path.join(dir, filename)
		strm_string = "plugin://" + ADDON_ID + "/?href=" + urllib.quote(href) + "&mode=10&name=" + urllib.quote(show_name + name) + "&path="+ urllib.quote(path)		
		file = xbmcvfs.File(path,'w')
		file.write(strm_string)
		file.close()
	except:
		print "Error while creating strm file for : " + name
	
def DeleteFavorites():
	dialog = xbmcgui.Dialog()
	if dialog.yesno("Remove", "Do you want to remove favorites?"):
		print "Removing favorites"
		DBC.execute("DELETE FROM ice_favorites")
		DBH.commit()


def AddToFavorites(name):
	#Needed to use X:N format to not alter the names of the TV shows
	print "Adding " + name + " to favorites."
	split = name.split(":")
	tv_show_data = LoadData("TV shows", split[0] + ".dat")
	to_add = tv_show_data[int(split[1])]
	name = to_add[0]
	url = to_add[1]
	if DB_TYPE == 'mysql':
		DBC.execute("INSERT INTO ice_favorites(name, url) VALUES(%s,%s)", [name, url])
	else:
		DBC.execute("INSERT INTO ice_favorites(name, url) VALUES(?,?)", [name, url])
	DBH.commit()
	#GetEpisodes(name, url)
	Notification("Favorite added", name + " was added to favorites.")


def RemoveFromFavorites(id):
	dialog = xbmcgui.Dialog()
	if DB_TYPE == 'mysql':
		DBC.execute("SELECT name FROM ice_favorites WHERE id=%s", [id])
	else:
		DBC.execute("SELECT name FROM ice_favorites WHERE id=?", [id])
	row = DBC.fetchone()
	name = str(row[0])
	if dialog.yesno("Remove", "Do you want to remove " + name + "?"):
		print "Removing " + name + " from favorites."
		if DB_TYPE == 'mysql':	
			DBC.execute("DELETE FROM ice_favorites WHERE id=%s", [id])
		else:
			DBC.execute("DELETE FROM ice_favorites WHERE id=?", [id])
		DBH.commit()
		xbmc.executebuiltin("Container.Refresh")
		

def CreateDirectory(dir_path):
	dir_path = dir_path.strip()
	if not xbmcvfs.exists(dir_path):
		xbmcvfs.mkdirs(dir_path)
			
def CleanFileName(s, remove_year, use_encoding = False, use_blanks = True):
	if remove_year:
		s = s[0:len(s)-7]
	s = s.replace(' (Eng subs)', '')
	s = s.replace(' (eng subs)', '')
	s = s.replace(' (English subs)', '')
	s = s.replace(' (english subs)', '')
	s = s.replace(' (Eng Subs)', '')
	s = s.replace(' (English Subs)', '')
	s = s.replace('&#x26;', '&')
	s = s.replace('&#x27;', '\'')
	s = s.replace('&#xC6;', 'AE')
	s = s.replace('&#xC7;', 'C')
	s = s.replace('&#xF4;', 'o')
	s = s.replace('&#xE9;', 'e')
	s = s.replace('&#xEB;', 'e')
	s = s.replace('&#xED;', 'i')
	s = s.replace('&#xEE;', 'i')
	s = s.replace('&#xA2;', 'c')
	s = s.replace('&#xE2;', 'a')
	s = s.replace('&#xEF;', 'i')
	s = s.replace('&#xE1;', 'a')
	s = s.replace('&#xE8;', 'e')
	s = s.replace('%2E', '.')
	if use_encoding:
		s = s.replace('"', '%22')
		s = s.replace('*', '%2A')
		s = s.replace('/', '%2F')
		s = s.replace(':', ',')
		s = s.replace('<', '%3C')
		s = s.replace('>', '%3E')
		s = s.replace('?', '%3F')
		s = s.replace('\\', '%5C')
		s = s.replace('|', '%7C')
		s = s.replace('&frac12;', '%BD')
		s = s.replace('&#xBD;', '%BD') #half character
		s = s.replace('&#xB3;', '%B3')
		s = s.replace('&#xB0;', '%B0') #degree character		
	if use_blanks:
		s = s.replace('"', ' ')
		s = s.replace('*', ' ')
		s = s.replace('/', ' ')
		s = s.replace(':', ' ')
		s = s.replace('<', ' ')
		s = s.replace('>', ' ')
		s = s.replace('?', ' ')
		s = s.replace('\\', ' ')
		s = s.replace('|', ' ')
		s = s.replace('&frac12;', ' ')
		s = s.replace('&#xBD;', ' ') #half character
		s = s.replace('&#xB3;', ' ')
		s = s.replace('&#xB0;', ' ') #degree character
	s = s.strip()
	return s

def FileAlreadyExist(filename, files):
	for file in files:
		if filename == file:
			return True			
	return False

def SetupAutoUpdate():
	source_path = os.path.join(xbmc.translatePath('special://profile/'), 'autoexec.py')
	try:
		file = open(source_path, 'r')
		content=file.read()
		file.close()
		index = content.find("xbmc.executebuiltin('RunScript(" + ADDON_ID + ",\"?mode=100\")')")
		if index > 0:
			Notification("Already set up", "Auto update is already set up in autoexec.py")
			return
	except:
		content = "import xbmc\n"
	content += "\nxbmc.executebuiltin('RunScript(" + ADDON_ID + ",\"?mode=100\")')"
	
	file = open(source_path, 'w')
	file.write(content)
	file.close()
	print "autoexec.py updated to include IceFilms auto update"
	dialog = xbmcgui.Dialog()	
	dialog.ok("Auto update added to autoexec.py", "To complete the setup:", " 1) Activate auto update in IceLibrary configs.", " 2) Restart XBMC.")	
	
def SetupIceLibrary(type):
	print "Trying to add IceLibrary source paths..."
	source_path = os.path.join(xbmc.translatePath('special://profile/'), 'sources.xml')
	
	try:
		file = open(source_path, 'r')
		content=file.read()
		file.close()
		soup = BeautifulSoup(content)
	except:
		soup = BeautifulSoup()
		sources_tag = Tag(soup, "sources")
		soup.insert(0, sources_tag)
		
	if soup.find("video") == None:
		sources = soup.find("sources")
		video_tag = Tag(soup, "video")
		sources.insert(0, video_tag)
		
	video = soup.find("video")

	if type=="movies":
		CreateDirectory(MOVIES_PATH)
		if len(soup.findAll(text="Movies (Icefilms)")) < 1:
			movie_source_tag = Tag(soup, "source")
			movie_name_tag = Tag(soup, "name")
			movie_name_tag.insert(0, "Movies (Icefilms)")
			MOVIES_PATH_tag = Tag(soup, "path")
			MOVIES_PATH_tag['pathversion'] = 1
			MOVIES_PATH_tag.insert(0, MOVIES_PATH)
			movie_source_tag.insert(0, movie_name_tag)
			movie_source_tag.insert(1, MOVIES_PATH_tag)
			video.insert(2, movie_source_tag)

	if type=="TV shows":
		CreateDirectory(TV_SHOWS_PATH)
		if len(soup.findAll(text="TV Shows (Icefilms)")) < 1:	
			tvshow_source_tag = Tag(soup, "source")
			tvshow_name_tag = Tag(soup, "name")
			tvshow_name_tag.insert(0, "TV Shows (Icefilms)")
			tvshow_path_tag = Tag(soup, "path")
			tvshow_path_tag['pathversion'] = 1
			tvshow_path_tag.insert(0, TV_SHOWS_PATH)
			tvshow_source_tag.insert(0, tvshow_name_tag)
			tvshow_source_tag.insert(1, tvshow_path_tag)
			video.insert(2, tvshow_source_tag)
	
	print soup.prettify()
	string = ""
	for i in soup:
		string = string + str(i)
	
	file = open(source_path, 'w')
	file.write(str(soup))
	file.close()
	print "Source paths added!"
	
	dialog = xbmcgui.Dialog()
	dialog.ok("Source folders added", "To complete the setup:", " 1) Restart XBMC.", " 2) Set the content type of added folders.")
	#Appearently this restarted everything and not just XBMC... :(
	#if dialog.yesno("Restart now?", "Do you want to restart XBMC now?"):
	#	xbmc.restart()
	
###########################
### Login Routines	###
###########################

def LoginDebrid():
	print "Login: Real-Debrid"
	if debrid_account:
         	debriduser = selfAddon.getSetting('realdebrid-username')
         	debridpass = selfAddon.getSetting('realdebrid-password')
		try:
			rd = debridroutines.RealDebrid(cookie_jar, debriduser, debridpass)
			if rd.Login():
				if not HideSuccessfulLogin:
					Notify('small','Real-Debrid', 'Account login successful.','')
			else:
                		Notify('big','Real-Debrid','Login failed.', '')
                 		print 'Real-Debrid Account: login failed'
		except Exception, e:
			print '**** Real-Debrid Error: %s' % e
              		Notify('big','Real-Debrid Login Failed','Failed to connect with Real-Debrid.', '', '', 'Please check your internet connection.')
			pass

def LoginMovreel():
	print "Login: Movreel:";


def LoginStartup():

     #Get whether user has set an account to use.
     
     #mega_account = str2bool(selfAddon.getSetting('megaupload-account'))
     debrid_account = str2bool(selfAddon.getSetting('realdebrid-account'))
     sharebees_account = str2bool(selfAddon.getSetting('sharebees-account'))
     movreel_account = str2bool(selfAddon.getSetting('movreel-account'))
     HideSuccessfulLogin = str2bool(selfAddon.getSetting('hide-successful-login-messages'))

     #Verify Read-Debrid Account
     if debrid_account:
         debriduser = selfAddon.getSetting('realdebrid-username')
         debridpass = selfAddon.getSetting('realdebrid-password')

         try:
             rd = debridroutines.RealDebrid(cookie_jar, debriduser, debridpass)
             if rd.Login():
                 if not HideSuccessfulLogin:
                     Notify('small','Real-Debrid', 'Account login successful.','')
             else:
                 Notify('big','Real-Debrid','Login failed.', '')
                 print 'Real-Debrid Account: login failed'
         except Exception, e:
              print '**** Real-Debrid Error: %s' % e
              Notify('big','Real-Debrid Login Failed','Failed to connect with Real-Debrid.', '', '', 'Please check your internet connection.')
              pass

     #Verify ShareBees Account
     if sharebees_account:
         loginurl='http://www.sharebees.com/login.html'
         op = 'login'
         login = selfAddon.getSetting('sharebees-username')
         password = selfAddon.getSetting('sharebees-password')
         data = {'op': op, 'login': login, 'password': password}
         cookiejar = os.path.join(cookie_path,'sharebees.lwp')
        
         try:
             html = net.http_POST(loginurl, data).content
             if re.search('op=logout', html):
                net.save_cookies(cookiejar)
             else:
                Notify('big','ShareBees','Login failed.', '')
                print 'ShareBees Account: login failed'
         except Exception, e:
             print '**** ShareBees Error: %s' % e
             Notify('big','ShareBees Login Failed','Failed to connect with ShareBees.', '', '', 'Please check your internet connection.')
             pass


     #Verify MovReel Account
     if movreel_account:
         loginurl='http://www.movreel.com/login.html'
         op = 'login'
         login = selfAddon.getSetting('movreel-username')
         password = selfAddon.getSetting('movreel-password')
         data = {'op': op, 'login': login, 'password': password}
         cookiejar = os.path.join(cookie_path,'movreel.lwp')
        
         try:
             html = net.http_POST(loginurl, data).content
             if re.search('op=logout', html):
                net.save_cookies(cookiejar)
             else:
                Notify('big','Movreel','Login failed.', '')
                print 'Movreel Account: login failed'
         except Exception, e:
             print '**** Movreel Error: %s' % e
             Notify('big','Movreel Login Failed','Failed to connect with Movreel.', '', '', 'Please check your internet connection.')
             pass
	
###################
### Icefilms 	###
###################
	
def GetAllAZ(type, create_strm_files, path, sub_path, silent = False):
	print 'Trying to scrape all ' + type + ' from A-Z categories'
	CreateDirectory(path)
	pDialog = xbmcgui.DialogProgress()
	if not silent:
		pDialog.create(' Scraping ' + type + ', A-Z')

	for character in AZ_DIRECTORIES:
		percent = int((100 * AZ_DIRECTORIES.index(character))/len(AZ_DIRECTORIES))
		
		if not GetItem(type, ICEFILMS_URL + sub_path + character, character, create_strm_files, pDialog, 0, silent):
			break
		if not silent:
			if (pDialog.iscanceled()):
				print 'Canceled scraping'
				return

	pDialog.close()
	print 'Scraping complete!'	
		
def GetFromPath(type, create_strm_files, path, sub_path, page_name, silent = False):
	print 'Scraping ' + type + ' from ' + page_name
	pDialog = xbmcgui.DialogProgress()
	if not silent:
		pDialog.create(' Scraping newly added ' + type)

	CreateDirectory(path)
	GetItem(type, ICEFILMS_URL + sub_path, page_name, create_strm_files, pDialog, 0, silent)
	
	if not silent:
		if (pDialog.iscanceled()):
			print 'Canceled scraping'
		else:
			pDialog.close()
	print 'Scraping complete!'	
	
def GetItem(type, page, page_name, create_strm_files, pDialog, percent, silent = False):
	print "Scanning " + page
	if not silent:
		pDialog.update(percent, page_name, '')
	
	pagedata = GetURL(page, silent = silent)
	if pagedata=='':
		return False
	
	soup = BeautifulSoup(pagedata)
	list = soup.find("span", { "class" : "list" })
	stars = list.findAll("img", { "class" : "star" })
	data = []
	
	for star in stars: 
		a = star.findNextSibling('a')
		name = str(a.string)
		if not silent:
			if (pDialog.iscanceled()):
				return False
			pDialog.update(percent, "Scraping " + type + " " + page_name, name)
		try:
			year = int(name[len(name)-5:len(name)-1])
		except:
			year = 0
		href = a['href']
		data.append([name,href])
		
		if type=="movies":
			hd_test = a.nextSibling.string
			passed_filter = PassMovieFilter(year, hd_test)
			if passed_filter and create_strm_files:
				CreateStreamFile(name, href, MOVIES_PATH, False)

		if type=="TV shows":
			passed_filter = PassTVShowFilter(year)
			if passed_filter and create_strm_files:
				if not GetEpisodes(name, href, silent):
					return False
				
	SaveData(type, page_name + ".dat", data)
	return True
	
def GetFavorites(file_name, silent = False):
	print "Fetching favorites"
	pDialog = xbmcgui.DialogProgress()
	if not silent:
		pDialog.create('Scraping favorites')
	DBC.execute("SELECT name, url FROM ice_favorites ORDER BY name ASC")
	rows = DBC.fetchall()
	index = 0
	for row in rows:
		name = str(row[0])
		url = str(row[1])
		index = index + 1		
		percent = int((100 * index) / len(rows))
		if not silent:
			if (pDialog.iscanceled()):
				return
			print "Scraping: " + name
			pDialog.update(percent, "Scraping TV show", name)
		GetEpisodes(name, url, silent)


	
def AddMovie(name):
	#Needed to use X:N format to not alter the names of movie
	print "Adding movie " + name
	CreateDirectory(MOVIES_PATH)
	split = name.split(":")
	movies_data = LoadData("movies", split[0] + ".dat")
	to_add = movies_data[int(split[1])]
	CreateStreamFile(to_add[0], to_add[1], MOVIES_PATH, False)
	Notification("Movie added", to_add[0])
	
def SaveData(type, file_name, data):
	s = ''
	for d in data:
		try:
			s = s + d[0] + "\t" + d[1] + "\n"
		except:
			print "Got a problem when saving data."
	if type=="movies":
		CreateDirectory(MOVIES_DATA_PATH)
		path = os.path.join(MOVIES_DATA_PATH, file_name.lower())
	if type=="TV shows":
		CreateDirectory(TV_SHOWS_DATA_PATH)
		path = os.path.join(TV_SHOWS_DATA_PATH, file_name.lower())

	file = open(path,'w')
	file.write(s)
	file.close()	

def LoadData(type, file_name):
	if type=="movies":
		directory =  MOVIES_DATA_PATH
	if type=="TV shows":
		directory = TV_SHOWS_DATA_PATH
	CreateDirectory(directory)
	try:
		path = os.path.join(directory, file_name.lower())
		fh = open(path, 'r')
		contents=fh.read()
		fh.close()
	except:
		return []

	file_data = []
	file_strings = contents.split("\n")
	for data_text in file_strings:
		data = data_text.split("\t")
		if len(data) > 1:
			file_data.append([data[0],data[1]])	
	return file_data

def GetEpisodes(show_name, href, silent = False):
	page = ICEFILMS_URL + href
	pagedata = GetURL(page, silent = silent)
	if pagedata=='':
		return False
	month = [' ','Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
	month_nr = [' ','01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
	soup = BeautifulSoup(pagedata)
	list = soup.find("span", { "class" : "list" })
	stars = list.findAll("img", { "class" : "star" })
	year_loc = soup.findAll( "a", {"name" : re.compile(r"[0-9]{4}")})
	print year_loc
	for y in year_loc:
		print y
		season = y['name']
		print season
		b = y.parent.nextSibling
		while getattr(b, 'name', None) != 'h3':
			try:
				if getattr(b, 'name', None) == 'img':
					a = b.findNextSibling('a')
					name_split = re.split(r'[^a-zA-Z0-9_]',str(a.string))
					try:
						name = season+'.'+month_nr[month.index(name_split[0])]+'.'+name_split[1]
					except ValueError:
						name = name_split[1]
					href = a['href']
					show_path = os.path.join(TV_SHOWS_PATH, CleanFileName(show_name, True, use_encoding = True))
					CreateDirectory(show_path)		
					season_path = os.path.join(show_path, 'Season ' + season)
					CreateDirectory(season_path)
					if re.search('\\(\\d\\d\\d\\d\\)$', show_name):
						has_year = True
					else:
						has_year = False
					sname = CleanFileName(show_name, has_year, False, False)
					CreateStreamFile(name, href, season_path, False, show_name=sname)	
				b = b.nextSibling
			except AttributeError:
				break

	for star in stars: 
		a = star.findNextSibling('a')
		name = str(a.string)
		href = a['href']
		save_episode = True
		
		#Get the season number
		season = name.split("x")[0]
		try:
			int(season)
		except:
			if EXCLUDE_PROBLEM_EPISODES:
				#print show_name, season
				save_episode = False
			else:
				season = "0"
		if save_episode:
			if re.search('\\(\\d\\d\\d\\d\\)$', show_name):
				has_year = True
			else:
				has_year = False
			show_path = os.path.join(TV_SHOWS_PATH, CleanFileName(show_name, has_year, use_encoding = True))
			CreateDirectory(show_path)
			season_path = os.path.join(show_path, 'Season ' + season)
			CreateDirectory(season_path)
			sname = CleanFileName(show_name, has_year, False, False)
			CreateStreamFile(name, href, season_path, False, show_name=sname)	
	return True
			
def LaunchSTRM(name, href, path):
	print 'Running .strm'
	print name
	STREAM_URL = href
	name = CleanFileName(name, False, use_encoding = False)
	
	
	url = ICEFILMS_URL + urllib2.unquote(href)

	pagedata = GetURL(url)
	if pagedata=='':
		return
	 
	match=re.compile('/membersonly/components/com_iceplayer/(.+?)" width=').findall(pagedata)
	match[0]=re.sub('%29',')',match[0])
	match[0]=re.sub('%28','(',match[0])
	for url in match:
		mirrorpageurl = ICEFILMS_URL + '/membersonly/components/com_iceplayer/' + url
	print mirrorpageurl

	mirrorpage=GetURL(mirrorpageurl, save_cookie = True)
	if pagedata=='':
		return
	
	# check for recaptcha
	has_recaptcha = CheckForCaptcha(mirrorpage)
	if has_recaptcha is False:
		HandleOptions(name, mirrorpage, path)
	elif has_recaptcha is True:
		return #TODO: Handle captchas
		
def CheckForCaptcha(url):
	print "Looking for a captcha..."
	return False

def HandleOptions(name, mirrorpage, path):
	dialog = xbmcgui.Dialog()
	soup = BeautifulSoup(mirrorpage)
	#Wanted to replace this with BautifulSoup ... but I'm to lazy :D
	try:
		#sec = re.search("f\.lastChild\.value=\"([^']+)\",a", mirrorpage).group(1)
		#t   = re.search('"&t=([^"]+)",', mirrorpage).group(1)
		sec = re.search("f\.lastChild\.value=\"(.+?)\",a", mirrorpage).group(1)
		t = re.search('"&t=([^"]+)",', mirrorpage).group(1)
		args = {'iqs': '', 'url': '', 'cap': ''}
		args['sec'] = sec
		args['t'] = t
		#cookie = soup.find("cookie").string
		cookie = re.search('<cookie>(.+?)</cookie>', mirrorpage).group(1)
	except:
		dialog = xbmcgui.Dialog()
		dialog.ok("Unexpected page content", "Unexpected page content returned from Icefilms.info")
		return
	
	quality_list = soup.findAll("div", { "class" : "ripdiv" })
	
	quality_options = []
	for quality in quality_list:
		quality_options.append(quality.b.string)
	
	print quality_options
	
	if AUTO_BEST_QUALITY:
		quality_select = 0
	elif AUTO_DVDRIP_QUALITY:
		if u'DVDRip / Standard Def' in quality_options:
			quality_select=quality_options.index(u'DVDRip / Standard Def')
		else:
			quality_select = dialog.select('Unable to understand quality options, pelase select quality', quality_options)
			print quality_select
			if quality_select < 0:
				return
	else:
		quality_select = dialog.select('Select quality', quality_options)
		print quality_select
		if quality_select < 0:
			return
	
	for quality in quality_list:
		if quality_options[quality_select] == quality.b.string:
			quality_choice = quality
			break
	
	mirror_list = quality_choice.findAll("p")

	mirror_options = []			
	mirror_id = []
	multiple_parts = False
	
	for mirror in mirror_list:
		if len(mirror.contents) > 0:
			if len(mirror.contents[0]) > 2: #Multi part
				links = mirror.findAll("a")
				if AUTO_PLAY_MIRRORS and AUTO_PLAY_PARTS:
					part_urls = []
					failed = False
					for link in links:
						part_id = link['onclick'][3:len(link['onclick'])-1]
						part_url = GetSource(int(part_id), args, cookie)
						if part_url == None:
							failed = True
							break
						part_urls.append(part_url)
					if not failed:
						url1 = HandleVidlink(part_urls[0])[0]
						if len(part_urls) > 1:
							url2 = HandleVidlink(part_urls[1])[0]
						else:
							url2 = ''
						if len(part_urls) > 2:
							url3 = HandleVidlink(part_urls[2])[0]
						else:
							url3 = ''
						if len(part_urls) > 3:
							url4 = HandleVidlink(part_urls[3])[0]
						else:
							url4 = ''
						StreamSource(name, url1, url2, url3, url4)
						return
				else:
					multiple_parts = True
					for link in links:
						print mirror.next
						mirror_options.append(mirror.next + link.next)
						mirror_id.append(link['onclick'][3:len(link['onclick'])-1])
			else: #Single part	
				link = mirror.find("a")
				opt = link.next[0:len(link.next)-2]
				is2shared = re.search('Hosted by 2Shared', str(link))
		                israpid = re.search('Hosted by RapidShare', str(link))
		                is180 = re.search('Hosted by 180upload', str(link))
				isspeedy = re.search('speedy\.sh/', str(link))
		                isvidhog = re.search('Hosted by VidHog', str(link))
		                isuploadorb = re.search('Hosted by UploadOrb', str(link))
		                issharebees = re.search('Hosted by ShareBees', str(link))
		                isglumbo = re.search('Hosted by GlumboUploads', str(link))
		                isjumbo = re.search('Hosted by JumboFiles', str(link))
		                ismovreel = re.search('Hosted by Movreel', str(link))
		                isbillion = re.search('Hosted by BillionUploads', str(link))
				ismega = re.search('Hosted by MegaRelease', str(link))
				islem = re.search('Hosted by LemUploads', str(link))
				ishuge = re.search('Hosted by HugeFiles', str(link))
				isentero = re.search('Hosted by EntroUpload', str(link))
				isepic = re.search('Hosted by EpicShare', str(link))

		                if is2shared:
					opt=opt+': 2S'
		                elif israpid:
		                 	opt=opt+': RS'
		                elif is180:
		                      	opt=opt+': 180'
		                elif isspeedy:
		                 	opt=opt+': SS'
		                elif isvidhog:
		                	opt=opt+': VH'
		                elif isuploadorb:
		                	opt=opt+': UO'
		                elif issharebees:
		                	opt=opt+': SB'
		                elif isglumbo:
		                	opt=opt+': GU'
		                elif isjumbo:
		                	opt=opt+': JF'
		                elif ismovreel:
		                	opt=opt+': MR'
		                elif isbillion:
		                	opt=opt+': BU'
				elif islem:
		                	opt=opt+': LU'
		                elif ishuge:
		                	opt=opt+': HF'
		                elif ismega:
		                	opt=opt+': ME'
		                elif isentero:
		                	opt=opt+': EU'
				elif isepic:
		                	opt=opt+': ES'
			
				mirror_options.append(opt)
				mirror_id.append(link['onclick'][3:len(link['onclick'])-1])
				'''if AUTO_PLAY_MIRRORS:
					mega_upload_url = GetSource(int(link['onclick'][3:len(link['onclick'])-1]), args, cookie)
					page=HandleVidlink(mega_upload_url)
					if page != None:
						resolved_url=page
						StreamSource(name, resolved_url)
						return
				else:
					mirror_options.append(link.next[0:len(link.next)-2])
					mirror_id.append(link['onclick'][3:len(link['onclick'])-1])'''

	if AUTO_PLAY_MIRRORS and not multiple_parts: #Failed to play any mirror.
		dialog.ok("Streaming failed", "No working mirror found")
		return
				
	print mirror_options;
	print mirror_id;
	mirror_select = dialog.select('Select mirror', mirror_options)
	print mirror_select
	if mirror_select < 0:
		return
	#AUTO_PLAY_PARTS
	my_icefilms_url = GetSource(int(mirror_id[mirror_select]), args, cookie)
	resolved_url = None
	try:
		resolved_url = urlresolver.HostedMediaFile(url=my_icefilms_url).resolve()
	except:
		print "Unable to resolve with urlresolver"
	
	if not resolved_url:
		from donnie import localresolvers
		print "Attempting localresolver"
		Resolver = localresolvers.localresolver()
		resolved_url = Resolver.resolve(my_icefilms_url)
		
	if not resolved_url:
		return False
	
	print "Playing File: " + path

	if DB_TYPE == 'mysql':
		DBC.execute("UPDATE episodeview set playCount=1 WHERE c18=%s", [path])
		DBH.commit()
	else:
		DBC.execute("SELECT idFile FROM episodeview WHERE c18=?", [path])
		row = DBC.fetchone()
		try:
			idFile = str(row[0])
			print "Update files by Id: " + idFile			
			DBC.execute("UPDATE files set playCount=1 WHERE idFile=?", [idFile])
			DBH.commit()
		except:
			print "SQL Error: " + "SELECT idFile FROM episodeview WHERE c18=%s" % path
	StreamSource(name, resolved_url)

def playStream(url, name):
	WaitIf()
	mplayer = MyPlayer()
    	mplayer.play(url, name)
	

def GetSource(id, args, cookie):
    print cookie
    m = random.randrange(100, 300) * -1
    s = random.randrange(5, 50)
    params = copy.copy(args)
    params['id'] = id
    params['m'] = m
    params['s'] = s
    paramsenc = urllib.urlencode(params)
    body = GetURL(ICEFILMS_AJAX, params = paramsenc, cookie = cookie)
    print 'response: %s' % body
    source = re.search('url=(http[^&]+)', body)
    if source:
        url = urllib.unquote(source.group(1))
    else:
        print 'GetSource - URL String not found'
        url = ''
    print 'url: %s' % url
    return url
	
def StreamSource(name,url1, url2 = '', url3 = '', url4 = ''):
	print 'attempting to stream url: ' + str(url1)	
	thumb = ''
	WaitIf()
	
	#print url1
	#print url2
	#print url3
	#print url4
	
	download = False #Can't get it to work :\
	if not download:
		#pl=xbmc.PlayList(1)
		#pl.clear()
		list_item = xbmcgui.ListItem(name, iconImage="DefaultVideoBig.png", thumbnailImage=thumb, path=url1)
		#xbmc.PlayList(1).add(url1, list_item)
		#print 'thread1 started'
		#if not url2=='':
		#	xbmc.PlayList(1).add(url2, list_item)
		#	print 'thread2 started'
		#if not url3=='':
		#	xbmc.PlayList(1).add(url3, list_item)
		#	print 'thread3 started'
		#if not url4=='':
		#	xbmc.PlayList(1).add(url4, list_item)
		#	print 'thread4 started'
			
		try:
			#xbmcplugin.setResolvedUrl(int(sys.argv[ 1 ]),True,pl)
			#xbmc.Player().play(pl)
			list_item.setProperty( "IsPlayable", "true" )
			xbmcplugin.setResolvedUrl(int(sys.argv[ 1 ]),True,list_item)
		except:
			print 'file streaming failed'
			Notification("Streaming failed", "Streaming failed")
	else:
		print 'starting threads'
		CreateDirectory(DOWNLOAD_PATH)
		
		pl=xbmc.PlayList(1)
		pl.clear()
		list_item = xbmcgui.ListItem('', iconImage="DefaultVideoBig.png", thumbnailImage=thumb)
		
		d_path1 = os.path.join(DOWNLOAD_PATH, 'part1.avi')
		d_thread1 = KThread(target=urllib.urlretrieve, args=(url1, d_path1))
		d_thread1.start()
		xbmc.PlayList(1).add(d_path1, list_item)
		print 'thread1 started'
		if not url2=='':
			d_path2 = os.path.join(DOWNLOAD_PATH, 'part2.avi')
			d_thread2 = KThread(target=urllib.urlretrieve, args=(url2, d_path2))
			d_thread2.start()
			xbmc.PlayList(1).add(d_path2, list_item)
			print 'thread2 started'
		if not url3=='':
			d_path3 = os.path.join(DOWNLOAD_PATH, 'part3.avi')
			d_thread3 = KThread(target=urllib.urlretrieve, args=(url3, d_path3))
			d_thread3.start()
			xbmc.PlayList(1).add(d_path3, list_item)
			print 'thread3 started'
		if not url4=='':
			d_path4 = os.path.join(DOWNLOAD_PATH, 'part4.avi')
			d_thread4 = KThread(target=urllib.urlretrieve, args=(url4, d_path4))
			d_thread4.start()
			xbmc.PlayList(1).add(d_path4, list_item)
			print 'thread4 started'
		
		#xbmc.Player().play(pl)
		
		xbmc.sleep(10000) # Set a 10 second delay to allow the file start downloading a bit.
		print 'wait completed'
		
		#list_item = xbmcgui.ListItem('', iconImage="DefaultVideoBig.png", thumbnailImage='', path=d_path1)
		#list_item.setProperty( "IsPlayable", "true" )
		
		#xbmcplugin.setResolvedUrl(int(sys.argv[ 1 ]),True,pl)
		xbmc.Player().play(pl)
		
		#thread2 = threading.Thread(target=xbmcplugin.setResolvedUrl, args=(int(sys.argv[ 1 ]),True,list_item))
		#thread2 = threading.Thread(target=xbmc.Player( xbmc.PLAYER_CORE_DVDPLAYER ).play, args=(d_path, list_item))
		
		
		while xbmc.Player().isPlayingVideo():
			pass
		while os.path.exists(d_path1):
			try:
				os.remove(d_path1)
				break
			except:
				pass

class KThread(threading.Thread):
  def __init__(self, *args, **keywords):
    threading.Thread.__init__(self, *args, **keywords)
    self.killed = False

  def start(self):
    self.__run_backup = self.run
    self.run = self.__run
    threading.Thread.start(self)

  def __run(self):
    sys.settrace(self.globaltrace)
    self.__run_backup()
    self.run = self.__run_backup

  def globaltrace(self, frame, why, arg):
    if why == 'call':
      return self.localtrace
    else:
      return None

  def localtrace(self, frame, why, arg):
    if self.killed:
      if why == 'line':
        raise SystemExit()
    return self.localtrace

  def kill(self):
    self.killed = True

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")
'''
class TwoSharedDownloader:
     
     def __init__(self):
          self.cookieString = ""
          self.re2sUrl = re.compile('(?<=window.location \=\')([^\']+)')
     
     def returnLink(self, pageUrl):

          # Open the 2Shared page and read its source to htmlSource
          request = urllib2.Request(pageUrl)
          response = urllib2.urlopen(request)
          htmlSource = response.read()
     
          # Search the source for link to the video and store it for later use
          match = re.compile('">(.+?)</div>').findall(htmlSource)
          fileUrl = match[0]
          
          # Return the valid link
          return fileUrl 

def SHARED2_HANDLER(url):
	downloader2Shared = TwoSharedDownloader()
	vidFile = downloader2Shared.returnLink(url)

	print '2Shared Direct Link: '+vidFile
	finalUrl = [1]
	finalUrl[0] = vidFile
	return finalUrl
'''
def HandleVidlink(url):
	#video link preflight, pays attention to settings / checks if url is mega or 2shared
	#Verify Read-Debrid Account
	debrid_account = str2bool(selfAddon.getSetting('realdebrid-account'))
	HideSuccessfulLogin = str2bool(selfAddon.getSetting('hide-successful-login-messages'))
	if debrid_account:
		debriduser = selfAddon.getSetting('realdebrid-username')
	 	debridpass = selfAddon.getSetting('realdebrid-password')

	 	try:
	     		rd = debridroutines.RealDebrid(cookie_jar, debriduser, debridpass)
	     		if rd.Login():
		 		if not HideSuccessfulLogin:
					Notification('Real-Debrid', 'Account login successful.')		    			
					#Notify('small','Real-Debrid', 'Account login successful.','')
	     			else:
					#Notification('Real-Debrid', 'Account login failed.')		 			
					#Notify('big','Real-Debrid','Login failed.', '')
		 			print 'Real-Debrid Account: login failed'
	 	except Exception, e:
	      		print '**** Real-Debrid Error: %s' % e
	      		Notification('Real-Debrid', 'Account login failed.')
			#Notify('big','Real-Debrid Login Failed','Failed to connect with Real-Debrid.', '', '', 'Please check your internet connection.')
	      	pass
	ismega = re.search('\.megaupload\.com/', url)
     	is2shared = re.search('\.2shared\.com/', url)
	israpid = re.search('rapidshare\.com/', url)
	is180 = re.search('180upload\.com/', url)
	isspeedy = re.search('speedy\.sh/', url)
	isvidhog = re.search('vidhog\.com/', url)
	isuploadorb = re.search('uploadorb\.com/', url)
	issharebees = re.search('sharebees\.com/', url)
	isglumbo = re.search('glumbouploads\.com/', url)
	isjumbo = re.search('jumbofiles\.com/', url)
	ismovreel = re.search('movreel\.com/', url)
	isbillion = re.search('billionuploads\.com/', url)

	host = re.search('//(.+?)/', url).group(1)

	if debrid_account:
		  debriduser = selfAddon.getSetting('realdebrid-username')
		  debridpass = selfAddon.getSetting('realdebrid-password')
		  rd = debridroutines.RealDebrid(cookie_jar, debriduser, debridpass)
		  
		  if rd.valid_host(host):
		      	if rd.Login():
				download_details = rd.Resolve(url)
			   	link = download_details['download_link']
			   	if not link:
					Notification('Real-Debrid', 'Error occurred attempting to stream the file.')			         
					return None
			   	else:
			       		print 'Real-Debrid Link resolved: %s ' % download_details['download_link']
			       		return link

	if is2shared:
		  shared2url=SHARED2_HANDLER(url)
		  return shared2url

	elif is180:
	  	return resolve_180upload(url)
	  
	elif isspeedy:
	  	return resolve_speedyshare(url)

	elif isvidhog:
	  	return resolve_vidhog(url)

	elif isuploadorb:
	  	return resolve_uploadorb(url)

	elif issharebees:
	  	return resolve_sharebees(url)

	elif isglumbo:
	  	return resolve_glumbouploads(url)

	elif isjumbo:
	  	return resolve_jumbofiles(url)

	elif ismovreel:
	  	return resolve_movreel(url)

	elif isbillion:
	  	return resolve_billionuploads(url)


def resolve_180upload(url):

    try:
        dialog = xbmcgui.DialogProgress()
        dialog.create('Resolving', 'Resolving 180Upload Link...')
        dialog.update(0)
        
        print '180Upload - Requesting GET URL: %s' % url
        html = net.http_GET(url).content
        
        op = 'download1'
        id = re.search('<input type="hidden" name="id" value="(.+?)">', html).group(1)
        rand = re.search('<input type="hidden" name="rand" value="(.+?)">', html).group(1)
        method_free = ''
        
        data = {'op': op, 'id': id, 'rand': rand, 'method_free': method_free}
        
        dialog.update(33)
        
        print '180Upload - Requesting POST URL: %s' % url
        html = net.http_POST(url, data).content
        
        op = 'download2'
        id = re.search('<input type="hidden" name="id" value="(.+?)">', html).group(1)
        rand = re.search('<input type="hidden" name="rand" value="(.+?)">', html).group(1)
        method_free = ''

        data = {'op': op, 'id': id, 'rand': rand, 'method_free': method_free, 'down_direct': 1}

        dialog.update(66)

        print '180Upload - Requesting POST URL: %s' % url
        html = net.http_POST(url, data).content
        link = re.search('<span style="background:#f9f9f9;border:1px dotted #bbb;padding:7px;">.+?<a href="(.+?)">', html,re.DOTALL).group(1)
        print '180Upload Link Found: %s' % link
    
        dialog.update(100)
        dialog.close()
	#do_wait('Resolving', 'Free', 5)
        return link
    except Exception, e:
        print '**** 180Upload Error occured: %s' % e
        raise
    

def resolve_billionuploads(url):
	try:
		#Show dialog box so user knows something is happening
		dialog = xbmcgui.DialogProgress()
		dialog.create('Resolving', 'Resolving BillionUploads Link...')       
		dialog.update(0)
		
		print 'BillionUploads - Requesting GET URL: %s' % url
		html = net.http_GET(url).content
		#Check page for any error msgs
		if re.search('This server is in maintenance mode', html):
			print '***** BillionUploads - Site reported maintenance mode'
			raise Exception('File is currently unavailable on the host')

		#Set POST data values
		op = 'download2'
		rand = re.search('<input type="hidden" name="rand" value="(.+?)">', html).group(1)
		postid = re.search('<input type="hidden" name="id" value="(.+?)">', html).group(1)
		method_free = re.search('<input type="hidden" name="method_free" value="(.*?)">', html).group(1)
		down_direct = re.search('<input type="hidden" name="down_direct" value="(.+?)">', html).group(1)

		#Captcha
		captchaimg = re.search('<img src="(http://BillionUploads.com/captchas/.+?)"', html)
		#dialog.close()

		if captchaimg:
			#Grab Image and display it
			img = xbmcgui.ControlImage(550,15,240,100,captchaimg.group(1))
			wdlg = xbmcgui.WindowDialog()
			wdlg.addControl(img)
			wdlg.show()

			#Small wait to let user see image
			xbmc.sleep(2000)

			#Prompt keyboard for user input
			kb = xbmc.Keyboard('', 'Type the letters in the image', False)
			kb.doModal()
			capcode = kb.getText()
			#Check input
			if (kb.isConfirmed()):
				userInput = kb.getText()
				if userInput != '':
					capcode = kb.getText()
				elif userInput == '':
					Notify('big', 'No text entered', 'You must enter text in the image to access video', '')
                   			return None
            			else:
                			return None
            			wdlg.close()
			data = {'op': op, 'rand': rand, 'id': postid, 'referer': url, 'method_free': method_free, 'down_direct': down_direct, 'code': capcode}

        	else:
            		data = {'op': op, 'rand': rand, 'id': postid, 'referer': url, 'method_free': method_free, 'down_direct': down_direct}
					
		dialog.update(50)

		print 'BillionUploads - Requesting POST URL: %s DATA: %s' % (url, data)
		html = net.http_POST(url, data).content
		dialog.update(100)
		link = re.search('&product_download_url=(.+?)"', html).group(1)
		link = link + "|referer=" + url
		dialog.close()
		return link


    	except Exception, e:
        	print '**** BillionUploads Error occured: %s' % e
        	raise

def resolve_speedyshare(url):

    try:    
        dialog = xbmcgui.DialogProgress()
        dialog.create('Resolving', 'Resolving SpeedyShare Link...')
        dialog.update(50)
        
        print 'SpeedyShare - Requesting GET URL: %s' % url
        html = net.http_GET(url).content
        
        dialog.close()
        
        host = 'http://speedy.sh'
        #host = re.search("<input value='(http://www[0-9]*.speedy.sh)/.+?'", html).group(1)
        link = re.search("<a class=downloadfilename href='(.+?)'>", html).group(1)
        return host + link
    except Exception, e:
        print '**** SpeedyShare Error occured: %s' % e
        raise

def resolve_vidhog(url):

    try:
        
        #Show dialog box so user knows something is happening
        dialog = xbmcgui.DialogProgress()
        dialog.create('Resolving', 'Resolving VidHog Link...')
        dialog.update(0)
        
        print 'VidHog - Requesting GET URL: %s' % url
        html = net.http_GET(url).content

        dialog.update(33)
        
        #Check page for any error msgs
        if re.search('This server is in maintenance mode', html):
            print '***** VidHog - Site reported maintenance mode'
            raise Exception('File is currently unavailable on the host')
        
        #Set POST data values
        op = re.search('<input type="hidden" name="op" value="(.+?)">', html).group(1)
        usr_login = re.search('<input type="hidden" name="usr_login" value="(.*?)">', html).group(1)
        postid = re.search('<input type="hidden" name="id" value="(.+?)">', html).group(1)
        fname = re.search('<input type="hidden" name="fname" value="(.+?)">', html).group(1)
        method_free = re.search('<input type="submit" name="method_free" value="(.+?)" class="freebtn right">', html).group(1)
        
        data = {'op': op, 'usr_login': usr_login, 'id': postid, 'fname': fname, 'referer': url, 'method_free': method_free}
        
        print 'VidHog - Requesting POST URL: %s DATA: %s' % (url, data)
        html = net.http_POST(url, data).content
        
        dialog.update(66)
                
        #Set POST data values
        op = re.search('<input type="hidden" name="op" value="(.+?)">', html).group(1)
        postid = re.search('<input type="hidden" name="id" value="(.+?)">', html).group(1)
        rand = re.search('<input type="hidden" name="rand" value="(.+?)">', html).group(1)
        method_free = re.search('<input type="hidden" name="method_free" value="(.+?)">', html).group(1)
        down_direct = int(re.search('<input type="hidden" name="down_direct" value="(.+?)">', html).group(1))
        wait = int(re.search('<span id="countdown_str">Wait <span id=".+?">([0-9]*)</span>', html).group(1))
        
        data = {'op': op, 'id': postid, 'rand': rand, 'referer': url, 'method_free': method_free, 'down_direct': down_direct}
        
        dialog.close()
        
        #Do wait time for free accounts    
        finished = do_wait('VidHog', '', wait)

        if finished:
            print 'VidHog - Requesting POST URL: %s DATA: %s' % (url, data)
            
            dialog.create('Resolving', 'Resolving VidHog Link...')
            dialog.update(66)
            
            html = net.http_POST(url, data).content
            
            dialog.update(100)
            
            dialog.close()
        
            link = re.search('<strong><a href="(.+?)">Click Here to download this file</a></strong>', html).group(1)
            return link
        else:
            return None
        
    except Exception, e:
        print '**** VidHog Error occured: %s' % e
        raise


def resolve_uploadorb(url):

    try:

        #Show dialog box so user knows something is happening
        dialog = xbmcgui.DialogProgress()
        dialog.create('Resolving', 'Resolving UploadOrb Link...')       
        dialog.update(0)
        
        print 'UploadOrb - Requesting GET URL: %s' % url
        html = net.http_GET(url).content
        
        dialog.update(33)
        
        #Check page for any error msgs
        if re.search('This server is in maintenance mode', html):
            print '***** UploadOrb - Site reported maintenance mode'
            raise Exception('File is currently unavailable on the host')

        #Set POST data values
        op = re.search('<input type="hidden" name="op" value="(.+?)">', html).group(1)
        usr_login = re.search('<input type="hidden" name="usr_login" value="(.*?)">', html).group(1)
        postid = re.search('<input type="hidden" name="id" value="(.+?)">', html).group(1)
        fname = re.search('<input type="hidden" name="fname" value="(.+?)">', html).group(1)
        method_free = re.search('<input type="submit" name="method_free" value="(.+?)" class="btn2">', html).group(1)
        
        data = {'op': op, 'usr_login': usr_login, 'id': postid, 'fname': fname, 'referer': url, 'method_free': method_free}
        
        print 'UploadOrb - Requesting POST URL: %s DATA: %s' % (url, data)
        html = net.http_POST(url, data).content

        dialog.update(66)
        
        #Set POST data values
        op = re.search('<input type="hidden" name="op" value="(.+?)">', html).group(1)
        postid = re.search('<input type="hidden" name="id" value="(.+?)">', html).group(1)
        rand = re.search('<input type="hidden" name="rand" value="(.+?)">', html).group(1)
        method_free = re.search('<input type="hidden" name="method_free" value="(.+?)">', html).group(1)
        down_direct = int(re.search('<input type="hidden" name="down_direct" value="(.+?)">', html).group(1))
        
        data = {'op': op, 'id': postid, 'rand': rand, 'referer': url, 'method_free': method_free, 'down_direct': down_direct}
        print data
        
        print 'UploadOrb - Requesting POST URL: %s DATA: %s' % (url, data)
        html = net.http_POST(url, data).content
        
        dialog.update(100)
        link = re.search('ACTION="(.+?)">', html).group(1)
        dialog.close()
        
        return link

    except Exception, e:
        print '**** UploadOrb Error occured: %s' % e
        raise


def resolve_sharebees(url):

    try:
        
        if str2bool(selfAddon.getSetting('sharebees-account')):
            print 'ShareBees - Setting Cookie file'
            cookiejar = os.path.join(cookie_path,'sharebees.lwp')
            net.set_cookies(cookiejar)
        
        #Show dialog box so user knows something is happening
        dialog = xbmcgui.DialogProgress()
        dialog.create('Resolving', 'Resolving ShareBees Link...')       
        dialog.update(0)
        
        print 'ShareBees - Requesting GET URL: %s' % url
        html = net.http_GET(url).content
        
        dialog.update(50)
        
        #Set POST data values
        #op = re.search('''<input type="hidden" name="op" value="(.+?)">''', html, re.DOTALL).group(1)
        op = 'download1'
        usr_login = re.search('<input type="hidden" name="usr_login" value="(.*?)">', html).group(1)
        postid = re.search('<input type="hidden" name="id" value="(.+?)">', html).group(1)
        fname = re.search('<input type="hidden" name="fname" value="(.+?)">', html).group(1)
        method_free = "method_free"
        
        data = {'op': op, 'usr_login': usr_login, 'id': postid, 'fname': fname, 'referer': url, 'method_free': method_free}
        
        print 'ShareBees - Requesting POST URL: %s DATA: %s' % (url, data)
        html = net.http_POST(url, data).content
        
        dialog.update(100)

        link = None
        sPattern = '''<div id="player_code">.*?<script type='text/javascript'>(eval.+?)</script>'''
        r = re.search(sPattern, html, re.DOTALL + re.IGNORECASE)
        
        if r:
            sJavascript = r.group(1)
            sUnpacked = jsunpack.unpack(sJavascript)
            print(sUnpacked)
            
            #Grab first portion of video link, excluding ending 'video.xxx' in order to swap with real file name
            #Note - you don't actually need the filename, but for purpose of downloading via Icefilms it's needed so download video has a name
            sPattern  = '''("video/divx"src="|addVariable\('file',')(.+?)video[.]'''
            r = re.search(sPattern, sUnpacked)              
            
            #Video link found
            if r:
                link = r.group(2) + fname
                dialog.close()
                return link

        if not link:
            print '***** ShareBees - Link Not Found'
            raise Exception("Unable to resolve ShareBees")

    except Exception, e:
        print '**** ShareBees Error occured: %s' % e
        raise


def resolve_glumbouploads(url):

    try:

        #Show dialog box so user knows something is happening
        dialog = xbmcgui.DialogProgress()
        dialog.create('Resolving', 'Resolving GlumboUploads Link...')       
        dialog.update(0)
        
        print 'GlumboUploads - Requesting GET URL: %s' % url
        html = net.http_GET(url).content
        
        dialog.update(50)
        
        #Set POST data values
        op = re.search('''<Form method="POST" action=''>.+?<input type="hidden" name="op" value="(.+?)">''', html, re.DOTALL).group(1)
        usr_login = re.search('<input type="hidden" name="usr_login" value="(.*?)">', html).group(1)
        postid = re.search('<input type="hidden" name="id" value="(.+?)">', html).group(1)
        fname = re.search("""input\[name="fname"\]'\).attr\('value', '(.+?)'""", html).group(1)
        method_free = re.search('<input class="slowdownload" title="Slow download" type="submit" name="method_free" value="(.+?)">', html).group(1)

        
        data = {'op': op, 'usr_login': usr_login, 'id': postid, 'fname': fname, 'referer': url, 'method_free': method_free}
        
        print 'GlumboUploads - Requesting POST URL: %s DATA: %s' % (url, data)
        html = net.http_POST(url, data).content
        
        dialog.update(100)
        
        #sPattern =  '<script type=(?:"|\')text/javascript(?:"|\')>(eval\('
        #sPattern += 'function\(p,a,c,k,e,d\)(?!.+player_ads.+).+np_vid.+?)'
        #sPattern += '\s+?</script>'

        link = None
        sPattern = '''<div id="player_code">.*?<script type='text/javascript'>(eval.+?)</script>'''
        r = re.search(sPattern, html, re.DOTALL + re.IGNORECASE)
        
        if r:
            sJavascript = r.group(1)
            sUnpacked = jsunpack.unpack(sJavascript)
            print(sUnpacked)
            
            #Grab first portion of video link, excluding ending 'video.xxx' in order to swap with real file name
            #Note - you don't actually need the filename, but for purpose of downloading via Icefilms it's needed so download video has a name
            sPattern  = '<embed id="np_vid"type="video/divx"src="(.+?)video.+'
            sPattern += '"custommode='
            r = re.search(sPattern, sUnpacked)              
            
            #Video link found
            if r:
                link = r.group(1) + fname
                dialog.close()
                return link

        if not link:
            print '***** GlumboUploads - Link Not Found'
            raise Exception("Unable to resolve GlumboUploads")

    except Exception, e:
        print '**** GlumboUploads Error occured: %s' % e
        raise

def resolve_jumbofiles(url):

    try:

        #Show dialog box so user knows something is happening
        dialog = xbmcgui.DialogProgress()
        dialog.create('Resolving', 'Resolving JumboFiles Link...')       
        dialog.update(0)
        
        print 'JumboFiles - Requesting GET URL: %s' % url
        html = net.http_GET(url).content
        
        dialog.update(33)
        
        #Check page for any error msgs
        if re.search('This server is in maintenance mode', html):
            print '***** JumboFiles - Site reported maintenance mode'
            raise Exception('File is currently unavailable on the host')

        #Set POST data values
        #op = re.search('<input type="hidden" name="op" value="(.+?)">', html).group(1)
        op = 'download1'
        postid = re.search('<input type="hidden" name="id" value="(.+?)">', html).group(1)
        fname = re.search('<input type="hidden" name="fname" value="(.+?)">', html).group(1)
        #method_free = re.search('<input type="hidden" name="method_free" value="(.*?)">', html).group(1)
        method_free = 'method_free'
                
        data = {'op': op, 'id': postid, 'referer': url, 'method_free': method_free}
        
        print 'JumboFiles - Requesting POST URL: %s DATA: %s' % (url, data)
        html = net.http_POST(url, data).content

        dialog.update(66)

        #Set POST data values
        #op = re.search('<input type="hidden" name="op" value="(.+?)">', html).group(1)
        op = 'download2'
        postid = re.search('<input type="hidden" name="id" value="(.+?)">', html).group(1)
        rand = re.search('<input type="hidden" name="rand" value="(.+?)">', html).group(1)
        method_free = 'method_free'
                
        data = {'op': op, 'id': postid, 'rand': rand, 'method_free': method_free}
        
        print 'JumboFiles - Requesting POST URL: %s DATA: %s' % (url, data)
        html = net.http_POST(url, data).content        

        dialog.update(100)        
        link = re.search('<FORM METHOD="LINK" ACTION="(.+?)">', html).group(1)
        dialog.close()
        
        return link

    except Exception, e:
        print '**** JumboFiles Error occured: %s' % e
        raise
        
def resolve_movreel(url):

    try:
	if str2bool(selfAddon.getSetting('movreel-account')):
         	print 'Movreel - Setting Cookie file'
         	cookiejar = os.path.join(cookie_path,'movreel.lwp')
         	net.set_cookies(cookiejar)

        #Show dialog box so user knows something is happening
        dialog = xbmcgui.DialogProgress()
        dialog.create('Resolving', 'Resolving Movreel Link...')       
        dialog.update(0)
        
        print 'Movreel - Requesting GET URL: %s' % url
        html = net.http_GET(url).content
        
        dialog.update(33)
        
        #Check page for any error msgs
        if re.search('This server is in maintenance mode', html):
            print '***** Movreel - Site reported maintenance mode'
            raise Exception('File is currently unavailable on the host')

        #Set POST data values
        op = re.search('<input type="hidden" name="op" value="(.+?)">', html).group(1)
        usr_login = re.search('<input type="hidden" name="usr_login" value="(.*?)">', html).group(1)
        postid = re.search('<input type="hidden" name="id" value="(.+?)">', html).group(1)
        fname = re.search('<input type="hidden" name="fname" value="(.+?)">', html).group(1)
        method_free = re.search('<input type="submit" name="method_free" style=".+?" value="(.+?)">', html).group(1)
        
        data = {'op': op, 'usr_login': usr_login, 'id': postid, 'referer': url, 'fname': fname, 'method_free': method_free}
        
        print 'Movreel - Requesting POST URL: %s DATA: %s' % (url, data)
        html = net.http_POST(url, data).content

        dialog.update(66)
        
        #Set POST data values
        op = re.search('<input type="hidden" name="op" value="(.+?)">', html).group(1)
        postid = re.search('<input type="hidden" name="id" value="(.+?)">', html).group(1)
        rand = re.search('<input type="hidden" name="rand" value="(.+?)">', html).group(1)
        method_free = re.search('<input type="hidden" name="method_free" value="(.+?)">', html).group(1)
        
        data = {'op': op, 'id': postid, 'rand': rand, 'referer': url, 'method_free': method_free, 'down_direct': 1}

        print 'Movreel - Requesting POST URL: %s DATA: %s' % (url, data)
        html = net.http_POST(url, data).content
        
        dialog.update(100)
        link = re.search('<a id="lnk_download" href="(.+?)">Download Original Video</a>', html, re.DOTALL).group(1)
        dialog.close()
        
        return link

    except Exception, e:
        print '**** Movreel Error occured: %s' % e
        raise


def WaitIf():
	#killing playback is necessary if switching playing of one megaup/2share stream to another
	if xbmc.Player().isPlayingVideo() == True:
		xbmc.Player().stop()

def DoWait(account, wait_time):
	# do the necessary wait, with  a nice notice and pre-set waiting time. I have found the below waiting times to never fail.
	if account == 'platinum':    
		return HandleWait(int(wait_time),'Megaupload','Loading video with your *Platinum* account.')
	elif account == 'premium':    
		return HandleWait(int(wait_time),'Megaupload','Loading video with your *Premium* account.')
	elif account == 'free':
		return HandleWait(int(wait_time),'Megaupload Free User','Loading video with your free account.')
	else:
		return HandleWait(int(wait_time),'Megaupload','Loading video.')

def HandleWait(time_to_wait,title,text):
	print 'waiting '+str(time_to_wait)+' secs'    

	pDialog = xbmcgui.DialogProgress()
	ret = pDialog.create(' '+title)

	secs=0
	percent=0
	
	cancelled = False
	while secs < time_to_wait:
		secs = secs + 1
		percent = int((100 * secs)/time_to_wait)
		secs_left = str((time_to_wait - secs))
		remaining_display = ' Wait '+secs_left+' seconds for the video stream to activate...'
		pDialog.update(percent,' '+text,remaining_display)
		xbmc.sleep(1000)
		if (pDialog.iscanceled()):
			cancelled = True
			break
	if cancelled == True:     
		print 'wait cancelled'
		return False
	else:
		print 'done waiting'
		return True

def do_wait(source, account, wait_time):
     # do the necessary wait, with  a nice notice and pre-set waiting time. I have found the below waiting times to never fail.
     
     if int(wait_time) == 0:
         wait_time = 1
         
     if account == 'platinum':    
          return handle_wait(int(wait_time),source,'Loading video with your *Platinum* account.')
               
     elif account == 'premium':    
          return handle_wait(int(wait_time),source,'Loading video with your *Premium* account.')
             
     elif account == 'free':
          return handle_wait(int(wait_time),source,'Loading video with your free account.')

     else:
          return handle_wait(int(wait_time),source,'Loading video.')


def handle_wait(time_to_wait,title,text):

    print 'waiting '+str(time_to_wait)+' secs'    

    pDialog = xbmcgui.DialogProgress()
    ret = pDialog.create(' '+title)

    secs=0
    percent=0
    increment = float(100) / time_to_wait
    increment = int(round(increment))

    cancelled = False
    while secs < time_to_wait:
        secs = secs + 1
        percent = increment*secs
        secs_left = str((time_to_wait - secs))
        remaining_display = ' Wait '+secs_left+' seconds for the video stream to activate...'
        pDialog.update(percent,' '+ text, remaining_display)
        xbmc.sleep(1000)
        if (pDialog.iscanceled()):
             cancelled = True
             break
    if cancelled == True:     
         print 'wait cancelled'
         return False
    else:
         print 'done waiting'
         return True




class MyPlayer (xbmc.Player):
	def __init__ (self, last_part=False):
		self.dialog = None
		xbmc.Player.__init__(self)
		print 'Initializing myPlayer...'

	def play(self, url, name):
		print 'Now im playing... %s' % url
		xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(url, name)            

	def isplaying(self):
		print 'Checking player'
		xbmc.Player.isPlaying(self)

	def onPlayBackEnded(self):
		print 'Checking for completion'

	def onPlayBackStopped(self):
		print 'Checking for completion'

###################
### Auto-update ###
###################

'''def AutoUpdateLibrary():
	if ADDON.getSetting('auto_update') == "false":
		return
	
	print "IceLibrary running an automatic update"
	
	xbmc.executebuiltin('CancelAlarm(updatelibrary)')
	
	timer_amounts = {}
	timer_amounts['0'] = '120'
	timer_amounts['1'] = '300'
	timer_amounts['2'] = '600'
	timer_amounts['3'] = '900'
	timer_amounts['4'] = '1440'

	#only do this if we are not playing anything
	if xbmc.Player().isPlaying() == False:
		if ADDON.getSetting('update_tvshows') == "true":
			UpdateFavorites(True)
			#xbmc.executebuiltin('UpdateLibrary(video,' + TV_SHOWS_PATH + ')')
		if ADDON.getSetting('update_movies') == "true":
			UpdateMovies(True)
			#xbmc.executebuiltin('UpdateLibrary(video,' + MOVIES_PATH + ')')
		xbmc.executebuiltin('UpdateLibrary(video)')
		
	#reset the timer
	xbmc.executebuiltin('AlarmClock(updatelibrary,XBMC.RunScript('+ADDON_ID+',"?mode=100"),' +
						timer_amounts[ADDON.getSetting('update_timer')] +  ',true)')

	print "IceLibrary update complete"'''


def auto_update_tvshows():
	if ADDON.getSetting('auto_update') == "false":
		return
	print "executing tvshows"
	UpdateFavorites(True)
	update_update_library(what='tvshows')

def auto_update_movies():
	if ADDON.getSetting('auto_update') == "false":
		return
	print "executing movies"
	UpdateMovies(True)
	update_update_library(what='movies')
	

def update_update_library(what='tvshows'):	
	if ADDON.getSetting('update_library') == "false":
		return
	if what=='tvshows':
		xbmc.executebuiltin('UpdateLibrary(video,' + TV_SHOWS_PATH + ')')
	else:
		xbmc.executebuiltin('UpdateLibrary(video,' + MOVIES_PATH + ')')	
		
##################
### Addon menu ###
##################

def AddonMenu():  #homescreen
	print 'IceLibrary menu'
	AddOption('Movies',True, 1000)
	AddOption('TV shows',True, 2000)
	AddOption('Resolver Settings',True, 3000)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def MoviesMenu(): #1000
	print 'Movie menu'
	AddOption('Update movies',False, 1100)
	AddOption('Pick movies',True, 1200)
	AddOption('Setup movies',True, 1300)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))	

def UpdateMovies(silent = False): #1100
	GetFromPath("movies", True, MOVIES_PATH, "/movies/added/1", 'added', silent)
	
def MoviesListMenu(): #1200
	AddOption('A-Z',True, 1210)
	AddOption('Genres',True, 1220)	
	AddOption('Popular',True, 1230)	
	AddOption('Highly rated',True, 1240)	
	AddOption('Newly released',True, 1250)	
	AddOption('Newly added',True, 1260)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))	

def MoviesAlphabetMenu(): #1210
	print 'Movies alphabet screen'
	for character in AZ_DIRECTORIES:
		AddOption(character,True,1211,character)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def MoviesLetterScreen(name): #1211
	print 'Movies letter ' + str(name) + ' screen'
	GetFromPath("movies", False, MOVIES_DATA_PATH, "/movies/a-z/" + str(name), str(name))
	AddOptionsFromFile("movies", str(name), 20, False)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def MovieGenresMenu(): #1220
	print 'Movies genres screen'
	AddOption("Action",True,1221,"action")
	AddOption("Animation",True,1221,"animation")
	AddOption("Comedy",True,1221,"comedy")
	AddOption("Documentary",True,1221,"documentary")
	AddOption("Drama",True,1221,"drama")
	AddOption("Family",True,1221,"family")
	AddOption("Horror",True,1221,"horror")
	AddOption("Romance",True,1221,"romance")
	AddOption("Sci-Fi",True,1221,"sci-fi")
	AddOption("Thriller",True,1221,"thriller")
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
	
def MovieGenreScreen(name): #1221
	print 'Movies genre ' + str(name) + ' screen'
	GetFromPath("movies", False, MOVIES_DATA_PATH, "/movies/added/" + str(name), str(name))
	AddOptionsFromFile("movies", str(name),20, False)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def MoviePopularScreen(): #1230
	print 'Movies popular screen'
	GetFromPath("movies", False, MOVIES_DATA_PATH, "/movies/popular/1", "popular")
	AddOptionsFromFile("movies", "popular",20, False)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
	
def MovieRating(): #1240
	print 'Movies rating screen'
	GetFromPath("movies", False, MOVIES_DATA_PATH, "/movies/rating/1", "rating")
	AddOptionsFromFile("movies", "rating",20, False)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def MovieReleased(): #1250
	print 'Movies release screen'
	GetFromPath("movies", False, MOVIES_DATA_PATH, "/movies/release/1", "release")
	AddOptionsFromFile("movies", "release",20, False)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def MovieAdded(): #1260
	print 'Movies added screen'
	GetFromPath("movies", False, MOVIES_DATA_PATH, "/movies/added/1", "added")
	AddOptionsFromFile("movies", "added",20, False)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
	
def MoviesSetupMenu(): #1300
	print 'Movies setup screen'
	AddOption("Scrape all movies",False,1310)
	AddOption("Add IceLibrary movie directory to XBMC sources",False,1320)
	AddOption("Remove the movie directory and all (Icefilms) movie files",False,1330)
	#AddOption("Install auto update code in autoexec.py",False,1340)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def GetAllMovies(): #1310
	GetAllAZ("movies", True, MOVIES_PATH, "/movies/a-z/")
	
def AddMovieDirectory(): #1320
	SetupIceLibrary("movies")
	
def RemoveMovieDirectory(): #1330
	RemoveDirectory(MOVIES_PATH)
	
def TVShowsMenu(): #2000
	print 'TV shows menu'
	AddOption('Update favorites',True, 2100)
	AddOption('View favorites',True, 2200)
	AddOption('Add favorites',True, 2300)
	AddOption('Setup TV shows',True, 2400)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))	
	
def UpdateFavorites(silent = False): #2100
	GetFavorites("favorites.dat", silent)
	
def FavoritesListScreen(): #2200
	#AddOptionsFromFile("TV shows", "favorites",40, False)
	DBC.execute("SELECT * FROM ice_favorites ORDER BY name ASC")
	rows = DBC.fetchall()
	print rows
	for row in rows:
		AddOption(str(row[1]), True, 40, str(row[0]))
	
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def TVShowListMenu(): #2300
	AddOption('A-Z',True, 2310)
	AddOption('Genres',True, 2320)	
	AddOption('Popular',True, 2330)	
	AddOption('Highly rated',True, 2340)	
	AddOption('Newly released',True, 2350)	
	AddOption('Newly added',True, 2360)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
	
def TVShowAlphabetMenu(): #2310
	print 'TV shows alphabet screen'
	for character in AZ_DIRECTORIES:
		AddOption(character,True,2311,character)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def TVShowLetterScreen(name): #2311
	print 'TV shows letter ' + str(name) + '  screen'
	GetFromPath("TV shows", False, TV_SHOWS_DATA_PATH, "/tv/a-z/" + str(name), str(name))
	AddOptionsFromFile("TV shows", str(name),30, True)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def TVShowGenresMenu(): #2320
	print 'TV shows genres screen'
	AddOption("Action",True,2321,"action")
	AddOption("Animation",True,2321,"animation")
	AddOption("Comedy",True,2321,"comedy")
	AddOption("Documentary",True,2321,"documentary")
	AddOption("Drama",True,2321,"drama")
	AddOption("Family",True,2321,"family")
	AddOption("Horror",True,2321,"horror")
	AddOption("Romance",True,2321,"romance")
	AddOption("Sci-Fi",True,2321,"sci-fi")
	AddOption("Thriller",True,2321,"thriller")
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
	
def TVShowGenreScreen(name): #2321
	print 'TV shows genre ' + str(name) + ' screen'
	GetFromPath("TV shows", False, TV_SHOWS_DATA_PATH, "/tv/added/" + str(name), str(name))
	AddOptionsFromFile("TV shows", str(name),30, True)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def TVShowPopularScreen(): #2330
	print 'TV shows popular screen'
	GetFromPath("TV shows", False, TV_SHOWS_DATA_PATH, "/tv/popular/1", "popular")
	AddOptionsFromFile("TV shows", "popular",30, True)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
	
def TVShowRating(): #2340
	print 'TV shows rating screen'
	GetFromPath("TV shows", False, TV_SHOWS_DATA_PATH, "/tv/rating/1", "rating")
	AddOptionsFromFile("TV shows", "rating",30, True)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def TVShowReleased(): #2350
	print 'TV shows release screen'
	GetFromPath("TV shows", False, TV_SHOWS_DATA_PATH, "/tv/release/1", "release")
	AddOptionsFromFile("TV shows", "release",30, True)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def TVShowAdded(): #2360
	print 'TV shows added screen'
	GetFromPath("TV shows", False, TV_SHOWS_DATA_PATH, "/tv/added/1", "added")
	AddOptionsFromFile("TV shows", "added",30, True)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
	
def TVShowSetupMenu(): #2400
	print 'TV shows setup screen'
	AddOption("Add IceLibrary TV shows directory to XBMC sources",False,2410)
	AddOption("Remove the TV shows directory and all (Icefilms) TV shows",False,2420)
	AddOption("Delete favorites file",False,2430)
	AddOption("Install auto update code in autoexec.py",False,2440)
	AddOption("Create Recently Aired Playlist",False,2450)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))	
	
def AddTVShowDirectory(): #2410
	SetupIceLibrary("TV shows")
	
def RemoveTVShowDirectory(): #2420
	RemoveDirectory(TV_SHOWS_PATH)
	
def DeleteFavoritesFile(): #2430
	DeleteFavorites()
	
def AddOption(text, isFolder, mode, name=''):
	li = xbmcgui.ListItem(text)
	url = sys.argv[0]+'?mode=' + str(mode) + '&name='+  name
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=isFolder)
	
def AddOptionsFromFile(type, name, mode, remove_favorites):
	file_data = LoadData(type, str(name) + ".dat")
	
	if remove_favorites:
		favorites_data = LoadData(type, "favorites.dat")
		for data in file_data:
			exclude = False
			for favorite in favorites_data:
				if len(data) > 0 and len(favorite) > 0:
					if data[1]==favorite[1]:
						exclude = True
			if not exclude:
				if len(data) > 0:
					index = file_data.index(data)
					text = CleanFileName(data[0], True, use_blanks = False)
					AddOption(text,False,str(mode),str(name)+':'+str(index))
	else:
		for data in file_data:
			if len(data) > 0:
				index = file_data.index(data)
				AddOption(data[0],False,str(mode),str(name)+':'+str(index))
	xbmcplugin.endOfDirectory(int(sys.argv[1]))	
		
########################
### Params and stuff ###
########################

def GetParams():
	param=[]
	paramstring=sys.argv[len(sys.argv)-1]
	if len(paramstring)>=2:
		cleanedparams=paramstring.replace('?','')
		if (paramstring[len(paramstring)-1]=='/'):
				paramstring=paramstring[0:len(paramstring)-2]
		pairsofparams=cleanedparams.split('&')
		param={}
		for i in range(len(pairsofparams)):
			splitparams={}
			splitparams=pairsofparams[i].split('=')
			if (len(splitparams))==2:
				param[splitparams[0]]=splitparams[1]			
	return param

params=GetParams()
url=None
name=None
mode=None
href=None
path=None

try:
		url=urllib.unquote_plus(params["url"])
except:
		pass
try:
		name=urllib.unquote_plus(params["name"])
except:
		pass
try:
		path=urllib.unquote_plus(params["path"])
except:
		pass
try:
		mode=int(params["mode"])
except:
		pass
try:
		href=urllib.unquote_plus(params["href"])
except:
		pass		
print '==========================PARAMS:\nHREF: %s\nNAME: %s\nMODE: %s\nURL: %s\nMYHANDLE: %s\nPARAMS: %s' % ( href, name, mode, url, sys.argv[1], params )

if mode==None: #Main menu
	#LoginStartup()	
	AddonMenu()
elif mode==10: #Run stream
	#LoginStartup()
	LaunchSTRM(name, href, path)
elif mode==20: #Add movie
	AddMovie(name)
elif mode==30: #Add TV show to favorites
	AddToFavorites(name)
elif mode==40: #Remove TV show from favorites
	RemoveFromFavorites(name)
elif mode==100: #Update the library and set a timer for the next update
	auto_update_tvshows()
elif mode==110: #Update the library and set a timer for the next update
	auto_update_movies()
elif mode==1000: #Movies menu
	MoviesMenu()
elif mode==1100: #Update movies
	UpdateMovies()
elif mode==1200: #Pick movies
	MoviesListMenu()
elif mode==1210: #Alphabet list
	MoviesAlphabetMenu()
elif mode==1211: #A
	MoviesLetterScreen(name)
elif mode==1220: #Genres
	MovieGenresMenu()
elif mode==1221: #Action
	MovieGenreScreen(name)
elif mode==1230: #Popular
	MoviePopularScreen()
elif mode==1240: #Rating
	MovieRating()
elif mode==1250: #Release
	MovieReleased()
elif mode==1260: #Added
	MovieAdded()
elif mode==1300: #Setup movies
	MoviesSetupMenu()
elif mode==1310: #Get all movies
	GetAllMovies()
elif mode==1320: #Add movie folder to XBMC sources
	AddMovieDirectory()
elif mode==1330: #Remove movie folder
	RemoveMovieDirectory()
elif mode==1340: #Setup auto update
	SetupAutoUpdate()
elif mode==2000: #TV Shows menu
	initilizeDatabase()
	TVShowsMenu()
elif mode==2100: #Update TV Shows
	UpdateFavorites()
elif mode==2200: #View favorites
	FavoritesListScreen()
elif mode==2300: #Add favorite menu
	TVShowListMenu()
elif mode==2310: #Alphabet list
	TVShowAlphabetMenu()
elif mode==2311: #A
	TVShowLetterScreen(name)
elif mode==2320: #Genres
	TVShowGenresMenu()
elif mode==2321: #Action
	TVShowGenreScreen(name)
elif mode==2330: #Popular
	TVShowPopularScreen()
elif mode==2340: #Rating
	TVShowRating()
elif mode==2350: #Release
	TVShowReleased()
elif mode==2360: #Added
	TVShowAdded()
elif mode==2400: #Setup TV Shows
	TVShowSetupMenu()
elif mode==2410: #Add TV shows folder to XBMC sources
	AddTVShowDirectory()
elif mode==2420: #Remove TV shows folder
	RemoveTVShowDirectory()
elif mode==2430: #Remove favorites file
	DeleteFavoritesFile()
elif mode==2440: #Setup auto update
	SetupAutoUpdate()
elif mode==2450: #Create RecentlyAired.xsp
	CreateRecentPlaylist()
elif mode==3000:
	urlresolver.display_settings()
