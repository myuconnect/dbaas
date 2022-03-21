from time import time 
class Timer: 
  
    def __init__(self, func): 
        self.function = func 
  
    def __call__(self, *args, **kwargs): 
        start_time = time() 
        result = self.function(*args, **kwargs) 
        end_time = time() 
        print("Execution took {} seconds".format(end_time-start_time)) 
        return result 
  
  
# adding a decorator to the class 
@Timer
def some_function(delay): 
    from time import sleep 
  
    # Introducing some time delay to  
    # simulate a time taking function. 
    sleep(delay) 
  
some_function(3) 

class ErrorCheck: 
  
    def __init__(self, function): 
        self.function = function 
  
    def __call__(self, *params): 
        if any([isinstance(i, str) for i in params]): 
            raise TypeError("parameter cannot be a string !!") 
        else: 
            return self.function(*params) 