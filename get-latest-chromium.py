#!/usr/bin/python
# determine major version of the python engine:
#   this script was originall written for py 2.6
#   but adapted for 3.1; I'd like both to work
import sys
pyver = int(sys.version.split(" ")[0].split(".")[0])
import time
import urllib
if pyver == 3:
  import urllib.request
else:
  import urllib2
import os
import datetime
import zipfile
import shutil
import traceback

start = datetime.datetime.now()
last_transferredK = 0
min_chunk = 1024
max_chunk = 65536
chunk = min_chunk
timeout = 180
blank = ""
BASE = "http://build.chromium.org/buildbot/snapshots/chromium-rel-xp/"

if pyver == 3:
  class ResumableDownloader(urllib.request.FancyURLopener):
    def http_error_206(self, url, fp, errcode, errmsg, headers, data=None):
      pass
else:
  class ResumableDownloader(urllib.FancyURLopener):
    def http_error_206(self, url, fp, errcode, errmsg, headers, data=None):
      pass

for i in range(75):
  blank += " "

def msg(s):
  sys.stdout.write(s)
  sys.stdout.flush()

def get_dl_secs():
  global start
  td = datetime.datetime.now() - start
  return td.seconds + (td.microseconds / 1000000.0)

def get_Kps(transferred, size):
  global last_transferredK, start
  secs = get_dl_secs()
  transferredK = (float(transferred) / 1024.0) - last_transferredK
  if last_transferredK != 0:
    start = datetime.datetime.now()
  last_transferredK += transferredK

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
  #msg("Downloaded: " + str(val / 1024) + " K (" + get_Kps(val, 0) + ")")
  msg("Downloaded: %i K (%s)" % ((val / 1024), get_Kps(val, 0)))

def status2(read, size):
  global start
  clearline()
  perc = "%.2f" % ((float(read) * 100.0) / float(size))
#  msg("Downloaded: " + str(read / 1024) + " / " + str(size / 1024) + " K   [" + str(perc)\
#      + "%] (" + get_Kps(read, size) + ")")
  msg("Downloaded: %i / %i K [%s %%] (%s)" % (read/1024, size/1024, perc, get_Kps(read, size)))

def unpack(src, dst, theme):
  if (dst == ""):
    return
  if not os.path.isdir(dst):
    try:
      os.mkdir(dst)
    except Exception as e:
      print("Can't extract to '" + dst + "': " + str(e))
      return
  msg("Extracting to " + dst)
  try:
    z = zipfile.ZipFile(src)
    for f in z.namelist():
      z.extract(f, sys.argv[1])
    z.close()
    print("  (ok)")
  except Exception as e:
    sys.stdout.write(" (fail)\n")
    print("(" + str(e) + ")")
  if (len(theme) > 0):
    msg("Setting theme to '" + theme + "'")
    theme_dll = os.path.join(dst, "chrome-win32", "themes", theme)
    theme_dll += ".dll"
    if not os.path.isfile(theme_dll):
      print("Can't find '" + theme_dll + "'; install your theme here first and re-run")
      return
    old_dll = os.path.join(dst, "chrome-win32", "themes", "default.dll")
    try:
      dst = old_dll + ".bak"
      if os.path.isfile(dst):
        os.remove(dst)
      shutil.copyfile(old_dll, dst)
      shutil.copyfile(theme_dll, old_dll)
      print("  (ok)")
    except Exception as e:
      print("Unable to set theme: " + str(e))

def usage():
  print("Usage: " + os.path.basename(sys.argv[0]) + " {<extract dir>} {-t <theme name>}")
  print("   <extract dir>  is a dir to optionally extract downloaded archive to")
  print("   <theme name>   is the name of a theme dll already in the themes dir of")
  print("                    your extracted chromium (so, first-time around, this will")
  print("                    b0rk and you will be told where to put  your theme dll.")
  print("                    Just re-run with the same arguments to apply the theme.")
  print("WARNING: themes seem to quickly become incompatible with the latest chromium")
  print("  builds. If you see a lot of red, just re-run without your -t argument to")
  print("  revert to the default chromium theme")

def get_ver():
  LATEST = BASE + "LATEST"
  fail = 0
  for i in range(5):
    try:
      #ver = urllib2.urlopen(LATEST, "rb").read().strip()
      ver = urllib.request.urlopen(LATEST).read().decode().strip()
      return ver
    except Exception as e:
      time.sleep(1)

  print("\nUnable to get LATEST version: " + str(e))
  return ""

