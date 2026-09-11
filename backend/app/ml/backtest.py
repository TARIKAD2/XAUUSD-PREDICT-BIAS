"""Expanding-window time-series validation utilities."""
def walk_forward_splits(size,initial_train,test_size):
 if initial_train<=0 or test_size<=0:raise ValueError("split sizes must be positive")
 end=initial_train
 while end+test_size<=size:
  yield range(0,end),range(end,end+test_size);end+=test_size