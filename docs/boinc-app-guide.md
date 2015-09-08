# 4.1 App Deployment

## 4.1.1 More Project Setup

Inside your project directory, which from here on out we will call `$PROJECTHOME`, do the following.

### 4.1.1.1 Application Setup

Under the apps directory, create a directory structure for you application of the form

```bash
    appname
        version_number
            architecture
                file_1
                file_2
                ...
```

For example:

```bash
    impact
        1.0
            i686-pc-linux-gnu
                impact_1.0_i686-pc-linux-gnu
                version.xml
            x86_64-pc-linux-gnu
                impact_1.0_x86_64-pc-linux-gnu
                version.xml
```

A list of compatible architectures can be found [here](http://boinc.berkeley.edu/trac/wiki/BoincPlatforms).

For our application, we used the Boinc wrapper instead of rewriting our application to use the Boinc API. You can find the wrapper executables for different architectures on the [BOINC website here](http://boinc.berkeley.edu/trac/wiki/WrapperApp). Download the appropriate wrapper and place it in the appropriate leaf directory for that architecture. For the wrapper to work with your application, you need to supply it with a `job.xml` file. We have named our job files in the following way:

```bash
    appname_job_version.xml
```

Inside the `job.xml` file, you need to add a job description. The following works for us (though the filenames are specific to our app; rename however you require).

```xml
  <job_desc>
      <task>
          <application>appname</application>
          <stdout_filename>md.log</stdout_filename>
          <stderr_filename>md.err</stderr_filename>
          <checkpoint_filename>md.rst</checkpoint_filename>
          <append_cmdline_args/>
      </task>
  </job_desc>
```

Note that the `job.xml` file does not have an architecture specific information in it's filename or contents. This makes it pretty easy to copy from one architecture subdirectory to another.

Inside the version.xml file of each architecture subdirectory, add something like

```xml
  <version>
     <file>
        <physical_name>wrapper_26006x_windowsx_x86x_64.exe</physicalx_name>
        <main_program/>
     </file>
     <file>
        <physical_name>appname_version_architecture.exe</physical_name>
        <logical_name>appname</logical_name>
     </file>
     <file>
        <physical_name>appname_job_version.xml</physical_name>
        <logical_name>job.xml</logical_name>
     </file>
  </version>
```

Rinse and repeat for each architecture subdirectory, for each version, for each app. The resulting directory structure should look like this example:

```bash
  apps/impact/1.20
  |-- windows_intelx86
  |   |-- impact_1.20_windows_intelx86.exe
  |   |-- impact_job_1.20_windows_intelx86.xml
  |   |-- version.xml
  |   `-- wrapper_26011_windows_intelx86.exe
  |-- windows_x86_64
  |   |-- impact_1.20_windows_x86_64.exe
  |   |-- impact_job_1.20_windows_x86_64.xml
  |   |-- version.xml
  |   `-- wrapper_26011_windows_x86_64.exe
  `-- x86_64-pc-linux-gnu
      |-- impact_1.20_x86_64-pc-linux-gnu
      |-- impact_job_1.20_x86_64-pc-linux-gnu.xml
      |-- version.xml
      `-- wrapper_26011_x86_64-pc-linux-gnu
```

Lastly, in the project root directory, edit the project.xml file to add your app information to it. You may also want to remove all the architectures listed that you do not plan to support.

```xml
  <boinc>
   <app>
    <name>appname</name>
    <user_friendly_name>App@Home</user_friendly_name>
   </app>
   <platform>
    <name>i686-pc-linux-gnu</name>
    <user_friendly_name>Linux/x86 32bit</user_friendly_name>
   </platform>
   <platform>
    <name>x86_64-pc-linux-gnu</name>
    <user_friendly_name>Linux/amd64 64bit</user_friendly_name>
   </platform>
  </boinc>
```

Inform you database of the new application and its supported platforms
using the `bin/xadd` script.

```bash
    \$PROJECTHOME/bin/xadd
```

You can verify that everything needed has been added by running the `bin/xadd` script again, which should display something like:

```bash
  Processing <Platform#None windows_intelx86> ...
    Skipped existing <Platform#None windows_intelx86>
  Processing <Platform#None windows_x86_64> ...
    Skipped existing <Platform#None windows_x86_64>
  Processing <Platform#None x86_64-pc-linux-gnu> ...
    Skipped existing <Platform#None x86_64-pc-linux-gnu>
```

Once you are satisfied that the appropriate files are located in each app subdirectory, you can try to inform your database of the application files. I recommend you double check you have everything right for the first time (because if you don’t, you either have to make a new version for your app, or worse, edit the database manually to remove your app). Once satisfied,

```bash
    $PROJECTHOME/bin/update_versions
```

the output of which typically looks like:

```bash
  Found app version directory for: impact 1.0 windows_intelx86
      Continue (y/n)? y
  cp apps/impact/1.0/windows_intelx86/impact_job_1.0.xml ...
  cp apps/impact/1.0/windows_intelx86/impact_1.0_windows ...
  cp apps/impact/1.0/windows_intelx86/wrapper_26006 ...
      Files:
          wrapper_26006_windows_intelx86.exe (main program)
          impact_1.0_windows_intelx86.exe
          impact_job_1.0.xml
      Flags:
          API version: 7.2.2
      Do you want to add this app version (y/n)? y
      App version added successfully; ID=1
  Found app version directory for: impact 1.0 x86_64-pc-linux-gnu
  cp apps/impact/1.0/x86_64-pc-linux-gnu/wrapper_26005_x86 ...
  cp apps/impact/1.0/x86_64-pc-linux-gnu/impact_1.0_x86_64 ...
      Files:
          wrapper_26005_x86_64-pc-linux-gnu (main program)
          impact_1.0_x86_64-pc-linux-gnu
          impact_job_1.0.xml
      Flags:
          API version: 7.1.2
      Do you want to add this app version (y/n)? y
      App version added successfully; ID=2
  Found app version directory for: impact 1.0 windows_x86_64
  cp apps/impact/1.0/windows_x86_64/wrapper_26006_windows_x86 ...
  cp apps/impact/1.0/windows_x86_64/impact_1.0_windows_x86_64 ...
      Files:
          wrapper_26006_windows_x86_64.exe (main program)
          impact_1.0_windows_x86_64.exe
          impact_job_1.0.xml
      Flags:
          API version: 7.2.2
      Do you want to add this app version (y/n)? y
      App version added successfully; ID=3
```

If there are any problems with the filenames and version references of one of your app architectures, this script should detect that and the defective architecture/version will not be added to the database.

Note: at this point, if everything goes well, it’s pretty strong confirmation that your install was successful. I’ve had problems running `update_versions` when I’ve had broken php-mysql interactions, etc.

## 4.2 App Deployment

Now that you have the basic infrastructure down, you can begin creating workunits.

### 4.2.1 Aside on the Upload/Download directories

You may notice that any files Boinc places in the upload and download directories gets places in seemingly randomly named subdirectories. This is because the two directories use hierarchical directory structures with 1024 subdirectories in each parent directory. Essentially, this is because if you have a flat directory structure then over time, when you accumulate hundreds of thousands to hundreds of millions of files, finding the correct files to associate with workunits may be taxing on the server. So instead, each directory has a maximum of 1024 items in it, and a simple 2-level hierarchical directory can accommodate 1,000,000+ files. Each file is hashed with md5, and the hash determines which directory it is placed in.

### 4.2.2 Work Unit Generation

This becomes very application specific, but essentially the routine is as follows. First create workunit templates. You need an input and output template in the `$PROJECTHOME/templates` directory. The input template should look something like

```xml
  <input_template>
    <file_info>
      <number>0</number>
    </file_info>
    <file_info>
      <number>1</number>
    </file_info>
    <file_info>
      <number>2</number>
      <sticky/>
      <no_delete/>
    </file_info>
    <file_info>
      <number>3</number>
      <sticky/>
      <no_delete/>
    </file_info>
    ...
    <workunit>
      <file_ref>
        <file_number>0</file_number>
        <open_name>filename0</open_name>
        <copy_file/>
      </file_ref>
      <file_ref>
        <file_number>1</file_number>
        <open_name>filename1</open_name>
        <copy_file/>
      </file_ref>
      <file_ref>
        <file_number>2</file_number>
        <open_name>filename2</open_name>
        <copy_file/>
      </file_ref>
      <file_ref>
        <file_number>3</file_number>
        <open_name>filename3</open_name>
        <copy_file/>
      </file_ref>
      ...
      <min_quorum>1</min_quorum>
      <target_nresults>1</target_nresults>
      <max_error_results>1</max_error_results>
      <max_success_results>1</max_success_results>
      <max_total_results>1</max_total_results>
      <delay_bound>65536</delay_bound>
      <command_line>FILES/OPTIONS NEEDED FOR APP</command_line>
    </workunit>
  </input_template>
```

and your output template should look like

```xml
  <output_template>
    <file_info>
      <name><OUTFILE_0/></name>
      <generated_locally/>
      <upload_when_present/>
      <url><UPLOAD_URL/></url>
      <max_nbytes>5000000</max_nbytes>
    </file_info>
    <file_info>
      <name><OUTFILE_1/></name>
      <generated_locally/>
      <upload_when_present/>
      <url><UPLOAD_URL/></url>
      <max_nbytes>5000000</max_nbytes>
    </file_info>
    ...
    <result>
      <file_ref>
        <file_name><OUTFILE_0/></file_name>
        <open_name>md.out</open_name>
        <copy_file/>
      </file_ref>
      <file_ref>
        <file_name><OUTFILE_1/></file_name>
        <open_name>md-out1.dms</open_name>
        <copy_file/>
      </file_ref>
      ...
    </result>
  </output\_template>
```

Then stage all necessary input files. Then call the `create_work` script.

### 4.2.3 Job Validation

Once results are computed for workunits, the clients transmit the results into the `$PROJECTHOME/upload/` directory. There they will wait until there are validated (validation-state changes from 0 to 1), assimilated (assimilated-state changes from 0 to 1), and ultimately deleted.

The role of validators is to ensure that your results are not malformed. However, what that means varies from application to application. For our application, we mostly just use the validator to make sure the workunit returned ”something”. All other validation occurs during assimilation.

To incorporate a validator into your workflow (we will use the `sample_trivial_validator` in the example below, although we actually use it to just validate any result that exists), open your `config.xml` file and towards the bottom between the `<daemons> </daemons>` tags, add

```xml
  <daemon>
    <cmd>sample_trivial_validator -app APPNAME -d 3 </cmd>
  </daemon>
```

The `-d 3` sets the debug level where 1 is the lowest and 4 is the highest.

### 4.2.4 Result Assimilation

Once results have been validated, they must then be assimilated, which means the results are taken from the `upload/` directory and ”something” is done with them. What that something is depends on your application. For example, it could be that your

### 4.2.5 Custom Daemons

For our purposes, we found it convenient to make new versions of several included BOINC scripts, such as `create_work` and `stage_file`, as well as creating our own assimilators and validators. Scripts that are
written in php, bash, or python can be edited directly, but the c/c++ files can be found recompiled in the BOINC source directory (which we had installed at `$BOINCSRC=/usr/local/source/boinc/`).

Assimilators, transitioners, and schedulers should be placed or linked in `$BOINCSRC/sched`. Then in `$BOINCSRC/sched/Makefile.am`, you will need to make appropriate changes to incorporate your file. All new scripts should have their names added under `schedshare_PROGRAMS`. Then, depending on the type of script, you should add one set of the following pairs of lines:

```bash
  new_assimilator_SOURCES = $(ASSIMILATOR_SOURCES) \
    new_assimilator.cpp
  new_assimilator_LDADD = $(SERVERLIBS)

  new_validator_SOURCES = $(VALIDATOR_SOURCES) \
    new_validator.cpp
  new_validator_LDADD = $(SERVERLIBS)

  new_work_generator_SOURCES = new_work_generator.cpp
  new_work_generator_LDADD = $(SERVERLIBS)

  ...
```

Then use `make` to compile your new script.

## 4.3. Client Setup


We have installed the BOINC client software on several hundred Windows 7 PCs and several dozen computers running different operating systems (Windows XP, Vista, Ubuntu/Debian, Arch Linux, CentOS, etc.). Clients
can be configured individually using the BOINC Manager or `boinccmd` utility on each machine or can be configured in groups using the web interface found at <http://hostname/projectname/> by attaching each
machine to the same user account. It’s important to note that the local settings override the web-based settings, so be cautious mixing the two methods of administration.

### 4.3.1 Recommended Client settings

We have found through trial and error several client settings that maximize the number of successful results returned. The most important settings are listed below:

When using the BOINC wrappers, there is some overhead required by the wrapper. We found that leaving 1(2) CPU(s) free on 4(8) core machines left enough resources available for wrapper overhead and system processes.

When this option is set to a value below 100%, it shoots for an average of `X%` of CPU time over the length of the computation. This results in the CPU cycling between periods of 100% usage and 0% usage which average to `X%`. Might as well use one less CPU and 100% usage of the remaining CPUs.

For running MD, this encourages jobs to be distributed by the server only when a CPU is available, and encourages the clients to return jobs immediately instead of bundling several completed jobs together before uploading back to the server.

This goes hand in hand with the previous setting.

Most of the other settings can be set to suite the particular use case of the client machines. We have two distinct sets of machines which operate on completely different configurations. One set run only at
night, are not installed as a Windows service, and are not configured to be interrupted by non-BOINC usage. The other set can in principle run at all times, but are configured to suspend work while the computer is in use and will only resume work 2 minutes after the machines’ default logout time after a continuous stretch of inactivity. BOINC is quite versatile and we have found success running MD in both of these configurations.

### 4.3.1 Windows client setup through installation script

We setup a custom batch script that would install the BOINC client software silently on Windows as a service. The script copied several files to the default locations on the Windows system, added/deleted some things from the Windows registry, and installed the BOINC client software. Below are the files either required for or copied during the installation process:

```bash
  silent_install
  |-- account_SERVER_IP_boincimpact.xml
  |-- boinc_7.2.42_windows_x86_64.exe
  |-- cc_config.xml
  |-- client_config.bat
  |-- README.txt
  |-- remote_hosts.cfg
  `-- silent_install.bat
```

Below is the batch script used for Windows installation:

```basic
@ECHO OFF
SETLOCAL
SET rst=no
GOTO parse

:usage
ECHO Usage: [/?] [/r]
ECHO.
ECHO    /h Display this text.
ECHO    /r Restart once installation is complete. Default: no.
GOTO end

:: PARSE ANY CMDLINE ARGS
:parse
IF [%1]==[] GOTO endparse
IF [%1]==[/?] GOTO usage && exit \b 0
IF [%1]==[/r] SET rst=yes && ECHO Will restart when complete.
SHIFT
GOTO parse
:endparse

:: BOINC CLIENT INSTALLATION
SET projurl="https://SERVER_IP/PROJECTNAME/"
SET projauth="AUTHENTICATION_KEY"

ECHO Silent install beginning...
boinc_7.2.42_windows_x86_64.exe /S /v"/qn^

ENABLEPROTECTEDAPPLICATIONEXECUTION3=1^

ENABLESCREENSAVER=0 ENABLEUSEBYALLUSERS=0^

ENABLESTARTMENUITEMS=0 LAUNCHPROGRAM=0^

RebootYesNo=No PROJINIT_URL=%projurl%^

PROJINT_AUTH=%projauth%"

:: BOINC CLIENT CONFIGURATION
SET datadir="%PROGRAMDATA%\BOINC\"

ECHO Copying configuration files...
COPY cc_config.xml %datadir%
COPY account_PROJECT_NAME_HERE.xml %datadir%
::COPY global_prefs_override.xml %datadir%
COPY remote_hosts.cfg %datadir%
DEL "%datadir%global_prefs_override.xml"

:: DISABLE BOINCMGR STARTUP
set boinckey="HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"

ECHO Disabling auto-startup and altering registry...
REG QUERY %boinckey% /v boincmgr 1>nul 2>&1
  && REG DELETE %boinckey% /v boincmgr /f
REG QUERY %boinckey% /v boinctray 1>nul 2>&1
  && REG DELETE %boinckey% /v boinctray /f
IF EXIST "%USERPROFILE%\Start Menu\Programs\BOINC" \
  RMDIR /S /Q "%USERPROFILE$\Start Menu\Programs\BOINC"
IF EXIST "%APPDATA%\Microsoft\Windows\Start Menu\Programs\BOINC" \
  RMDIR \S \Q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\BOINC"

:: This was needed prior to the newest versions of the BOINC
:: wrappers.
ECHO Upgrading boinc accounts to administrator...
net localgroup administrators "boinc_project" /add 2> silent_install.log
net localgroup administrators "boinc_master" /add 2> silent_install.log

ECHO Installation and configuration complete.
IF %rst%==yes (
    ECHO Restarting...
    shutdown /r
) ELSE (
    ECHO Exiting...
)

:end
ENDLOCAL
```

The registry key editing is so that there is no discernible trace of BOINC running during use by normal (non-administrator) users. The user account promotion is to circumvent a bug present in earlier versions of the BOINC wrappers. This has since been fixed and can be disregarded if using wrapper version 26011 or greater, or if you are running a native BOINC app.

## 4.4 Troubleshooting

Below are errors we have run into in the process of setting up our workflow using BOINC and the solutions we have used to correct them.

### 4.4.1 _EXIT\_CHILD\_FAILED (195)_

For a time, this was a very common error and the most difficult to solve. This can occur for several reasons:

-   Your application has exited with a non-zero error code. Test your
    job locally to ensure that it works first before distributing it on
    BOINC.
-   The computation has exited and restarted for some reason. If the job
    restarts more than 100 times, the wrapper will kill the application
    and return this error. Investigate any reason that would cause your
    application to restart many times in succession.

### 4.4.2 _ERR\_RESULT\_START (-185)_

Check that the client can write to the `BOINC_DATA_DIR/slots/*` if it was installed with the default install paths.

During trouble shooting, we would run boinc-client as `boinc-client –exit_after_finish` to look at error files and such before they were deleted. Often, this would cause the `slots` subdirectories to
be owned by another user (like root) instead of boinc. You can just `rm` or `chown` them.

### 4.4.3 _EXIT\_TIME\_LIMIT\_EXCEEDED (197)_

Ensure that the supplied estimate and bound for the computation's FLOPs are appropriate for the computation. We have found that setting the FLOPs bound to be a factor of 10 greater than the estimate to be a good protocol.

