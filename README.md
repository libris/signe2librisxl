# Signe Newspaper Data 2 Libris XL

## Setup

Important: install ODBC Driver 18 for SQL Server! See:
<https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver15>.

(The use of `--system-site-packages` when creating the virtualenv below is
needed if you want/have to install pyodbc using your distro's package manager.)
```sh
$ python3 -m venv --system-site-packages .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
$ cp signe.ini.in signe.ini # edit for correct credentials!
```
## Extract & Transform
```sh
$ python -m signedata signe.ini
```
## Load

The supplied $BUILDDIR now contains jsonl files with records that XL can load.

## Mappings

See the `mappings/` directory for identities this data needs to map to. This
must be integrated into the base Libris data for this dataset to be
operational.
