# **ScrapeTournamentMatches**
Repository for scraping tournament matches data.

> **Note: It scrapes round-robin matches, rather than playoffs matches.**
>> In order to change this behaviour, you have to modify the function `_get_main_seaction_query` inside `src/bet_explorer/scrape_matches.py`.

## **Getting Started**
---

Python version: 3.10

### **Conda**

Creating a virtual environment:

```
$ conda env create -f environment.yml
```

Activating virtual environment:
```
$ conda activate scrape_matches
```

### **Pip**

Creating a virtual environment:

```
$ python3 -m venv env
```

Activating virtual environment:

```
$ source env/bin/activate
```

Installing all required packages:

```
$ python3 -m pip install -r requirements.txt
```

<br>

## **How to Run**
---

All that is needed is:

- Setup configuration parameters:
    - Setup `src/scrape.json`.
    - Setup parameters in whatever `src/<...>.py` you want to run.

    See [Parameters](#parameters) for more details.

- Run the main python script:

    ```
    $ cd src
    $ python3 scrape.py  # scraping matches
    $ python3 format.py  # formatting matches
    $ python3 filter.py  # filter matches
    ```

<br>

## **Formats**
---
For information about what data will be scraped and saved you can read:

- `scrape`: Read `src.bet_explorer.scrape.save_web_scraped_matches` documentation.
- `format`: Read `src.bet_explorer.scrape.save_formatted_web_scraped_all_sports` documentation.
- `filter`: Same format as `format`.

## **Configuration**
---

By default, everything is logged to `logs/`. 

Severity level can be changed in `src/logs/logs.py`.

### **Parameters**

**Scrape Parameters**

All default values are defined inside `src/scrape.json`. 

- **"sports"**: List of desired sports.

- **"url_paths"**:  Which `betexplorer.com` webpage paths to use. 

    They are of the form "{sport}/{country}/{tournament-name}".

    - **"mode"**: There are three possible modes for this.

        - **"file"**: It will take paths from the "file" provided in `src/parameters.json`. 

            Default file contains various tournaments for basketball, soccer, ,handball and volleyball. 
            
            However, given that `betexplorer.com` changes its webpage paths if tournaments have their names changed, some default values might be invalid. 
        
        - **"json_list"**: It will take paths from the "list" provided in `src/parameters.json`.

            You can scrape a short number of tournaments so that you don't have to wait for long. 

        - **"homepage"**: It will web scrape `betexplorer.com`'s home page for tournament paths. 
        
            Only useful if you don't have any paths at your disposal.

            If you should this option, all scraped paths will be logged to `src/logs/web_scrape.log`.

    - **"list"**: list of url paths for "json_list" mode.

    - **"file"**: path for "file" mode.

- **"seasons"**: Which tournament seasons we should scrape.

    - **"first"**: List with first seasons to be considered for all tournaments. 

        - First entry should be just a year. 
        
            It will be used for tournaments which start and end in the same year.

        - Second entry should be two years separated by "-". 
        
            It will be used for tournament which start in one year and end in the next.

    - **"last"**: List with last seasons to be considered for all tournaments. 

        - It should have the same kind of entries as "first_season".

    **Note**: All seasons between "first_season" and "last_season" will be scraped.

**Format Parameters**

The only required parameter is what sports should be formatted.

By default it takes them from `src/scrape.json`. But you can also write them directly into `format.py`.


**Filter Parameters**

The only required parameter is what sports should be filtered.

By default it takes them from `src/scrape.json`. But you can also write them directly into `format.py`.

Optional parameters which can be changed in `src/filter.py`:
- Whether invalid matches should be removed: 
    - `filter_matches: Literal['no', 'before', 'after']` parameter in `bet.filter.filter_and_save_tournaments_all_sports` function call.
        - **"no"**: Do not filter them out.
        - **"before"**: Filter them 'before' applying filtering functions
        - **"after"**: Filter them 'after' applying filtering functions
        - **Any other value**: same as "no".
- Add/Remove new functions to filter tournaments: 
    - Add to `src.bet_explorer.filter.filter_functions`.
    - Add/remove from `src/filter.py` filtering function list: `FILTERING_FUNCTIONS`.


<br>

## **Licensing**
---

This repository is licensed under the Apache License, Version 2.0. See LICENSE for the full license text.
