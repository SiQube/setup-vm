from __future__ import annotations

import argparse
import os
import pwd
import shutil
import subprocess
from typing import NamedTuple

import yaml


USER_NAME = pwd.getpwuid(os.getuid()).pw_name
USER_HOME = f'/home/{USER_NAME}'


def _print_line(s: str) -> None:
    print(79*'=')
    print(s.center(79))
    print(79*'=', flush=True, end='\n\n')


def _preprocess_cmd_and_print(
        cmd: str | tuple[str, ...],
) -> tuple[tuple[str, ...], str | None]:
    if isinstance(cmd, str):
        print_string = cmd
        tuplified_cmd = cmd,
        return tuplified_cmd, print_string
    else:
        print_string = ' '.join(cmd)
        return cmd, print_string


def _sudo_apt_install(cmd: str | tuple[str, ...]) -> None:
    _cmd, print_cmd = _preprocess_cmd_and_print(cmd)
    _print_line(f'sudo apt install {print_cmd}')
    subprocess.run(('sudo', 'apt', 'install', *_cmd, '-y'))


def _sudo_bash_cmd(cmd: str) -> None:
    _print_line(f'bash {cmd}')
    subprocess.run(('bash', cmd))


class Repo(NamedTuple):
    owner: str
    repo: str
    destination: str | None = None

    def __str__(self) -> str:
        return f'{self.owner}/{self.repo}'

    @property
    def get_clone_cmd(self) -> tuple[str, ...]:
        if self.destination:
            return 'git', 'clone', f'git@github.com:{self}', self.destination
        return 'git', 'clone', f'git@github.com:{self}'

    @property
    def _get_print_line(self) -> str:
        if self.destination:
            print_line = f'cloning repo {self} to {self.destination}'
        else:
            print_line = f'cloning repo {self}'
        return print_line


def _clone_github_repo(repo: Repo) -> None:
    _print_line(repo._get_print_line)
    subprocess.run(args=repo.get_clone_cmd)


def _move_file(origin: str, destination: str) -> None:
    _print_line(f'moving from {origin} to {destination}')
    shutil.move(origin, destination)


def _delete_directory(directory: str) -> None:
    _print_line(f'deleting {directory=}')
    shutil.rmtree(directory)


def _delete_file(file: str) -> None:
    _print_line(f'deleting {file=}')
    os.remove(file)


def _run_python(cmd: str | tuple[str, ...], cwd: str | None = None) -> None:
    _cmd, print_cmd = _preprocess_cmd_and_print(cmd)
    _print_line(f'running python3 {print_cmd}')

    subprocess.run(('python3', *_cmd), cwd=cwd)


