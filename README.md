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

In addition to the implementation of these steps, we also wanted to push the code a little further and visualize the weights of each particle in rviz. Not only would it provide a nice visual representation of how the particle filter works, but it would prove a valuable time-saving tool when debugging the code.

### 2. Code Structure
(maybe a flow diagram for code here?)
#### 2.1 Initialize Particles

#### 2.2 Update Particles with Odom
#### 2.3 Weight Particles
#### 2.4 Resample Particles
#### 2.5 Update Robot Pose

### 3. Looking Back
#### 3.1 Compromises
Once the basic concepts of the particle filter were functional, we looked towards optimizing the accuracy of the pose estimate. As stated in section 2.3, the particles were weighted using the algebraic equation: 1/((.1x^2)+1). In this model, .1 represents the steepness of the curve as it goes towards its maximum (large values resulting in a pointy peak, small numbers resulting in a broad peak). Changing this value affected the distribution of particle weights. We noticed that, when this value was around one, the particles were converging on the robot almost immediately, but would not align with the true pose. On the other end of the spectrum, spreading the particles too wide meant that they would not be able to agree on a single location for the pose. With this information, we decided to lean towards a broader particle spread, as an uncertain estimate was favorable to an incorrect one.
#### 3.2 Challenges
A reccurring obstacle during this project was moving between different reference frames. While a few helper functions were given in the scaffolded version of this code, it was difficult to determine when and where a transformation had to be made. This issue led to a slightly larger problem when we misinterpreted the strategy to weight each particle. Rather than translating lidar scan points, we were directly comparing the closest distance of the robot to that of each particle. This set us back in the project, but also provided an opportunity to work on other steps. By the time it was understood that our weigh particles section required modification, it was relativily easy to test the results in rviz immediately.
#### 3.3 What Went Well
Although this project had challenges, two aspects that went particularly well for us were how we weighted the particles and inserted noise. Both of these factors significanlty impacted the accuracy of the robot pose estimate, and both were written clearly and in strategic locations. It was valuable to have parameters whose affect on the robot was well understood, and easily changed. This left us some extra buffer space from imperfections in other parts of the code, such as the particle update with Odom section.

### 4. Looking Forward
#### 4.1 Future Improvements
If given more time on the project, we would first like to further refine the pose estimate. Ideally, the particle filter would be able to guess the pose with a high certainty. We would like to see the particles spread out slightly for each resampling, then tightly converge when updated with the LIDAR. These qualities describe the begining of a very robust particle filter. After this, it may be interesting to return values from the filter to quantify certainty, accuracy, and other metrics. With such information we would be able to methodically optimize the particle filter with the adjustment of a few variables.
Possibly beyond the scope of our current abilities, it may be worthwile to combine the particle filter with other robotic concepts, like room mapping. Such programs could allow a robot to 'remember' a room, and locate features out of its view.
#### 4.2 Lessons Learned
