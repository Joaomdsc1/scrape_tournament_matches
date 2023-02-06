# ScrapeTournamentMatches
Repository for scraping tournament matches data.

## **Getting Started**
---

Python version: 3.10

### **Conda**

Creating a virtual environment:

```
conda env create -f environment.yml
```

Activating virtual environment:
```
conda activate scrape_matches
```

### **Pip**

Creating a virtual environment:

```
python3 -m venv env
```

Activating virtual environment:

```
source env/bin/activate
```

Installing all required packages:

```
python3 -m pip install -r requirements.txt
```

**Remark**: This project has been developed entirely with a conda environment. It should still work with pip since `requirements.txt` was created automatically:

```
pip list --format=freeze > requirements.txt
```

<br>
