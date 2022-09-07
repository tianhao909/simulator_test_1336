#-*- coding: UTF-8 -*-
from __future__ import print_function
import csv
import re
import sys
import types
import time
import math
import argparse
import copy
import os

#rom simulator.run_sim import fit_first_sim_jobs, smallest_first_sim_jobs
#from simulator.run_sim import parse_cluster_spec
#from simulator.jobs import JOBS
#from simulator.run_sim import try_get_job_res
#from simulator.cluster import CLUSTER
import util01
import flags01
import jobs01
import cluster01
import log01
import lp01


FLAGS01 = flags01.FLAGS01

#prepare JOBS list
JOBS01 = jobs01.JOBS01
CLUSTER01 = cluster01.CLUSTER01
LOG01 = log01.LOG01


#parse input arguments
flags01.DEFINE_string('trace_file', 'tf_job.csv',
                '''Provide TF job trace file (*.csv, *.txt).
                    *.csv file, use \',\' as delimiter; *.txt file, user \' \' as deliminter. 
                    Default file is tf_job.csv ''')
flags01.DEFINE_string('log_path', 'result-' + time.strftime("%Y%m%d-%H-%M-%S", time.localtime()),
                '''Simulation output folder, including cluster/node/gpu usage trace, pending job_queue info.
                Default folder is result-[time]''')
flags01.DEFINE_string('scheme', 'yarn',
                '''
                Job placement scheme:
                0.count, just resource counting, without assignment (which gpu, which cpu)
                1.yarn, ms yarn
                2.random
                3.crandom (consolidate + random)
                4.greedy
                5.balance
                6.cbalance (consolidate + balance)
                Default is yarn''')
flags01.DEFINE_string('schedule', 'fifo',
                '''
                Job schedule scheme:
                1.fifo
                2.fjf, fit job first( in fifo order)
                3.sjf, smallest job first
                4.lpjf, longest pending job first
                5.shortest, shortest-remaining-time job first
                6.shortest-gpu, shortest-remaining-gputime job first 
                7.dlas, discretized las 
                8.dlas-gpu, dlas using gpu time
                Default is fifo''')
# flags.DEFINE_string('scheme', 'random',
#                 ''' TF job placement scheme (PS, and workers). 
#                     Schemes:
#                         1.random: randomly place PS and workers across all hosts
#                         2.none: all jobs have the same placement (e.g. every ps0 on Node1)
#                         3.half_random: for each job, still one ps/worker per machine, placements are random
#                     Default scheme is random ''')
flags01.DEFINE_integer('num_switch', 1, 
                '''Part of cluster spec: the number of switches in this cluster, default is 1''')
flags01.DEFINE_integer('num_node_p_switch', 32, 
                '''Part of cluster spec: the number of nodes under a single switch, default is 32''')
flags01.DEFINE_integer('num_gpu_p_node', 8, 
                '''Part of cluster spec: the number of gpus on each node, default is 8''')
flags01.DEFINE_integer('num_cpu_p_node', 64,
                '''Part of cluster spec: the number of cpus on each node, default is 64''')
flags01.DEFINE_integer('mem_p_node', 256,
                '''Part of cluster spec: memory capacity on each node, default is 128''')
flags01.DEFINE_string('cluster_spec', None,
                '''Part of cluster spec: cluster infra spec file, 
                this file will overwrite the specs from num_switch, num_node_p_switch, and num_gpu_p_node
                Spec format:
                    num_switch,num_node_p_switch,num_gpu_p_node
                    int,int,int''')

flags01.DEFINE_boolean('print', False, 
                '''Enable print out information, default is False''')
flags01.DEFINE_boolean('flush_stdout', True, 
                '''Flush stdout, default is True''')
flags01.DEFINE_version('0.1')


def parse_job_file01(trace_file):
    #check trace_file is *.csv
    fd = open(trace_file, 'r')
    deli = ','
    if ((trace_file.find('.csv') == (len(trace_file) - 4))):
        deli = ','
    elif ((trace_file.find('.txt') == (len(trace_file) - 4))):
        deli = ' '

    reader = csv.DictReader(fd, delimiter = deli) 
    ''' Add job from job trace file'''
    keys = reader.fieldnames
    util01.print_fn('--------------------------------- Read TF jobs from: %s ---------------------------------' % trace_file) 
    util01.print_fn('    we get the following fields:\n        %s' % keys)
    job_idx = 0
    for row in reader:
        #add job into JOBS
        JOBS01.add_job01(row)
        # JOBS.read_job_info(job_idx, 'num_gpu')
        job_idx += 1

    assert job_idx == len(JOBS01.job_list) 
    assert JOBS01.num_job == len(JOBS01.job_list) 
    # JOBS.print_all_job_size_info()
    JOBS01.sort_all_jobs()
    # print(lp.prepare_job_info(JOBS.job_list[0]))
    util01.print_fn('---------------------------------- Get %d TF jobs in total ----------------------------------' % job_idx)
    # JOBS.read_all_jobs()
    fd.close()


