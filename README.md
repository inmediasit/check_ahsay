# check_ahsay

This is a monitoring plugin for Ahsay Backup.

## Required packages
* python3
* python3-requests

```
usage: check_ahsay.py [-h] --hostname <IP or URI> --user USER --password
                      PASSWORD --login-name LOGIN_NAME [--backup-date DATE]

Nagios check for Ahsay backup states

optional arguments:
  -h, --help            show this help message and exit
  --hostname <IP or URI>, -H <IP or URI>
                        Host name argument for Ahsay server
  --user USER, -u USER  Username for the Ahsay REST API
  --password PASSWORD, -p PASSWORD
                        Password to the given username
  --login-name LOGIN_NAME, -l LOGIN_NAME
                        Login name of the backup job who needs to be checked
  --backup-date DATE, -d DATE
                        Date of the backup job in yyyy-MM-dd format (not
                        required)
```