#!/bin/bash
# on graupel, first: ebruning@graupel:/archive/GLM/realtime/aws$ ./open_reverse_ssh.sh 
ssh -p 2388 ebruning@localhost "cd /archive/GLM/realtime/aws/ && ./rsync_glm_west.sh"
