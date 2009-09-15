#!/usr/bin/python
# vim: expandtab
import time
import urllib
import urllib2
import sys
import os
import datetime
import zipfile
import shutil
import platform

start = datetime.datetime.now()
chunk = 8196
timeout = 180
blank = ""
if os.name == "posix":
	if platform.machine().find("64") > -1:
		BASE = "http://build.chromium.org/buildbot/snapshots/chromium-rel-linux-64/"
	else:
		BASE = "http://build.chromium.org/buildbot/snapshots/chromium-rel-linux/"
elif os.name == "mac":
	BASE = "http://build.chromium.org/buildbot/snapshots/chromium-rel-mac/"
else:
	BASE = "http://build.chromium.org/buildbot/snapshots/chromium-rel-xp/"

for i in range(75):
  blank += " "

def msg(s):
  sys.stdout.write(s)
  sys.stdout.flush()

def get_dl_secs():
  global start
  td = datetime.datetime.now() - start
  return td.seconds

def get_Kps(transferred, size):
  secs = get_dl_secs()
  transferredK = (float(transferred) / 1024.0)
  if (secs > 0):
    transferredKS = (float(transferredK) / float(secs))
    if (size > 0):
      eta_secs = (float(size - transferred) / 1024.0) / transferredKS
      eta_min = eta_secs / 60
      eta_secs = eta_secs % 60
      ETA = "%02i:%02i" % (eta_min, eta_secs)
      return "%.2f KB/s  ETA: %s" % (transferredKS, ETA)
    else:
      return "%.2f KB/s" % transferredKS
  else:
    return ""

def clearline():
  global blank
  sys.stdout.write("\r" + blank + "\r")

def status1(val):
  secs = get_dl_secs()
  clearline()
  msg("Downloaded: " + str(val / 1024) + " K (" + get_Kps(val, 0) + ")")

def status2(read, size):
  global start
  clearline()
  perc = "%.2f" % ((float(read) * 100.0) / float(size))
  msg("Downloaded: " + str(read / 1024) + " / " + str(size / 1024) + " K   [" + str(perc)\
      + "%] (" + get_Kps(read, size) + ")")

def unpack(src, dst):
  if (dst == ""):
    return
  if not os.path.isdir(dst):
    try:
      os.mkdir(dst)
    except Exception, e:
      print("Can't extract to '" + dst + "': " + str(e))
      return
  msg("Extracting to " + dst)
  try:
    z = zipfile.ZipFile(src)
    for f in z.namelist():
      z.extract(f, sys.argv[1])
    z.close()
    print("  (ok)")
  except Exception, e:
    sys.stdout.write(" (fail)\n")
    print("(" + str(e) + ")")

def usage():
  print("Usage: " + os.path.basename(sys.argv[0]) + " {<extract dir>} ")
  print("   <extract dir>  is a dir to optionally extract downloaded archive to")

def get_ver():
  LATEST = BASE + "LATEST"
  fail = 0
  for i in range(5):
    try:
      ver = urllib.urlopen(LATEST, "rb").read().strip()
      return ver
    except Exception, e:
      time.sleep(1)

  print("\nUnable to get LATEST version: " + str(e))
  return ""

def update_chrome(known_version = ""):
  if ((sys.argv[1:].count("-h") > 0) or (sys.argv[1:].count("-h") > 0)):
    usage()
    sys.exit(0)
  extract_out = ""
  lastarg = ""
  for arg in sys.argv[1:]:
		if os.path.isdir(arg):
			extract_out = arg
		elif os.path.isdir(os.path.dirname(arg)) and not os.path.isfile(arg):
			try:
				os.mkdir(arg)
			except Exception, e:
				print("Can't make output dir '" + arg + "': " + str(e));
				sys.exit(1)
			extract_out = arg

  ver = known_version
  if (ver == ""):
    msg("Determining latest version...")
    ver = get_ver()
    if (len(ver) == 0):
      sys.exit(1)
    print("  (ok)")

  LAST = os.path.join(os.path.expanduser("~"), ".CHROME-LATEST-VERSION")
  if os.name == "posix":
    OUT = "chrome-linux.zip"
  elif os.name == "mac":
    OUT = "chrome-mac.zip"
  else:
    OUT = "chrome-win32.zip"
  if (os.path.isfile(LAST)):
    last_dl = open(LAST, "rb").read().strip()
    if (last_dl == ver):
      print(" -> Already have latest version (" + ver + ")")
      unpack(OUT, extract_out)
      sys.exit(0)

  INSTALLER = BASE + ver + "/" + OUT

  print("Download starts... (version: " + ver + ")")
  print("[ url: " + INSTALLER + " ]")
  try:
    start = datetime.datetime.now()
    fp = urllib2.urlopen(INSTALLER, "rb")
    h = fp.headers.headers;
    stLen = 0
    for h in fp.headers.headers:
      parts = h.strip().split(":")
      if (parts[0].lower() == "content-length"):
        stLen = int(parts[1].strip())
    stRead = 0
    new = ""
    oldlen = -1
    if (stLen == 0):
      # can't determine length; just carry on
      while (oldlen != len(new)):
        oldlen = len(new)
        new += fp.read(chunk)
        status1(len(new))
    else:
      fail = 0
      while (stRead < stLen):
        part = fp.read(chunk)
        stRead += len(part)
        new += part
        if (len(part) == 0):
          fail += 1
        else:
          fail = 0
        if (fail > timeout):
          newver = get_ver()
          if (newver != ver):
            print("\nVersion changed upstreeam! Trying again...")
            update_chrome()
          else:
            print("timed out ):")
            print("URL was: " + INSTALLER)
            sys.exit(1)
        elif (fail > 0):
          time.sleep(1)
        status2(stRead, stLen)

  except Exception, e:
    print("Unable to download latest zip (" + INSTALLER + "): " + str(e))
    sys.exit(1)

  print("\nWriting to file...")
  try:
    fp = open(OUT, "wb")
    fp.write(new)
    fp.close()
  except Exception, e:
    print("Unable to save new archive: " + str(e))
    sys.exit(1)

  print("Chrome archive updated successfully!")
  try:
    fp = open(LAST, "wb")
    fp.write(ver)
    fp.close()
  except Exception, e:
    print("WARNING: Unable to save download version to '" + LAST + "': " + str(e))

  unpack(OUT, extract_out)

if __name__ == "__main__":
  update_chrome()