def update_chrome(known_version = ""):
  global chunk,min_chunk,max_chunk,pyver
  if ((sys.argv[1:].count("-h") > 0) or (sys.argv[1:].count("-h") > 0)):
    usage()
    sys.exit(0)
  extract_out = ""
  theme = ""
  lastarg = ""
  for arg in sys.argv[1:]:
    if arg == "-t":
      lastarg = arg
    else:
      if (lastarg == "-t"):
        theme = arg
      elif os.path.isdir(arg):
        extract_out = arg
      elif os.path.isdir(os.path.dirname(arg)):
        try:
          os.mkdir(arg)
          extract_out = arg
        except:
          print("Can't find or create dir %s; aborting" % arg)
          sys.exit(1)

  ver = known_version
  if (ver == ""):
    msg("Determining latest version...")
    ver = get_ver()
    if (len(ver) == 0):
      sys.exit(1)
    print("  (ok)")

  LAST = os.path.join(os.path.expanduser("~"), ".CHROME-LATEST-VERSION")
  OUT = "chrome-win32.zip"
  if (os.path.isfile(LAST)):
    last_dl = open(LAST, "r").read().strip()
    if (last_dl == ver):
      print(" -> Already have latest version (" + ver + ")")
      tmp = os.path.join(os.path.expanduser("~"), OUT)
      if os.path.isfile(tmp):
        unpack(OUT, extract_out, theme)
      sys.exit(0)

  INSTALLER = BASE + ver + "/" + OUT

  print("Download starts... (version: " + ver + ")")
  print("(url: " + INSTALLER + ")")
  offset = 0

  attempts = 0
  while True:
    if attempts > 0:
      print("Resuming from %i bytes..." %(offset))
    attempts += 1
    try:
      start = datetime.datetime.now()
      if pyver == 2:
        fp = urllib2.urlopen(INSTALLER)
        headers = fp.headers.headers;
      else:
        fp = urllib.request.urlopen(INSTALLER)
        headers = fp.getheaders()
      stLen = 0
      resuming = False
      for h in headers:
        if pyver == 2:
          parts = h.strip().split(":")
        else:
          parts = h
        if (parts[0].lower() == "content-length"):
          resuming = True
          stLen = int(parts[1].strip())
          if offset > 0:
            fp.close()
            r = ResumableDownloader()
            r.addheader("Range", "bytes=" + str(offset) + "-")
            fp = r.open(INSTALLER)
            for h in fp.headers.headers:
              parts = h.strip().split(":")
              if (parts[0].lower() == "content-length"):
                stLen = int(parts[1].strip())
      if offset > 0 and not resuming:
        offset = 0
      stRead = 0
      new = ""
      oldlen = -1
      if offset == 0:
        fpout = open(os.path.join(os.path.expanduser("~"), OUT) + ".part", "wb")
      else:
        fpout = open(os.path.join(os.path.expanduser("~"), OUT) + ".part", "ab")
      if (stLen == 0):
        read_bytes = 0;
        fail = 0
        # can't determine length; just carry on
        while (oldlen != read_bytes) and (fail < 5):
          oldlen = read_bytes
          part = fp.read(chunk)
          if len(part) == 0:
            fail == 1
            time.sleep(50)
            continue
          read_bytes += len(part)
          fpout.write(part)
          status1(len(new))
        break
      else:
        fail = 0
        while (stRead < stLen):
          part = fp.read(chunk)
          stRead += len(part)
          if len(part) < chunk:
            chunk -= min_chunk
            if chunk <= 0:
              chunk = min_chunk
          else:
            if chunk < max_chunk:
              chunk += min_chunk
          fpout.write(part)
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
              fpout.close()
              fp.close()
              offset = os.stat(OUT + ".part").st_size
              break
          elif (fail > 0):
            time.sleep(1)
          status2(stRead, stLen)
        if (stRead >= stLen):
          break

    except Exception as e:
      print("Unable to download latest zip (" + INSTALLER + "): " + str(e))
      traceback.print_exc()
      sys.exit(1)

  #print("\nWriting to file...")
  #try:
  #  fp = open(OUT, "wb")
  #  fp.write(new)
  #  fp.close()
  #except Exception as e:
  #  print("Unable to save new archive: " + str(e))
  #  sys.exit(1)
  fpout.close()
  if os.path.isfile(OUT):
    os.remove(OUT)
  os.rename(OUT + ".part", OUT)
  print("Chrome archive updated successfully!")
  try:
    fp = open(LAST, "w")
    fp.write(ver)
    fp.close()
  except Exception as e:
    print("WARNING: Unable to save download version to '" + LAST + "': " + str(e))

  unpack(OUT, extract_out, theme)

if __name__ == "__main__":
  #update_chrome()
  #sys.exit(0)
  try:
    update_chrome()
  except KeyboardInterrupt:
    print("aborted.")
