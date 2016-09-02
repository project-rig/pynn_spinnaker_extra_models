
import os

for numPatterns in range(1):
  print "******* Iteration ", numPatterns, " ********"
  os.system("date")
  try:
    #cmdString = "python ./partitioned_single_network_w_recurrence.py %d " % (numPatterns*100+400)
    cmdString = "python ./partitioned_single_network.py %d " % (numPatterns*100+50)
    #cmdString = "python ./binary_network.py %d " % (numPatterns*100+500)
    print "Executing: ", cmdString
    os.system(cmdString)
    os.system("date")
  except:
    print "Run failed!"
    os.system("date")

