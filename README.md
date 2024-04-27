# Python script to scrap data from Instagram and send it into Telegram chat

You need to login to your server via SSH or open the terminal if it's on your local machine.
I will use code snippets for Ubuntu/Debian server OS.

<b>Download package information from all configured sources for your current OS.</b>
```
sudo apt-get update
```

<b>Install ZIP utility</b>
```
sudo apt install unzip
```

<b>Install python package manager</b>
```
sudo apt install python3-pip
```

<b>Using pip install tendo which will help us to make sure that we run our script as a singleton</b>
```
pip install tendo
```

\
\
<b>Install Selenium package to automate web browser interaction</b>
```
pip install selenium
```

\
\
<b>Install Beautifulsoup to scrape information from web pages</b>
```
pip install beautifulsoup4
```

\
\
<b>Install lxml library for processing XML and HTML in the Python language.</b>
```
pip install lxml
```
\
\
<b>Install chromedriver binary file. It's a standalone server which provides capabilities for navigating to web pages, user input, JavaScript execution, and more</b>
```
pip install chromedriver-py
```

\
\
<b>Download latest Google Chrome package:</b>
```
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
```
\
\
<b>Install this debian package</b>
```
sudo dpkg -i google-chrome-stable_current_amd64.deb
```
\
\
<b>dpkg: dependency problems can throw an error during the Chrome installation process in Ubuntu. You can fix it with this:</b>
```
sudo apt install -f
```

\
\
<b>Install Google Chrome again with fixed dependencies</b>
```
sudo dpkg -i google-chrome-stable_current_amd64.deb
```

<b>Google Chrome version check:</b>
```
google-chrome --version
```


\
\
the last part of this configuation guide is in progress...