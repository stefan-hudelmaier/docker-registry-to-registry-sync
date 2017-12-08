import yaml
import docker
from docker_registry_client._BaseClient import BaseClientV2 as RegistryClient


def get_all_images(registry_url, client, names):

    images = []
    for name in names:
        print(">>>" + registry_url + '/' + name)
        images += client.images.list(name=registry_url + '/' + name)

    return images


def get_tags(images):

    tags = []
    for image in images:
        tags.append(image.tags)

    return tags


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

    import sys
    sys.exit(0)

    with open('config.yml') as f:
        config = yaml.load(f)

    src_client = docker.from_env()
    dst_client = docker.from_env()
    src_registry_url = config['source_registry']['url']
    dst_registry_url = config['target_registry']['url']

    src_client.login(registry=src_registry_url, username=str(config['source_registry']['username']),
                     password=str(config['source_registry']['password']))

    dst_client.login(registry=dst_registry_url, username=str(config['target_registry']['username']),
                     password=str(config['target_registry']['password']))

    images_names = [image['name'] for image in config['images']]
    src_images = get_all_images(src_registry_url, src_client, images_names)
    dst_images = get_all_images(dst_registry_url, dst_client, images_names)

    for dst_image in dst_images:
        for dst_tag in dst_image.tags:
            if dst_tag.startswith(src_registry_url + '/'):
                print("Removing destination tag %s from local host" % dst_tag)
                dst_client.images.remove(dst_tag, noprune=True)

    dst_images = get_all_images(dst_registry_url, dst_client, images_names)
    print(src_images)
    print(dst_images)

    src_tags = get_tags_without_registry(src_registry_url, src_images)
    dst_tags = get_tags_without_registry(dst_registry_url, dst_images)

    missing_tags = src_tags - dst_tags
    print(missing_tags)

    for missing_tag in missing_tags:
        src_tag = src_registry_url + '/' + missing_tag
        dst_tag = dst_registry_url + '/' + missing_tag

        print("Changing %s to %s" % (src_tag, dst_tag,))

        src_image = src_client.images.get(name=src_tag)
        src_image.tag(dst_tag)

        print(dst_tag)
        dst_client.images.push(dst_tag)
