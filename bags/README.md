# Bag Explanation
Each bag file captures the data from all available published topics while running the particle filter. All bag files are collected using the `ac109_1` map.

## default
* This is the final optimization that we landed on
* A probability function:
    * <img src="https://latex.codecogs.com/gif.latex?f(x) = \frac{1}{(.1x)^{2}+1}" /> 
* 300 particles

Results

* The particle filter works relatively well given a good intial estimate with 2D Pose Estimate. The robot estimation follows the ground truth red arrow most of the time.
* The probability function doesn't allow the particles to converge too much which is good in that the robot pose estimation won't ever be skewed too far one way.

## aggresive_convergence
* A probability function:
    * <img src="https://latex.codecogs.com/gif.latex?f(x) = \frac{1}{x^{2}+1}" /> 
* 300 particles

Results

* The particle filter performs worse than the default as it lags behind and is often biased toward a direction
* The probability function is more steep for accurate particles. Because of this the particles converge too easily, not allowing for enough diversity between particles to correctly adjust in the map.

## less_particles
* A probability function:
    * <img src="https://latex.codecogs.com/gif.latex?f(x) = \frac{1}{(.1x)^{2}+1}" /> 
* 100 particles

Results

* The particle filter performs as good as the default or slightly worse.
* With fewer particles, the partile filter still seems to run fairly accurately. However, because there are less particles, they do not cover as much ground and possible variations resulting in some lacking resolution.