from __future__ import division, print_function

import argparse
import json
import os

BASE_CONFIG_DIR = os.path.join('.', 'codegen')

GO_VERSION_FORMAT = '0.{0}{1:02d}.{2}'


def set_android_version(new_version, filename=os.path.join(BASE_CONFIG_DIR, 'config-android.json')):
    config = read_config(filename)
    config['artifactVersion'] = str.join('.', map(str, new_version))
    save_config(config, filename)


def set_go_version(new_version, filename=os.path.join(BASE_CONFIG_DIR, 'config-go.json')):
    go_version = GO_VERSION_FORMAT.format(*new_version)
    config = read_config(filename)
    config['packageVersion'] = go_version
    save_config(config, filename)


def set_java_version(new_version, filename=os.path.join(BASE_CONFIG_DIR, 'config-java.json')):
    config = read_config(filename)
    config['artifactVersion'] = str.join('.', map(str, new_version))
    save_config(config, filename)


def set_net_version(new_version, filename=os.path.join(BASE_CONFIG_DIR, 'config.json')):
    config = read_config(filename)
    config['packageVersion'] = str.join('.', map(str, new_version))
    save_config(config, filename)


def set_node_version(new_version, filename=os.path.join(BASE_CONFIG_DIR, 'config.json')):
    config = read_config(filename)
    config['npmVersion'] = str.join('.', map(str, new_version))
    save_config(config, filename)


def set_php_version(new_version, filename=os.path.join(BASE_CONFIG_DIR, 'config.json')):
    config = read_config(filename)
    config['artifactVersion'] = str.join('.', map(str, new_version))
    save_config(config, filename)


def set_python_version(new_version, filename=os.path.join(BASE_CONFIG_DIR, 'config-python.json')):
    config = read_config(filename)
    config['packageVersion'] = str.join('.', map(str, new_version))
    save_config(config, filename)


def read_config(filename):
    with open(filename, 'rb') as rf:
        config = json.load(rf)
    return config


def save_config(config, filename):
    with open(filename, 'wb') as wf:
        json.dump(config, wf, indent=4, sort_keys=True)


def main(new_version):
    assert len(new_version) == 2
    new_version = tuple(new_version + [0])

    set_android_version(new_version)
    set_go_version(new_version)
    set_java_version(new_version)
    set_net_version(new_version)
    set_node_version(new_version)
    set_php_version(new_version)
    set_python_version(new_version)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('new_version', type=int, nargs=2)
    args = parser.parse_args()
    return vars(args)


if __name__ == '__main__':
    main(**parse_args())