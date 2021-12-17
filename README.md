# echrciter 

Make oscola-style bibetex citations for echr cases

```bash
usage: echr_citer.py [-h] [-a [APPNO]] [-n [CITATION_NAME]]

Generate a bibtex citation for an ECtHR case

optional arguments:
  -h, --help            show this help message and exit
  -a [APPNO], --app-no [APPNO]
                        Case application number.
  -n [CITATION_NAME], --citation-name [CITATION_NAME]
                        Citation name.

```

## Usage 

```bash
python3 echrciter.py -a "42750/09" -n "delrio09"  
```

```bash
@jurisdiction{delrio09,
title={Galan v. Italy (dec.)},
date={2021},
number={63772/16},
pages={63772},
institution={ECHR},
keywords={echr},
reporter={ECHR},
volume={6},
}
```
