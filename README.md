# Feed Bot

A discord bot for emulating an rss feed reader within your guild channels

[Discord Developer Portal](https://discord.com/developers/applications)
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

### Digital Ocean Droplet (Optional) Production Environment

**Click the badge below to get $200 in credit over 60 days on your Digital Ocean Account:**
[![DigitalOcean Referral Badge](https://web-platforms.sfo2.cdn.digitaloceanspaces.com/WWW/Badge%201.svg)](https://www.digitalocean.com/?refcode=9aa3573418e4&utm_campaign=Referral_Invite&utm_medium=Referral_Program&utm_source=badge)

#### Create The Droplet

After signing up and creating a new project called `Discord Feed Bot`, click the green `Create+` icon and select `DROPLET`. *A droplet is virtual machine that will act as your remote server. Its Digital Ocean's equivalent of an AWS EC2 instance.*

1) Under `Choose Region` select the region for your droplet. Try to choose the region closest to your end users.
2) Scroll down, leave `Ubuntu` as the default `OS`, `Basic` as the default `Droplet Size`
3) Select `Regular` for `CPU options` and select the `$6/mo` option.
4) Decide on whether you want to have droplet backups and choose your authentication method for interacting with the droplet. Finish enabling recommended/optional resources as your scroll to the bottom of the page. Once happy click `Create Droplet` when it is no longer disabled.

#### Configure DOCTL CLI Tool

Now lets interact with [the droplet from the command line using doctl](https://docs.digitalocean.com/reference/doctl/how-to/install/). Follow the steps outlined in the article before continuing. For `Step 4: Validate that doctl is working` run:
```bash
$ doctl compute droplet ls
```
You should see the name of your droplet under `Name`.

#### SSH Into Droplet

Now lets ssh into the droplet and get the bot up and running:
```bash
$ doctl compute ssh <droplet-id|name>
root@<name>:~#
```

The snap package manager comes pre-installed on the virtual machine for ubuntu. To install docker run:
```bash
root@<name>:~# apt install docker.io docker-compose
```

Download the latest versioned release. As of typing that is `0.1.3`.
```bash
root@<name>:~# curl -L https://github.com/Audiosutras/feed_bot/archive/refs/tags/0.1.3.tar.gz -o feed_bot_0.1.3.tar.gz
root@<name>:~# tar -xvzf feed_bot_0.1.3.tar.gz
```

Add our `BOT_TOKEN` to an `.env` file in the `feed_bot-0.1.3` directory
```bash
root@<name>:~# cd feed_bot-0.1.3
root@<name>:~# echo "BOT_TOKEN=<discord_bot_token>" >> .env
```

Start `Feed Bot`:
```bash
root@<name>:~# docker-compose -f compose-prod.yaml up -d
```
