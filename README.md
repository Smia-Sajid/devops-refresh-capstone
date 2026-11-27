# DevOps refresh — Days 1–7 (Thu 19 – Wed 25 Nov 2026)

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

## Day 5 — ConfigMaps + Secrets (Mon 23 Nov)

No config or password is hard-coded in the Deployment anymore.
Config lives in a ConfigMap, the password in a Secret.

- `k8s/configmap.yaml` — `app-config`: PORT, DB_HOST, DB_PORT,
  POSTGRES_USER, POSTGRES_DB. Safe to commit, no passwords in it.
- `k8s/secret.yaml` — `db-secret`: only the placeholder
  `"changeme"`, the same default as in `.env.example`. Never commit
  a real password here. For a real one, use
  `kubectl create secret generic db-secret --from-literal=POSTGRES_PASSWORD='...'`
  and do not keep it in Git.
- `k8s/deployment.yaml` — the container now gets its env from both
  with `envFrom`, instead of the hard-coded `env:` block from Day 4.

### 1. Apply the ConfigMap + Secret FIRST

Order matters — a pod whose `envFrom` names a missing ConfigMap
or Secret will not start:

```bash
kubectl apply -f k8s/configmap.yaml -f k8s/secret.yaml
```

### 2. Redeploy

```bash
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
kubectl get pods,svc
kubectl get configmap app-config -o yaml
kubectl exec deploy/my-app -- printenv | grep -E 'PORT|DB_|POSTGRES_'
```

Open http://localhost:30080 — Day 2 message again. `/health`
will still say `"db": "unreachable"`, expected: no database in
the cluster yet, that is Day 7.

Done when: no password or config is hard-coded in the image or
the Deployment.

## Day 6 — Ingress + rolling update (Tue 24 Nov)

Two things today: reach the app by a hostname instead of a port
number, then update it without downtime — and roll it back.

- `k8s/ingress.yaml` — `my-app`: host `my-app.local`, path `/`,
  to the `my-app` Service on port 8000.
- `k8s/deployment.yaml` — image is now `my-app:day6`, with an
  explicit rolling-update strategy (`maxSurge: 1`,
  `maxUnavailable: 0`), so pods update one at a time and the app
  never goes down.
- `app.py` — only the `/` message changed, to
  `Hello from Smi's Docker refresh - Day 6 is running!` That is
  the point: the message is how you can see which version is live.

### 1. Enable the Ingress controller

```bash
minikube addons enable ingress
kubectl get pods -n ingress-nginx
```

For kind instead:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.3/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=120s
```

### 2. Point the hostname at the cluster

```bash
echo "$(minikube ip) my-app.local" | sudo tee -a /etc/hosts
```

On Windows, add the same line to
`C:\Windows\System32\drivers\etc\hosts`, using the minikube IP.
On kind without extra port mappings, use a port-forward instead
and keep the `Host` header:

```bash
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8080:80
curl -H "Host: my-app.local" http://localhost:8080
```

### 3. Apply the Ingress and check the old version first

```bash
kubectl apply -f k8s/ingress.yaml
kubectl get ingress my-app
curl http://my-app.local
```

You should still see the Day 2 message here — the new image has
not rolled out yet. NodePort http://localhost:30080 still works
as a fallback.

### 4. Build the new version and roll it out

```bash
docker build -t my-app:day6 .
minikube image load my-app:day6        # Minikube
# or
kind load docker-image my-app:day6     # kind
kubectl apply -f k8s/deployment.yaml
kubectl rollout status deployment/my-app
kubectl get pods -w
```

Or, without editing any file:

```bash
kubectl set image deployment/my-app app=my-app:day6
kubectl rollout status deployment/my-app
```

Now `curl http://my-app.local` should show the Day 6 message.
Watch the pods while it rolls: old pods end one by one as new
ones become ready — that is the zero-downtime update.

### 5. Roll it back

```bash
kubectl rollout history deployment/my-app
kubectl rollout undo deployment/my-app
kubectl rollout status deployment/my-app
curl http://my-app.local
```

The Day 2 message is back. That is the safety net: a bad version
goes away with one command. Note that `rollout undo` changes
only the cluster — the files in this repo stay on Day 6, so
re-applying `k8s/deployment.yaml` rolls forward to Day 6 again.

