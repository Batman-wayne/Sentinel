#Created by: Nicholas O'Brien
#Project Sentinel; main script
#Created: December 7th, 2019
#Last Edit: December 8th, 2019
import sys
import ast
sys.path.append("..\PARSER")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import time
import RANSAC.RANSAC as RANSAC
##import PARSER
import EKF.EKF as EKF
import numpy as np
import KALMAN
##import ANGLEPARSE
X = 10 #mm, the maximum distance a point must be from an LSRP in RANSAC to be considered in tolerance.
C = 800 #Consensus for RANSAC, number of points that must pass the tolerance check of the LSRP
N = 100 #Max number of trials in RANSAC before ending
S = 50 #Number of points to sample for RANSAC
S_LIM = 100 #mm, half the length of a side of the cube to draw around the randomly sampled point in RANSAC

LSRP_list = []
# Log file locations 
sample_logs = '../../../sample_logs/'
#single_scan = '../../sample_logs/Static-sweep0_11-26-19.log'
#single_scan = '../../sample_logs/Static-sweep1_11-26-19.log'
##single_scan = '../../sample_logs/Static-sweep_11-26-19.log'
##single_scan = '../../sample_logs/dynamic_12-26-19_2252.log'
#single_scan = '../../sample_logs/Dynamic-sweep_11-26-19.log'
#single_scan = '../../sample_logs/Sweep2_11-22-19.log'
##lidar_4 = '../../sample_logs/attempt-4-lidar.log'
##angle_4 = '../../sample_logs/attempt-4.log'
##lidar_5 = '../../sample_logs/attempt-5-lidar.log'
##angle_5 = '../../sample_logs/attempt-5.log'
##lidar_6 = '../../sample_logs/attempt-6-lidar.log'
##angle_6 = '../../sample_logs/attempt-6.log'

##parsed_log_file = '2020-1-9_22-28-2-DIAGNOSTIC_RUN.txt'
##parsed_log_file = '2020-1-9_22-42-41-NICK1.txt'
##parsed_log_file = '2020-1-9_22-44-47-NICK2.txt'
##parsed_log_file = '2020-1-9_22-53-29-LIGHTSOUT.txt'
##parsed_log_file = '2020-1-9_22-53-55-LIGHTSOUTNICK.txt'
##parsed_log_file = '2020-1-9_22-54-27-MOVINGNICK.txt'
##parsed_log_file = '2020-1-9_22-57-23-BALLBOX.txt'
##parsed_log_file = '2020-1-9_22-59-1-BALLRAISEDBOX.txt'
##parsed_log_file = '2020-1-9_22-58-33-SNOWMAN.txt'p

##parsed_log_file = 'test_2-23-20.txt'
parsed_log_file = 'test0_2-23-20.txt'
##parsed_log_file = 'test1_2-23-20.txt'
parsed_log_file = sample_logs + parsed_log_file

x = [[0.0], [0.0], [0.0], [6.0], [3.0], [1.0]]
dx_sum = np.zeros((3,1))
P = np.zeros((6,6))
Landmark_Positions = {1:3}
dt1 = 0.0
dt2 = 0.0 #In reality, these would be grabbed from the Arduino.

####res = PARSER.parser(lidar_4)
##lidar_p4 = PARSER.parser(lidar_4)
##lidar_p5 = PARSER.parser(lidar_5)
##lidar_p6 = PARSER.parser(lidar_6)
##
##angle_p4 = ANGLEPARSE.angle_parser(angle_4)
##angle_p5 = ANGLEPARSE.angle_parser(angle_5)
##angle_p6 = ANGLEPARSE.angle_parser(angle_6)
with open(parsed_log_file, 'r') as file:
    stringdicts = file.readlines()
    res = []
    for stringdict in stringdicts:
        newdict = ast.literal_eval(stringdict)
        newdict['Motor encoder'] = float(newdict['Motor encoder'])
        res.append(newdict)
