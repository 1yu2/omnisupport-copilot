# OrbStack 外置硬盘本地运行手册

本文档记录当前机器上运行 OmniSupport Copilot 的本地配置：项目从外置硬盘启动，并尽量把项目持久化数据放到外置硬盘，减少系统内部磁盘占用。

## 当前目录布局

项目路径：

```bash
/Volumes/Move/omnisupport-copilot
```

本机专用运行文件：

```bash
infra/env/.env.local
.docker/compose/local-storage.yml
.docker/compose/registry-mirror.yml
.docker/volumes/
```

这些文件和目录属于本机运行状态，不是通用业务代码。当前仓库已有 `.env.*` 和 `.docker/` 忽略规则，所以它们不会进入 git；本文档本身会被 git 追踪。

## 哪些数据在外置硬盘上

`.docker/compose/local-storage.yml` 会把主要持久化服务数据绑定到外置硬盘：

```text
/Volumes/Move/omnisupport-copilot/.docker/volumes/postgres
/Volumes/Move/omnisupport-copilot/.docker/volumes/minio
/Volumes/Move/omnisupport-copilot/.docker/volumes/dagster
/Volumes/Move/omnisupport-copilot/.docker/volumes/phoenix
```

验证 Docker volume 是否确实绑定到了这些路径：

```bash
docker volume inspect infra_postgres_data infra_minio_data infra_dagster_data infra_phoenix_data
```

输出里的 `Options.device` 应该指向 `/Volumes/Move/omnisupport-copilot/.docker/volumes/...`。

查看外置硬盘上的项目运行数据占用：

```bash
cd /Volumes/Move/omnisupport-copilot
du -sh .docker .docker/volumes .docker/volumes/*
```

## 哪些内容仍然在 OrbStack 内部

Docker 镜像层、容器 writable layer、BuildKit 构建缓存仍然在 OrbStack 的 Docker 数据区里。项目级 compose bind mount 只能迁移服务数据，不能把这些 Docker 内部层自动迁到外置硬盘。

查看 Docker 内部占用：

```bash
docker system df
```

构建后减少系统内部磁盘占用：

```bash
docker builder prune -af
```

这个命令会删除未使用的构建缓存，不会删除正在运行的容器、服务镜像，也不会删除外置硬盘上的数据库和对象存储数据。代价是下次重新 build 会慢一些。

如果系统盘压力仍然很大，先列出镜像，再手动删除无关旧项目镜像：

```bash
docker image ls
docker image rm IMAGE_ID_OR_NAME
```

不要删除 OmniSupport 当前运行容器正在使用的镜像，除非你准备之后重新构建。

## 内存和磁盘的区别

外置硬盘能减少的是系统内部磁盘占用，主要是项目持久化数据。它不能减少 RAM 内存占用。

如果要减少 RAM 占用：

- 不使用时停止整套服务：

```bash
cd /Volumes/Move/omnisupport-copilot
docker compose --env-file infra/env/.env.local \
  -f infra/docker-compose.yml \
  -f .docker/compose/local-storage.yml \
  -f .docker/compose/registry-mirror.yml \
  down
```

- 不需要 UI 和观测服务时，只启动核心依赖和 API：

```bash
cd /Volumes/Move/omnisupport-copilot
docker compose --env-file infra/env/.env.local \
  -f infra/docker-compose.yml \
  -f .docker/compose/local-storage.yml \
  -f .docker/compose/registry-mirror.yml \
  up -d postgres minio minio_init rag_api tool_api
```

- 临时停掉较重的 UI / 可观测服务：

```bash
docker stop omni_dagster omni_phoenix omni_otel_collector
```

也可以在 OrbStack 设置里调整全局内存限制，或使用：

```bash
orbctl config set memory_mib VALUE
```

这个设置会影响所有 OrbStack 工作负载，不只影响当前项目。

## 启动完整服务