Done when: you can update the app without downtime and roll back
if it breaks.

## Day 7 — Kubernetes checkpoint: full app + database (Wed 25 Nov)

The checkpoint: everything from Days 1–6 running together in the
cluster, from the YAML in this repo — no Compose, no manual steps
left out of Git.

- `k8s/postgres-pvc.yaml` — `pgdata`, 1Gi, so the database survives
  a pod restart.
- `k8s/postgres-deployment.yaml` — `db`, 1 replica of
  `postgres:16-alpine`, the same image as Compose on Day 2. It gets
  `POSTGRES_USER` / `POSTGRES_DB` from the Day 5 ConfigMap and
  `POSTGRES_PASSWORD` from the Day 5 Secret (placeholder only).
- `k8s/postgres-service.yaml` — `db`, ClusterIP on 5432. The name
  matters: the app already looks for `DB_HOST=db`, so this Service
  is what flips `/health` to `"db": "postgres"`. The database is
  not exposed outside the cluster — no NodePort, no Ingress for it.
- No app change today: the app Deployment already points at `db`,
  and `/health` checks on every request, so the app needs no
  redeploy or rebuild once the database is up.

### 1. Apply, in this order

```bash
kubectl apply -f k8s/configmap.yaml -f k8s/secret.yaml
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/postgres-deployment.yaml -f k8s/postgres-service.yaml
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml -f k8s/ingress.yaml
```

### 2. Check the whole stack

```bash
kubectl get pods,svc,pvc,ingress
kubectl logs deployment/db
kubectl get pods -w
curl http://my-app.local/health
curl http://my-app.local
```

You should now see `"db": "postgres"` on `/health` — the first time
in the cluster — and the Day 6 message on `/`. NodePort
http://localhost:30080/health works as a fallback check.

### 3. Screenshots to take

- `kubectl get pods,svc,pvc,ingress` showing app (3 pods), db
  (1 pod), both Services, the PVC Bound, and the Ingress.
- The app in a browser at http://my-app.local, and
  http://my-app.local/health showing `"db": "postgres"`.

### 4. What still feels shaky — your Day 12–14 fix list

Write it here honestly after running the checkpoint; do not leave
it blank. Start from these, keep the ones that are true for you:

- [ ] Postgres is 1 replica with one ReadWriteOnce PVC — it cannot
  scale like the app, and deleting the PVC deletes the data.
- [ ] The Secret still holds the placeholder password — a real
  password must come from `kubectl create secret`, never from Git.
- [ ] The app image is still local (`my-app:day6`) — the Day 3
  Docker Hub push is what makes it pullable elsewhere.
- [ ] Anything else that broke or felt unclear today: ___________

Done when: the repo has working K8s YAML for app + database, and
the screenshots prove it.

## Day 8 — Jenkins, first pipeline (Thu 26 Nov)

Jenkins runs in Docker on your laptop, and the pipeline lives in
this repo as `Jenkinsfile` — a Declarative Pipeline that checks
out the repo and prints hello. No build, no test, no deploy yet:
today is only "a push can trigger a Jenkins job".

### 1. Run Jenkins in Docker

```bash
docker run -d --name jenkins -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home jenkins/jenkins:lts
docker logs jenkins
```

Copy the initial admin password from the logs, open
http://localhost:8080, and log in. Choose **Install suggested
plugins**, then also install **Docker Pipeline** (Manage Jenkins →
Plugins → Available plugins → search "Docker Pipeline" → Install).

### 2. Create the pipeline job

- New Item → name it `devops-refresh-capstone` → **Pipeline** → OK.
- Under Pipeline, set Definition to **Pipeline script from SCM**,
  SCM to **Git**, and Repository URL to
  `https://github.com/Smia-Sajid/devops-refresh-capstone.git`.
- Script Path stays `Jenkinsfile`. Save, then **Build Now**.

### 3. Check it

The build should go green and the console output should show
`Hello from Jenkins - Day 8 pipeline is running!` plus the
`ls -la` listing of the checked-out repo. Take a screenshot of
the green build — that is your first Jenkins proof for Day 13.

Done when: a push can trigger a Jenkins job, and the first build
is green.

## Day 9 — Build + test in Jenkins (Fri 27 Nov)

