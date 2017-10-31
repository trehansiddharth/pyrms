pyrms
=====

PyRMS is the Robot Module System for Python, a module system similar to ROS that
emphasizes safe and efficient data flow. It allows roboticists to focus on
robotics while PyRMS provides guarantees on program operation and perfmance. It
integrates well with scientific computing libraries such as NumPy and OpenCV.

Programs written using RMS are comprised of multiple `Module`s operating in
parallel and communicating information on a common `Interface`. RMS determines
which modules can operate independently of each other and which modules need
to operate in a certain order in order to prevent invalidating the data on the
`Interface`. Under the hood, `Modules`s are separate processes, and `Interface`s
consist of shared memory and a system of process locks.
