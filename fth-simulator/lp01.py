
"""
set J;
/* there are multiple components in the new job */

set N;
/* nodes in the cluster */


param g{j in J}, integer, >=0;
param c{j in J}, integer, >=0;
param t{j in J}, >=0;
/* resource requirements (GPU, CPU) and network traffic of each component in the new job */

param fg{n in N}, integer, >=0;
param fc{n in N}, integer, >=0;
/* free GPUs and CPUs on each machine */
param ct{n in N}, >=0;
/* current network traffic on each machine */


var p{j in J, n in N}, binary, >= 0;
/* objective variable: placement of the new job */
/* binary is also a constraint */

var maxt;
/* max network traffic load in the cluster */

minimize z: maxt;

s.t. optcon{n in N}: ct[n] + sum{j in J} (p[j, n] * t[j]) <= maxt; 
/* optimization constraint: min(max{network load}) */

s.t. fgcap{n in N}: sum{j in J} (p[j,n] * g[j]) <= fg[n];
/* free gpu constraint */

s.t. fccap{n in N}: sum{j in J} (p[j,n] * c[j]) <= fc[n];
/* free cpu constraint */

s.t. jgcon{j in J}: sum{n in N} (p[j,n] * g[j]) - g[j] = 0;
s.t. jccon{j in J}: sum{n in N} (p[j,n] * c[j]) - c[j] = 0;
/* job gpu / cpu consistency */

"""

from __future__ import print_function
from sre_parse import FLAGS

import sys

'''
import cplex
from cplex.exceptions import CplexError

from cplex.six.moves import range
'''

import util01 
import flags01
import jobs01
import cluster01
import switch01
import node01
FLAGS01 = flags01.FLAGS01
CLUSTER01=cluster01.CLUSTER01
JOBS = jobs01.JOBS01



'''
sample data:
j: [ps0, ps1, ps2, w0, w1, w2]
node: [n0, n1]
#gpu requirement
g = [0,0,0,1,1,1]
#cpu requirement
c = [4,4,4,2,2,2]
#network traffic
t = [40,10,10,20,20,20]

t = [15,5,5,15]
num_ps = 4
num_w = 4
m_size = 40
ps_c = 4
w_c = 2

#free cpus on nodes
fc = [40,40]
#free gpus on nodes
fg = [4,4]
#current network load on nodes
ct = [30,0]
'''

def placement(new_job):
    pass