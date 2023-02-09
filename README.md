# **ScrapeTournamentMatches**
Repository for scraping tournament matches data.

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

**Remark**: This project has been developed entirely with a conda environment. It should still work with pip since `requirements.txt` was created automatically:

```
$ pip list --format=freeze > requirements.txt
```

<br>

## **How to Run**
---

All that is needed is:

- Setup the configuration file `src/parameters.json`.

    See [Parameters](#parameters) for more details.

- Run the main python script:

    ```
    $ cd src
    $ python3 main.py
    ```

<br>

## **Configuration**
---

By default, everything is logged to `logs/`. 

Severity level can be changed in `src/logs/logs.py`.

### **Parameters**

All default values are  defined inside `src/parameters.json`. 

- **"should_scrape"**: Whether or not data should be scraped.

    - By default data will be saved to `data/bet_explorer/{sport}.csv`.
    - See `src/bet_explorer/__init__.py` for details about the output.


- **"should_format"**: Whether or not data should be formatted. 

    - By default data will be saved to `data/formatted/{sport}.csv`
    - See `src/bet_explorer/__init__.py` for details about the output.

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

    - **"list"**: list of url paths for "json_list" mode.

    - **"file"**: path for "file" mode.

- **"sports"**: List of desired sports.

- **"seasons"**: Which tournament seasons we should scrape.

    - **"first"**: List with first seasons to be considered for all tournaments. 

        - First entry should be just a year. 
        
            It will be used for tournaments which start and end in the same year.

        - Second entry should be two years separated by "-". 
        
            It will be used for tournament which start in one year and end in the next.

    - **"last"**: List with last seasons to be considered for all tournaments. 

        - It should have the same kind of entries as "first_season".

    **Note**: All seasons between "first_season" and "last_season" will be scraped.

<br>

## **Licensing**
---

This repository is licensed under the Apache License, Version 2.0. See LICENSE for the full license text.
