# Use the official Miniconda (Python 3) as the parent image
FROM continuumio/miniconda3

RUN conda update -n base conda

# User glm does not exist yet.
RUN groupadd -r glm && useradd --no-log-init -r -g glm glm
ENV HOME /home/glm

# Set up all the GLM bits in home.
WORKDIR $HOME

# Add the requirements file from this distribution
COPY requirements.txt requirements.txt

# Clone glmtools and supporting libraries not available in conda
RUN git clone https://github.com/deeplycloudy/glmtools.git
WORKDIR $HOME/glmtools
RUN git checkout unifiedgridfile
RUN conda env create -f environment.yml

# Only needed for plotting
RUN conda install -c conda-forge cartopy

# Back to home after getting the right branch of glmtools
WORKDIR $HOME

# Install cron and copy in the crontab
# RUN apt-get update && apt-get -y install cron
# # Copy and give execution rights
# ADD cron/crontab /etc/cron.d/glm-cron
# RUN chmod 0644 /etc/cron.d/glm-cron
# # Apply the cron job
# RUN crontab /etc/cron.d/glm-cron
# CMD service cron start

# Copy the realtime processing applications
COPY aws_realtime aws_realtime

# Activate the glmval environment (using exec form that avoids nested shells)
# and install glmtools and its supporting requirements into it.
# The commented-out RUN commands below this aren't properly inheriting
# the conda environment, and most references online seem to prefer modifying
# the path directly, avoiding the use of the activate script.
# Another example used run, but prepended each with a bin/bash and the activate command
# That is in keeping with the Docker approach of stacking changes to the 
# environment. Here, we just do it all at once.
RUN ["/bin/bash", "-c", \
     "source activate glmval && pip install -r requirements.txt && \
     cd glmtools && python setup.py install" \
    ]

# Install the support packages
# RUN pip install -r requirements.txt

# Install glmtools itself
# WORKDIR $HOME/glmtools
# RUN python setup.py install

# glmtools uses lmatools which imports pyplot from matplotlib
# so set the backend to non-interactive to avoid an import error
ENV MPLBACKEND Agg

