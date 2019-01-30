# glmtools-docker
Dockerized glmtools

## Setup

### Build the glmtest Docker image

```
cd ~/sources/glmtools-docker
docker build -t glmtest .
```
## Process some GLM data. 

To look around the glmtest image,

```bash
# Start up an interactive shell, mounting the raw L2 and destination grid
# directories on your local server (here, in /archive) to glm_raw_data and glm_grid_data in the container
docker run -i -t \
  --mount 'type=bind,src=/archive/GLM/GLM-L2-LCFA_G16,dst=/glm_raw_data' \
  --mount 'type=bind,src=/archive/GLM/GLM-L2-GRID_G16,dst=/glm_grid_data' \
  glmtest /bin/bash
```

To process the current minute,

```bash
docker run -i -t \
  --mount 'type=bind,src=/archive/GLM/GLM-L2-LCFA_G16,dst=/glm_raw_data' \
  --mount 'type=bind,src=/archive/GLM/GLM-L2-GRID_G16,dst=/glm_grid_data' \
  glmtest /home/glm/aws_realtime/run.sh
```

## Plot GLM data using this Docker container

Make sure to add a line to your `docker run` command for the container to add
the directory that will receive the plots. The scripts will create a
YYYY/Mon/DD directory structure within this directory.

```bash
docker run -i -t \
  --mount 'type=bind,src=/archive/GLM/GLM-L2-LCFA_G16,dst=/glm_raw_data' \
  --mount 'type=bind,src=/archive/GLM/GLM-L2-GRID_G16,dst=/glm_grid_data' \
  --mount 'type=bind,src=/archive/GLM/GLM-L2-IMGSCONUS_G16,dst=/glm_plots' \
  glmtest /home/glm/aws_realtime/run_with_plots.sh
```
