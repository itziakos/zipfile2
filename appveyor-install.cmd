"%sdkverpath%" -q -version:"%sdkver%"
call setenv /x64

rem install python packages
pip install --cache-dir c:/egg_cache haas
pip install --cache-dir c:/egg_cache coverage
pip install --cache-dir c:/egg_cache mock
pip install --cache-dir c:/egg_cache tox

rem install zipfile2
python setup.py develop
