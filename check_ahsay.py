#!/usr/bin/env python3


# check_ahsay
# Copyright (C) 2018 inmedis.it GmbH
#
# This file is part of check_ahsay.
#
# check_ahsay is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# check_ahsay is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with check_ahsay. If not, see <http://www.gnu.org/licenses/>.

import argparse
import requests
import json
from datetime import date, timedelta

OK = ['BS_STOP_SUCCESS', 'BS_STOP_SUCCESS_WITH_ERROR', 'BS_STOP_SUCCESS_WITH_WARNING']
WARNING = ['BS_STOP_BY_USER']
CRITICAL = ['BS_STOP_BY_SYSTEM_ERROR', 'BS_STOP_BY_SCHEDULER', 'BS_STOP_BY_QUOTA_EXCEEDED', 'BS_STOP_MISSED_BACKUP', 'BS_BACKUP_NOT_FINISHED', 'BS_MISSED_DATABASAE', 'BS_MISSED_PUBLIC_FOLDER', 'BS_MISSED_VIRTUAL_MACHINE', 'BS_STILL_RUNNING']
exit_code = 0

def set_exit_code(code):
    global exit_code
    if code > exit_code:
        exit_code = code

def get_status():
    if exit_code == 0:
        return 'OK'
    elif exit_code == 1:
        return 'WARNING'
    elif exit_code == 2:
        return 'CRITICAL'
    else:
        return 'UNKNOWN'


def set_status(status):
    if status in OK:
        set_exit_code(0)
    elif status in CRITICAL:
        set_exit_code(2)
    elif status in WARNING:
        set_exit_code(1)
    else:
        set_exit_code(3)


def main():
    # parse variables from commandline
    parser = argparse.ArgumentParser(description='Nagios check for Ahsay backup states')
    parser.add_argument('--hostname',
                        '-H',
                        required=True,
                        type=str,
                        help='Host name argument for Ahsay server',
                        dest='hostname',
                        metavar='<IP or URI>')
    parser.add_argument('--user',
                        '-u',
                        required=True,
                        type=str,
                        help='Username for the Ahsay REST API',
                        dest='user')
    parser.add_argument('--password',
                        '-p',
                        required=True,
                        type=str,
                        help='Password to the given username',
                        dest='password')
    parser.add_argument('--login-name',
                        '-l',
                        required=True,
                        type=str,
                        help='Login name of the backup job who needs to be checked',
                        dest='login_name')
    parser.add_argument('--backup-date',
                        '-d',
                        required=False,
                        type=str,
                        help='Date of the backup job in yyyy-MM-dd format (not required)',
                        dest='date')
    # get the arguments
    args = parser.parse_args()

    if args.date is None:
        yesterday = date.today() - timedelta(1)
        date_formatted = yesterday.strftime('%Y-%m-%d')
    else:
        date_formatted = args.date

    # get values for HTTP JSON POST request
    payload = {
        'SysUser': args.user,
        'SysPwd': args.password,
        'LoginName': args.login_name,
        'BackupDate': date_formatted
    }
    response = requests.post('http://' + args.hostname + '/obs/api/json/ListBackupJobStatus.do', data=payload)
    content = json.loads(response.text)
    data = content.get('Data')
    output = ''
    if data is not None:
        for i in data:
            job_name = i.get('BackupSetName')
            backup_status = i.get('BackupJobStatus')
            set_status(backup_status)
            output += 'Backup Job "{}" returned status {}\n'.format(job_name, backup_status)
    else:
        print("CRITICAL: Es besteht keine Verbindung zum Backupserver")
        exit(3)

    output = '{}\n{}'.format(get_status(), output)
    print(output)
    exit(exit_code)

if __name__ == '__main__':
    main()
