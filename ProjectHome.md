Short description:
Get latest Chromium browser build. Update any time you want to. No installer. No constantly-running background updater service. Just pure Chromium. Quick, resumable downloader.

Long description:
This is a python script to get the latest auto build of chromium from build.chromium.org. Everyone knows the famous Google Chrome -- but not everyone knows the base project Chromium. Now, imagine if you could have a simple "unzip-to-install; delete-to-uninstall" browser that was the latest and greatest from the Chromium development team without having to manually find, download and extract it. Imagine having the goodness of the Chrome browser without the background updater service chewing resources on your machine. Imagine if you could easily get the builds for the more non-mainstream targets (linux, linux64, mac), without much (if any) effort. Imagine also if you could have a plain old zip file to give your friends, instead of an installer which requires internet connectivity and bandwidth to install. You can stop imagining (:

This script is dead-easy to use. The only requirement is that you have some fairly recent version of python installed (known working Python versions: ActivePython: 2.5 and 2.6; Python installer from python.org: 2.6 and 3.1; Python installed via default repositories under Ubuntu: 2.6 and 3.1).
This is a CLI app. Under Windows, if you just want the zip file, you can double-click to run -- a CMD.EXE session will launch for you. Under other operating systems, pop a console to run from the commandline.
Optionally, the script can unpack the downloaded archive to a destination directory, specified on the commandline (ie: "get-latest-chromium.py /home/bob/chrome" or "get-latest-chromium.py "C:\Program Files\Chromium").

Personally, I run this script via a scheduled task (and will be adding it to cron, once I remove the package source for Google Chrome).