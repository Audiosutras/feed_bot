# Feed Bot

A discord bot for emulating an rss feed reader within your guild channels
---
### Table of Contents
- #### [Environment Variables](#environment-variables)
- #### [Development](#development)
- #### [Deployment](#deployment)
- #### [Production](#production)

### Environment Variables

Add `BOT_TOKEN` environment variable. You can get this token [here](https://discord.com/developers/applications/1198387310014767104/information)


Make sure to enable the `Message Content` intent for the bot whose token you are using.

### Development

#### Running the project is done within a Docker Container
If you are on linux make sure to check out the [linux post-install](https://docs.docker.com/engine/install/linux-postinstall/) section in the docker docs to giver your user permissions

```bash
$ sudo groupadd docker
$ sudo usermod -aG docker $USER
# close and re-open terminal
$ newgrp docker
```
Now that your user has permissions and you have cloned the repository you can run:

```bash
$ docker compose watch
```

This project features hot-reloading of the container (syncing/restarting) when changes are made to the `feed_bot` directory and packages are added to `pyproject.toml`.

To view logs in a different terminal instance run
```bash
$ docker compose logs --follow bot
```

To stop the container and remove persisting volumes
```bash
$ docker compose down -v
```

### Outside of the container

Open a `terminal` instance and `cd` into the project's root directory.

Configure `pre-commit`` for linting and style guide coverage. Run:
```bash
$ pre-commit install
```

To add a python package run:
```bash
$ poetry add <pypi_package>
```

You may need to install the project locally first with [poetry](https://python-poetry.org/)
```bash
$ poetry install
```

### Deployment
This project utilizes [Github Actions](https://docs.github.com/en/packages/managing-github-packages-using-github-actions-workflows/publishing-and-installing-a-package-with-github-actions#publishing-a-package-using-an-action) for deploying a production ready docker container to the github container registry. For more information see [working with the container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

To push a new container image to github packages create a `release` from the `main` branch with a specified [git tag](https://git-scm.com/book/en/v2/Git-Basics-Tagging). The git tag should be labelled with a version number such as [1.2.3](https://github.com/docker/metadata-action?tab=readme-ov-file#tags-input).

```bash
(main branch) $ git tag 1.2.3
(main branch) $ git tag push 1.2.3
(main branch) $ gh release create
```

### Production

Make sure that you have docker installed. You can either create a file called `compose-prod.yaml` and copy the contents of the `compose-prod.yaml` file that you see in this repository or copy the repository.

Run
```bash
$ docker compose -f compose-prod.yaml up -d
```
This will start `Feed Bot`.

**Make sure** you have added your [Bot token](#environment-variables)
