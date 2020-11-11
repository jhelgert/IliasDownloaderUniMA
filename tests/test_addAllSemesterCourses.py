from IliasDownloaderUniMA import IliasDownloaderUniMA
from bs4 import BeautifulSoup
import datetime
import math

no_regular_course = """
<a class="il_ContainerItemTitle" href="ilias.php?ref_id=988270&amp;cmdClass=ilrepositorygui&amp;cmdNode=vi&amp;baseClass=ilrepositorygui">Digitalisierung in der Lehre (Hilfskräfte und Tutorinnen und Tutoren)</a>
"""

regular_course_hws = """
<a class="il_ContainerItemTitle" href="ilias.php?ref_id=1020946&amp;cmdClass=ilrepositorygui&amp;cmdNode=vi&amp;baseClass=ilrepositorygui">GPU Programming [V] [1. PG] (HWS 2020)</a>
"""

regular_course_wt = """
<a class="il_ContainerItemTitle" href="ilias.php?ref_id=1022636&amp;cmdClass=ilrepositorygui&amp;cmdNode=vi&amp;baseClass=ilrepositorygui">OPM 561 Production Management: Lean Approaches and Variability [V] (WT 2020)</a>
"""

regular_course_fss = """
<a class="il_ContainerItemTitle" href="ilias.php?ref_id=965388&amp;cmdClass=ilrepositorygui&amp;cmdNode=vi&amp;baseClass=ilrepositorygui">BE 511 Business Economics II [V] (FSS 2020)</a>
"""

regular_course_st = """
<a class="il_ContainerItemTitle" href="ilias.php?ref_id=862822&amp;cmdClass=ilrepositorygui&amp;cmdNode=vi&amp;baseClass=ilrepositorygui">OPM 601 Supply Chain Management [V] [1. PG] (ST 2020)</a>
"""

def test_no_regular_course():
	m = IliasDownloaderUniMA()
	m.current_semester_pattern = rf"\((HWS|WT) 2020\)"
	m.login_soup = BeautifulSoup(no_regular_course, "lxml")
	m.addAllSemesterCourses()
	assert len(m.courses) == 0

def test_a_regular_course_hws():
	m = IliasDownloaderUniMA()
	m.current_semester_pattern = rf"\((HWS|WT) 2020\)"
	m.login_soup = BeautifulSoup(regular_course_hws, "lxml")
	m.addAllSemesterCourses()
	assert len(m.courses) == 1
	assert m.courses[0]['name'] == "GPU Programming (HWS 2020)"
	assert m.courses[0]['url'] == m.createIliasUrl(1020946)


def test_a_regular_course_wt():
	m = IliasDownloaderUniMA()
	m.current_semester_pattern = rf"\((HWS|WT) 2020\)"
	m.login_soup = BeautifulSoup(regular_course_wt, "lxml")
	m.addAllSemesterCourses()
	assert len(m.courses) == 1
	assert m.courses[0]['name'] == "OPM 561 Production Management: Lean Approaches and Variability (WT 2020)"
	assert m.courses[0]['url'] == m.createIliasUrl(1022636)


def test_a_regular_course_fss():
	m = IliasDownloaderUniMA()
	m.current_semester_pattern = rf"\((FSS|ST) 2020\)"
	m.login_soup = BeautifulSoup(regular_course_fss, "lxml")
	m.addAllSemesterCourses()
	assert len(m.courses) == 1
	assert m.courses[0]['name'] == "BE 511 Business Economics II (FSS 2020)"
	assert m.courses[0]['url'] == m.createIliasUrl(965388)


def test_a_regular_course_st():
	m = IliasDownloaderUniMA()
	m.current_semester_pattern = rf"\((FSS|ST) 2020\)"
	m.login_soup = BeautifulSoup(regular_course_st, "lxml")
	m.addAllSemesterCourses()
	assert len(m.courses) == 1
	assert m.courses[0]['name'] == "OPM 601 Supply Chain Management (ST 2020)"
	assert m.courses[0]['url'] == m.createIliasUrl(862822)

# ------------------------------------------------------------------------------

def test_own_pattern1():
	"""
	All HWS/WT/FSS/ST 2020 courses
	"""
	m = IliasDownloaderUniMA()
	m.login_soup = BeautifulSoup(no_regular_course + regular_course_hws + regular_course_wt + regular_course_fss + regular_course_st, "lxml")
	m.addAllSemesterCourses(semester_pattern=r"\(([A-Z]{2,3}) (\d{4})\)")
	assert len(m.courses) == 4

def test_own_pattern2():
	"""
	All courses on the ilias main page (even non-regular semester courses)
	"""

	m = IliasDownloaderUniMA()
	m.login_soup = BeautifulSoup(no_regular_course + regular_course_hws + regular_course_wt + regular_course_fss + regular_course_st, "lxml")
	m.addAllSemesterCourses(semester_pattern=r".*")
	assert len(m.courses) == 5


def test_own_pattern_with_excluded_id():
	"""
	All HWS/WT/FSS/ST 2020 courses, except the course with
	ref id 862822.
	"""

	m = IliasDownloaderUniMA()
	m.login_soup = BeautifulSoup(no_regular_course + regular_course_hws + regular_course_wt + regular_course_fss + regular_course_st, "lxml")
	m.addAllSemesterCourses(semester_pattern=r"\(([A-Z]{2,3}) 2020\)", exclude_ids=[862822])
	assert len(m.courses) == 4
