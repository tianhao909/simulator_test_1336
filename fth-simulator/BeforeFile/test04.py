#-*- coding: UTF-8 -*-
import argparse
# import the module 
import sys



def main():  
    # initializing the list 
    li = [1, -22, 43, 89, 2, 6, 3, 16]

    # assigning a larger value manually 
    # curr_min = 999999
    # assigning a larger value with  
    # maxint constant 
    #curr_min = sys.maxint
    curr_min = 1e9

    #https://vimsky.com/examples/usage/sys-maxint-in-python.html

    # loop to find minimum value 
    for i in range(0, len(li)):

        # update curr_min if a value lesser than it is found
        if li[i] < curr_min:
            curr_min = li[i]

    print("The minimum value is " + str(curr_min))

if __name__ == '__main__':
    main()

