import time, sys, os, math
from datetime import datetime, date
import xbmc
import xbmcaddon
import xbmcvfs
from donnie.settings import Settings

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")


class IceLibraryService:
	def __init__(self):

		self.addon_id = "plugin.video.icelibrary2"
		self.initiated = datetime.now()
		self.delay = 30
		self.timers = {}

	def getSetting(self, setting):
		return xbmcaddon.Addon(self.addon_id).getSetting(setting)

	def getBoolSetting(self, setting):
		return  str2bool(xbmcaddon.Addon(self.addon_id).getSetting(setting))

	def setSetting(self, setting, value):
		return xbmcaddon.Addon(self.addon_id).setSetting(setting, value)

	def isEnabled(self):
		return self.getBoolSetting('auto_update')

	def setLastRun(self, event, runtime):
		self.setSetting('last-run_'+event,runtime)

	def timestamp(self, d):
   		return time.mktime(d.timetuple())

	def getNextRun(self, f, delay=0):
		seconds =  f * 3600
		delay = delay * 60;
		today = date.today()
		zero = self.timestamp(today)
		now = self.timestamp(datetime.now())
		delta = (now - zero) / (seconds)
		offset = math.ceil(delta)
		next =  offset * seconds + (zero + delay)
		next = datetime.fromtimestamp(next)
		return next
	
		
	def getLastRun(self, event):
		runtime=self.getSetting('last-run_'+event)
		if runtime:
			try:
				lastrun = datetime.strptime(runtime, '%Y-%m-%d %H:%M:%S.%f')
			except TypeError:
				 lastrun = datetime.fromtimestamp(time.mktime(time.strptime(runtime, '%Y-%m-%d %H:%M:%S.%f')))
			return lastrun
		else:
			return self.initiated
	
	def loadSettings(self):
		xbmc.log("Loading service settings")
		self.enabled = self.getBoolSetting('auto_update')
		self.update_timer = self.convertSettingToHours(self.getBoolSetting('update_timer'))
		self.update_tvshows = self.getBoolSetting('update_tvshows')
		self.update_movies = self.getBoolSetting('update_movies')
		self.update_library = self.getBoolSetting('update_library')
		self.update_artwork = self.getBoolSetting('update_artwork')
	
	def clearTimers(self):
		xbmc.log("Clear timers")
		self.setLastRun('tvshows', '')
		self.setLastRun('movies', '')
	
	def removeFile(self, path):
		if xbmcvfs.exists(path):
		    try:
			print "Unlinking: %s" % path
			xbmcvfs.delete(path)
		    except:
			print "Exception: ",str(sys.exc_info())

	def setupTimers(self):
		xbmc.log("Launching timers")
		if not self.enabled:
			return

		if self.update_tvshows:
			nextrun = self.getNextRun(self.update_timer)
			print "Next tvshow update schedualed to run at " + str(nextrun)
			self.timers['tvshows'] = {}
			self.timers['tvshows']['lastrun'] = self.getLastRun('tvshows')
			self.timers['tvshows']['interval'] = self.update_timer
			self.timers['tvshows']['nextrun'] = nextrun
			self.timers['tvshows']['command'] = 'RunScript(' + self.addon_id + ', mode=100)'
		else:
			self.timers['tvshows'] = None

		if self.update_movies:
			nextrun = self.getNextRun(self.update_timer, 10)
			print "Next movie update schedualed to run at " + str(nextrun)
			self.timers['movies'] = {}
			self.timers['movies']['lastrun'] = self.getLastRun('movies')
			self.timers['movies']['interval'] = self.update_timer
			self.timers['movies']['nextrun'] = nextrun
			self.timers['movies']['command'] = 'RunScript(' + self.addon_id + ', mode=110)'
		else:
			self.timers['movies'] = None


	def convertSettingToHours(self, t):
		h = 0
		timers = [2, 4, 8, 12, 24]
		h=timers[int(t)]
		return h
		
	
	def start(self):
		xbmc.log("Icelibrary2 service starting...")
		self.loadSettings()
		self.clearTimers()
		self.setupTimers()
		self.run()
	
	def run(self):
		xbmc.log("Waiting for next event...")
		while(not xbmc.abortRequested):
			if self.enabled:
				self.evaluateTimers()
				#print 'z'
			time.sleep(self.delay)
			if self.enabled != self.isEnabled() :
				self.loadSettings()
				self.setupTimers()
		xbmc.log("Icelibrary2 Service stopping...")

	
	def evaluateTimers(self):
		now = self.timestamp(datetime.now())
		if self.update_tvshows:
			if now > self.timestamp(self.timers['tvshows']['nextrun']):
				self.execute('tvshows')

		if self.update_movies:
			if now > self.timestamp(self.timers['movies']['nextrun']):
				self.execute('movies')



	def execute(self, event):
		xbmc.log("Executing: " + event)
		xbmc.log(str(datetime.now()))
		self.timers[event]['lastrun'] =  datetime.now()
		self.timers[event]['nextrun'] = self.getNextRun(self.timers[event]['interval'])
		self.setLastRun(event, str(self.timers[event]['lastrun']))
		xbmc.executebuiltin(self.timers[event]['command'])
		xbmc.log("Waiting for next event...")

if __name__ == '__main__':
	ILS = IceLibraryService()
	ILS.start()
