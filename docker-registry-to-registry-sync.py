import yaml
import docker
from docker_registry_client._BaseClient import BaseClientV2 as RegistryClient
from requests import HTTPError


def get_all_images(registry_url, client, names):
    images = []
    for name in names:
        print(">>>" + registry_url + '/' + name)
        images += client.images.list(name=registry_url + '/' + name)

    return images


def get_tags(client, image_names):
    result = set()
    for image_name in image_names:
        try:
            tags = client.get_repository_tags(name=image_name)['tags']
        except HTTPError as e:
            if e.response.status_code == 404:
                print("image %s not found" % image_name)
                tags = []
            else:
                raise e

        for tag in tags:
            result.add(image_name + ':' + tag)

    return result


def get_tags_without_registry(registry_url, images):
    result = set()

    for tags in [image.tags for image in images]:
        for tag in tags:
            tag_parts = tag.split('/')

            if len(tag_parts) != 3:
                print("Tag %s does not consist of 3 parts, skipping" % tag)
                continue

            if tag_parts[0] != registry_url:
                print("Tag %s does not belong to registry %s, skipping" % (tag, registry_url,))
                continue

            result.add('/'.join(tag_parts[1:]))

    return result


if __name__ == '__main__':

    with open('config.yml') as f:
        config = yaml.load(f)

    src_registry_url = config['source_registry']['url']
    dst_registry_url = config['target_registry']['url']
    src_client = RegistryClient(src_registry_url, username=str(config['source_registry']['username']),
                                password=str(config['source_registry']['password']))

    dst_client = RegistryClient(dst_registry_url, username=str(config['source_registry']['username']),
                                password=str(config['source_registry']['password']))

    images_names = [image['name'] for image in config['images']]
    src_tags = get_tags(src_client, images_names)
    dst_tags = get_tags(dst_client, images_names)

    print(src_tags)
    print(dst_tags)

    missing_tags = src_tags - dst_tags
    print(missing_tags)

    import sys
    sys.exit(0)

    for missing_tag in missing_tags:
        src_tag = src_registry_url + '/' + missing_tag
        dst_tag = dst_registry_url + '/' + missing_tag

        print("Changing %s to %s" % (src_tag, dst_tag,))

        src_image = src_client.images.get(name=src_tag)
        src_image.tag(dst_tag)

        print(dst_tag)
        dst_client.images.push(dst_tag)