```bash
cd /Volumes/Move/omnisupport-copilot
docker compose --env-file infra/env/.env.local \
  -f infra/docker-compose.yml \
  -f .docker/compose/local-storage.yml \
  -f .docker/compose/registry-mirror.yml \
  up -d
```

只有 Dockerfile 或依赖发生变化时才需要加 `--build`：

```bash
docker compose --env-file infra/env/.env.local \
  -f infra/docker-compose.yml \
  -f .docker/compose/local-storage.yml \
  -f .docker/compose/registry-mirror.yml \
  up -d --build
```

## 验证服务

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

预期结果包含：

```text
rag_api: status ok, database ok
tool_api: status ok
```

浏览器访问：

```text
http://localhost:3000  Dagster
http://localhost:9001  MinIO Console
http://localhost:6006  Phoenix
```

查看容器状态：

```bash
docker compose --env-file infra/env/.env.local \
  -f infra/docker-compose.yml \
  -f .docker/compose/local-storage.yml \
  -f .docker/compose/registry-mirror.yml \
  ps
```

## MinIO 初始化说明

`minio_init` 是一次性容器。看到它显示 `Exited (0)` 是正常完成，不是失败。

验证退出码和日志：

```bash
docker inspect omni_minio_init --format '{{.Name}} exit={{.State.ExitCode}} status={{.State.Status}}'
docker logs omni_minio_init
```

日志中应包含 bucket 创建信息和：

```text
MinIO buckets initialized
```

列出 bucket：

```bash
docker run --rm --entrypoint /bin/sh --network infra_omni_net \
  docker.1ms.run/minio/mc:latest \
  -c 'mc alias set local http://minio:9000 minioadmin minioadmin >/dev/null && mc ls local'
```

预期 bucket 包括：`omni-raw-documents`、`omni-raw-tickets`、`omni-parsed`、`omni-indexes`、`omni-evals`、`omni-releases`、`omni-lakehouse`。

## Ticket Simulator 说明

主 compose 文件里的 `ticket_simulator` 也是一次性容器。它生成工单后退出，`Exited (0)` 表示完成。

注意：它的 Dockerfile 默认把输出写到容器内 `/data/tickets-seed-batch-001.jsonl`。如果想持久保存到外置硬盘项目目录，建议使用下面的 bind mount 方式。

使用已经构建好的轻量 simulator 镜像生成持久 seed 文件：

```bash
cd /Volumes/Move/omnisupport-copilot
docker run --rm \
  -v /Volumes/Move/omnisupport-copilot/data/canonization/tickets:/data \
  infra-ticket_simulator \
  python ticket_simulator.py --count 500 --output /data/tickets-seed-001.jsonl
```

验证：

```bash
wc -l data/canonization/tickets/tickets-seed-001.jsonl
ls -lh data/canonization/tickets/tickets-seed-001.jsonl
```

预期结果：`500` 行。

不要为了只生成 ticket seed 去构建 `devbox`。`devbox` 会安装 Dagster、dbt、pyarrow 等重依赖，会产生更多临时构建缓存。

## Docker Hub 拉取失败处理

这台机器之前的 OrbStack Docker 代理配置指向了失效端口 `host.docker.internal:7897`，会导致 Docker Hub 拉取镜像时 EOF。已清理该失效配置：

```bash
~/.orbstack/config/docker.json
```

由于直连 Docker Hub 仍可能失败，`.docker/compose/registry-mirror.yml` 会把第三方服务镜像指向 `docker.1ms.run`。

为了让本地构建解析 Python 基础镜像时不再访问 Docker Hub metadata，也创建过本地 tag：

```bash
docker tag python:3.11-slim-bookworm python:3.11-slim
```

## 当前已验证状态

编写本文档时，当前机器上的验证结果为：

```text
RAG API health: ok, database ok
Tool API health: ok
MinIO init: exit 0, buckets present
Ticket seed: 500 lines at data/canonization/tickets/tickets-seed-001.jsonl
Docker Build Cache: 0B after prune
External-drive runtime data: under .docker/volumes
```
