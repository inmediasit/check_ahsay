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
from datetime import date, timedelta, datetime

OK = ['BS_STOP_SUCCESS', 'BS_STOP_SUCCESS_WITH_ERROR',
      'BS_STOP_SUCCESS_WITH_WARNING', 'OK']
WARNING = ['BS_STOP_BY_USER']
CRITICAL = ['BS_STOP_BY_SYSTEM_ERROR', 'BS_STOP_BY_SCHEDULER', 'BS_STOP_BY_QUOTA_EXCEEDED', 'BS_STOP_MISSED_BACKUP', 'BS_BACKUP_NOT_FINISHED',
            'BS_MISSED_DATABASAE', 'BS_MISSED_PUBLIC_FOLDER', 'BS_MISSED_VIRTUAL_MACHINE', 'BS_STILL_RUNNING', 'BS_STOP_INCOMPLETE']
exit_code = 0
exit_code_map = {
    0: 'OK',
    1: 'WARNING',
    2: 'CRITICAL',
    3: 'UNKNOWN'
}


def set_exit_code(code):
    global exit_code
    if code > exit_code:
        exit_code = code


def set_status(status):
    if status in OK:
        set_exit_code(0)
    elif status in CRITICAL:
        set_exit_code(2)
    elif status in WARNING:
        set_exit_code(1)
    else:
        set_exit_code(3)


def parse_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')


def main():
    # parse variables from commandline
    parser = argparse.ArgumentParser(
        description='Nagios check for Ahsay backup states')
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

    try:
        response = requests.post(
            'http://' + args.hostname + '/obs/api/json/ListBackupJobStatus.do', data=payload)
    except requests.ConnectionError:
        print("Could not connect to Ahsay API")
        exit(3)
    else:
        content = json.loads(response.text)
        data = content.get('Data')
        output = ''
        if data:
            # order backup jobs by date
            data.sort(key=lambda x: parse_date(x['StartTime']))

            backup_jobs = dict()
            other_jobs = dict()
            # backups are available
            for i in data:
                job_name = i.get('BackupSetName')
                # check for existing jobs
                other_job = backup_jobs.get(job_name, None)
                if other_job:
                    other_jobs[job_name] = other_job
                else:
                    backup_jobs[job_name] = i

            # run check logic on jobs we care about
            for i, job in enumerate(backup_jobs.values()):
                backup_status = job.get('BackupJobStatus')
                set_status(backup_status)
                output += '{index}. Backup Job "{name}" at {date} returned status {status}\n'.format(
                    index=i + 1, name=job.get('BackupSetName'), date=job.get('StartTime'), status=backup_status)

            # if we have superseded jobs, print them anyway
            if other_jobs.values():
                output += '\n--- Superseded jobs at {date} ------\n'.format(
                    date=date_formatted)
                for otherjob in other_jobs.values():
                    output += '* Job "{name}" at {date} –– Status: {status}\n'.format(
                        name=otherjob.get('BackupSetName'), date=otherjob.get('StartTime'), status=other_job.get('BackupJobStatus'))
                output += 40*'-' + '\n'
        else:
            # there are no backups available
            set_status(content.get('Status'))
            output += content.get('Message')

        output = '{}\n{}'.format(
            exit_code_map.get(exit_code, 'UNKNOWN'), output)
        print(output)
        exit(exit_code)


if __name__ == '__main__':
    main()
