# <プロジェクト名>

これは uv を用いた Python プロジェクトのテンプレートリポジトリです.


## 開発環境の構築

### 仮想環境の有効化と無効化

```zsh
# プロジェクトの backend ディレクトリで以下を実行
$ uv sync
```

### Formatter, Linter の適用

```zsh
# formatter の適用
$ make fmt

# linter の適用
$ make lint
```

### Test と Coverage の取得

```zsh
# test
$ make test

# coverage の取得
$ make coverage

# coverage の可視化
$ make vis_coverage
```
