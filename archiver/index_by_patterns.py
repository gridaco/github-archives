import click
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
import utils.patterns

__DIR = pathlib.Path(__file__).parent.absolute()
__DSDIR = os.path.join(__DIR, 'samples/s')  # default
__DBPATH = os.path.join(__DIR, 'samples/s.db')  # default

TMPDIR = os.path.join(tempfile.gettempdir(), 'public-github-archives/index')


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


def with_patterns(path, patterns):
    files = []
    for p in patterns:
        files += glob.glob(path+'/**/'+p, recursive=True)
    return files


@click.command()
@click.option('--dir', help='source archives directory', type=click.Path(exists=True))
@click.option('--db', 'dbfile', help='db file path', type=click.Path())
@click.option('--patterns', 'patternsfile', default=None, help='file path for line splitted list of patterns to match - e.g. .gitignore', type=click.Path(exists=True))
def main(dir, dbfile, patternsfile):
    patterns = utils.patterns.read_patterns(patternsfile)
    samples = github_archives_index.Indexer(dir)
    repos = samples.read_index()
    db, cursor = initdb(dbfile)
    total = len(repos)

    progress = tqdm(total=total, desc='indexing')

    # iterate over repos
    for item in repos:
        tqdm.write('👇 '+item)
        # unzip
        _i = os.path.join(dir, item+'.zip')
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
            files = with_patterns(path, patterns)
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
    # close db
    db.close()


def clean():
    # clear temp dir
    shutil.rmtree(TMPDIR)


# python index_by_patterns.py --patterns="./patterns/react.include" --dir="./samples/s" --db="./samples/s.db"
if __name__ == "__main__":
    try:
        main()
        clean()

    except KeyboardInterrupt as e:
        clean()
        exit()
