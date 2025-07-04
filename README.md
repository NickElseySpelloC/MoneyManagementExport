# MoneyManagement Export
This app is designed to download Australian wholesale fund prices from moneymanagement.com.au. It's a companion project to the [YahooFinance app](https://github.com/NickElseySpelloC/YahooFinance) and the [InvestSmart Export app](https://github.com/NickElseySpelloC/InvestSmartExport). This app uses the Playwright Python library to "scrape" the MoneyManagement web pages, so it might not be 100% reliable. 

# Features
* Extracts price, effective date, fund name, symbol and currency from a specified URL
* Save price data to a CSV 
* Error and retry handling
* Designed to be run as a scheduled task (e.g. from crontab)
* Can send email notifications when there is a critical failure.

# Installation & Setup
Currently this app only supports macOS / Linux

## Prerequisites
### 1. Python 3.x installed:
    brew install python3

### 2. UV for Python installed:
    brew install uvicorn

### 3. Playwright installed. 
    uv sync
    playwright install

The _launch_ shell script used to run the app uses the *uv sync* command to ensure that all the prerequitie Python packages are installed in the virtual environment.

# Configuration File 
The script uses the *config.yaml* YAML file for configuration. An example of included with the project (*config.yaml.example*). Copy this to *config.yaml* before running the app for the first time.  Here's an example config file:
```
MoneyManagement:
  HeadlessMode: True
  PageLoad: 4
  Funds: 
    - URL: "https://investmentcentre.moneymanagement.com.au/factsheets/AH/l1o7/bentham-global-income"
    - URL: "https://investmentcentre.moneymanagement.com.au/factsheets/AH/09x2/pimco-global-bond-wholesale"
    - URL: "https://investmentcentre.moneymanagement.com.au/factsheets/AH/l1l3/merlon-australian-share-income"
      Symbol: HBC0011AU
      Name: "Merlon Australian Share Income (FPL)"

Files:
    OutputCSV: price_data.csv
    DaysToSave: 90
    Logfile: logfile.log
    LogfileMaxLines: 200
    LogfileVerbosity: detailed
    ConsoleVerbosity: detailed

Email:
    EnableEmail: True
    SendEmailsTo: john.doe@gmail.com
    SMTPServer: smtp.gmail.com
    SMTPPort: 587
    SMTPUsername: john.doe@gmail.com
    SMTPPassword: <Your SMTP password>
    SubjectPrefix: 
```

## Configuration Parameters
### Section: MoneyManagement

| Parameter | Description | 
|:--|:--|
| HeadlessMode | If False, the browser window won't be displayed when scraping the InvestSmart watchlist. You should set this to True initially to make sure everything is working OK. |
| PageLoad | The timeout when waiting for a web page to load and the relevant elements to be available. |
| Funds | A list of fund to get data for. At the minimum you must specify the URL to the fund's page. Optionally you can also supply the name and APIR Symbol code if it's not listed on the web page |

### Section: Files

| Parameter | Description | 
|:--|:--|
| OutputCSV | The name of the CSV file to write prices to. If the file already exists, prices will be appended to the end of the CSV file. | 
| DaysToSave | Fund price data is appended to the CSV file. This setting sets the maximum number of days to keep price data for. Set to 0 or blank if not truncation is required. | 
| LogfileName | The name of the log file, can be a relative or absolute path. | 
| LogfileMaxLines | Maximum number of lines to keep in the log file. If zero, file will never be truncated. | 
| LogfileVerbosity | The level of detail captured in the log file. One of: none; error; warning; summary; detailed; debug; all | 
| ConsoleVerbosity | Controls the amount of information written to the console. One of: error; warning; summary; detailed; debug; all. Errors are written to stderr all other messages are written to stdout | 

### Section: Email

| Parameter | Description | 
|:--|:--|
| EnableEmail | Set to *True* if you want to allow the app to send emails. If True, the remaining settings in this section must be configured correctly. | 
| SMTPServer | The SMTP host name that supports TLS encryption. If using a Google account, set to smtp.gmail.com |
| SMTPPort | The port number to use to connect to the SMTP server. If using a Google account, set to 587 |
| SMTPUsername | Your username used to login to the SMTP server. If using a Google account, set to your Google email address. |
| SMTPPassword | The password used to login to the SMTP server. If using a Google account, create an app password for the app at https://myaccount.google.com/apppasswords  |
| SubjectPrefix | Optional. If set, the app will add this text to the start of any email subject line for emails it sends. |

# Running the Script
Run the app using the relavant shell script for your operating system:

    launch.sh

# Troubleshooting
## Playwright not installed exception
After doing `uv sync` to download the playwright library you must then do:![alt](
    
    playwright install

You only need to do this once

## "No module named xxx"
Ensure all the Python modules are installed in the virtual environment. Make sure you are running the app via the *launch* script.

## ModuleNotFoundError: No module named 'requests'
If you can run the script just fine from the command line, but you're getting this error when running from crontab, make sure the crontab environment has the Python3 folder in it's path. First, at the command line find out where python3 is being run from:

`which python3`

And then add this to a PATH command in your crontab:

`PATH=/usr/local/bin:/usr/bin:/bin`
`0 8 * * * /Users/bob/scripts/InvestSmartExport/launch.sh`