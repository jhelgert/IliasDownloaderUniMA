from IliasDownloaderUniMA import IliasDownloaderUniMA
from bs4 import BeautifulSoup
import datetime
import math
import pytest

### Tests for _parseFileProperties()
# ------------------------------------------------------------------------------

threeItems = """
<div class="ilListItemSection il_ItemProperties">
		<span class="il_ItemProperty">
		
		tar.gz&nbsp;&nbsp;</span>

		<span class="il_ItemProperty">
		
		287,3 KB&nbsp;&nbsp;</span>

		<span class="il_ItemProperty">
		
		17. Sep 2020, 14:59&nbsp;&nbsp;</span>
</div>
"""

fourItemsVerfuegbarkeit = """
<div class="ilListItemSection il_ItemProperties">
		<span class="il_ItemProperty">
		
		pdf&nbsp;&nbsp;</span>

		<span class="il_ItemProperty">
		
		500,8 KB&nbsp;&nbsp;</span>

		<span class="il_ItemProperty">
		
		17. Sep 2020, 14:59&nbsp;&nbsp;</span>

		<br>
		<span class="il_ItemProperty">
		
		Verfügbarkeit: 12. Okt 2020, 17:00 - 28. Feb 2021, 15:00&nbsp;&nbsp;</span>
</div>
"""

fourItemsMissingFileExtension = """
<div class="ilListItemSection il_ItemProperties">
		<span class="il_ItemProperty">
		
		Dateiendung fehlt&nbsp;&nbsp;</span>
	
		<span class="il_ItemProperty">
		
		&nbsp;&nbsp;</span>
		
		<span class="il_ItemProperty">
		
		739 Bytes&nbsp;&nbsp;</span>
		
		<span class="il_ItemProperty">
		
		31. Aug 2020, 12:31&nbsp;&nbsp;</span>	
</div>
"""

fourItemsVersion = """
<div class="ilListItemSection il_ItemProperties">
		<span class="il_ItemProperty">
		
		pdf&nbsp;&nbsp;</span>

		<span class="il_ItemProperty">
		
		903,1 KB&nbsp;&nbsp;</span>

		<span class="il_ItemProperty">
		
		Version: 2&nbsp;&nbsp;</span>

		<span class="il_ItemProperty">
		
		31. Aug 2020, 14:57&nbsp;&nbsp;</span>
</div>
"""

fiveItemsVersionVerfuegbarkeit = """
<div class="ilListItemSection il_ItemProperties">
		<span class="il_ItemProperty">
		
		pdf&nbsp;&nbsp;</span>

		<span class="il_ItemProperty">
		
		500,8 KB&nbsp;&nbsp;</span>

		<span class="il_ItemProperty">
		
		Version: 2&nbsp;&nbsp;</span>

		<span class="il_ItemProperty">
		
		17. Sep 2020, 14:59&nbsp;&nbsp;</span>

		<br>
		<span class="il_ItemProperty">
		
		Verfügbarkeit: 12. Okt 2020, 17:00 - 28. Feb 2021, 15:00&nbsp;&nbsp;</span>
</div>
"""

m = IliasDownloaderUniMA()

def test_parseFileProperties_threeItems():
	soup = BeautifulSoup(threeItems, "lxml")
	assert m._parseFileProperties(soup) == ('.tar.gz', 0.2873, datetime.datetime(2020, 9, 17, 14, 59))

def test_parseFileProperties_fourItemsVersion():
	soup = BeautifulSoup(fourItemsVersion, "lxml")
	assert m._parseFileProperties(soup) == ('.pdf', 0.9031, datetime.datetime(2020, 8, 31, 14, 57))

def test_parseFileProperties_fourItemsVerfuegbarkeit():
	soup = BeautifulSoup(fourItemsVerfuegbarkeit, "lxml")
	assert m._parseFileProperties(soup) == ('.pdf', 0.5008, datetime.datetime(2020, 9, 17, 14, 59))

def test_parseFileProperties_fourItemsMissingFileExtension():
	soup = BeautifulSoup(fourItemsMissingFileExtension, "lxml")
	assert m._parseFileProperties(soup) == ('', 0.000739, datetime.datetime(2020, 8, 31, 12, 31))

def test_parseFileProperties_fiveItemsVersionVerfuegbarkeit():
	soup = BeautifulSoup(fiveItemsVersionVerfuegbarkeit, "lxml")
	assert m._parseFileProperties(soup) == ('.pdf', 0.5008, datetime.datetime(2020, 9, 17, 14, 59))