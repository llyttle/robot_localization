# Robot Localization Project
Richard Gao & Loren Lyttle

### 1. Project overview
#### 1.1 Description
This project's purpose was to understand, create, and implement the key aspects of a particle filter. Particle filters are increasingly significant in the world today as robots are introduced to non-experimental environments. In this context, we were tasked with getting a Neato robot to locate itself on a given map using primarily wheel encoder and LIDAR measurements. The general plan for the project was to use a bag file, taken with the help of ROS's gmapping feature, and a guess at the robot's initial pose. In running our particle filter, we would slowly refine the estimate of the robot's position until it closely matched the true path it took.
#### 1.2 Project Goals
The basic structure of a particle filter has 5 components. In successfully constructing a particle filter, these 5 key steps are repeated to estimate the Neato's position in the map over the course of the execution:

1. Initialize a span of particles in the map either randomly or over a gaussian distribution.
2. Update the particles with reference to the Neato's movement in Odom.
3. Calculate the weights of each particle based on the resembelance of their surroundings to the Neato's.
4. Resample particles with probability proportional to their weights.
5. Using the particle field, update the estimated pose of the robot.

In addition to the implementation of these steps, we wanted to push the code a little further and visualize the weights of each particle in rviz. Not only would it provide a nice visual representation of how the particle filter works, but it would prove a valuable time-saving tool when debugging the code.

### 2. Code Structure
(maybe a flow diagram for code here?)
#### 2.1 Initialize Particles
In this step particles are placed onto the map in semi-random orientations. We chose to initialize the particles around the robot with thier positions selected from a gaussian distribution. This ensured that each time the particle field was initialized, they would stay around the robot while still being able to adapt to most translations. We chose the value of 0.3 for the standard deviation of the distribution; reasonably small because we were confident that our initial estimate of the robot pose was accurate. A gaussian distribution was also drawn from to define the theta value of each particle. This time, the standard deviation was even smaller at 0.1. Because we manually set the initial estimate, we were confident that its orientation would be very similar to that of the true pose. All particles started with identical weights of 1. These parameters were simple to conceptualize, and worked reasonably well throughout the project.

<p align="center">
![alt text](https://github.com/hardlyrichie/robot_localization/blob/master/media/pasted%20image%200.png "normal_dist")
</p>

Another possible course for this step was to evenly distribute particles across the entire map. This would be beneficial if the initial pose estimate was very uncertain becuase most of the map can be tested. In the previously mentioned model, it was a requirement that the initial pose was close to the true pose.
#### 2.2 Update Particles with Odom
To update the particles with odom, we first believed that simply adding delta[0] and delta[1] to each particle's location would be sufficient. However, this does not account for the difference between the odom and map frames. 
#### 2.3 Weigh Particles
remember to talk about normalizing
#### 2.4 Resample Particles
#### 2.5 Update Robot Pose

### 3. Looking Back
#### 3.1 Compromises
Once the basic concepts of the particle filter were functional, we looked towards optimizing the accuracy of the pose estimate. As stated in section 2.3, the particles were weighted using the algebraic equation: 1/((.1x^2)+1). In this model, .1 represents the steepness of the curve as it goes towards its maximum (large values resulting in a pointy peak, small numbers resulting in a broad peak). Changing this value affected the distribution of particle weights. We noticed that, when this value was around one, the particles were converging on the robot almost immediately, but would not align with the true pose. On the other end of the spectrum, spreading the particles too wide meant that they would not be able to agree on a single location for the pose. With this information, we decided to lean towards a broader particle spread, as an uncertain estimate was favorable to an incorrect one.
#### 3.2 Challenges
A recurring obstacle during this project was moving between different reference frames. While a few helper functions were given in the scaffolded version of this code, it was difficult to determine when and where a transformation had to be made. This issue led to a slightly larger problem when we misinterpreted the strategy to weight each particle. Rather than translating lidar scan points, we were directly comparing the closest distance of the robot to that of each particle. This set us back in the project, but also provided an opportunity to work on other steps. By the time it was understood that our weigh particles section required modification, it was relatively easy to test the results in rviz immediately.
#### 3.3 What Went Well
Although this project had challenges, two aspects that went particularly well for us were how we weighted the particles and inserted noise. Both of these factors significantly impacted the accuracy of the robot pose estimate, and both were written clearly and in strategic locations. It was valuable to have parameters whose affect on the robot was well understood, and easily changed. This left us some extra buffer space from imperfections in other parts of the code, such as the particle update with Odom section.

### 4. Looking Forward
#### 4.1 Future Improvements
If given more time on the project, we would first like to further refine the pose estimate. Ideally, the particle filter would be able to guess the pose with a high certainty. We would like to see the particles spread out slightly for each resampling, then tightly converge when updated with the LIDAR. These qualities describe the beginning of a very robust particle filter. After this, it may be interesting to return values from the filter to quantify certainty, accuracy, and other metrics. With such information we would be able to methodically optimize the particle filter with the adjustment of a few variables.
Possibly beyond the scope of our current abilities, it may be worthwhile to combine the particle filter with other robotic concepts, like room mapping. Such programs could allow a robot to 'remember' a room, and locate features out of its view.
#### 4.2 Lessons Learned
