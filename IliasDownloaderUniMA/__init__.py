#!/usr/bin/env python3

from requests import session, get
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path as plPath
from dateutil.parser import parse as parsedate
from datetime import datetime
from multiprocessing.pool import ThreadPool
import math
import os	
import shutil
import re

##### TO DO
#
##
## Dokumentation der einzelnen Methoden
## Login check
## README erweitern

class IliasDownloaderUniMA():
	"""
	Base class
	"""
	
	base_url = "https://ilias.uni-mannheim.de/"

	def __init__(self):
		"""
		Constructs a new instance.
		"""
		self.courses = []
		self.folders_to_scan = []
		self.tasks_to_scan = []
		self.files = []
		self.params = {'num_scan_threads' : 10, 'num_download_threads': 10, 'download_path': os.getcwd()}
		self.session = None
		self.soup = None


	def setParam(self, param, value):
		"""
		Sets the parameter.
	
		:param      arg:    The parameter we want to alter
		:type       arg:    string
		:param      value:  The new parameter value
		:type       value:  str or int
		"""

		if param in ['num_scan_threads', 'num_download_threads']:
			if type(value) is int:
				self.params[param] = value
		elif param == 'download_path':
			if os.path.isdir(value):
				self.params[param] = value


	def createIliasUrl(self, iliasid):
		"""
		Creates an ilias url.
	
		:param      iliasid:  The ilias_id
		:type       iliasid:  int
	
		:returns:   feasible url
		:rtype:     str
		"""

		return "https://ilias.uni-mannheim.de/ilias.php?ref_id=" \
		+ str(iliasid) \
		+ "&cmd=frameset&cmdClass=ilrepositorygui" \
		+ "&cmdNode=vi&baseClass=ilrepositorygui"


	def login(self, login_id, login_pw):
		"""
		create requests session and log into ilias.uni-mannheim.de
	
		:param      args:       login details (uni-id and password)
		:type       args:       list
				
		:raises     TypeError:  
		"""
		if type(login_id) is not str or type(login_pw) is not str:
			raise TypeError("...")
		data = {'username': login_id, 'password': login_pw}
		head = {
			'Accept-Encoding': 'gzip, deflate, sdch, br',
			'Accept-Language': 'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4',
			'Upgrade-Insecure-Requests': '1',
			'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
			'Connection': 'keep-alive',
		}
		self.session = session()
		self.soup = BeautifulSoup(self.session.get("https://cas.uni-mannheim.de/cas/login").content, "lxml")
		form_data = self.soup.select('form[action^="/cas/login"] input')
		data.update({inp["name"]: inp["value"] for inp in form_data if inp["name"] not in data})
		self.session.post('https://cas.uni-mannheim.de/cas/login', data=data, headers=head)


	def checkLogin(self, soup):
		pass # To do


	def addCourse(self, iliasid):
		"""
		Adds a course to the courses list.
	
		:param      iliasid:  the ilias ref id of the course
		:type       iliasid:  int
		"""

		url = self.createIliasUrl(iliasid)
		soup = BeautifulSoup(self.session.get(url).content, "lxml")
		course_name = soup.find_all("ol", "breadcrumb")[0].find_all('li')[2].get_text()
		course_name = re.sub(r"\[.*\] ", "", course_name)
		self.courses += [{'name' : course_name, 'url': url}]


	def addCourses(self, *iliasids):
		"""
		Adds multiple courses to the courses list
	
		:param      iliasids:  the ilias ref ids of the courses
		:type       iliasids:  list
		"""

		for iliasid in iliasids:
			self.addCourse(iliasid)


	def translate_date(self, datestr):
		"""
		Translates a timestamp %d. %M %Y, %h:%m into an english one by only
		translating %M, i.e. the month, from german to english.
	
		:param      datestr:  date (with german months)
		:type       datestr:  str
	
		:returns:   date (with english months)
		:rtype:     str
		"""

		today = datetime.now()
		gestern = today.replace(day = today.day-1).strftime("%d. %b %Y")
		d = {"Mär": "Mar", "Mai": "May", "Jun": "Jun", "Jul": "Jul", "Okt": "Oct", "Dez": "Dec",
		"Gestern": gestern, "Heute": today.strftime("%d. %b %Y")}
		for key in d.keys():
			datestr = datestr.replace(key, d[key])
		return datestr

	def _determineItemType(self, url):
		if "target=file" in url:
			return "file"
		elif "calldirectlink" in url:
			return "link"
		elif "showThreads" in url:
			return "forum"
		elif "showOverview" in url:
			return "task"
		else:
			return "folder"

	def _parseFileProperties(self, bs_item):
		p = bs_item.find_all('span', 'il_ItemProperty')
		file_ending = p[0].get_text().split()[0]
		file_size_tmp = p[1].get_text().replace(",", ".").split()
		file_size = float(file_size_tmp[0])
		if file_size_tmp[1] == "KB":
			file_size *= 1e-3
		file_mod_date = parsedate(self.translate_date(p[-1].get_text()), dayfirst=True)
		return file_ending, file_size, file_mod_date


	def scanFolder(self, course_name, url_to_scan):
		"""
		Scans a folder.
	
		:param      args:  course name and the url we want to scan
		:type       args:  list
		"""

		if len(self.folders_to_scan) > 0:
			self.folders_to_scan.pop()
		url = urljoin(self.base_url, url_to_scan)
		soup = BeautifulSoup(self.session.get(url).content, "lxml")
		file_path = course_name + "/" +  "/".join(soup.find("body").find("ol").text.split("\n")[-2]) + "/"
		items = soup.find_all("div", "il_ContainerListItem")
		for i in items:
			subitem = i.find('a', href=True)
			el_url =  subitem['href']
			el_name = subitem.get_text()
			el_type = self._determineItemType(el_url)
			if el_type == "file":
				file_ending, file_size, file_mod_date = self._parseFileProperties(i)
				el_name += "." + file_ending
				self.files += [{'course': course_name, 'type': el_type, \
					'name': el_name, \
					'size': file_size, \
					'mod-date': file_mod_date, \
					'url': el_url, \
					'path': file_path}]
			elif el_type == "folder":
				self.folders_to_scan += [{'type': el_type, 'name': el_name, 'url': el_url}]
			elif el_type == 'task':
				self.tasks_to_scan += [{'type' : el_type, 'name': el_name, 'url': el_url}]


	def searchFolderForFiles(self, course_name):
		"""
		Scans an ilias url and all nested subfolders for files
	
		:param      arg:  url for the "dateien" folder
		:type       arg:  str
		"""
		while len(self.folders_to_scan) > 0:
			results = ThreadPool(self.params['num_scan_threads']).imap_unordered(lambda x: self.scanFolder(course_name, x['url']), self.folders_to_scan)
			for r in results:
				pass

	def scanTaskUnit(self, task_unit_name, url_to_scan):
		if len(self.tasks_to_scan) > 0:
			self.tasks_to_scan.pop()
		url = urljoin(self.base_url, url_to_scan)
		soup = BeautifulSoup(self.session.get(url).content, "lxml")
		file_path = task_unit_name + "/"
		task_items = soup.find_all("div", {"id":"infoscreen_section_1"})[0].find_all("div", "form-group")
		for i in task_items:
			el_url = i.find('a')['href']
			el_name = i.find("div", 'il_InfoScreenProperty').get_text()
			file_mod_date = ...
			file_size = math.nan



	def scanCourses(self):
		"""
		Scans all courses inside the instance's courses list.
		"""

		for course in self.courses:
			self.folders_to_scan += [{'type' : 'folder', 'name': course['name'], 'url': course['url']}]
			print(f"Scanning {course['name']} with {self.params['num_scan_threads']} Threads....")
			self.searchFolderForFiles(course['name'])
			
			
	def downloadFile(self, file):
		"""
		Downloads a file.
	
		:param      file:  The file
		:type       file:  dict
	
		:returns:   { description_of_the_return_value }
		:rtype:     { return_type_description }
		"""

		file_dl_path = os.path.join(self.params['download_path'],file['path'], file['name'])
		file_mod_date = file['mod-date'].timestamp()
		size = file['size']
		# Does the file already exists locally and is the newest version?
		if os.path.exists(file_dl_path) and file_mod_date < os.path.getmtime(file_dl_path):
			return
		else:
			# Download the file
			r = self.session.get(file['url'], stream=True)
			if r.status_code == 200:
				try:
					with open(file_dl_path, 'wb') as f:
						print(f"Downloading {file['course']}: {file['name']} ({size:.1f} MB)...")
						shutil.copyfileobj(r.raw, f)
				except Exception as e:
					return e


	def downloadAllFiles(self):
		"""
		Downloads all files inside the instance's files list.
		"""

		# Scan all files
		self.scanCourses()
		# Check the file paths
		paths = list(set([os.path.join(self.params['download_path'],f['path']) for f in self.files]))
		for p in paths:
			if not plPath(p).exists():
				plPath(p).mkdir(parents=True, exist_ok=True)
		# Download all files
		for r in ThreadPool(self.params['num_download_threads']).imap_unordered(self.downloadFile, self.files):
			pass

