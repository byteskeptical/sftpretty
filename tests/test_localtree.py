'''test sftpretty.helpers.localtree'''

import pytest

from blddirs import build_dir_struct
from pathlib import Path
from sftpretty.helpers import localtree
from sys import getrecursionlimit


def test_localtree(tmp_path):
    '''test the localtree function, with recurse'''
    build_dir_struct(tmp_path.as_posix())
    container = {}
    local = tmp_path.joinpath('pub').as_posix()

    localtree(container, local, '/remote')

    expected = {
        local: [(f'{local}/foo1', '/remote/pub'),
                (f'{local}/foo2', '/remote/pub')],
        f'{local}/foo2': [(f'{local}/foo2/bar1', '/remote/pub/foo2')]
    }

    assert container.keys() == expected.keys()
    for branch in expected:
        assert set(container[branch]) == set(expected[branch])


def test_localtree_deep(tmp_path):
    '''test a tree deeper than the recursion limit is mapped'''
    container = {}
    levels = getrecursionlimit() + 100
    local = tmp_path.joinpath('deep')
    local.mkdir()

    branch = local
    try:
        for _ in range(levels):
            try:
                branch.joinpath('d').mkdir()
            except OSError:
                pytest.skip('platform path limit reached')
            branch = branch.joinpath('d')

        localtree(container, local.as_posix(), '/remote')

        assert len(container) == levels
    finally:
        while branch != local:
            branch.rmdir()
            branch = branch.parent


def test_localtree_hidden(tmp_path):
    '''test dot directories are mapped'''
    build_dir_struct(tmp_path.as_posix())
    container = {}
    local = tmp_path.joinpath('pub').as_posix()
    tmp_path.joinpath('pub', '.hidden').mkdir()

    localtree(container, local, '/remote', recurse=False)

    assert (f'{local}/.hidden', '/remote/pub') in container[local]


def test_localtree_leaf(tmp_path):
    '''test a directory holding no sub-directories creates no key'''
    build_dir_struct(tmp_path.as_posix())
    container = {}

    localtree(container, tmp_path.joinpath('pub', 'foo1').as_posix(),
              '/remote')

    assert container == {}


def test_localtree_missing(tmp_path):
    '''test a local directory that does not exist raises'''
    with pytest.raises(FileNotFoundError):
        localtree({}, tmp_path.joinpath('nonesuch').as_posix(), '/remote')


def test_localtree_no_recurse(tmp_path):
    '''test only the first level is mapped without recursing'''
    build_dir_struct(tmp_path.as_posix())
    container = {}
    local = tmp_path.joinpath('pub').as_posix()

    localtree(container, local, '/remote', recurse=False)

    assert container.keys() == {local}
    assert set(container[local]) == {(f'{local}/foo1', '/remote/pub'),
                                     (f'{local}/foo2', '/remote/pub')}


def test_localtree_notadirectory(tempfile_containing):
    '''test a file in place of a local directory raises'''
    with pytest.raises(NotADirectoryError):
        localtree({}, tempfile_containing(contents='eels'), '/remote')


def test_localtree_parents_first(tmp_path):
    '''test a branch is always mapped before any of its children'''
    build_dir_struct(tmp_path.as_posix())
    container = {}
    tmp_path.joinpath('pub', 'foo2', 'bar1', 'baz1').mkdir()

    localtree(container, tmp_path.joinpath('pub').as_posix(), '/remote')

    branches = list(container)
    for index, branch in enumerate(branches):
        parents = [parent for parent in branches
                   if branch.startswith(f'{parent}/')]

        assert all(branches.index(parent) < index for parent in parents)


def test_localtree_put_d_contract(tmp_path):
    '''test the directory name appended to its remote is the final path'''
    build_dir_struct(tmp_path.as_posix())
    container = {}

    localtree(container, tmp_path.joinpath('pub').as_posix(), '/remote')

    for branch in container.values():
        for path, remote in branch:
            relative = Path(path).relative_to(tmp_path).as_posix()

            assert f'{remote}/{Path(path).name}' == f'/remote/{relative}'


