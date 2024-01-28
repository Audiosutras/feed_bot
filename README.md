# Feed Bot

### Environment Variables

Add `BOT_TOKEN` environment variable. You can get this token [here](https://discord.com/developers/applications/1198387310014767104/information)


Make sure to enable the `Message Content` intent for the bot whose token you are using.

### Development

1. Within a Docker Container
Make sure that you have Docker installed. After cloning the repository run:
```bash
$ sudo docker compose watch
```

This project features hot-reloading of the container (syncing/restarting) when changes are made to the `feed_bot` directory and packages are added to `pyproject.toml`.

To view logs in a different terminal instance run
```bash
$ sudo docker compose logs --follow bot
```

To stop the container and remove persisting volumes
```
$ sudo docker compose down -v
```

2. Local Machine Development
*TO DO*
### Deployment

This project utilizes [Github Actions](https://docs.github.com/en/packages/managing-github-packages-using-github-actions-workflows/publishing-and-installing-a-package-with-github-actions#publishing-a-package-using-an-action) for deploying a production ready docker container to the github container registry. For more information see [working with the container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

To push a new container to github packages merge code from `main` into into the `release` branch.

### Production

**Make sure** you have added your [Bot token](#environment-variables)

Make sure that you have docker installed. You can either create a file called `compose-prod.yaml` and copy the contents of the `compose-prod.yaml` file that you see in this repository or copy the repository.

Run
```
$ docker compose -f compose-prod.yaml up -d
```
This will start `Feed Bot`.
