# 3.1 Introduction

We have successfully created Boinc servers on Debian/Ubuntu and openSUSE machines, both physical and virtual.  The Debian builds were typically for test or temporary servers.  The openSUSE build details the necessary steps we used to get Boinc running on our publicly-facing production server.  Both sets of
installation instructions advocate installing from source; we have had mixed results with the `boinc-server-maker` package, and it makes recompiling several boinc-related tools difficult or impossible without also downloading the source.

# 3.2 Basic Server Setup
## 3.2.1 Debian
### 3.2.1.1 User Setup
For all of our builds, we’ve made a user named `boincadm`. If using an existing server, creating a new user is probably best. Either way, create your user and add that group to the `www-data` group.

```bash
  sudo adduser --system --group boincadm
  sudo usermod -aG boincadm www-data
```

### 3.2.1.2 Install necessary packages

The big things you need are all things related to:

-   C/C++, python2
-   Web server with php
-   MySQL and addons for php and python

On Debian, the complete list of packages we needed is as follows:

```bash
  sudo apt-get install git vim zip m4 libtool autoconf automake \
                       gcc pkg-config python2.7 mysql apache2 \
                       php5 php5-cli php5-gd php5-mysql \
                       libcurl4-openssl-dev openssl \
                       libapache2-mod-php5 python-mysqldb \
                       libssl-dev dh-autoreconf libmysqld-dev \
                       libmysql++-dev libmysql++3 mysql-server \
                       libmysqlclient-dev freeglut3-dev
```

We have found that for Debian/Ubuntu (unlike for openSUSE), all of the required libraries can be installed easily via `apt-get`. A couple of the libmysql packages aren't necessarily needed, but we found it easier to install all of them. Ensure that the `-dev` versions of the `openssl`, `GLU`, and `mysql` packages are installed; for `mysql`, get the `-dev` packages in addition to `mysql-server`, etc.

### 3.2.1.3 Compiling from source

Download the Boinc source from the Berkeley git repository:

```bash
  git clone git://boinc.berkeley.edu/boinc-v2.git boinc
```

In theory, you should just be able to do the following:

```bash
  cd boinc
  ./_autosetup
  ./configure --disable-client --disable-manager
  make
```

However, you may find you are missing packages during `_autosetup` and `configure`. The packages that have given us trouble are `openssl`, `mysql`, and `GLU*`. To assuage the configuration script, make sure you have the following:

```bash
    openssl libssl-dev libcurl4-openssl-dev
    mysql-server libmysql++-dev libmysqld-dev php5-mysql python-mysqldb
    freeglut3-dev (although we didn’t need graphics, so this could be incomplete)
```

Once you get through `_autosetup` and `configure –disable-client –disable-manager`, don’t forget to `make`.

## 3.2.2 openSUSE
### 3.2.2.1 Server Installation

First, download the source code via `git`, which we placed in `/usr/local/src/`:

```bash
  cd /usr/local/src/boinc
  mkdir boinc
  git clone git://boinc.berkeley.edu/boinc-v2.git boinc
```

One can get the latest source code by running `git pull` in the `/usr/local/src/boinc` directory.

To begin the server installation,

```bash
  cd boinc
  ./_autosetup
```