def test_localtree_relative(tmp_path, monkeypatch):
    '''test a relative localdir descends the working directory'''
    build_dir_struct(tmp_path.as_posix())
    container = {}
    monkeypatch.chdir(tmp_path.joinpath('pub'))

    localtree(container, '.', '/remote', recurse=False)

    assert container.keys() == {Path.cwd().as_posix()}


@pytest.mark.parametrize('remotedir, expected', (
    ('/', '/pub'),
    ('/remote', '/remote/pub'),
    ('/remote/', '/remote/pub')),
    ids=('root', 'plain', 'trailing'))
def test_localtree_remotedir(remotedir, expected, tmp_path):
    '''test remote roots join without doubling the separator'''
    build_dir_struct(tmp_path.as_posix())
    container = {}
    local = tmp_path.joinpath('pub').as_posix()

    localtree(container, local, remotedir, recurse=False)

    assert {remote for _, remote in container[local]} == {expected}


def test_localtree_seeded(tmp_path):
    '''test a container seeded by put_r is extended, not replaced'''
    build_dir_struct(tmp_path.as_posix())
    local = tmp_path.joinpath('pub').as_posix()
    container = {local: [(local, '/remote')]}

    localtree(container, local, '/remote')

    assert (local, '/remote') in container[local]
    assert len(container[local]) == 3


def test_localtree_symlink(tmp_path):
    '''test a link pointing outside the tree is followed'''
    build_dir_struct(tmp_path.as_posix())
    container = {}
    local = tmp_path.joinpath('pub').as_posix()
    tmp_path.joinpath('outside', 'deep').mkdir(parents=True)
    tmp_path.joinpath('pub', 'link').symlink_to(
        tmp_path.joinpath('outside'), target_is_directory=True)

    localtree(container, local, '/remote')

    assert (f'{local}/link', '/remote/pub') in container[local]
    assert (f'{local}/link/deep',
            '/remote/pub/link') in container[f'{local}/link']


def test_localtree_symlink_dangling(tmp_path):
    '''test a link with no target is skipped'''
    build_dir_struct(tmp_path.as_posix())
    container = {}
    local = tmp_path.joinpath('pub').as_posix()
    gone = tmp_path.joinpath('pub', 'nonesuch')
    gone.mkdir()
    tmp_path.joinpath('pub', 'gone').symlink_to(gone,
                                                target_is_directory=True)
    gone.rmdir()

    localtree(container, local, '/remote', recurse=False)

    assert f'{local}/gone' not in [path for path, _ in container[local]]


def test_localtree_symlink_duplicate(tmp_path):
    '''test the same target is only followed once'''
    build_dir_struct(tmp_path.as_posix())
    container = {}
    local = tmp_path.joinpath('pub').as_posix()
    for link in ('one', 'two'):
        tmp_path.joinpath('pub', link).symlink_to(
            tmp_path.joinpath('pub', 'foo1'), target_is_directory=True)

    localtree(container, local, '/remote')

    assert len([path for path, _ in container[local]
                if path.endswith(('/one', '/two'))]) == 1


def test_localtree_symlink_loop(tmp_path):
    '''test a link to its own parent is never descended'''
    build_dir_struct(tmp_path.as_posix())
    container = {}
    local = tmp_path.joinpath('pub').as_posix()
    tmp_path.joinpath('pub', 'cycle').symlink_to(
        tmp_path.joinpath('pub'), target_is_directory=True)

    localtree(container, local, '/remote')

    assert f'{local}/cycle' not in [path for path, _ in container[local]]
    assert container.keys() == {local, f'{local}/foo2'}


def test_localtree_trailing_slash(tmp_path):
    '''test a trailing separator on localdir is absorbed'''
    build_dir_struct(tmp_path.as_posix())
    container = {}
    local = tmp_path.joinpath('pub').as_posix()

    localtree(container, f'{local}/', '/remote', recurse=False)

    assert container.keys() == {local}


def test_localtree_unsupported(tmp_path):
    '''test a non string localdir raises'''
    with pytest.raises(AttributeError):
        localtree({}, tmp_path, '/remote')
