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
import shutil

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
        'CREATE TABLE IF NOT EXISTS files (repo text, path text, content text, language text, PRIMARY KEY (repo, path))')
    db.commit()
    return db, cursor


db, cursor = initdb(DBPATH)


def with_extensios(path, exts):
    files = []
    for ext in exts:
        files += glob.glob(path+'/**/*'+ext, recursive=True)
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
            tqdm.write('👇 '+item)
            # unzip
            _i = os.path.join(DSDIR, item+'.zip')
            _o = os.path.join(TMPDIR, item)
            path = None
            # if file exists
            if os.path.isfile(_i):
                _ = unarchiver.unzip_file(_i, _o)
                if _:
                    path = _['final_path']
                else:
                    tqdm.write('❌ unzip failed: '+_i)

            else:
                tqdm.write(f'❌ zip file for {item} not found: '+_i)

            if path is None:
                files = []
            else:
                files = with_extensios(path, exts)
                # read already-indexed files from db.
                indexed = []
                for row in cursor.execute('SELECT path FROM files WHERE repo = ?', (item,)):
                    indexed.append(row[0])
                # remove already-indexed files
                files = [f for f in files if os.path.relpath(
                    f, path) not in indexed]

            for _f in files:
                relpath = os.path.relpath(_f, path)
                lang = Path(_f).suffix.split('.')[-1]
                # index files to sqlite db
                if os.path.isfile(_f):
                    with open(_f, 'r') as f:
                        try:
                            content = f.read()
                            # columns: repo, path, content
                            # insert if not exists
                            cursor.execute(
                                'INSERT OR IGNORE INTO files VALUES (?, ?, ?, ?)', (item, relpath, content, lang))
                            tqdm.write(f'✅ {item} {relpath}')
                            db.commit()
                        except UnicodeDecodeError as e:
                            tqdm.write(
                                f'skipping (decode error): {item} {relpath}')
                            pass

            progress.update(1)

    except KeyboardInterrupt as e:
        # clear temp dir
        shutil.rmtree(TMPDIR)
        # close db
        db.close()
        exit()
