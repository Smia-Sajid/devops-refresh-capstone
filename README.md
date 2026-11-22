# DevOps refresh — Days 1–4 (Thu 19 – Sun 22 Nov 2026)

Your tiny app is already written — `app.py` uses only the Python standard
library, so there is nothing to `pip install`. About 2 hours a day, from
the 14-day checklist (`workspace/devops-refresh-checklist.md`).

If Day 1 slipped, do Day 1 first, then Day 2 — move the day, don't restart.

## Day 1 — Docker, first image (Thu 19 Nov)

### 1. Install Docker, prove it works

Install Docker Desktop (Windows/Mac) or Docker Engine (Linux), then:

```bash
docker run hello-world
```

### 2. Build your image

From inside this folder:

```bash
docker build -t my-app:day1 .
```

### 3. Run it and check it in a browser

```bash
docker run -p 8000:8000 my-app:day1
```

Open http://localhost:8000 — you should see
`Hello from Smi's Docker refresh - Day 1 is running!`

Stop it with `Ctrl+C` in the terminal, then remove the container:

```bash
docker ps -a
docker rm <container-id>
```

Done when: you can build and run your own image from scratch, without
copying a tutorial Dockerfile blindly.

## Day 2 — Multi-stage build + Compose (Fri 20 Nov)

The `Dockerfile` in this folder is now the multi-stage version, and there
is a new `docker-compose.yml` (app + Postgres) and a new `/health`
endpoint in `app.py`. No `pip install` is still needed.

### 1. Compare the image sizes

Tag Day 1 first if you haven't already, then build Day 2 and compare:

```bash
docker build -t my-app:day1 .   # only if you skipped tagging it on Day 1
docker build -t my-app:day2 .
docker images my-app
```

Honest note: this app has no dependencies, so the Day 2 image will only
be a little smaller than Day 1 — the point is learning the multi-stage
pattern and how to measure it, not a big saving today.

### 2. Start app + database with one command

```bash
cp .env.example .env   # then change the password inside .env
docker compose up
```

Compose starts the database first, waits until Postgres is healthy
(`pg_isready`), then starts the app. Check both:

- http://localhost:8000 — `Hello from Smi's Docker refresh - Day 2 is running!`
- http://localhost:8000/health — `{"status": "ok", "db": "postgres", ...}`

`/health` sends a real Postgres startup message and only reports
`"postgres"` when the other end answers like Postgres — it stops before
login, so the app never needs the database password. A plain TCP check
would not be enough: a proxy can accept the connection with no database
behind it.

Useful checks while it runs:

```bash
docker compose ps
docker compose logs db
docker volume ls   # pgdata is the named volume holding the database data
```

### 3. Stop it

```bash
docker compose down        # stops everything, keeps the data in pgdata
docker compose down -v     # also deletes pgdata — only when you want a clean start
```

Done when: app + database start together with `docker compose up`, and
`/health` says `"db": "postgres"`.

## Day 3 — Publish it (Sat 21 Nov)

Today is about making the image runnable by someone else, not just on
your laptop.

### 1. Log in to Docker Hub

Create a free account at hub.docker.com if you don't have one, then
on your laptop:

```bash
docker login
```

Use your own Docker Hub username and password / token. Never put a
password in the repo or in a script.

### 2. Tag and push the Day 2 image

Replace `YOUR-DOCKERHUB-USERNAME` with your own username, or use the
script — it does the same three steps:

```bash
docker build -t my-app:day2 .
docker tag my-app:day2 YOUR-DOCKERHUB-USERNAME/my-app:day2
docker push YOUR-DOCKERHUB-USERNAME/my-app:day2
```

Or:

```bash
./scripts/publish.sh YOUR-DOCKERHUB-USERNAME day2
```

### 3. Pull it on a clean run and confirm it still works

```bash
docker pull YOUR-DOCKERHUB-USERNAME/my-app:day2
docker run -p 8000:8000 YOUR-DOCKERHUB-USERNAME/my-app:day2
```

Open http://localhost:8000 — you should see the Day 2 message.
Note: this run has no database, so `/health` will say
`"db": "unreachable"` here. That is expected — the database comes
from Compose (Day 2), this image on its own is just the app.

Done when: someone else could run your app from your Docker Hub image
+ this README alone.

## Day 4 — Kubernetes, first deployment (Sun 22 Nov)

The app only — no database yet. The database moves to Kubernetes on
Day 7, and config/secrets move on Day 5.

### 1. Start a local cluster

Install `kubectl` plus kind or Minikube, then create a cluster:

```bash
kind create cluster        # kind
# or
minikube start             # Minikube
```

### 2. Load the local image into the cluster

The Deployment uses your local Day 2 image, `my-app:day2` — the
cluster cannot see your laptop's Docker images unless you load it in:

```bash
kind load docker-image my-app:day2     # kind
# or
minikube image load my-app:day2        # Minikube
```

You do **not** need the Day 3 Docker Hub push done first for this
step. After that push, replace the image in
`k8s/deployment.yaml` with `<your-docker-hub-username>/my-app:day2`
and the cluster will pull it instead.

### 3. Deploy and check

```bash
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
kubectl get pods,svc
kubectl scale deployment my-app --replicas=3
kubectl get pods -w
```

The Service is a NodePort on 30080, so open
http://localhost:30080 — you should see the Day 2 message.
`/health` will say `"db": "unreachable"` here. That is expected:
there is no database in the cluster yet on Day 4.

Done when: your app is running in Kubernetes, not just in Docker.

## If Docker will not install

Tell Muse what your laptop is (Windows/Mac/Linux, roughly how old) and the
exact error — that decides whether to fix the install or use a lighter
route (e.g. Docker in a cloud VM) instead of losing the day to setup.

## What was verified here, and what was not

- `app.py` was run here and returned the Day 2 message on `/`. Its
  `/health` check was tested two ways: against a small stub server that
  answers with a Postgres auth message it correctly reported
  `"db": "postgres"`, and with no database behind the connection it
  correctly reported `"db": "unreachable"` — including on this machine,
  where a proxy accepts bare TCP connections, which is why `/health`
  does a real Postgres handshake instead of a TCP check.
- `docker-compose.yml` parses as valid YAML.
- `docker build` / `docker compose up` were **not** tested here — Docker
  is not installed on this machine, so run those on your laptop and tell
  Muse the exact error if one appears. The real Postgres check happens
  on your laptop, via Compose.
- Day 3: `scripts/publish.sh` was syntax-checked here (`sh -n`), but
  the actual `docker push` to Docker Hub was **not** done here — it
  needs your Docker Hub account and `docker login` on your laptop.
- Day 4: `k8s/deployment.yaml` (3 replicas, `my-app:day2`,
  `imagePullPolicy: IfNotPresent`) and `k8s/service.yaml` (NodePort
  30080) were checked here as valid YAML with no passwords in them.
  `kubectl apply` was **not** tested here — there is no cluster on
  this machine, so run it on your laptop after loading the image
  into kind/Minikube.
