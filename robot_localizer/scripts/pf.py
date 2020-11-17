#!/usr/bin/env python3

""" This is the starter code for the robot localization project """

import rospy

from std_msgs.msg import Header, String
from sensor_msgs.msg import LaserScan, PointCloud
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped, PoseArray, Pose, Point, Quaternion
from visualization_msgs.msg import Marker, MarkerArray
from nav_msgs.srv import GetMap
from copy import deepcopy

import tf
from tf import TransformListener
from tf import TransformBroadcaster
from tf.transformations import euler_from_quaternion, rotation_matrix, quaternion_from_matrix
from random import gauss

import math
import time

from scipy.stats import norm
import numpy as np
from numpy.random import random_sample
from sklearn.neighbors import NearestNeighbors
from occupancy_field import OccupancyField
from helper_functions import TFHelper
from functools import reduce

class Particle(object):
    """ Represents a hypothesis (particle) of the robot's pose consisting of x,y and theta (yaw)
        Attributes:
            x: the x-coordinate of the hypothesis relative to the map frame
            y: the y-coordinate of the hypothesis relative ot the map frame
            theta: the yaw of the hypothesis relative to the map frame
            w: the particle weight (the class does not ensure that particle weights are normalized
    """

    def __init__(self,x=0.0,y=0.0,theta=0.0,w=1.0):
        """ Construct a new Particle
            x: the x-coordinate of the hypothesis relative to the map frame
            y: the y-coordinate of the hypothesis relative ot the map frame
            theta: the yaw of the hypothesis relative to the map frame
            w: the particle weight (the class does not ensure that particle weights are normalized """ 
        self.w = w
        self.theta = theta
        self.x = x
        self.y = y

    def as_pose(self):
        """ A helper function to convert a particle to a geometry_msgs/Pose message """
        orientation_tuple = tf.transformations.quaternion_from_euler(0,0,self.theta)
        return Pose(position=Point(x=self.x,y=self.y,z=0), orientation=Quaternion(x=orientation_tuple[0], y=orientation_tuple[1], z=orientation_tuple[2], w=orientation_tuple[3]))

    def as_marker(self, id):
        """ A helper function to create visualization_msgs/Marker to visualize particle weights shown by alpha"""
        marker = Marker()
        marker.header.frame_id = "map"
        marker.header.stamp = rospy.Time.now()
        marker.ns = "particle"
        marker.id = id
        marker.type = Marker.ARROW
        marker.action = Marker.ADD
        marker.pose = self.as_pose()
        marker.scale.x = 0.5
        marker.scale.y = 0.1
        marker.scale.z = 0.1
        marker.color.a = self.w
        marker.color.r = 0.0
        marker.color.g = 0.0
        marker.color.b = 1.0
        return marker

