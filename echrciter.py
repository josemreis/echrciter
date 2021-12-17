import argparse
import sys
from typing import Optional
import requests
import re
import time
import random
from datetime import datetime

## fix to the cyper issue: https://stackoverflow.com/questions/38015537/python-requests-exceptions-sslerror-dh-key-too-small
requests.packages.urllib3.disable_warnings()
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ":HIGH:!DH:!aNULL"
try:
    requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += (
        ":HIGH:!DH:!aNULL"
    )
except AttributeError:
    # no pyopenssl support used / needed / available
    pass


TEMPLATE_URL_ECHR_RECORDS = """https://www.echr.coe.int/app/query/results?query=contentsitename:PORTAL AND (applicationnumber:"{application_number}") AND ((subcategory:"e-reports"))&select=Rank,Created,FirstName,LastName,url2,contentcategory,subcategory,contentlanguage,hearingdate,hudocdate,hearingtype,imageurl,state,sharepointid,postponed,cancelled,webcastitemid,createdAsDate,modifiedAsDate,Title,text,country,pagedescription,comment,statementoffactdescription1,statementoffacturl1,statementoffactdescription2,statementoffacturl2,prdescription,prurl,fcdescription,fcurl,gcjdescription,gcjurl,cjdescription,cjurl,decisiondescription,decisionurl,deliveryvideodescription1,deliveryvideourl1,deliveryvideodescription2,deliveryvideourl2,title0fre,text0fre,country0fre,pagedescription0fre,comment0fre,statementoffactdescription10fre,statementoffacturl10fre,statementoffactdescription20fre,statementoffacturl20fre,prdescription0fre,prurl0fre,fcdescription0fre,fcurl0fre,gcjdescription0fre,gcjurl0fre,cjdescription0fre,cjurl0fre,decisiondescription0fre,decisionurl0fre,deliveryvideodescription10fre,deliveryvideourl10fre,deliveryvideodescription20fre,deliveryvideourl20fre,PortalRanking,PortalDate&sort=&start=0&length=20&rankingModelId=55555555-0000-0000-0000-000000000000"""
TEMPLATE_URL_HUDOC = """https://hudoc.echr.coe.int/app/query/results?query=contentsitename=ECHR {application_number} AND (doctype:CLIN OR doctype:CLINF)&select=sharepointid,Rank,ECHRRanking,languagenumber,itemid,docname,doctype,application,appno,conclusion,importance,originatingbody,typedescription,kpdate,kpdateAsText,documentcollectionid,documentcollectionid2,languageisocode,extractedappno,isplaceholder,doctypebranch,respondent,advopidentifier,advopstatus,ecli,appnoparts,sclappnos&sort=&start=0&length=500"""


class NoCases(Exception):
    pass

def parse_args() -> argparse.Namespace:
    """argument parser"""

    ## parse CLI args
    parser = argparse.ArgumentParser(
        prog="echr_citer.py",
        description="Generate a bibtex citation for an ECtHR case",
    )

    parser.add_argument(
        "-a",
        "--app-no",
        dest="appno",
        nargs="?",
        type=str,
        default=None,
        help="Case application number.",
    )

    parser.add_argument(
        "-n",
        "--citation-name",
        dest="citation_name",
        nargs="?",
        type=str,
        default="fooh",
        help="Citation name.",
    )

    # parse. If no args display the "help menu"
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    return parser.parse_args()


def validate_appno(app_no: str) -> str:
    if re.match(r"[0-9]+/[0-9]{2}", app_no):
        return app_no
    else:
        raise ValueError(f"{app_no} is not a valid application number")


def make_query(url: str, max_retries=5, max_sleep=5):
    attempt = 0
    while True:
        attempt += 1
        try:
            response = requests.get(url)
            return response
        except Exception as e:
            if attempt == max_retries:
                raise e
            else:
                print(f"Failed to query {url} due to: {e}\n retrying in few seconds")
                time.sleep(attempt ** 2 + random.random())
                continue