def parse_cluster_spec01():
    if FLAGS01.cluster_spec:
        print(FLAGS01.cluster_spec)
        spec_file = FLAGS01.cluster_spec
        fd = open(spec_file, 'r')
        deli = ','
        if ((spec_file.find('.csv') == (len(spec_file) - 4))):
            deli = ','
        elif ((spec_file.find('.txt') == (len(spec_file) - 4))):
            deli = ' '
        reader = csv.DictReader(fd, delimiter = deli) 
        keys = reader.fieldnames
        util01.print_fn(keys)
        if 'num_switch' not in keys:
            return
        if 'num_node_p_switch' not in keys:
            return
        if 'num_gpu_p_node' not in keys:
            return
        if 'num_cpu_p_node' not in keys:
            return
        if 'mem_p_node' not in keys:
            return
        
        ''' there should be only one line remaining'''
        assert reader.line_num == 1

        ''' get cluster spec '''
        for row in reader:
            # util.print_fn('num_switch %s' % row['num_switch'])
            FLAGS01.num_switch = int(row['num_switch'])
            FLAGS01.num_node_p_switch = int(row['num_node_p_switch'])
            FLAGS01.num_gpu_p_node = int(row['num_gpu_p_node'])
            FLAGS01.num_cpu_p_node = int(row['num_cpu_p_node'])
            FLAGS01.mem_p_node = int(row['mem_p_node'])
        fd.close()

    util01.print_fn("num_switch: %d" % FLAGS01.num_switch)
    util01.print_fn("num_node_p_switch: %d" % FLAGS01.num_node_p_switch)
    util01.print_fn("num_gpu_p_node: %d" % FLAGS01.num_gpu_p_node)
    util01.print_fn("num_cpu_p_node: %d" % FLAGS01.num_cpu_p_node)
    util01.print_fn("mem_p_node: %d" % FLAGS01.mem_p_node)

    '''init infra'''
    CLUSTER01.init_infra()
    # util.print_fn(lp.prepare_cluster_info())
    util01.print_fn('--------------------------------- End of cluster spec ---------------------------------')
    return 

'''
Allocate job resource
'''
def try_get_job_res(job):
    '''
    select placement scheme
    '''
    if FLAGS01.scheme == 'yarn':
        ret = CLUSTER01.ms_yarn_placement(job)
    elif FLAGS01.scheme == 'balance':
        ret = lp01.placement(job)
        # ret = lp.min_new_job(job)
    elif FLAGS01.scheme == 'random':
        ret = CLUSTER01.random_placement(job)
    elif FLAGS01.scheme == 'crandom':
        ret = CLUSTER01.consolidate_random_placement(job)
    elif FLAGS01.scheme == 'greedy':
        ret = CLUSTER01.greedy_placement(job)
    elif FLAGS01.scheme == 'gandiva':
        ret = CLUSTER01.gandiva_placement(job)
    elif FLAGS01.scheme == 'count':
        ret = CLUSTER01.none_placement(job)
    else:
        ret = CLUSTER01.ms_yarn_placement(job)
    if ret == True:
        # job['status'] = 'RUNNING'
        pass
    return ret

# def one_queue_fifo_sim_jobs01():
#     '''
#     run jobs in fifo order;
#     new jobs are added to the end of the pending queue
#     ''' 
#     while( len(JOBS01.job_events) + len(JOBS01.pending_jobs)) > 0:
#         if len(JOBS01.job_events) == 0:
#             util01.print_fn("This cluster is not large enough to run the job")
#             break

#         event01 = JOBS01.job_events[0]
#         event_time = event01['time']
#         # util.print_fn('--------------------------------- Handle event[time %d]------------------------------------' % event_time)
#         #for ending jobs, release gpu
#         has_ejob = False
#         for e_job in event01['end_jobs']:
#             #remove from migratable jobs, if it's there
#             # JOBS.remote_migratable(e_job)

#             #job completes
#             CLUSTER01.release_job_res(e_job) #
#             # CLUSTER.release_gpus(e_job)
#             LOG01.job_comple(e_job, event_time) #
#             has_ejob = True
        
#         # for new-start jobs, try to start
#         for s_job in event01['start_jobs']:
#             #add into pending list
#             JOBS01.move_to_pending(s_job)