If this complains, you’re missing something fundamental, like a compiler. The software prerequisites are listed for [Server and Graphic apps](http://boinc.berkeley.edu/trac/wiki/SoftwarePrereqsUnix).

Only the packages required for the server and graphical applications are needed (those for the client and manager are not). Everything required is available in `yast`, after translating package names and finding the right packages containing the missing libraries. The list of packages we had to install or verify were installed are:

    git make m4 libtool autoconf automake gcc gcc-c++
    pkg-config python(2.x) python-devel* python-mysql
    mysql sqlite3 sqlite3-devel apache2 apache2-mod_php5
    php5 php5-gd php5-fastcgi* libcurl-devel freeglut-devel
    libXmu-devel libXi-devel libjpeg8-devel FastCGI-devel

`*` may not be needed.

For `_autosetup` to work, make sure you have installed the needed compilers, like `gcc`. Next, we run the configure script to get it ready for installation. This checks compiler flags, libraries, etc. We want to
do it for the server only, so run

```bash
    ./configure --disable-client --disable-manager
```

This will most likely complain about missing libraries or headers. Although most packages appear as stated on the Boinc website, some packages do not provide all of the necessary libraries. To find what was missing, we ran the above `configure` command and looked for errors in the log which mentioned what library or header file was missing. We then searched `yast` for the file name (without extension), and made sure that the scope of the search included the "Provides" list. This almost always resulted in a match with some `*-devel` package which would satisfy `configure` after installation.

Below is a list of notable libraries that were not easily installed:

-   `X11` - The libraries weren't in a package together.
-   `libXmu-devel, libXi-devel` - These were needed to make the appropriate headers existed for the `configure` script to ensure that `GLUT` was installed.
-    `php5-cli` - This is in the `php5` module.
-    `mod_ssl` - This package is currently part of the standard `apache` package.

Lastly, we found that `configure` gave one warning concerning `fastcgi`:

```bash
    checking if CFLAG '-include fcgi_stdio.h' works... no
    configure: WARNING:  fcgi-stdio.h not found.
    ------------------------------------------------------------
    Disabling FCGI.  Will not build components that require FCGI
    ------------------------------------------------------------
```

You can look for where your `fastcgi` installation is by doing

```bash
    find / -name fcgi_stdio.h -print
```

The solution to this error is to symlink the `fcgi_.h` headers (for us, located in `/usr/include/fastcgi/`) to `/usr/include/` where `configure` is looking for them. This can be done with the one-liner:

```bash
    pushd /usr/include && for H in `ls -1 fastcgi/*.h`;\
        do HFILE=`basename $H`; ln -s $H $HFILE; done && popd
```

To ensure the configuration is properly set up, run the two commands again

```bash
    ./_autosetup
    ./configure --disable-client --disable-manager
```

If there are no warnings or errors, you can move onto `make`. To ensure that the distribution has been properly purged of previous `make`-related files, first run

```bash
    make distclean
```

This is especially important if you have `git pull`ed after having run `make` previously. Now you can run

```bash
    make
```

This should hopefully compile successfully and concludes the setup of the source code.

# 3.3 Basic Project Initialization

## 3.3.1 Ubuntu project setup

This setup parallels much of what is available at the [Debian BOINC guide](https://wiki.debian.org/BOINC/ServerGuide/Initialisation). For the Debian/Ubuntu project setup, we put all of the project-specific variables in the file ` /.boinc.config`

```bash
    dbname=boinctest
    dbuser=boincadm
    dbpasswd=boincadmpw
    dbhost=localhost
    hosturl=http://a.b.c.d
    projectname=boinctest
    projectnicename="BoincTestProject@Home"
    installroot=/home/boincadm/projects
```

and sourced them

```bash
  source .boinc.config
```

Then create the `$installroot` dir and change it’s ownership.

```bash
  sudo mkdir -p \$installroot \&\& sudo chown boincadm:www-data \$installroot
```

To setup the mysql database, we just paste this line into the terminal.

```bash
    cat <<EOMYSQL | mysql -u root -p;
    DROP DATABASE IF EXISTS \$dbname;
    CREATE USER '\$dbuser'@'localhost' IDENTIFIED BY '\$dbpasswd';
    GRANT ALL PRIVILEGES ON \$dbname.* TO '\$dbuser'@'localhost';
    EOMYSQL
    fi
```

If you didn’t set up a root password for your build (which you need to open mysql as root), you can do

```bash
    sudo mysqladmin password
```

to set one.

If you are using the `boinc-server-maker` package, this part is tough because the package is broken in some ways as of September 2014. Read more below or skip if building from source.

#### 3.3.1.1 Using boinc-server-maker package

I had a hard time getting this to work; the hardest part was getting `make_project` to find `boinc_config_path.py`. I tried symlinking, creating a `__init__.py` file. Try the following:

```bash
    sudo ln -s /usr/share/python-support/boinc-server/Boinc/\
    boinc_path_config.py /usr/share/pyshared/Boinc/boinc_path_config.py

    PYTHONPATH=$PYTHONPATH:/usr/share/pyshared/Boinc/ \
    /usr/share/boinc-server/tools/make\_project \
    --url_base "$hosturl" \
    --db_name "$dbname" \
    --db_user "$dbuser" \
    --db_passwd "$dbpasswd" \
    --drop_db_first  \
    --project_root "$installroot"/"$projectname" \
    --srcdir /usr/share/boinc-server/ \
    "$projectname" "$projectnicename"
```

If that doesn’t work, try adding

```bash
    PYTHONPATH=$PYTHONPATH:/usr/share/python-support/boinc-server/Boinc/
```

and retrying the above `make_project` command.

#### 3.3.1.2 Installing from source

If installing from source, from the `/home/boincadm/`

```bash
    sudo ./boinc/tools/make_project \
      --url_base "$hosturl" \
      --db_name "$dbname" \
      --db_user "$dbuser" \
      --db_passwd "$dbpasswd" \
      --drop_db_first \
      --db_host "$dbhost" \
      --project_root "$installroot"/"$projectname" \
      --srcdir "/home/boincadm/boinc" \
      "$projectname" "$projectnicename"
```

Your project should now be ready to go. Proceed to app development.

### 3.3.2 openSUSE Project Setup

To begin the project initialization, we first made the user `boincadm` and the group `boinc`. The `boinc` group has the members `boincadm` and `wwwrun` (the user that runs `apache` on openSUSE). We set the
`umask 0002` globally for all users in `/etc/bash.bashrc.local`, but it may be better to do this for only the two users `boincadm` and `wwwrun` instead. `umask 0007` may be better in this case to prevent world
readability.

The `make_project` script has its own annoyances, specifically that it insists on creating the database for the project; this requires the database user for the project, `boincadm`, to have blanket `CREATE`
privileges (and blanket `DROP` privileges are recommended). These should be dropped immediately after the project is created. We have written the dev mailinglist asking for `make_project` to accept an existing
database, which may simplify things for database/server administrators.

We ran the following `mysql` commands:

```bash
    mysql -u root -p
    >CREATE USER 'boincadm'@'localhost' IDENTIFIED BY 'the_password';
    >GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,DROP,REFERENCES,INDEX,
     ALTER,CREATE TEMPORARY TABLES,LOCK TABLES ON `boinc_project`.*
     TO 'boincadm'@'localhost';
    >GRANT CREATE,DROP ON *.* TO 'boincadm'@'localhost';
    >quit;
```

where `the_password` and `boinc_project` were specified for our specific project.

Then we ran `make_project` with the required database options specified in the command (as user `boincadm` to ensure all files/directories had proper permissions):

```bash
    su boincadm
    ./make_project
      --url_base "hosturl" \
      --db_name "dbname" \
      --db_user "dbuser" \
      --db_passwd "dbpasswd" \
      --drop_db_first  \
      --project_root "installroot"/"projectname" \
      --srcdir /usr/local/src/boinc/ \
       "projectname" "projectnicename"
    mysql -u root -p
    >REVOKE CREATE,DROP ON *.* FROM 'boincadm'@'localhost';
    >quit;
```

Notice that the `make_project` script was run as the `boincadm` user. This was to ensure the proper ownership on everything created by `make_work`. The permissions on these files and directories were very
liberal (likely due to the `umask 0002`). The only thing we did was remove world read/execute from the project folder. Notably, we did not move the `keys` subdirectory off-site, though if we open the project up to the public, we likely will.

Lastly, openSUSE 13.1 ships with `apache 2.4`, which uses a new `mod_authz_host` module. However, the version on our server comes with the `access_compat` module compiled in. Basically, the old "Order
allow,deny" and "Allow from all" style directives are deprecated in `apache 2.4`, but supported by the built-in but no-way-to-disable `access_compat` module. So, older configurations continue to work. But,
the recommendation of changing those lines to "Require all granted" fails because there were earlier definitions for a blanket "Deny from all" applied to the root of the filesystem. The documentation for the interaction of `access_compat` and `mod_authz_host` is scarce. As a result, we left the two lines allowing access, and added the "Require all granted" line as suggested. The latter is not necessary, but is there as a reminder that the new syntax is supported.

A caveat to the configuration using `.htpasswd` is that one can not use php as cgi with `suexec` because http authentication is not supported with that setup. That would have allowed the web php and cgi to run as `boincadm` directly, removing any need to change any `umask`, and removing the need for `wwwrun` to be in any group.

This requires `apache` to run php itself with `mod_php5`. We did not change the `php.ini` file for this project.

### 3.3.3 Finishing Touches

Move to the install directory:

```bash
    cd "$installroot"/"$projectname"
```

#### 3.3.3.1 Directory Permissions

Then you may need to do the following (I found I didn’t need sudo since boincadm was the owner...)

```bash
    sudo chown boincadm:boincadm  -R .
    sudo chmod g+w -R .
    sudo chmod 02770 -R upload html/cache html/inc html/languages \
      html/languages/compiled html/user_profile
    hostname=`hostname`
    sudo chgrp -R www-data log_"$hostname" upload

    sudo chmod o+x html/inc && sudo chmod -R o+r html/inc
    sudo chmod o+x html/languages/ html/languages/compiled
```

#### 3.3.3.2 Set up a cron job

Set a cronjob to start the boinc server daemons (substitute Vim for your favorite editor)

```bash
    sudo EDITOR=vim crontab -e
    */5 * * * * \$INSTALLROOT/PROJECTNAME/bin/start --cron
```

#### 3.3.3.3 Web Admin site

Make the `PROJECTNAME_ops` site password protected with whatever username/password you like

```bash
    sudo htpasswd -c html/ops/.htpasswd USERNAME
```

On some systems, you may have to use `htpasswd2` which I think requires the full path to the `.htpasswd` file:

```bash
    sudo htpasswd2 -c ~/projects/PROJECTNAME/html/ops/.htpasswd USERNAME
```

#### 3.3.3.4 Configure Apache

Config apache2 to host the site and make sure the appropriate mods are installed

```bash
    sudo cp ${projectname}.httpd.conf  /etc/apache2/sites-available/
    sudo a2ensite ${projectname}.httpd.conf
    sudo service apache2 reload
    sudo a2enmod cgi
    sudo a2enmod php5
    sudo service apache2 restart
```

#### 3.3.3.5 Fix bugs

Lastly, in your config.xml file, under `<config>`, add the following to fix a bug in the status website

```xml
    <uldl_pid>/var/run/apache2.pid</uldl_pid>
```

On openSUSE, the pid is

```xml
    <uldl_pid>/var/run/httpd.pid</uldl_pid>
```

#### 3.3.3.6 Install Virtualenv (optional)

If you need to install virtualenv and do not have or want to use sudo, follow these instructions.

```bash
    curl -O https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.11.tar.gz
    tar -xzf virtualenv-1.11.tar.gz
    cd virtualenv-1.11
    python virtualenv.py venv
```

Edit your `.bashrc` file to include something like

```bash
    source ~/virtualenv-1.11/venv/bin/activate
```

### 3.3.4 VirtualBox considerations

If running in a virtualbox, make sure you port-forward port 80 to the guest port 80. The easiest way to do this is to run virtualbox as root. Apparently there are some other ways to route host:80 to host:8080 to guest:80 using iptables but I could'’t get it to work. Alternatively, you could just port-forward port 8080 and access your site at <http://hosturl:8080/PROJECTNAME>.

To do forward ports in virtualbox, select the virtual server and open up `Settings` `-->` `Network` `-->` `Advanced (under NAT)` `-->` `Port Forward`. 

Additionally, we found that virtualized servers became unstable when running for long periods of time with frequent communication to clients when using the NAT network settings. The solution was to obtain a
separate IP address for the virtual server and using bridged networking. 
