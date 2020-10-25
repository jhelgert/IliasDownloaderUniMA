from IliasDownloaderUniMA import IliasDownloaderUniMA
from bs4 import BeautifulSoup
import datetime
import math

# Test for parseVideos()
# ------------------------------------------------------------------------------
v_with_caption = """
<html>
 <body>
  <figure class="ilc_media_cont_MediaContainer" style="display:table; margin-left: 0px;" xmlns:xhtml="http://www.w3.org/1999/xhtml">
   <div class="ilc_Mob" style="width:400px;">
    <div class="mejs-container svg ilPageVideo mejs-video" id="mep_0" style="width: 400px; height: 300px;">
     <div class="mejs-inner">
      <div class="mejs-mediaelement">
       <video class="ilPageVideo" height="300" oncontextmenu="return false;" preload="none" src="./data/ILIAS/mobs/mm_1318784/Session_02_DesignofFlowLinesPart1.mp4?il_wac_token=88ff75878db690a37e5fddfddcf055beea79693a&amp;il_wac_ttl=3&amp;il_wac_ts=1603624381" width="400">
        <source src="./data/ILIAS/mobs/mm_1318784/Session_02_DesignofFlowLinesPart1.mp4?il_wac_token=88ff75878db690a37e5fddfddcf055beea79693a&amp;il_wac_ttl=3&amp;il_wac_ts=1603624381" type="video/mp4">
         <object data="libs/bower/bower_components/mediaelement/build/flashmediaelement.swf" height="300" type="application/x-shockwave-flash" width="400">
          <param name="movie" value="libs/bower/bower_components/mediaelement/build/flashmediaelement.swf"/>
          <param name="flashvars" value="controls=true&amp;file=./data/ILIAS/mobs/mm_1318784/Session_02_DesignofFlowLinesPart1.mp4?il_wac_token=88ff75878db690a37e5fddfddcf055beea79693a&amp;il_wac_ttl=3&amp;il_wac_ts=1603624381"/>
         </object>
        </source>
       </video>
      </div>
      </div>
      </div>
      </div>
   <figcaption style="display: table-caption; caption-side: bottom;">
    <div class="ilc_media_caption_MediaCaption">
     Recording Session 02 Line Balancing
    </div>
   </figcaption>
  </figure>
 </body>
</html>
"""

v_without_caption = """
<html>
 <body>
  <figure class="ilc_media_cont_MediaContainer" style="display:table; margin-left: 0px;" xmlns:xhtml="http://www.w3.org/1999/xhtml">
   <div class="ilc_Mob">
    <div class="mejs-container svg ilPageVideo mejs-video" id="mep_0" style="width: 480px; height: 270px;">
     <div class="mejs-inner">
      <div class="mejs-mediaelement">
       <video class="ilPageVideo" oncontextmenu="return false;" preload="none" src="./data/ILIAS/mobs/mm_1299655/HS20_EinfPoWi_Politische_Kultur_und_Sozialisation_A_komprimiert.m4v?il_wac_token=60e9a0575393b725438513fc1d2aadfba054221a&amp;il_wac_ttl=3&amp;il_wac_ts=1603624667">
        <source src="./data/ILIAS/mobs/mm_1299655/HS20_EinfPoWi_Politische_Kultur_und_Sozialisation_A_komprimiert.m4v?il_wac_token=60e9a0575393b725438513fc1d2aadfba054221a&amp;il_wac_ttl=3&amp;il_wac_ts=1603624667" type="video/mp4">
         <object data="libs/bower/bower_components/mediaelement/build/flashmediaelement.swf" type="application/x-shockwave-flash">
          <param name="movie" value="libs/bower/bower_components/mediaelement/build/flashmediaelement.swf"/>
          <param name="flashvars" value="controls=true&amp;file=./data/ILIAS/mobs/mm_1299655/HS20_EinfPoWi_Politische_Kultur_und_Sozialisation_A_komprimiert.m4v?il_wac_token=60e9a0575393b725438513fc1d2aadfba054221a&amp;il_wac_ttl=3&amp;il_wac_ts=1603624667"/>
         </object>
        </source>
       </video>
      </div>
     </div>
    </div>
   </div>
  </figure>
 </body>
</html>
"""

v_no_video = """
<html>
 <body>
  <figure class="ilc_media_cont_MediaContainer" style="display:table; margin-left: 0px;" xmlns:xhtml="http://www.w3.org/1999/xhtml">
   <div class="ilc_Mob">
    <img border="0" src="./data/ILIAS/mobs/mm_1171726/Quiz_03_Game.png?il_wac_token=4cac4b488b6d370df459c74070c97f07408afd8b&amp;il_wac_ttl=3&amp;il_wac_ts=1603624808" style="width:100%"/>
   </div>
  </figure>
 </body>
</html>
"""

m = IliasDownloaderUniMA()

# We ignore the video size for the test as it's not possible to test
# the HEAD requests without being logged into ilias.

def test_parseVideos_no_video():
  soup = BeautifulSoup(v_no_video, "lxml")
  assert m.parseVideos(soup) == None

def test_parseVideos_without_caption():
  soup = BeautifulSoup(v_without_caption, "lxml")
  v_name, v_size, v_mod_date, v_url = m.parseVideos(soup)
  assert v_name == 'HS20_EinfPoWi_Politische_Kultur_und_Sozialisation_A_komprimiert.m4v'
  assert v_mod_date == datetime.datetime.fromisoformat('2000-01-01')
  assert v_url == 'https://ilias.uni-mannheim.de/data/ILIAS/mobs/mm_1299655/HS20_EinfPoWi_Politische_Kultur_und_Sozialisation_A_komprimiert.m4v?il_wac_token=60e9a0575393b725438513fc1d2aadfba054221a&il_wac_ttl=3&il_wac_ts=1603624667'

def test_parseVideos_with_caption():
  soup = BeautifulSoup(v_with_caption, "lxml")
  v_name, v_size, v_mod_date, v_url = m.parseVideos(soup)
  assert v_name == 'Session_02_DesignofFlowLinesPart1.mp4'
  assert v_mod_date == datetime.datetime.fromisoformat('2000-01-01')
  assert v_url == "https://ilias.uni-mannheim.de/data/ILIAS/mobs/mm_1318784/Session_02_DesignofFlowLinesPart1.mp4?il_wac_token=88ff75878db690a37e5fddfddcf055beea79693a&il_wac_ttl=3&il_wac_ts=1603624381"