Day 8 proved a push can trigger a job. Day 9 makes Jenkins do
real work on every push: compile the app, then run its tests —
and fail the build if either step fails.

- `test_app.py` — 3 tests, Python standard library only, same
  pattern as the revived CI repo: it starts the real app on a
  free local port and checks `/` returns the Docker refresh
  message, `/health` says `"db": "unreachable"` with no database,
  and `/health` says `"db": "postgres"` against a small stub
  that answers like Postgres. Run it any time with
  `python3 -m unittest -v`.
- `Jenkinsfile` — two new stages after Hello: **Build**
  (`python3 -m py_compile app.py test_app.py`) and **Test**
  (`python3 -m unittest -v`). The `post` block now also says
  plainly whether the build went green or red, and which stage
  to look at when it is red.

### 1. See it go red once, on purpose

This is the point of the day — a pipeline you have never seen
fail will not teach you what red means:

```bash
# In Jenkins, run the job once with a deliberate break, e.g.
# change one test expectation in test_app.py, Build Now, watch
# it go red — then undo the change, Build Now again, watch it
# go green. Do not commit the broken version to GitHub.
```

### 2. Check it

The green build's console should show all 3 tests passing
(`Ran 3 tests ... OK`) and `Day 9 pipeline is green: build and
tests passed.` Take a screenshot of the green build — that is
your Day 13 proof that Jenkins builds and tests on every push.

If Jenkins says `python3: not found`, install it inside the
Jenkins container first — do not change the Jenkinsfile:

```bash
docker exec -u root jenkins apt-get update && docker exec -u root jenkins apt-get install -y python3
```

Then Build Now again. No app change today: the app still
returns the Day 6 message on `/`, so the Day 7 Kubernetes
checkpoint is untouched.

Done when: Jenkins builds and tests on every push, and you have
seen it go red and back to green.

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
- Day 5: `k8s/configmap.yaml`, `k8s/secret.yaml` and the updated
  `k8s/deployment.yaml` (envFrom, no hard-coded env) were checked
  here as valid YAML. The Secret holds only the placeholder
  `"changeme"` — no real password. `kubectl apply` was **not**
  tested here, same as Day 4.
- Day 6: `k8s/ingress.yaml`, the updated `k8s/deployment.yaml`
  (image `my-app:day6`, rolling-update strategy, no hard-coded
  env) and the updated `app.py` were checked here as valid YAML /
  run here — `app.py` returned the Day 6 message on `/` and
  `"db": "unreachable"` on `/health` (expected, no database in
  the cluster yet). `kubectl apply`, the Ingress controller and
  the rollout were **not** tested here — there is no cluster on
  this machine, so run those on your laptop.
- Day 7: `k8s/postgres-deployment.yaml` (1 replica, `postgres:16-alpine`,
  envFrom the Day 5 ConfigMap + Secret, PVC mount, `pg_isready`
  readiness probe), `k8s/postgres-service.yaml` (ClusterIP `db`
  on 5432) and `k8s/postgres-pvc.yaml` (1Gi, ReadWriteOnce) were
  checked here as valid YAML, with no real password anywhere — the
  Secret still holds only the placeholder. `kubectl apply` was
  **not** tested here — there is no cluster on this machine, so
  run it on your laptop and confirm `/health` says
  `"db": "postgres"` there.
- Day 8: `Jenkinsfile` (Declarative Pipeline: Checkout stage with
  `checkout scm` + `ls -la`, Hello stage printing the Day 8
  message) was checked here by reading it back — it has no
  credentials and no build/deploy step, as planned. Jenkins itself
  was **not** run here — there is no Docker on this machine, so
  run `docker run jenkins/jenkins:lts` on your laptop, install the
  suggested plugins + Docker Pipeline, and point the job at this
  repo with Script Path `Jenkinsfile`.
- Day 9: `test_app.py` (3 tests, same pattern as the revived CI
  repo) was run here — all 3 passed in 0.04s — and the updated
  `Jenkinsfile` (Checkout, Hello, Build with `py_compile`, Test
  with `python3 -m unittest -v`, plus green/red `post` messages)
  was checked here by reading it back, braces balanced, no
  credentials in it. Jenkins itself was **not** run here — there
  is no Docker on this machine, so run the job on your laptop
  and confirm the console shows `Ran 3 tests ... OK`.