class ParticleFilter:
    """ The class that represents a Particle Filter ROS Node
        Attributes list:
            initialized: a Boolean flag to communicate to other class methods that initializaiton is complete
            base_frame: the name of the robot base coordinate frame (should be "base_link" for most robots)
            map_frame: the name of the map coordinate frame (should be "map" in most cases)
            odom_frame: the name of the odometry coordinate frame (should be "odom" in most cases)
            scan_topic: the name of the scan topic to listen to (should be "scan" in most cases)
            n_particles: the number of particles in the filter
            d_thresh: the amount of linear movement before triggering a filter update
            a_thresh: the amount of angular movement before triggering a filter update
            laser_max_distance: the maximum distance to an obstacle we should use in a likelihood calculation
            pose_listener: a subscriber that listens for new approximate pose estimates (i.e. generated through the rviz GUI)
            particle_pub: a publisher for the particle cloud
            laser_subscriber: listens for new scan data on topic self.scan_topic
            tf_listener: listener for coordinate transforms
            tf_broadcaster: broadcaster for coordinate transforms
            particle_cloud: a list of particles representing a probability distribution over robot poses
            current_odom_xy_theta: the pose of the robot in the odometry frame when the last filter update was performed.
                                   The pose is expressed as a list [x,y,theta] (where theta is the yaw)
            map: the map we will be localizing ourselves in.  The map should be of type nav_msgs/OccupancyGrid
    """
    def __init__(self):
        self.initialized = False        # make sure we don't perform updates before everything is setup
        rospy.init_node('pf')           # tell roscore that we are creating a new node named "pf"

        self.base_frame = "base_link"   # the frame of the robot base
        self.map_frame = "map"          # the name of the map coordinate frame
        self.odom_frame = "odom"        # the name of the odometry coordinate frame
        self.scan_topic = "scan"        # the topic where we will get laser scans from 

        self.n_particles = 300          # the number of particles to use

        self.d_thresh = 0.2             # the amount of linear movement before performing an update
        self.a_thresh = math.pi/6       # the amount of angular movement before performing an update

        self.laser_max_distance = 2.0   # maximum penalty to assess in the likelihood field model

        # Setup pubs and subs

        # pose_listener responds to selection of a new approximate robot location (for instance using rviz)
        rospy.Subscriber("initialpose", PoseWithCovarianceStamped, self.update_initial_pose)

        # publish the current particle cloud.  This enables viewing particles in rviz.
        self.particle_pub = rospy.Publisher("particlecloud", PoseArray, queue_size=10)
        self.weight_pub = rospy.Publisher('visualization_marker', MarkerArray, queue_size=10)

        # laser_subscriber listens for data from the lidar
        rospy.Subscriber(self.scan_topic, LaserScan, self.scan_received)

        # enable listening for and broadcasting coordinate transforms
        self.tf_listener = TransformListener()
        self.tf_broadcaster = TransformBroadcaster()

        # Holds all particles
        self.particle_cloud = []
        # Holds pre-normalized probabilities for each particle
        self.scan_probabilities = []

        # change use_projected_stable_scan to True to use point clouds instead of laser scans
        self.use_projected_stable_scan = False
        self.last_projected_stable_scan = None
        if self.use_projected_stable_scan:
            # subscriber to the odom point cloud
            rospy.Subscriber("projected_stable_scan", PointCloud, self.projected_scan_received)

        self.current_odom_xy_theta = []
        self.occupancy_field = OccupancyField()
        self.transform_helper = TFHelper()
        self.initialized = True

    def update_robot_pose(self, timestamp):
        """ Update the estimate of the robot's pose given the updated particles.
            There are two logical methods for this:
                (1): compute the mean pose
                (2): compute the most likely pose (i.e. the mode of the distribution)
        """
        # first make sure that the particle weights are normalized
        self.normalize_particles()

        # Calculate the mean pose
        if self.particle_cloud:
            mean_x, mean_y, mean_theta = 0, 0, 0
            for particle in self.particle_cloud:
                mean_x += particle.x
                mean_y += particle.y
                mean_theta += particle.theta
            mean_x /= len(self.particle_cloud)
            mean_y /= len(self.particle_cloud)
            mean_theta /= len(self.particle_cloud)
            self.robot_pose = Particle(mean_x, mean_y, mean_theta).as_pose()
        else:
            self.robot_pose = Pose()

        self.transform_helper.fix_map_to_odom_transform(self.robot_pose, timestamp)

    def projected_scan_received(self, msg):
        self.last_projected_stable_scan = msg

    def update_particles_with_odom(self, msg):
        """ Update the particles using the newly given odometry pose.
            The function computes the value delta which is a tuple (x,y,theta)
            that indicates the change in position and angle between the odometry
            when the particles were last updated and the current odometry.

            msg: this is not really needed to implement this, but is here just in case.
        """
        new_odom_xy_theta = self.transform_helper.convert_pose_to_xy_and_theta(self.odom_pose.pose)
        # compute the change in x,y,theta since our last update
        if self.current_odom_xy_theta:
            old_odom_xy_theta = self.current_odom_xy_theta
            delta = (new_odom_xy_theta[0] - self.current_odom_xy_theta[0],
                     new_odom_xy_theta[1] - self.current_odom_xy_theta[1],
                     new_odom_xy_theta[2] - self.current_odom_xy_theta[2])

            self.current_odom_xy_theta = new_odom_xy_theta
        else:
            self.current_odom_xy_theta = new_odom_xy_theta
            return

        # Modify particles using delta and inject noise.
        for particle in self.particle_cloud:
            # Step 1: turn particles in direction of translation
            # Compute the unit vector of the desired heading to move in
            heading_mag = math.sqrt(delta[0]**2 + delta[1]**2)
            heading_uv = np.array([delta[0] / heading_mag, delta[1] / heading_mag])
            
            # Compute the unit vector of the robot's current heading
            robot_uv = np.array([np.cos(self.current_odom_xy_theta[2]), np.sin(self.current_odom_xy_theta[2])])
            
            # Calculate the angle r_1 that is between the current heading and target heading
            r_1 = np.arccos(np.dot(robot_uv, heading_uv))

            particle.theta += r_1 + np.random.normal(scale=.05)
            
            # Step 2: move particles forward distance of translation
            d = math.sqrt(delta[0]**2 + delta[1]**2) + np.random.normal(scale=.05)
            # Decompose the translation vector into x and y componenets
            particle.x += d * np.cos(particle.theta)
            particle.y += d * np.sin(particle.theta)
            
            # Step 3: turn particles to final angle
            r_2 = delta[2] - r_1
            particle.theta += r_2

    def map_calc_range(self,x,y,theta):
        """ Difficulty Level 3: implement a ray tracing likelihood model... Let me know if you are interested """
        # TODO: nothing unless you want to try this alternate likelihood model
        pass

    def resample_particles(self):
        """ Resample the particles according to the new particle weights.
            The weights stored with each particle should define the probability that a particular
            particle is selected in the resampling step.  You may want to make use of the given helper
            function draw_random_sample.
        """
        # make sure the distribution is normalized
        self.normalize_particles()
        weights = []
        for particle in self.particle_cloud:
            weights.append(particle.w)

        choices = self.draw_random_sample(self.particle_cloud, weights, self.n_particles)

        # Reset particle cloud
        self.particle_cloud = []
        # Populate particle cloud with sampled choices
        for chosen_particle in choices:
            self.particle_cloud.append(Particle(chosen_particle.x, chosen_particle.y, chosen_particle.theta, chosen_particle.w))

    def update_particles_with_laser(self, msg):
        """ Updates the particle weights in response to the scan contained in the msg """
        lidar_scan_angles = range(360)

        # Populates lidar_scan list with (theta, distance) for each lidar scan angle
        lidar_scan = []
        for theta in lidar_scan_angles:
            distance = msg.ranges[theta]
            point = (theta, distance)
            lidar_scan.append(point)

        # Calculates the probability that each particle is the best estimate for the robot location 
        self.scan_probabilities = []
        for p in self.particle_cloud:
            particle_theta_prob = []
            for point in lidar_scan:
                x_vector = p.x + point[1] * math.cos(math.radians(point[0]) + p.theta)
                y_vector = p.y + point[1] * math.sin(math.radians(point[0]) + p.theta)
                closest_object = self.occupancy_field.get_closest_obstacle_distance(x_vector, y_vector)
                # Calculate probabilities using a tuned function
                particle_theta_prob.append(1/((0.1*closest_object)**2+1))

            # Combine probability at every theta for every particle
            self.scan_probabilities.append(reduce(lambda a, b: a*b, particle_theta_prob))
        
    @staticmethod
    def draw_random_sample(choices, probabilities, n):
        """ Return a random sample of n elements from the set choices with the specified probabilities
            choices: the values to sample from represented as a list
            probabilities: the probability of selecting each element in choices represented as a list
            n: the number of samples
        """
        values = np.array(range(len(choices)))
        probs = np.array(probabilities)
        bins = np.add.accumulate(probs)
        inds = values[np.digitize(random_sample(n), bins)]
        samples = []
        for i in inds:
            samples.append(deepcopy(choices[int(i)]))
        return samples

    def update_initial_pose(self, msg):
        """ Callback function to handle re-initializing the particle filter based on a pose estimate.
            These pose estimates could be generated by another ROS Node or could come from the rviz GUI """
        xy_theta = self.transform_helper.convert_pose_to_xy_and_theta(msg.pose.pose)
        self.initialize_particle_cloud(msg.header.stamp, xy_theta)

    def initialize_particle_cloud(self, timestamp, xy_theta=None):
        """ Initialize the particle cloud.
            Arguments
            xy_theta: a triple consisting of the mean x, y, and theta (yaw) to initialize the
                      particle cloud around.  If this input is omitted, the odometry will be used """
        if xy_theta is None:
            xy_theta = self.transform_helper.convert_pose_to_xy_and_theta(self.odom_pose.pose)
        
        # Create particles based on gaussian distribution centered around xy_theta
        self.particle_cloud = [] 
        for g in range(self.n_particles):
            x = np.random.normal(xy_theta[0], scale=0.3)
            y = np.random.normal(xy_theta[1], scale=0.3)
            theta = np.random.normal(xy_theta[2], scale=0.1)
            self.particle_cloud.append(Particle(x, y, theta, 1))

        self.normalize_particles()
        self.update_robot_pose(timestamp)

    def normalize_particles(self):
        """ Make sure the particle weights define a valid distribution (i.e. sum to 1.0) """
        # Check if scan probabilities has been populated for each particle
        if len(self.scan_probabilities) == len(self.particle_cloud):
            sum_of_prob = sum(self.scan_probabilities)

            for i, particle in enumerate(self.particle_cloud):
                particle.w = self.scan_probabilities[i] / sum_of_prob

    def publish_particles(self, msg):
        particles_conv = []
        for p in self.particle_cloud:
            particles_conv.append(p.as_pose())
        # actually send the message so that we can view it in rviz
        self.particle_pub.publish(PoseArray(header=Header(stamp=rospy.Time.now(),
                                            frame_id=self.map_frame),
                                  poses=particles_conv))
    
    def publish_weights(self, msg):
        # Visualize particle weights in rviz to get a better debug each particle
        weight_markers = MarkerArray()
        for i, particle in enumerate(self.particle_cloud):
            weight_markers.markers.append(particle.as_marker(i))
        self.weight_pub.publish(weight_markers)

    def scan_received(self, msg):
        """ This is the default logic for what to do when processing scan data.
            Feel free to modify this, however, we hope it will provide a good
            guide.  The input msg is an object of type sensor_msgs/LaserScan """
        if not(self.initialized):
            # wait for initialization to complete
            return

        # wait a little while to see if the transform becomes available.  This fixes a race
        # condition where the scan would arrive a little bit before the odom to base_link transform
        # was updated.
        self.tf_listener.waitForTransform(self.base_frame, msg.header.frame_id, msg.header.stamp, rospy.Duration(0.5))
        if not(self.tf_listener.canTransform(self.base_frame, msg.header.frame_id, msg.header.stamp)):
            # need to know how to transform the laser to the base frame
            # this will be given by either Gazebo or neato_node
            return

        if not(self.tf_listener.canTransform(self.base_frame, self.odom_frame, msg.header.stamp)):
            # need to know how to transform between base and odometric frames
            # this will eventually be published by either Gazebo or neato_node
            return

        # calculate pose of laser relative to the robot base
        p = PoseStamped(header=Header(stamp=rospy.Time(0),
                                      frame_id=msg.header.frame_id))
        self.laser_pose = self.tf_listener.transformPose(self.base_frame, p)

        # find out where the robot thinks it is based on its odometry
        p = PoseStamped(header=Header(stamp=msg.header.stamp,
                                      frame_id=self.base_frame),
                        pose=Pose())
        self.odom_pose = self.tf_listener.transformPose(self.odom_frame, p)
        # store the the odometry pose in a more convenient format (x,y,theta)
        new_odom_xy_theta = self.transform_helper.convert_pose_to_xy_and_theta(self.odom_pose.pose)
        if not self.current_odom_xy_theta:
            self.current_odom_xy_theta = new_odom_xy_theta
            return

        if not(self.particle_cloud):
            # now that we have all of the necessary transforms we can update the particle cloud
            self.initialize_particle_cloud(msg.header.stamp)
        elif (math.fabs(new_odom_xy_theta[0] - self.current_odom_xy_theta[0]) > self.d_thresh or
              math.fabs(new_odom_xy_theta[1] - self.current_odom_xy_theta[1]) > self.d_thresh or
              math.fabs(new_odom_xy_theta[2] - self.current_odom_xy_theta[2]) > self.a_thresh):
            # we have moved far enough to do an update!
            self.update_particles_with_odom(msg)    # update based on odometry
            if self.last_projected_stable_scan:
                last_projected_scan_timeshift = deepcopy(self.last_projected_stable_scan)
                last_projected_scan_timeshift.header.stamp = msg.header.stamp
                self.scan_in_base_link = self.tf_listener.transformPointCloud("base_link", last_projected_scan_timeshift)

            self.update_particles_with_laser(msg)   # update based on laser scan
            self.update_robot_pose(msg.header.stamp)                # update robot's pose
            self.resample_particles()               # resample particles to focus on areas of high density
        # publish particles (so things like rviz can see them)
        self.publish_particles(msg)
        self.publish_weights(msg)

if __name__ == '__main__':
    n = ParticleFilter()
    r = rospy.Rate(5)

    while not(rospy.is_shutdown()):
        # in the main loop all we do is continuously broadcast the latest map to odom transform
        n.transform_helper.send_last_map_to_odom_transform()
        r.sleep()
