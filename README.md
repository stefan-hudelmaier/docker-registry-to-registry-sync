# docker-registry-to-registry-sync
Project for syncing images from one registry to another

## Goal

Make is possible to sync all tags of a number of docker repositories
from one registry to another. Can be useful if you have an interal docker
registry but want to sync a subset of the docker images to a public registry
(e.g. Docker Hub).

## Usage

### Configuration

Create a `config.yml` file. Example:

```yaml
source_registry:
  url: https://docker.example.com
  username: some_user
  password: some_password

destination_registry:
  url: http://127.0.0.1:5000

repositories:
  - company/super-project
  - company/cool-project

```

The meaning of the settings:

* `source-registry`: The registry to sync from
* `destination-registry`: The registry to sync to
* `repositories`: A list of docker repositores, consisting of the repository name
  and image name (without the registry part).
  
When the images are synced, the registry part of the tag is replaced, e.g.
in the example above the tag `docker.example.com/company/super-project` is
re-tagged as `127.0.0.1:5000/company/super-project` and pushed to `127.0.0.1:5000`.

### Passwords as environment variables

You can specify the registry passwords using the `SOURCE_REGISTRY_PASSWORD` 
and `DESTINATION_REGISTRY_PASSWORD` environment variables instead of 
including them in the `config.yml` file.

### Execution via docker:

```
docker --rm -it \
    -v $(pwd)/config.yml:/config.yml \
    stefanhudelmaier/docker-registry-to-registry-sync
```

When using environment variables for the passwords:
```
docker --rm -it \
    -e SOURCE_REGISTRY_PASSWORD=secret \
    -e DESTINATION_REGISTRY_PASSWORD=secret \
    -v $(pwd)/config.yml:/config.yml \
    stefanhudelmaier/docker-registry-to-registry-sync
```

