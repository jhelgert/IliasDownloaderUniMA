
# Ilias Downloader UniMA

A simple python package to download files from https://ilias.uni-mannheim.de.

## Key features

- Automatically synchronizes all files for each download. Only new or updated files will be downloaded.
- Uses the [multiprocessing](https://docs.python.org/3/library/multiprocessing.html) package to accelerate the download.

## Install

Easy way via pip:

```bash
pip3 install iliasDownloaderUniMA
```

Otherwise you can clone or download this repo and then run

``` bash
python3 setup.py install 
```

inside the repo directory.

## Usage

Besides the uni-id and the password, only the ref id is required to download
the files for a course. In general, a simple download script looks like this:

```python
from IliasDownloaderUniMA import IliasDownloaderUniMA

m = IliasDownloaderUniMA()
m.setParam('download_path', '/path/where/you/want/your/files/')
m.login('your_uni_id', 'your_password')
m.addCourse(ilias_course1_ref_id)
m.addCourse(ilias_course2_ref_id)
m.downloadAllFiles()
```

A more specific example:

```python
from IliasDownloaderUniMA import IliasDownloaderUniMA

m = IliasDownloaderUniMA()
m.setParam('download_path', '/Users/jonathan/Desktop/')
m.login('jhelgert', 'my_password')
m.addCourse(954265)   # OPM 601 Supply Chain Management
m.addCourse(965389)   # BE 511 Business Economics II
m.downloadAllFiles()
```

Note that the backslash `\` is a special character inside a python string.
So on a windows machine it's necessary to use a raw string for the `download_path`:

```python
m.setParam('download_path', r'C:\Users\jonathan\Desktop\')
```



### Where to get the ilias_course_ref_id?

![](https://i.imgur.com/1MKl9un.png)

### Parameters

The Parameters can be set by the `.setParam(param, value)` method, where
`param` is one of the following parameters:

- `num_scan_threads` number of threads used for scanning for files
inside the folders (default: 5).
- `num_download_threads` number of threads used for download all files (default: 5).
- `download_path` the path all the files will be downloaded to (default: the current working directory).


```python
from IliasDownloaderUniMA import IliasDownloaderUniMA

m = IliasDownloaderUniMA()
m.setParam('download_path', '/Users/jonathan/Desktop/')
m.setParam('num_scan_threads', 20)
m.setParam('num_download_threads', 20)
m.login('jhelgert', 'my_password')
m.addCourse(954265)   # OPM 601 Supply Chain Management
m.addCourse(965389)   # BE 511 Business Economics II
m.downloadAllFiles()
```


## Contribute

Feel free to contribute! :)
