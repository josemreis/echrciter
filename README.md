# echrciter 

Make oscola-style bibtex citations for echr cases

```bash
usage: echrciter.py [-h] [-a [APPNO]] [-n [CITATION_NAME]]

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
title={Del Río Prada v. Spain},
date={2012},
number={42750/09},
pages={42750},
institution={ECHR},
keywords={echr},
reporter={ECHR},
volume={6},
}
```
