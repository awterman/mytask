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
