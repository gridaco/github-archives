import click
from tqdm import tqdm
import glob
import shutil
import pathlib
import random
import math
import os
import os.path
import github_archives_index as indexer
import settings as settings

_DIR = pathlib.Path(__file__).parent.absolute()

# select random data from datasource, make a smaller sample for testing

DS_ORIGIN_DIR = settings.ARCHIVES_DIR
MAX_DEFAULT = 10000


def make_samples_list(origin_dir, max_count):

    # since the origin datasource is too large, we need to use index file to get the samples
    # list the repositories with MAX_SAMPLE_COUNT

    indexes = indexer.read_index_from_file(
        os.path.join(origin_dir, "index"))

    # select MAX_SAMPLE_COUNT from indexes randomly
    if max_count is math.inf or max_count is None or max_count >= len(indexes):
        targets = indexes
        random.shuffle(targets)
    else:
        targets = []
        _count = len(indexes)
        while len(targets) < max_count and len(targets) < _count:
            target = random.choice(indexes)
            if target not in targets:
                targets.append(target)
                indexes.remove(target)

    return targets


def cp(origin_dir, target_dir, repository, ext="zip"):
    try:
        # copy the repository from origin_dir to target_dir
        _org = repository.split("/")[0]
        _repo = repository.split("/")[1]
        filename = _repo+"."+ext
        origin_path = os.path.join(origin_dir, _org, filename)
        target_path = os.path.join(target_dir, _org, filename)
        if not os.path.exists(os.path.join(target_dir, _org)):
            os.makedirs(os.path.join(target_dir, _org))
        shutil.copy(origin_path, target_path)

        # get the size of the file
        size = os.path.getsize(target_path)
        return size
    except Exception as e:
        return 0


def clear_dir(target_dir):
    # remove all directories and files under target_dir (if exists)
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)


@click.command()
@click.option('--target', default='~/data/github-public-archives/samples', help='target sample dir')
@click.option('--max-mb', type=click.INT, default=50 * 1024, help='max sample size in MB')
@click.option('--max-count', type=click.INT, default=None, help='max sample count (number of repos)')
@click.option('--clear', type=click.BOOL, default=False, help='rather to clear the target dir before sampling')
def main(target, max_mb, max_count, clear):
    if clear:
        clear_dir(target)

    targets = make_samples_list(DS_ORIGIN_DIR, max_count)
    print("selected %d repositories" % len(targets))

    # if target dir not exists, create it
    if not os.path.exists(target):
        os.makedirs(target)

    samples_indexer = indexer.Indexer(target)

    progress_bar = tqdm(total=max_mb * 1024 * 1024,
                        unit='iB', unit_scale=True, leave=True)

    cpdsize = 0
    while cpdsize < max_mb * 1024 * 1024 and len(targets) > 0:
        repo = random.choice(targets)
        targets.remove(repo)
        size = cp(DS_ORIGIN_DIR, target, repo)
        samples_indexer.add(repo)
        cpdsize += size
        progress_bar.update(size)


if __name__ == "__main__":
    main()
    pass