#         if CLUSTER01.check_free_gpu() > 0:
#             #for pending jobs, try to start
#             new_start_list = list()
#             for p_job in JOBS01.pending_jobs:
#                 # ret = CLUSTER.alloc_gpus(p_job)
#                 ret = try_get_job_res(p_job)
#                 if ret == True:
#                     ''' if remove_from_pending, then will miss the next p_job in the list '''
#                     new_start_list.append(p_job)
#                     #if job is migratable, add into migratable job list
#                     # JOBS.add_migratable(p_job)
#                     # JOBS.remove_from_pending(p_job, event_time)
#                     # JOBS.add_job_end_event(p_job)
#                     # util.print_fn('----job[%d] starts from pending' % p_job['job_idx'])
#                     # JOBS.read_job_info(p_job['job_idx'])
#                 else:
#                     break

#             for ns_job in new_start_list:
#                 JOBS01.remove_from_pending(ns_job, event_time)
#                 JOBS01.add_job_end_event(ns_job)
#                 util01.print_fn('----job[%d] starts from pending' % ns_job['job_idx'])

#         #sort pending jobs based on the num_gpu
#         #JOBS.pending_jobs.sort(key = lambda e:e.__getitem__('num_gpu'))

#         #remove time_event
#         JOBS01.job_events.pop(0)
#         JOBS01.job_events.sort(key = lambda e:e.__getitem__('time'))
#         # JOBS.print_job_events()

#         LOG01.checkpoint(event_time)
        


def one_queue_fifo_sim_jobs01():
    '''
    run jobs in fifo order;
    new jobs are added to the end of the pending queue
    '''
    while (len(JOBS01.job_events) + len(JOBS01.pending_jobs))> 0:
        if len(JOBS01.job_events) == 0:
            util01.print_fn("This cluster is not large enough to run the job")
            break

        event = JOBS01.job_events[0]
        event_time = event['time']
        # util.print_fn('--------------------------------- Handle event[time %d]------------------------------------' % event_time)
        #for ending jobs, release gpu
        has_ejob = False
        for e_job in event['end_jobs']:
            #remove from migratable jobs, if it's there
            # JOBS.remote_migratable(e_job)

            #job completes
            CLUSTER01.release_job_res(e_job)
            # CLUSTER.release_gpus(e_job)
            LOG01.job_complete(e_job, event_time)
            has_ejob = True


        #for new-start jobs, try to start
        for s_job in event['start_jobs']:
            #add into pending list
            JOBS01.move_to_pending(s_job)


        if CLUSTER01.check_free_gpu() > 0:
            #for pending jobs, try to start
            new_start_list = list()
            for p_job in JOBS01.pending_jobs:
                # ret = CLUSTER.alloc_gpus(p_job)
                ret = try_get_job_res(p_job)
                if ret == True:
                    ''' if remove_from_pending, then will miss the next p_job in the list '''
                    new_start_list.append(p_job)
                    #if job is migratable, add into migratable job list
                    # JOBS.add_migratable(p_job)
                    # JOBS.remove_from_pending(p_job, event_time)
                    # JOBS.add_job_end_event(p_job)
                    # util.print_fn('----job[%d] starts from pending' % p_job['job_idx'])
                    # JOBS.read_job_info(p_job['job_idx'])
                else:
                    break
            for ns_job in new_start_list:
                JOBS01.remove_from_pending(ns_job, event_time)
                JOBS01.add_job_end_event(ns_job)
                util01.print_fn('----job[%d] starts from pending' % ns_job['job_idx'])


        #sort pending jobs based on the num_gpu
        #JOBS.pending_jobs.sort(key = lambda e:e.__getitem__('num_gpu'))

        #remove time_event
        JOBS01.job_events.pop(0)
        JOBS01.job_events.sort(key = lambda e:e.__getitem__('time'))
        # JOBS.print_job_events()

        LOG01.checkpoint(event_time)

