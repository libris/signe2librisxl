# Signe Newspaper Data 2 Libris XL

## Setup

Important: install ODBC Driver 18 for SQL Server! See:
<https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver15>.

(The use of `--system-site-packages` when creating the virtualenv below is
needed if you want/have to install pyodbc using your distro's package manager.)

Install uv: https://github.com/astral-sh/uv

```sh
$ uv venv --system-site-packages
$ source .venv/bin/activate
$ cp signe.ini.in signe.ini # edit for correct credentials!
```
## Extract & Transform
```sh
$ python -m signedata signe.ini
```

(Note: if you _don't_ need `--system-site-packages`, you can skip `uv venv`/`source`
and simply run `uv run python -m signedata signe.ini`.)

## Load

The supplied $BUILDDIR now contains jsonl files with records that XL can load.

## About The Mappings

This data maps to Libris base data (mainly id.kb.se terms). Some of these have
been set up specifically to support this Signe data, namely frequencies and
a-regions.

(If these are specific to Signe only, we have a bigger coordination problem.)

### Temporality

This data uses a qualification model of time, meaning that we use specific
qualified relations to capture relations restricted to a certain date range.

This has a precursor in the existing use of `provisionActivity` and structured
values, as well as following the rationale in the accepted BF 2.1 [Proposal:
pubFrequency/PubFrequency for recording complex frequency
information](https://github.com/lcnetdev/bibframe-ontology/issues/76).

Furthermore, as these qualifications relate to the instances of the serial that
were issued during a given period, we use the specific `firstIssue` and
`lastIssue` properties throughout to clearly reflect that.

Particularly, this can be used, e.g. in an application consuming this data, as
an indication that the qualified data applies to any issue (any entity linking
to a serial using `isIssueOf`) which has a `date` (of `publication`) that falls
within the qualified date range.
