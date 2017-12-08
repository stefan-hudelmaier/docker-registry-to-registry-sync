from urllib.parse import urlparse

import os
import yaml
import docker
from docker_registry_client import DockerRegistryClient
from requests import HTTPError


def get_tags(client, repositories):
    result = set()
    for repository in repositories:
        try:
            tags = client.repository(repository).tags()
        except HTTPError as e:
            if e.response.status_code == 404:
                print("repository %s not found" % repository)
                tags = []
            else:
                raise e

        for tag in tags:
            result.add(repository + ':' + tag)

    return result


def strip_scheme(url):
    parsed_url = urlparse(url)
    scheme = "%s://" % parsed_url.scheme
    return parsed_url.geturl().replace(scheme, '', 1)


def load_config():
    with open('config.yml') as f:
        return yaml.load(f)


def determine_password(config, kind):
    if kind == 'src':
        config_file_key = 'source_registry'
        env_var = 'SOURCE_REGISTRY_PASSWORD'
    elif kind == 'dst':
        config_file_key = 'destination_registry'
        env_var = 'DESTINATION_REGISTRY_PASSWORD'
    else:
        raise Exception("Invalid registry kind:", kind)

    config_file_password = config[config_file_key].get('password')
    if config_file_password is not None:
        return str(config_file_password)

    env_value = os.environ.get(env_var)

    if env_value is not None:
        print("Using password from environment variable", env_var)
        return env_value

    return None


if __name__ == '__main__':

    config = load_config()

    src_registry_url = config['source_registry']['url']
    dst_registry_url = config['destination_registry']['url']
    src_username = str(config['source_registry']['username'])
    src_password = determine_password(config, 'src')
    dst_username = str(config['destination_registry']['username'])
    dst_password = determine_password(config, 'dst')

    src_client = DockerRegistryClient(src_registry_url, username=src_username,
                                      password=src_password)

    dst_client = DockerRegistryClient(dst_registry_url, username=dst_username,
                                      password=dst_password)

    docker_client = docker.from_env()
    docker_client.login(registry=src_registry_url, username=src_username,
                        password=src_password)

    docker_client.login(registry=dst_registry_url, username=dst_username,
                        password=dst_password)

    repositories = config['repositories']
    src_tags = get_tags(src_client, repositories)
    dst_tags = get_tags(dst_client, repositories)

    missing_tags = src_tags - dst_tags

    for missing_tag in missing_tags:
        src_tag = strip_scheme(src_registry_url) + '/' + missing_tag
        dst_tag = strip_scheme(dst_registry_url) + '/' + missing_tag

        print("Pulling:", src_tag)
        docker_client.images.pull(src_tag)

        print("Changing %s to %s" % (src_tag, dst_tag,))

        src_image = docker_client.images.get(name=src_tag)
        src_image.tag(dst_tag)

        print("Pushing:", dst_tag)
        docker_client.images.push(dst_tag)
