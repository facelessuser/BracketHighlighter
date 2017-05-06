"""Spell check with aspell."""
from __future__ import unicode_literals
import subprocess
import os
import sys
import yaml
import codecs

PY3 = sys.version_info >= (3, 0)

USER_DICT = '.dictionary'
BUILD_DIR = os.path.join('.', 'build', 'docs')
MKDOCS_CFG = 'mkdocs.yml'
COMPILED_DICT = os.path.join(BUILD_DIR, 'dictionary.bin')
MKDOCS_SPELL = os.path.join(BUILD_DIR, MKDOCS_CFG)
MKDOCS_BUILD = os.path.join(BUILD_DIR, 'site')


def console(cmd, input_file=None):
    """Call with arguments."""

    returncode = None
    output = None

    if sys.platform.startswith('win'):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        process = subprocess.Popen(
            cmd,
            startupinfo=startupinfo,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            shell=False
        )
    else:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            shell=False
        )

    if input_file is not None:
        with open(input_file, 'rb') as f:
            process.stdin.write(f.read())
    output = process.communicate()
    returncode = process.returncode

    assert returncode == 0, "Runtime Error: %s" % (
        output[0].rstrip().decode('utf-8') if PY3 else output[0]
    )

    return output[0].decode('utf-8') if PY3 else output[0]


def yaml_dump(data, stream=None, dumper=yaml.Dumper, **kwargs):
    """Special dumper wrapper to modify the yaml dumper."""

    class Dumper(dumper):
        """Custom dumper."""

    if not PY3:
        # Unicode
        Dumper.add_representer(
            unicode,  # noqa
            lambda dumper, value: dumper.represent_scalar(u'tag:yaml.org,2002:str', value)
        )

    return yaml.dump(data, stream, Dumper, **kwargs)


def yaml_load(source, loader=yaml.Loader):
    """
    Wrap PyYaml's loader so we can extend it to suit our needs.

    Load all strings as unicode: http://stackoverflow.com/a/2967461/3609487.
    """

    def construct_yaml_str(self, node):
        """Override the default string handling function to always return Unicode objects."""
        return self.construct_scalar(node)

    class Loader(loader):
        """Define a custom loader to leave the global loader unaltered."""

    # Attach our unicode constructor to our custom loader ensuring all strings
    # will be unicode on translation.
    Loader.add_constructor('tag:yaml.org,2002:str', construct_yaml_str)

    return yaml.load(source, Loader)


def patch_doc_config(config_file):
    """Patch the config file to wrap arithmatex with a tag aspell can ignore."""

    nospell = {
        'tex_inline_wrap': ['<nospell>\\(', '</nospell>\\)'],
        'tex_block_wrap': ['<nospell>\\[', '</nospell>\\]']
    }
    with open(config_file, 'rb') as f:
        config = yaml_load(f)

    index = 0
    for extension in config.get('markdown_extensions', []):
        if isinstance(extension, str if PY3 else unicode) and extension == 'pymdownx.arithmatex':  # noqa
            config['markdown_extensions'][index] = {'pymdownx.arithmatex': nospell}
            break
        elif isinstance(extension, dict) and 'pymdownx.arithmatex' in extension:
            extension['pymdownx.arithmatex'] = nospell
            break
        index += 1

    with codecs.open(MKDOCS_SPELL, "w", encoding="utf-8") as f:
        yaml_dump(
            config, f,
            width=None,
            indent=4,
            allow_unicode=True,
            default_flow_style=False
        )
    return MKDOCS_SPELL


def build_docs():
    """Build docs with MkDocs."""
    print('Building Docs...')
    print(
        console(
            [
                sys.executable,
                '-m', 'mkdocs', 'build', '--clean',
                '-d', MKDOCS_BUILD,
                '-f', patch_doc_config(MKDOCS_CFG)
            ]
        )
    )


def compile_dictionary():
    """Compile user dictionary."""
    if os.path.exists(COMPILED_DICT):
        os.remove(COMPILED_DICT)
    print("Compiling Custom Dictionary...")
    print(
        console(
            [
                'aspell',
                '--lang=en',
                '--encoding=utf-8',
                'create',
                'master',
                COMPILED_DICT
            ],
            USER_DICT
        )
    )


def check_spelling():
    """Check spelling."""
    print('Spell Checking...')

    fail = False

    for base, dirs, files in os.walk(MKDOCS_BUILD):
        # Remove child folders based on exclude rules
        for f in files:
            if f.endswith('.html'):
                file_name = os.path.join(base, f)
                wordlist = console(
                    [
                        'aspell',
                        'list',
                        '--lang=en',
                        '--mode=html',
                        '--encoding=utf-8',
                        '--add-html-skip=code',
                        '--add-html-skip=pre',
                        '--add-html-skip=nospell',
                        '--add-html-skip=nav',
                        '--add-html-skip=footer',
                        '--extra-dicts=%s' % COMPILED_DICT
                    ],
                    file_name
                )

                words = [w for w in sorted(set(wordlist.split('\n'))) if w]

                if words:
                    fail = True
                    print('Misspelled words in %s' % file_name)
                    print('-' * 80)
                    for word in words:
                        print(word)
                    print('-' * 80)
                    print('\n')
    return fail


def main():
    """Main."""
    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)
    build_docs()
    compile_dictionary()
    return check_spelling()


if __name__ == "__main__":
    sys.exit(main())