def fetch_case_details(app_no: str, max_attempts=5) -> Optional[dict]:
    """make a request to hudoc and return the json data"""
    query_url = TEMPLATE_URL_HUDOC.format(application_number=app_no)
    try:
        resp = make_query(url=query_url)
    except Exception as e:
        raise (f"Requests error:{e}")
    ## parse
    resp_json = resp.json()
    ## extract the relevant case details
    case_details = {}
    if resp_json.get("resultcount") < 1:
        raise NoCases("No cases found in hudoc")
    for result_dict in resp_json.get("results"):
        lang_dict = result_dict.get("columns")
        if lang_dict.get("appnoparts").replace(";", "/") == app_no:
            ## fetch the year
            ruling_year = str(
                datetime.strptime(lang_dict.get("kpdate").split(" ")[0], "%m/%d/%Y").year
            )
            ## prepare theappno
            extracted_appno = lang_dict.get("appnoparts").replace(";", "/")
            lang_number = int(lang_dict.get("languagenumber"))
            if lang_number <= 2:
                if lang_number == 1:
                    lang = "en"
                elif lang_number == 2:
                    lang = "fr"
            # prepare the dict
            case_details[lang] = {
                "title": lang_dict.get("docname"),
                "date": ruling_year,
                "number": extracted_appno,
            }
        return case_details


def roman_numeral_to_int(numeral: str = "VII"):
    d = {"M": 1000, "D": 500, "C": 100, "L": 50, "X": 10, "V": 5, "I": 1}
    ans = 0
    n = len(numeral)
    for (idx, c) in enumerate(numeral):
        if idx < n - 1 and d[c] < d[numeral[idx + 1]]:
            ans -= d[c]
        else:
            ans += d[c]
    return ans


def fetch_records_details(app_no: str) -> dict:
    """fetch metadata about where it was reported"""
    query_url = TEMPLATE_URL_ECHR_RECORDS.format(application_number=app_no)
    try:
        resp = make_query(url=query_url)
    except Exception as e:
        raise (f"Requests error:{e}")
    ## parse
    resp_json = resp.json()
    if resp_json.get("resultcount") < 1:
        raise ValueError("Case not found in echr records")
    report_numbers = set()
    for result_dict in resp_json.get("results"):
        lang_dict = result_dict.get("columns")
        title_raw = lang_dict.get("Title")
        ## fetch the report number
        report_n_raw = re.search(r"([0-9]{4}\-[A-Z]{1,4})(?=$)", title_raw)
        if report_n_raw:
            report_n_roman = report_n_raw.group(1).split("-")[-1]
            report_numbers.add(roman_numeral_to_int(report_n_roman))
    if report_numbers:
        return {"volume": list(report_numbers)[0]}


def make_bibtex_dict(case_details: dict, volume_number: Optional[int]) -> dict:
    bibtex_dict = {
        "title": {case_details.get("title")},
        "date": {case_details.get("date")},
        "number": {case_details.get("number")},
        "pages": {case_details.get("number").split("/")[0]},
        "institution": {"ECHR"},
        "keywords": {"echr"},
    }
    if volume_number:
        bibtex_dict["reporter"] = {"ECHR"}
        bibtex_dict["volume"] = {str(volume_number)}
    return bibtex_dict


def main():
    ## parse the arguments
    args = parse_args()
    ## validate the appno
    appno = validate_appno(args.appno.strip())
    ## fetch case detailks
    try:  
        case_details_raw = fetch_case_details(app_no=appno)
    except NoCases:
        case_details_raw = None
        pass
    if not case_details_raw:
        print(f"Case {appno} not found in HUDOC's database")
        sys.exit(1)
    # filter the english version if it exists, else replace the "c." with "v."
    for lang in case_details_raw:
        if lang == "en":
            case_details = case_details_raw[lang]
            break
        else:
            case_details = case_details_raw[lang]
    if not case_details:
        print(f"No english or french translation of case {appno} found in HUDOC's database")
        sys.exit(1)
    ## fetch the echr report volume
    reporter_volume = None
    try:
        reporter_volume = fetch_records_details(app_no=appno).get("volume")
    except:
        pass
    ## make bibtex dict
    bib_dict = make_bibtex_dict(case_details, reporter_volume)
    out = "@jurisdiction{{{citation_name},\n".format(citation_name=args.citation_name)
    for entry_key, entry_value in bib_dict.items():
        out += f"{entry_key}={entry_value},\n".replace("'", '')
    out += "}"
    ## print
    print(out)


if __name__ == "__main__":
    main()
