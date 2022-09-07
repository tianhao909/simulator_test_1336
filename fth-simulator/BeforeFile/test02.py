#-*- coding: UTF-8 -*-
import argparse

def main():  
    #if FLAGS01.schedule01 == 'multi-dlas-gps':
    # sim_job_events()
    # if FLAGS01.schedule01 == 'fifo':
    #     one_queue_fifo_sim_jobs01()
    # parser = argparse.ArgumentParser(description='命令行中传入一个数字')
    # #type是要传入的参数的数据类型  help是该参数的提示信息
    # parser.add_argument('integers', type=str, help='传入的数字')

    # args = parser.parse_args()
    # #获得传入的参数
    # print(args)

    # parser = argparse.ArgumentParser(description='命令行中传入一个数字')
    # #type是要传入的参数的数据类型  help是该参数的提示信息
    # parser.add_argument('integers', type=str, help='传入的数字')
    # args = parser.parse_args()
    # #获得integers参数
    # print(args.integers)

    # parser = argparse.ArgumentParser(description='命令行中传入一个数字')
    # parser.add_argument('integers', type=int, nargs='+',help='传入的数字')
    # args = parser.parse_args()

    # print(sum(args.integers))

    # parser = argparse.ArgumentParser(description='姓名')
    # parser.add_argument('--param1', type=str,help='姓')
    # parser.add_argument('--param2', type=str,help='名')
    # args = parser.parse_args()
    
    # #打印姓名
    # print(args.param1+args.param2)

    #python assert如果发生异常就说明表达示为假。可以理解表示式返回 值为假 时就会触发异常。
    
    a = 1

    b = -1

    assert a > 0, b < 0

    print('正常输出,表达式返回真了') # 输出：正常输出,表达式返回真了

    print('aaaaaaaaaaaaaa')

if __name__ == '__main__':
    main()