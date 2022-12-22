import tempfile
import pathlib
from pathlib import Path
import sqlite3
import settings as settings
import os
from tqdm import tqdm
import github_unarchives as unarchiver
import github_archives_index
import glob

_DIR = pathlib.Path(__file__).parent.absolute()
TMPDIR = os.path.join(tempfile.gettempdir(), 'public-github-archives/index')
DSDIR = os.path.join(_DIR, 'samples/s')

DBPATH = os.path.join(_DIR, 'samples/s.db')


def initdb(path):
    # create db if not exists
    if not os.path.exists(path):
        open(path, 'w').close()

    db = sqlite3.connect(path)
    cursor = db.cursor()
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS files (repo text, path text, content text)')
    db.commit()
    return db, cursor


db, cursor = initdb(DBPATH)


def with_extensios(path, exts):
    files = []
    for ext in exts:
        print('ext', ext, path)
        files += glob.glob(path+'/**/*'+ext, recursive=True)
        print(files)
    return files


samples = github_archives_index.Indexer(DSDIR)
repos = samples.read_index()
total = len(repos)

# patterns
exts = ['.js', '.jsx', '.css']


if __name__ == "__main__":
    try:

        progress = tqdm(total=total, desc='indexing')

        # iterate over repos
        for item in repos:
            # unzip
            _i = os.path.join(DSDIR, item+'.zip')
            _o = os.path.join(TMPDIR, item)
            path = None
            # if file exists
            if os.path.exists(_i):
                _ = unarchiver.unzip_file(_i, _o)
                if _:
                    path = _['final_path']
                else:
                    tqdm.write('unzip failed: '+_i)

            else:
                tqdm.write('archive zip file not found: '+_i)

            if path is None:
                files = []
            else:
                files = with_extensios(path, exts)

            for _f in files:
                tqdm.write(f'indexing..: {item} {relpath}')
                relpath = os.path.relpath(_f, path)
                # index files to sqlite db
                with open(_f, 'r') as f:
                    content = f.read()
                    cursor.execute(
                        # columns: repo, path, content
                        'INSERT INTO files VALUES (?, ?, ?)', (item, relpath, content))
                    tqdm.write(f'indexed: {item} {relpath}')
                    db.commit()

            progress.update(1)

    except KeyboardInterrupt as e:
        db.close()
        exit()