def fit_first_sim_jobs01():
    '''
    new jobs are added to the end of the ending queue
    but any fit job should be executed in fifo order
    '''
    # print('fth job_events= %d \n',JOBS.job_events)
    while (len(JOBS01.job_events) + len(JOBS01.pending_jobs)) > 0:
        if len(JOBS01.job_events) == 0:
            util01.print_fn("This cluster is not large enough to run the job")
            break
    
            event = JOBS01.job_events

        event = JOBS01.job_events[0]
        event_time = event['time']
        # util.print_fn('--------------------------------- Handle event[time %d]------------------------------------' % event_time)
        #for ending jobs, release gpu
        for e_job in event['end_jobs']:
            #remove from migratable jobs, if it's there
            # JOBS.remote_migratable(e_job)

            #job completes
            CLUSTER01.release_job_res(e_job)
            # CLUSTER.release_gpus(e_job)
            LOG01.job_complete(e_job,event_time)

        #for new-start jobs, try to start
        for s_job in event['start_jobs']:
            #add into pending list
            JOBS01.move_to_pending(s_job)

        new_start_list = list()
        for p_job in JOBS01.pending_jobs:
            # ret = CLUSTER.alloc_gpus(p_job)
            if CLUSTER01.check_free_gpu() <=0:
                break
            ret = try_get_job_res(p_job)
            if ret == True:
                ''' if remove_from_pending, then will miss the next p_job in the list '''
                new_start_list.append(p_job)
                # JOBS.remove_from_pending(p_job, event_time)
                # JOBS.add_job_end_event(p_job)
                # util.print_fn('----job[%d] starts from pending' % p_job['job_idx'])
            else:
                continue

        for ns_job in new_start_list:
            JOBS01.remove_from_pending(ns_job, event_time)
            JOBS01.add_job_end_event(ns_job)
            util01.print_fn('----job[%d] starts from pending' % ns_job['job_idx'])

        #sort pending jobs based on the num_gpu
        #JOBS.pending_jobs.sort(key = lambda e:e.__getitem__('num_gpu'))            

        #remove time_event
        JOBS01.job_events.pop(0)
        JOBS01.job_events.sort(key = lambda e:e.__getitem__('time'))
        # JOBS.print_job_events()


        # print('====fth event_time=',event_time)
        LOG01.checkpoint(event_time)



def smallest_first_sim_jobs01(gputime=False):
    '''
    new jobs are added to the end of the ending queue
    but in the queue, shortest (gpu) job first be served, until no resource
    '''

    end_events = list()
    while (len(JOBS01.job_events) + len(JOBS01.runnable_jobs))> 0:
        if (len(JOBS01.job_events) + len(end_events)) == 0:
            util01.print_fn("This cluster is not large enough to run the job")
            break

        #decide which is the next event: start or end  ?
        start_time = sys.maxint
        if len(JOBS01.job_events) > 0:
            start_event = JOBS01.job_events[0]
            start_time = start_event['time']
        end_time = sys.maxint
        if len(end_events) > 0:
            end_event = end_events[0]
            end_time = end_event['time']

        if end_time < start_time:
            event_time = end_time
            event = end_events[0]
        elif end_time > start_time:        
            event_time = start_time
            # print("start-time %d, end_time %d" % (start_time, end_time))
            event = JOBS01.job_events.pop(0)
        elif end_time == start_time and end_time != sys.maxint:
            event_time = start_time
            event = JOBS01.job_events.pop(0)
            event['end_jobs'] = end_events[0]['end_jobs']

        assert event_time == event['time']

        #for ending jobs, release gpu
        if 'end_jobs' in event:
            for e_job in event['end_jobs']:
                #job completes
                CLUSTER01.release_job_res(e_job)
                # CLUSTER.release_gpus(e_job)
                LOG01.job_complete(e_job, event_time)
                JOBS01.runnable_jobs.remove(e_job)

        #for new-start jobs, add to runnable
        if 'start_jobs' in event:
            for s_job in event['start_jobs']:
                #add into runnable list with pending status
                JOBS01.move_to_runnable(s_job)
                s_job['remaining_time'] = s_job['duration']
                s_job['remaining_gputime'] = int(s_job['remaining_time'] * s_job['num_gpu'])
                util01.print_fn('---- job[%d] is added' % s_job['job_idx'])



def main():  


    if FLAGS01.schedule == 'multi-dlas-gpu': 
        if FLAGS01.scheme != 'count':
            util01.print_fn("In Main, multi-dlas-gpu without count")
            exit()

    ''' Parse input'''
    parse_job_file01(FLAGS01.trace_file) 
    parse_cluster_spec01() 
      

    ''' prepare logging '''
    LOG01.init_log()

    ''' Prepare jobs'''
    JOBS01.prepare_job_start_events01()
    # print('bbbbbbbbbbb')

    # sim_job_events()
    if FLAGS01.schedule == 'fifo':
        print('cccccccccc')
        one_queue_fifo_sim_jobs01()
        print('dddddddddddd')
    elif FLAGS01.schedule == 'fjf':
        fit_first_sim_jobs01()
    elif FLAGS01.schedule == 'sjf':
        smallest_first_sim_jobs01(False)
    else: 
        one_queue_fifo_sim_jobs01()

    #one_queue_fifo_sim_jobs01()
    print('aaaaa')

