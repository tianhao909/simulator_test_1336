#-*- coding: UTF-8 -*-
import argparse
# import the module 
import sys



def main():  
    L=[('b',2), ('a',1), ('c',3), ('d',4)]
    #2、利用参数 cmp 排序
    L2=sorted(L, cmp=lambda x,y : cmp(x[1], y[1]))
    print("L= " , L)
    print('L2= ' , L2)
    

if __name__ == '__main__':
    main()

