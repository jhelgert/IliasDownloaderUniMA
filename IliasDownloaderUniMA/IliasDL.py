#!/usr/bin/env python3

from requests import session, get, ConnectionError
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path as plPath
from dateparser import parse as parsedate
from datetime import datetime
from multiprocessing.pool import ThreadPool
import math
import os	
import shutil
import re

class IliasDownloaderUniMA():
	"""
	Base class
	"""
	
	base_url = "https://ilias.uni-mannheim.de/"
	desktop_url = "https://ilias.uni-mannheim.de/ilias.php?baseClass=ilPersonalDesktopGUI"


	def __init__(self):
		"""
		Constructs a new instance.
		"""
		self.current_semester_pattern = self.getCurrentSemester()
		self.courses = []
		self.to_scan = []
		self.files = []
		self.params = {
			'num_scan_threads' : 5, 
			'num_download_threads': 5, 
			'download_path': os.getcwd(),
			'tutor_mode': False,
			'verbose' : False
		}
		self.session = None
		self.login_soup = None
		self.background_task_files = []
		self.background_tasks_to_clean = []
		self.external_scrapers = []


	def getCurrentSemester(self):
		d = datetime.now()
		if d.month in range(2, 8):
			return rf"\((FSS|ST) {d.year}\)"
		else:
			return rf"\((HWS|WT) {d.year}\)"


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
		if param == 'download_path':
			if os.path.isdir(value):
				self.params[param] = value
		if param == 'verbose':
			if type(value) is bool:
				self.params[param] = value
		if param == 'tutor_mode':
			if type(value) is bool:
				self.params[param] = value


	def createIliasUrl(self, iliasid):
		"""
		Creates an ilias url from the ilias ref id.
	
		:param      iliasid:  The ilias ref id
		:type       iliasid:  int
	
		:returns:   feasible url
		:rtype:     str
		"""

		return self.base_url + "ilias.php?ref_id=" + str(iliasid) \
		+ "&cmd=frameset" + "&cmdClass=ilrepositorygui" \
		+ "&cmdNode=vi" + "&baseClass=ilrepositorygui"


	def login(self, login_id, login_pw):
		"""
		create requests session and log into ilias.uni-mannheim.de
	
		:param      args:       login details (uni-id and password)
		:type       args:       list
				
		:raises     TypeError:  
		"""
		if type(login_id) is not str or type(login_pw) is not str:
			raise TypeError("...")
		# User data and user-agent
		data = {'username': login_id, 'password': login_pw}
		head = {
			'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) "\
							+ "AppleWebKit/537.36 (KHTML, like Gecko) " \
							+ "Chrome/56.0.2924.87 Safari/537.36",
			'Connection': 'keep-alive'
		}
		self.session = session()
		self.login_soup = BeautifulSoup(self.session.get("https://cas.uni-mannheim.de/cas/login").content, "lxml")
		form_data = self.login_soup.select('form[action^="/cas/login"] input')
		data.update({inp["name"]: inp["value"] for inp in form_data if inp["name"] not in data})
		self.session.post('https://cas.uni-mannheim.de/cas/login', data=data, headers=head)
		self.login_soup = BeautifulSoup(self.session.get(self.base_url).content, "lxml")
		# Login successful? FIY
		if not self.login_soup.find("a", {'id' : 'mm_desktop'}):
			raise ConnectionError("Couldn't log into ILIAS. Make sure your provided uni-id and the password are correct.")


	def addCourse(self, iliasid, course_name=None):
		"""
		Adds a course to the courses list.
	
		:param      iliasid:  the ilias ref id of the course
		:type       iliasid:  int
		"""

		url = self.createIliasUrl(iliasid)
		if not course_name:
			soup = BeautifulSoup(self.session.get(url).content, "lxml")
			course_name = soup.select_one("#mainscrolldiv > ol > li:nth-child(3) > a").text
		if (course_name := re.sub(r"\[.*\] ", "", course_name)):
			self.courses += [{'name' : course_name, 'url': url}]


	def addCourses(self, *iliasids):
		"""
		Adds multiple courses to the courses list
	
		:param      iliasids:  the ilias ref ids of the courses
		:type       iliasids:  list
		"""

		for iliasid in iliasids:
			self.addCourse(iliasid)


	def addAllSemesterCourses(self, semester_pattern=None, exclude_ids=[]):
		"""
		Extracts the users subscribed courses of the specified semester 
		and adds them to the course list.

		:param      semester_pattern:  semester or regex for semester
		:type       semester_pattern:  string
		:param      exclude_ids:  optional ilias ids to ignore
		:type       exclude_ids:  list
		"""

		if semester_pattern is None:
			semester_pattern = self.current_semester_pattern

		# Performance gain in case of many courses
		semester_compiled = re.compile(semester_pattern)
		extract_compiled = re.compile(r"ref_id=(\d+)")

		for course in self.login_soup.find_all("a", "il_ContainerItemTitle"):
			course_name = course.text

			if semester_compiled.search(course_name):
				url = course["href"]

				if (match := extract_compiled.search(url)):
					iliasid = int(match.group(1))

					if iliasid not in exclude_ids:
						self.addCourse(iliasid, course_name)


	def _determineItemType(self, url):
		if "target=file" in url:
			return "file"
		elif "calldirectlink" in url:
			return "link"
		elif "showThreads" in url:
			return "forum"
		elif "showOverview" in url:
			return "task"
		elif "ilHTLMPresentationGUI" in url:
			return "lernmaterialien"
		else:
			return "folder"


	def _parseFileProperties(self, bs_item):
		"""
		Tries to parse the file's size, modification date and the file ending.
		Note: there are some cases where Ilias doesn't provide a modification 
		date and/or a file size.

		:param      bs_item:  The beautifulsoup item
		:type       bs_item:  { type_description }

		:returns:   file ending, file size, file modification date
		:rtype:     tuple
		"""

		props = bs_item.find_all('span', 'il_ItemProperty')
		p = [i for i in props if len(i.text.split()) > 0 and "Version" not in i.text]
		# Parse the file ending
		if len(p[0].text.split()) > 1:
			file_ending = ""
		else:
			file_ending = "." + p[0].text.split()[0]

		# Parse the file size
		if len(p) > 1:
			size_tmp = p[1].text.lower().replace(".","").replace(",", ".").split()
			size = float(size_tmp[0])
			if size_tmp[1] == "kb":
				size *= 1e-3
			elif size_tmp[1] == "bytes":
				size *= 1e-6
		else:
			size = math.nan

		# Parse the modification date
		if len(p) > 2:
			mod_date = parsedate(p[2].text)
		else:
			mod_date = datetime.fromisoformat('2000-01-01')

		return file_ending, size, mod_date


	def parseVideos(self, mc_soup):
		# Checks if there's a video inside the mediacontainer:
		if (vsoup := mc_soup.find('video', {"class": "ilPageVideo"})):
			if (v_src := vsoup.find('source')['src']):
				v_url = urljoin(self.base_url, v_src)
				v_name = re.search(r"mobs/mm_\d+/(.*)\?il_wac_token.*", v_src).group(1)
				try:
					v_size = float(self.session.head(v_url).headers['Content-Length']) * 1e-6
				except:
					v_size = math.nan
				# The HEAD requests misses the 'last-modified' key, so it's not
				# possible to get the mod date from there :(
				v_mod_date = datetime.fromisoformat('2000-01-01')
			return v_name, v_size, v_mod_date, v_url
		else:
			return None


	def scanMediaContainer(self, course_name, file_path, soup):
		"""
		Scans videos on the top of the course inside the MediaContainer and
		adds them to the list 'to_scan'.

		:param      soup:  The soup
		:type       soup:  { type_description }
		"""

		if self.params['verbose']:
			print(f"Scanning Videos...")
		for mc in soup.find_all("figure", {"class": "ilc_media_cont_MediaContainer"}):
			if (video := self.parseVideos(mc)):
				v_name, v_size, v_mod_date, v_url = video
				self.files += [{ 
					'course': course_name, 
					'type': 'file',
					'name': v_name,
					'size': v_size,
					'mod-date': v_mod_date,
					'url': v_url,
					'path': file_path
				}]


	def scanContainerList(self, course_name, file_path, soup):
		"""
		Scans the soup object for links inside the ContainerList and adds
		them to the list 'to_scan'. See _determineItemType() for the possible types of links.

		:param      soup:  
		:type       soup:  bs4.BeautifulSoup
		"""

		for i in (items := soup.find_all("div", "il_ContainerListItem")):
			if (subitem := i.find('a', href=True)):
				el_url =  urljoin(self.base_url, subitem['href'])
				el_name = subitem.text
				el_type = self._determineItemType(el_url)
				if el_type == "file":
					ending, size, mod_date = self._parseFileProperties(i)
					self.files += [{
						'course': course_name, 
						'type': el_type,
						'name': el_name + ending,
						'size': size,
						'mod-date': mod_date,
						'url': el_url,
						'path': file_path
					}]
				elif el_type in ["folder", "task", "lernmaterialien"]:
					self.to_scan += [{
						'type': el_type, 
						'name': el_name, 
						'url': el_url
					}]


	def scanFolder(self, course_name, url_to_scan):
		"""
		Scans a folder.

		:param      course_name:  The name of the course the folder belongs to
		:type       course_name:  str
		:param      url_to_scan:  The url to scan
		:type       url_to_scan:  str
		"""


		url = urljoin(self.base_url, url_to_scan)
		soup = BeautifulSoup(self.session.get(url).content, "lxml")
		file_path = course_name + "/" +  "/".join(soup.find("body").find("ol").text.split("\n")[4:-1]) + "/"
		file_path = file_path.replace(":", " - ")
		if self.params['verbose']:
			print(f"Scanning Folder...\n{file_path}\n{url}")
			print("-------------------------------------------------")
		self.scanMediaContainer(course_name, file_path, soup)
		self.scanContainerList(course_name, file_path, soup)


	def scanTaskUnit(self, course_name, url_to_scan):
		"""
		Scans a task unit.

		:param      course_name:  The name of the course the Task belongs to
		:type       course_name:  str
		:param      url_to_scan:  The url to scan
		:type       url_to_scan:  str
		"""

		url = urljoin(self.base_url, url_to_scan)
		soup = BeautifulSoup(self.session.get(url).content, "lxml")
		task_unit_name = soup.find("a", {"class" : "ilAccAnchor"}).text  
		file_path = course_name + "/" + "Aufgaben/" + task_unit_name + "/"
		file_path = file_path.replace(":", " - ")
		task_items = soup.find("div", {"id":"infoscreen_section_1"}).find_all("div", "form-group")
		if self.params['verbose']:
			print(f"Scanning TaskUnit...\n{file_path}\n{url}")
			print("-------------------------------------------------")
		for i in task_items:
			el_url = urljoin(self.base_url, i.find('a')['href'])
			el_name = i.find("div", 'il_InfoScreenProperty').text
			el_type = 'file'
			file_mod_date = datetime.fromisoformat('2000-01-01')
			file_size = math.nan
			self.files += [{
				'course': course_name,
				'type': el_type,
				'name': el_name,
				'size': file_size,
				'mod-date': file_mod_date,
				'url': el_url,
				'path': file_path
			}]
		# Now scan the submissions
		if self.params['tutor_mode']:
			self.scanTaskUnitSubmissions(course_name, file_path, soup)


	def scanTaskUnitSubmissions(self, course_name, file_path, soup):

		form_data = {
			'user_login': '',
			'cmd[downloadSubmissions]': 'Alle Abgaben herunterladen'
		}

		# Deadline finished?
		deadline = soup.select_one('#infoscreen_section_2 > div:nth-child(2) > div.il_InfoScreenPropertyValue.col-xs-9').text
		if (deadline_time := parsedate(deadline)) < datetime.now():
			# Access to the submissions?
			if (tab_grades := soup.select_one('#tab_grades > a')):
				tab_grades_url = urljoin(self.base_url, tab_grades['href'])
				submissions_soup = BeautifulSoup(self.session.get(tab_grades_url).content, "lxml")
				form_action_url = urljoin(self.base_url, submissions_soup.find('form', {'id': 'ilToolbar'})['action'])
				# Post form data
				r = self.session.post(form_action_url, data=form_data)
				el_name = submissions_soup.select_one('#il_mhead_t_focus').text.replace("\n", "") + ".zip"
				# Add backgroundtask file to list, we parse the download links
				# later from the background tasks tab from the page header
				self.background_task_files += [{
						'course': course_name, 
						'type': 'file',
						'name': el_name,
						'size': math.nan,
						'mod-date': deadline_time,
						#'url': dl_url,
						'path': file_path
					}]


	def searchBackgroundTaskFile(self, el_name):
		#
		# TO DO: Cleanup!!!
		#
		for idx, f in enumerate(self.background_task_files):
			f["name"] = f["name"].encode()
			f["name"] = f["name"].replace('ü'.encode(), b'ue')
			f["name"] = f["name"].replace('Ü'.encode(), b'Ue')
			f["name"] = f["name"].replace('ä'.encode(), b'ae')
			f["name"] = f["name"].replace('Ä'.encode(), b'Ae')
			f["name"] = f["name"].replace('ö'.encode(), b'oe')
			f["name"] = f["name"].replace('Ö'.encode(), b'Oe')
			f["name"] = f["name"].replace('ß'.encode(), b'ss')
			f["name"] = f["name"].decode('utf-8')
			if f["name"] == el_name:
				return self.background_task_files.pop(idx)


	def parseBackgroundTasks(self):
		# time.sleep(5) # Not really needed?
		# Reload ilias main page to parse the background tasks bar on the top
		desktop_soup = BeautifulSoup(self.session.get(self.desktop_url).content, "lxml") 
		tasks_tab_url = urljoin(self.base_url, desktop_soup.select_one('#mm_tb_background_tasks')['refresh-uri'])
		tasks_tab_soup = BeautifulSoup(self.session.get(tasks_tab_url).content, "lxml")
		# Extract the items
		for i in tasks_tab_soup.find_all('div', {'class': 'il-item-task'}):
			# Extract the download url and the remove url
			dl, rm = i.find_all('button', {'class': 'btn btn-default'})
			dl_url = urljoin(self.base_url, dl['data-action'])
			rm_url = urljoin(self.base_url, rm['data-action'])
			self.background_tasks_to_clean.append(rm_url)
			# Add file to downloads
			el_name = i.find('div', {'class' : 'il-item-task-title'}).text.replace("\n", "") + ".zip"
			if (bt := self.searchBackgroundTaskFile(el_name)): 
				self.files += [{
					'course': bt['course'], 
					'type': 'file',
					'name': el_name,
					'size': bt['size'],
					'mod-date': bt['mod-date'],
					'url': dl_url,
					'path': bt['path']
				}]


	def scanLernmaterial(self, course_name, url_to_scan):
		pass
		# ... to do ...


	def scanHelper(self, course_name, el):
		if len(self.to_scan) > 0:
			self.to_scan.pop()
		if el['type'] == "folder":
			self.scanFolder(course_name, el['url'])
		if el['type'] == "task":
			self.scanTaskUnit(course_name, el['url'])
		elif el['type'] == 'lernmaterialien':
			self.scanLernmaterial(course_name, el['url'])


	def searchForFiles(self, course_name):
		"""
		Scans an ilias url and all nested subfolders for files
	
		:param      arg:  url for the "dateien" folder
		:type       arg:  str
		"""
		while len(self.to_scan) > 0:
			results = ThreadPool(self.params['num_scan_threads']).imap_unordered(lambda x: self.scanHelper(course_name, x), self.to_scan)
			for r in results:
				pass

	def addExternalScraper(self, scraper, *args):
		self.external_scrapers.append({'fun' : scraper, 'args': args})


	def scanCourses(self):
		"""
		Scans all courses inside the instance's courses list.
		"""

		for course in self.courses:
			self.to_scan += [{
				'type' : 'folder', 
				'name': course['name'], 
				'url': course['url']
			}]
			print(f"Scanning {course['name']} with {self.params['num_scan_threads']} Threads....")
			self.searchForFiles(course['name'])
		# External Scrapers
		for d in self.external_scrapers:
			print(f"Scanning {d['args'][0]} with the external Scraper....")
			self.files += d['fun'](*d['args'])
			
			
	def downloadFile(self, file):
		"""
		Downloads a file.
	
		:param      file:  The file we want do download
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
		if self.params['tutor_mode']:
			# Parse the background tasks, i.e. add them to the download files
			self.parseBackgroundTasks()
		# Check the file paths
		paths = list(set([os.path.join(self.params['download_path'],f['path']) for f in self.files]))
		for p in paths:
			if not plPath(p).exists():
				plPath(p).mkdir(parents=True, exist_ok=True)
		# Download all files
		for r in ThreadPool(self.params['num_download_threads']).imap_unordered(self.downloadFile, self.files):
			pass
		# Clean the background tasks tab
		if self.params['tutor_mode']:
			if self.params['verbose']:
				print("Tutor mode. Cleaning the background tasks...")
			for r in ThreadPool(self.params['num_download_threads']).imap_unordered(lambda x: self.session.get(x), self.background_tasks_to_clean):
				pass
