import logging
import os
import urlparse
logger = logging.getLogger(__name__)

def updatetree(source, dest, overwrite=False):
  parsed_url = urlparse.urlparse(dest)
  logger.debug(parsed_url)

  if parsed_url.scheme == '':
    import shutil
    if overwrite and os.path.exists(parsed_url.path):
      logger.debug("Deleting existing '%s'", parsed_url.path)
      shutil.rmtree(parsed_url.path)
      logger.debug("Local copy '%s' -> '%s'", source, parsed_url.path)
      shutil.copytree(source, parsed_url.path)
    else:
      dest = parsed_url.path
      def visit(arg, dirname, names):
        logger.debug("Visit '%s'", dirname)
        abs_dir = os.path.normpath(os.path.join(dest, os.path.relpath(dirname, source)))
        logger.debug("abs_dir '%s'", abs_dir)
        for name in names:
          src = os.path.join(dirname, name)
          dst = os.path.join(abs_dir, name)
          logger.debug("Processing '%s'", src)
          if os.path.isdir(src):
            if not os.path.isdir(dst):
              logger.debug("mkdir '%s'", dst)
              os.mkdir(dst)
          else:
            if os.path.exists(dst):
              if overwrite:
                logger.debug("overwrite '%s' -> '%s'", src, dst)
                shutil.copyfile(src,dst)
              else:
                logger.debug("will not overwrite '%s'", dst)
            else:
              logger.debug("copy '%s' -> '%s'", src, dst)
              shutil.copyfile(src,dst)

      # TODO: mkdir -p behaviour
      if not os.path.exists(dest):
        os.mkdir(dest)

      os.path.walk(source, visit, None)

  elif parsed_url.scheme == 'ssh':
    import paramiko
    import getpass

    # Work out host details
    host = parsed_url.hostname
    port = parsed_url.port if parsed_url.port else 22
    transport = paramiko.Transport((host,port))

    # Connect the transport
    username = parsed_url.username if parsed_url.username else getpass.getuser()
    logger.debug("Using username '%s'", username)
    if parsed_url.password:
      logger.debug("Using password")
      transport.connect(username = username, password = parsed_url.password)
    # TODO allow the keyfile to be configured in .hydratrc
    elif os.path.exists(os.path.expanduser('~/.ssh/id_rsa')):
      logger.debug("Using private key")
      privatekeyfile = os.path.expanduser('~/.ssh/id_rsa')
      mykey = paramiko.RSAKey.from_private_key_file(privatekeyfile)
      transport.connect(username = username, pkey = mykey)
    logger.debug("Transport Connected")
    # Start the sftp client
    sftp = paramiko.SFTPClient.from_transport(transport)

    def visit(arg, dirname, names):
      logger.debug("Visit '%s'", dirname)
      abs_dir = sftp.normalize(os.path.relpath(dirname, source))
      logger.debug("abs_dir '%s'", abs_dir)
      for name in names:
        src = os.path.join(dirname, name)
        dst = os.path.join(abs_dir, name)
        logger.debug("Processing '%s'", src)
        if os.path.isdir(src):
          try:
            sftp.stat(dst)
          except IOError:
            sftp.mkdir(dst)
        else:
          try:
            sftp.stat(dst)
            if overwrite:
              logger.debug("overwrite '%s'", dst)
              sftp.put(src, dst)
          except IOError:
            sftp.put(src, dst)

    head = str(parsed_url.path)
    tails = []
    done = False
    # Roll back the path until we find one that exists
    while not done:
      try:
        sftp.stat(head)
        done = True
      except IOError:
        head, tail = os.path.split(head)
        tails.append(tail)

    # Now create all the missing paths that don't exist
    for tail in reversed(tails):
      head = os.path.join(head, tail)
      sftp.mkdir(head)

    sftp.chdir(parsed_url.path)
    os.path.walk(source, visit, None)

  else:
    raise ValueError, "Don't know how to use scheme '%s'" % parsed_url.scheme

def main():
  import sys
  logging.basicConfig(level = logging.DEBUG)
  updatetree(sys.argv[1], sys.argv[2], overwrite=False)