##res = ANGLEPARSE.merge(angle_p4,lidar_p4) #This line takes the angle values and merges them with the lidar values.
i=0
lenres = len(res)
print("Successfully parsed the scan! Now removing empty messages and sorting scans by frames...")
while i<lenres:
# These are only included so that RANSAC can run its sampling algorithm
#angle_increment = np.radians(res[index]['Angular Increment']) #for when the angle increment value is returned correctly by the parser
#
#This for loop will simulate receiving a continuous stream of scans from the LIDAR
    if res[i]['Angular Increment']=='' or res[i]['Quantity']!=len(res[i]['Measurement']): #sometimes, the dynamic scan returns blank dictionary. this removes it
        del res[i]
        lenres = len(res)
    else:
        i += 1
        
frame = []
for i in range(0, len(res), 1):
    frame.append(res[i])

xk_1 = np.asarray([[RANSAC.calculateQ(frame[0]['Motor encoder']*np.pi/180,np.pi/2)],[RANSAC.calculateQ(frame[0]['Motor encoder']*np.pi/180,0)],[0]])
Pk_1 = np.eye(3)
tk_1 = frame[0]['Time of transmission']
frame[0]['Euler'] = xk_1

error = [0]
errorphi = [0]
errortheta = [0]
errorpsi = [0]
Pnorm = [1]
Qk = np.diag([1, 1, 100])
Rk = np.diag([1, 1, 1])

for i in range(1,len(frame),1):
    theta_m = frame[i]['Motor encoder']*np.pi/180
    omega = [[frame[i]['Gx']],[frame[i]['Gy']],[frame[i]['Gz']]]
    dt = frame[i]['Time of transmission']-tk_1
    (xk, Pk) = KALMAN.KALMAN(xk_1, Pk_1, theta_m, omega, dt, Qk, Rk)
    xk_1 = xk
    Pk_1 = Pk
    errorvec = xk-KALMAN.Gravity([[frame[i]['Ax']],[frame[i]['Ay']],[frame[i]['Az']]])
    errorphi.append(errorvec[0])
    errortheta.append(errorvec[1])
    errorpsi.append(errorvec[2])
    error.append(np.linalg.norm(errorvec))
    Pnorm.append(np.linalg.norm(Pk))
    tk_1 = frame[i]['Time of transmission']
    frame[i]['Euler'] = xk
    print(Pk)
##    print(dt)
##kalmanscan = RANSAC.ConvertToCartesianEulerAngles(frame)
##scan = RANSAC.ConvertToCartesian(frame)
##lenscan = len(scan)
indices = range(0,len(error),1)
plt.plot(indices,error, indices, errorphi, indices, errortheta, indices, errorpsi, indices, Pnorm)
plt.legend(("norm", "phi", "theta", "psi", "P_Norm"))
plt.show()



#for plotting the points later
##xsk = []
##ysk = []
##zsk = []
##for point in kalmanscan.values():
##    xsk.append(point[0][0])
##    ysk.append(point[1][0])
##    zsk.append(point[2][0])
##
##xs = []
##ys = []
##zs = []
##for point in scan.values():
##    xs.append(point[0])
##    ys.append(point[1])
##    zs.append(point[2])
##
##fig = plt.figure()
##plt.clf()
##ax = Axes3D(fig)
##ax.scatter(xs, ys, zs, s=1, marker='o', color='r')
##ax.scatter(xsk, ysk, zsk, s=1, color='b')
####    ax.scatter(xfs, yfs, zfs, s=1, marker='x', color='b')
##ax.set_xlabel('X')
##ax.set_ylabel('Y')
##ax.set_zlabel('Z')
##ax.set_xlim3d(-3000, 3000)
##ax.set_ylim3d(-3000, 3000)
####    ax.set_zlim3d(-2000, 2000)
##RANSAC.plotLSRPs(ax, LSRP_list, ymax=7000)
##ax.view_init(45, -90)
##plt.show(False)