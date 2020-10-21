# Robot Localization Project
Richard Gao & Loren Lyttle

### 1. Project overview
#### 1.1 Description
This project's purpose was to understand, create, and implement the key aspects of a particle filter. Particle filters are increasingly significant in the world today as robots are introduced to non-experimental environments. In this context, we were tasked with getting a Neato robot to locate itself on a given map using primarily wheel encoder and LIDAR measurments. The general plan for the project was to use a bag file, taken with the help of ROS's gmapping feature, and a guess at the robot's initial pose. In running our particle filter, we would slowly refine the estimate of the robot's position until it closely matched the true path it took.
#### 1.2 Project Goals
The basic structure of a particle filter has 5 components. In succesfully constructing a particle filter, these 5 key steps are repeated to estimate the Neato's position in the map over the course of the excecution:

1. Initialize a span of particles in the map either randomly or over a gaussian distribution.
2. Update the particles with reference to the Neato's movement in Odom.
3. Calculate the weights of each particle based on the resemblence of their surroundings to the Neato's.
4. Resample particles with probability proportional to their wegihts.
5. Using the particle field, update the estimated pose of the robot.


### 2. Code Structure
(maybe a flow diagram for code here?)
#### 2.1 Initialize Particles
#### 2.2 Update Particles with Odom
#### 2.3 Weight Particles
#### 2.4 Resample Particles
#### 2.5 Update Robot Pose

### 3. Looking Back
#### 3.1 Challenges
There were a few times during this project when the challenges rose high enough to impede further progress. 
#### 3.2 What went well
Although this project had challenges, two aspects that went particularly well for us were how we weighted the particles and inserted noise. Both of these factors significanlty impacted the accuracy of the robot pose estimate, and both were written clearly and in strategic locations. It was valuable to have parameters whose affect on the robot was well understood, and easily changed. This left us some extra buffer space from imperfections in other parts of the code, such as the particle update with Odom section.

### 4. Looking Forward
#### 4.1 Future Improvements
#### 4.2 Lessons Learned