# def main():
#     print('aaa')




# def main():

#     if FLAGS01.schedule == 'multi-dlas-gpu': 
#         if FLAGS01.scheme != 'count':
#             util01.print_fn("In Main, multi-dlas-gpu without count")
#             exit()
#     ''' Parse input'''
#     parse_job_file01(FLAGS01.trace_file)
#     parse_cluster_spec01()

#     ''' prepare logging '''
#     LOG01.init_log()

#     # lp.placement(JOBS.job_list[0])
#     ''' Prepare jobs'''
#     JOBS01.prepare_job_start_events01()

#     # sim_job_events()
#     if FLAGS01.schedule == 'fifo':
#         one_queue_fifo_sim_jobs01()
#     elif FLAGS01.schedule == 'fjf':
#         fit_first_sim_jobs01()
#     elif FLAGS.schedule == 'sjf':
#         smallest_first_sim_jobs(False)
#     elif FLAGS.schedule == 'lpjf':
#         longest_pending_first_sim_jobs()
#     elif FLAGS.schedule == 'shortest':
#         shortest_first_sim_jobs()
#     elif FLAGS.schedule == 'shortest-expected':
#         JOBS.job_dist_data = parse_job_dist()
#         shortest_first_sim_jobs()
#     elif FLAGS.schedule == 'shortest-gpu':
#         shortest_first_sim_jobs(True)
#     elif FLAGS.schedule == 'dlas':
#         JOBS.job_dist_data = parse_job_dist()
#         dlas_sim_jobs()
#     elif FLAGS.schedule == 'dlas-gpu':
#         dlas_sim_jobs(True)
#     elif FLAGS.schedule == 'dlas-gpu-gittins':
#         JOBS.job_dist_data = parse_job_dist()
#         dlas_sim_jobs(True)
#     elif FLAGS.schedule == 'dlas-gpu-gittins-1':
#         JOBS.job_dist_data = parse_job_dist()
#         dlas_sim_jobs(True, 1)
#     elif FLAGS.schedule == 'dlas-gpu-gittins-2':
#         JOBS.job_dist_data = parse_job_dist()
#         dlas_sim_jobs(True, 2)
#     elif FLAGS.schedule == 'dlas-gpu-gittins-4':
#         JOBS.job_dist_data = parse_job_dist()
#         dlas_sim_jobs(True, 4)
#     elif FLAGS.schedule == 'dlas-gpu-gittins-8':
#         JOBS.job_dist_data = parse_job_dist()
#         dlas_sim_jobs(True, 8)
#     elif FLAGS.schedule == 'dlas-gpu-pack':
#         CLUSTER.init_dlas_pack_gpu()
#         dlas_pack_sim_jobs(True)
#     elif FLAGS.schedule == 'multi-dlas-gpu':
#         # JOBS.init_reserve_gpus(CLUSTER.num_gpu)
#         # JOBS.test_reserve_gpus(CLUSTER.num_gpu)
#         multi_dlas_sim_jobs(True)
#     elif FLAGS.schedule == 'gittins':
#         # JOBS.init_reserve_gpus(CLUSTER.num_gpu)
#         # JOBS.test_reserve_gpus(CLUSTER.num_gpu)
#         job_dist_data = parse_job_dist()
#         gittins_sim_jobs(job_dist_data, True, True)
#     elif FLAGS.schedule == 'dlas-gpu-1':
#         dlas_sim_jobs(True,1)
#     elif FLAGS.schedule == 'dlas-gpu-2':
#         dlas_sim_jobs(True,2)
#     elif FLAGS.schedule == 'dlas-gpu-05':
#         dlas_sim_jobs(True, 0.5)
#     elif FLAGS.schedule == 'dlas-gpu-4':
#         dlas_sim_jobs(True, 4)
#     elif FLAGS.schedule == 'dlas-gpu-8':
#         dlas_sim_jobs(True, 8)
#     elif FLAGS.schedule == 'dlas-gpu-10':
#         dlas_sim_jobs(True, 10)
#     elif FLAGS.schedule == 'dlas-gpu-100':
#         dlas_sim_jobs(True, 100)
#     elif FLAGS.schedule == 'dlas-gpu-1000':
#         dlas_sim_jobs(True, 1000)
#     elif FLAGS.schedule == 'gandiva':
#         CLUSTER.init_gandiva_nodes()
#         gandiva_sim_jobs(True, 1000)
#     elif FLAGS.schedule == 'gpu-demands':
#         sim_gpu_demands()
#     else:
#         one_queue_fifo_sim_jobs()





if __name__ == '__main__':
    main()