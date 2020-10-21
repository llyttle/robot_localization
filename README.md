# Robot Localization Project
Richard Gao & Loren Lyttle

### 1. Project overview
#### 1.1 Description
This project's purpose was to understand, create, and implement the key aspects of a particle filter. Particle filters are increasingly significant in the world today as robots are introduced to non-experimental environments. In this context, we were tasked with getting a Neato robot to locate itself on a given map using primarily wheel encoder and LIDAR measurments.
#### 1.2 Project Goals
The basic structure of a particle filter has 5 components. In succesfully constructing a particle filter, these 5 key steps are repeated to refine the estimate of the Neato's position in the map over the course excecution:

1. Initialize a span of particles in the map either randomly or over a gaussian distribution.
2. Update the particles with reference to the Neato's movement in Odom.
3. Calculate the weights of each particle based on the resemblence of their surroundings to the Neato's.
4. Resample particles with probability proportional to their wegihts.
5. Using the particle field, update the estimated pose of the robot.



### Code

### Difficult Choices

### Challenges

### Future Improvements

### Lessons Learned
