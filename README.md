# Bittensor

## Wallet

### Install btcli

https://github.com/opentensor/btcli/tree/fe486075576e8c6bd1ed28783c7cfe893e340588?tab=readme-ov-file#install-on-macos-and-linux

### Wallet Commands

#### Create New Wallet

```bash
btcli create
```

#### Create Wallet from Mnemonic

```bash
btcli wallet regen-coldkey --mnemonic "word1 word2 ... word12" --wallet-name some_name --network test
```

#### Transfer Balance

```bash
btcli wallet transfer --dest 5Dp8... --amount 100 --wallet-name some_name --network test
```

# Project

## Setup

### Install Dependencies

```bash
uv sync
```

### Install Project

```
uv pip install -e .
```

## Local Development

Copy `.env.example` to `.env` and set the environment variables.

### Run Project

```
uv run uvicorn mytask.main:app --reload
```

### Run Celery Worker

```
celery -A mytask.workers.celery worker --loglevel=info
```

## Build Docker Image

- Copy `.env.example` to `.env.docker` and set the environment variables.
- Setup a Bittensor wallet at 

```
docker compose up --build
```