def _execute_cmd(cmd: str | tuple[str, ...], cwd: str | None = None) -> None:
    _cmd, print_cmd = _preprocess_cmd_and_print(cmd)
    _print_line(f'execute cmd: {print_cmd}')
    subprocess.run(args=_cmd, cwd=cwd)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--install-guest-edition',
        '-i',
        action='store_true',
    )
    parser.add_argument('--testing', action='store_true')
    parser.add_argument('--clean-up', action='store_true')
    args = parser.parse_args()

    if args.clean_up:
        _delete_file(f'{USER_HOME}/.vimrc_cl_install')
        _delete_file(f'{USER_HOME}/.vimrc')
        _delete_directory(f'{USER_HOME}/opt')
        _delete_file('/tmp/virtualenv.pyz')
        _execute_cmd(('sudo', 'rm', '/bin/virtualenv'))
        _execute_cmd(('sudo', 'rm', '-rf', f'{USER_HOME}/.vim'))

    # update apt
    _execute_cmd(('sudo', 'apt', 'upgrade', '-y'))
    _execute_cmd(('sudo', 'apt', 'update', '-y'))

    # setup git
    _execute_cmd(('git', 'config', '--global', 'user.name', '"SiQube"'))
    _execute_cmd(
        (
            'git',
            'config',
            '--global',
            'user.email',
            '"reich.davidr@gmail.com"',
        ),
    )

    # get vim
    _sudo_apt_install('vim')
    _clone_github_repo(Repo('siqube', 'scratch'))
    _move_file('scratch/.vimrc_cl_install', USER_HOME)
    # setup youcompleteme
    _execute_cmd(
        (
            'mkdir',
            '-p',
            '/etc/apt/keyrings',
        ),
    )
    _sudo_apt_install('cmake')
    _sudo_apt_install('mono-complete')
    _sudo_apt_install('golang')
    _sudo_apt_install('nodejs')
    _sudo_apt_install('openjdk-17-jdk')
    _sudo_apt_install('openjdk-17-jre')
    _sudo_apt_install('npm')
    _execute_cmd(('sudo', 'mkdir', '-p', f'{USER_HOME}/.vim/bundle'))
    _execute_cmd(('sudo', 'chmod', '777', f'{USER_HOME}/.vim'))
    _execute_cmd(('sudo', 'chmod', '777', f'{USER_HOME}/.vim/bundle'))
    _clone_github_repo(
        Repo(
            'ycm-core',
            'YouCompleteMe',
            f'{USER_HOME}/.vim/bundle/YouCompleteMe',
        ),
    )
    _execute_cmd(
        (
            'git',
            'submodule',
            'update',
            '--init',
            '--recursive',
        ),
        cwd=f'{USER_HOME}/.vim/bundle/YouCompleteMe',
    )
    _sudo_apt_install('python3-dev')
    _run_python(
        ('install.py', '--all'),
        f'{USER_HOME}/.vim/bundle/YouCompleteMe',
    )

    _clone_github_repo(
        Repo('VundleVim', 'Vundle.vim', f'{USER_HOME}/.vim/bundle/Vundle.vim'),
    )
    _execute_cmd(
        (
            'vim',
            '-u',
            f'{USER_HOME}/.vimrc_cl_install',
            '+PluginInstall',
            '+qall',
        ),
    )
    _move_file('scratch/.vimrc', USER_HOME)
    _execute_cmd(('vim', f'{USER_HOME}/.vimrc', '+PluginInstall', '+qall'))
    _delete_directory('scratch')
    if args.testing:
        _execute_cmd(('sudo', 'rm', '-rf', f'{USER_HOME}/.vim'))
        _delete_file(f'{USER_HOME}/.vimrc')

    # basic apt packages I need
    _sudo_apt_install('perl')
    _sudo_apt_install('make')
    _sudo_apt_install('gcc')
    _sudo_apt_install('bzip2')
    _sudo_apt_install('curl')
    _sudo_apt_install('build-essential')

    # setup virtualenv
    _execute_cmd(
        (
            'curl',
            '--location',
            '--output',
            '/tmp/virtualenv.pyz',
            'https://bootstrap.pypa.io/virtualenv.pyz',
        ),
    )
    _run_python(('/tmp/virtualenv.pyz', f'{USER_HOME}/opt/venv'))
    _execute_cmd((f'{USER_HOME}/opt/venv/bin/pip', 'install', 'virtualenv'))
    _execute_cmd(
        (
            'sudo',
            'ln',
            '-s',
            f'{USER_HOME}/opt/venv/bin/virtualenv',
            '/bin/virtualenv',
        ),
    )

    if args.testing:
        _delete_directory(f'{USER_HOME}/opt')
        _delete_file('/tmp/virtualenv.pyz')
        _execute_cmd(
            (
                'sudo',
                'rm',
                '/bin/virtualenv',
            ),
        )

    # install python versions
    _sudo_apt_install('software-properties-common')
    _execute_cmd(('sudo', 'add-apt-repository', 'ppa:deadsnakes/ppa', '-y'))
    with open('python_versions.yaml') as yaml_file:
        python_versions = yaml.safe_load(yaml_file)
    for python_version in python_versions:
        _sudo_apt_install(f'python{python_version}')

    if args.install_guest_edition:
        # install guess edition
        _sudo_bash_cmd(f'/media/{USER_NAME}/VBox_GAs_7.0.12/autorun.sh')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
