# CrispritzWebApp
Versione corrente: app_v5.py


Installare il conda di crispritz, poi in quel conda aggiungere:


Dash (Testato con 1.1.1)
```
conda install -c conda-forge dash
```
Dash-renderer (Testato con 1.0.1)
```
conda install -c conda-forge dash-renderer
```
Dash daq (Testato con 0.1.7)
```
conda install -c conda-forge dash-daq
```
Flask-Caching (Vengono installati anche Flask-1.1.1 Flask-Caching-1.7.2 Jinja2-2.10.1 MarkupSafe-1.1.1 Werkzeug-0.15.5 click-7.0 itsdangerous-1.1.0)
```
conda install -c conda-forge flask-caching
```
Comando rename
```
sudo apt install rename
```
Bootstrap for dash
```
conda install -c conda-forge dash-bootstrap-components
```
pdftoppm to create png results
```
sudo apt-get install python-poppler
```
Estrarre gli zip in genome_library per poter fare la ricerca con i bulges


Dentro la cartella CrispritzWebApp, eseguire:
```
python3 app_v5.py
```
La pagina principale si trova su:
```
127.0.0.1:8050
```
Esempio di pagina wait job:
```
127.0.0.1:8050/load?job=3M2G83R5O9
```
Esempio di result summary:
```
127.0.0.1:8050/result?job=3M2G83R5O9
```
Esempio di targets per guida:
```
127.0.0.1:8050/result?job=3M2G83R5O9#GAGTCCGAGCAGAAGAAGAANNN
```
