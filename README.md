# Bài thực hành 04 — TurtleBot 4

Nguyễn Văn Tổng · 23020766 · K68E-RE

Bài này dùng TurtleBot 4 trong Gazebo để xây dựng bản đồ bằng SLAM Toolbox,
lưu bản đồ, định vị bằng AMCL và điều hướng bằng Nav2. Môi trường thực hiện
là Ubuntu 24.04, ROS 2 Jazzy và Gazebo Harmonic.

Robot dùng model của `nav2_minimal_tb4_sim`. World `hri_lab.sdf` có tường,
hai vách ngăn và một cột; các vật thể được khai báo cục bộ nên không cần tải
world từ Gazebo Fuel.

## Cài đặt và build

Máy cần có ROS 2 Jazzy. Cài các package còn thiếu:

```bash
sudo apt update
sudo apt install ros-jazzy-nav2-bringup \
  ros-jazzy-nav2-minimal-tb4-sim \
  ros-jazzy-slam-toolbox \
  ros-jazzy-tf2-tools \
  ros-jazzy-rviz2
```

Clone và build:

```bash
git clone https://github.com/VTongg159/hri-assignment-04.git
cd hri-assignment-04
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
export ROS_DOMAIN_ID=19
```

Trong mỗi terminal mới, vào thư mục repo rồi chạy:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=19
```

## Tạo bản đồ

Terminal 1 chạy Gazebo và RViz:

```bash
ros2 launch hri_turtlebot4_navigation simulation.launch.py
```

Terminal 2 chạy SLAM Toolbox:

```bash
ros2 launch hri_turtlebot4_navigation mapping.launch.py
```

Terminal 3 điều khiển robot:

```bash
ros2 run hri_turtlebot4_navigation wasd_teleop.py
```

`W/S` tiến/lùi, `A/D` quay trái/phải. Space hoặc `X` dừng, `Q` hoặc `Ctrl+C`
thoát. Giữ phím để di chuyển. Robot dừng khi không nhận phím trong 0,5 giây.
Tốc độ mặc định là 0,15 m/s và 0,60 rad/s; có thể giảm khi mapping:

```bash
ros2 run hri_turtlebot4_navigation wasd_teleop.py --ros-args \
  -p linear_speed:=0.12 -p angular_speed:=0.45
```

Đặt Fixed Frame của RViz là `map`. Cho robot đi qua các khu vực chính, quay
chậm và quay lại một vài vị trí cũ. Kiểm tra tường không bị lệch hoặc nhân đôi
trước khi lưu bản đồ.

Trong terminal khác, từ thư mục gốc repo:

```bash
ros2 run nav2_map_server map_saver_cli \
  -f src/hri_turtlebot4_navigation/maps/map \
  --ros-args -p use_sim_time:=true \
  -p save_map_timeout:=10.0 \
  -p map_subscribe_transient_local:=true

ls -lh src/hri_turtlebot4_navigation/maps/map.yaml \
  src/hri_turtlebot4_navigation/maps/map.pgm
```

`map.pgm` chứa ảnh occupancy grid. `map.yaml` chứa độ phân giải, gốc bản đồ,
đường dẫn ảnh và ngưỡng occupied/free. Giữ cả hai file cùng nhau.

## Localization và Nav2

Dừng teleop, SLAM và simulation bằng `Ctrl+C`. Build lại để cập nhật map:

```bash
colcon build --symlink-install
source install/setup.bash
```

Khởi động lại cùng world trong terminal 1:

```bash
ros2 launch hri_turtlebot4_navigation simulation.launch.py
```

Terminal 2 nạp map và chạy AMCL:

```bash
ros2 launch hri_turtlebot4_navigation localization.launch.py
```

Trong RViz, dùng **2D Pose Estimate** đặt vị trí và hướng gần đúng của robot.
Scan cần khớp gần với tường trên map. Khi định vị ổn, chạy Nav2 ở terminal 3:

```bash
ros2 launch hri_turtlebot4_navigation navigation.launch.py
```

Kiểm tra hệ thống ở terminal khác:

```bash
ros2 run hri_turtlebot4_navigation verify_system.py
```

Thoát teleop trước khi gửi goal. Dùng **Nav2 Goal** chọn ba vùng trống khác nhau
trên RViz, kéo mũi tên đặt hướng và chờ từng goal kết thúc. Robot phải tự chạy
sau khi nhận goal. Chụp global path, costmap và kết quả của từng lần chạy.

## Khi robot chưa di chuyển

Kiểm tra các node đã active và costmap có publisher:

```bash
ros2 lifecycle get /map_server
ros2 lifecycle get /amcl
ros2 lifecycle get /planner_server
ros2 lifecycle get /controller_server
ros2 lifecycle get /bt_navigator
ros2 topic info /global_costmap/costmap
ros2 topic info /local_costmap/costmap
```

Nếu chỉ có AMCL và Map Server, cần chạy thêm `navigation.launch.py`.
Topic tồn tại nhưng publisher count bằng 0 nghĩa là chưa có node phát dữ liệu.

Nếu scan lệch tường, đặt lại **2D Pose Estimate**, kiểm tra đúng bản đồ và
chạy một simulation duy nhất. Không chạy SLAM cùng AMCL vì cả hai cùng cung cấp
TF `map → odom`.

## Topic và TF

| Topic | Kiểu message | Vai trò |
| --- | --- | --- |
| `/scan` | `sensor_msgs/msg/LaserScan` | Dữ liệu LiDAR |
| `/odom` | `nav_msgs/msg/Odometry` | Chuyển động cục bộ |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | Lệnh vận tốc |
| `/map` | `nav_msgs/msg/OccupancyGrid` | Bản đồ |
| `/tf`, `/tf_static` | `tf2_msgs/msg/TFMessage` | Quan hệ frame |
| `/amcl_pose` | `geometry_msgs/msg/PoseWithCovarianceStamped` | Pose từ AMCL |
| `/plan` | `nav_msgs/msg/Path` | Đường đi toàn cục |

Chuỗi TF: `map → odom → base_footprint → base_link → rplidar_link`.
SLAM hoặc AMCL cung cấp `map → odom`; odometry cung cấp chuyển động cục bộ.
Backend hiện tại nhận `Twist`; nếu đổi simulator, kiểm tra lại kiểu `/cmd_vel`.

## Cấu trúc repo

```text
src/hri_turtlebot4_navigation/
  launch/                     Simulation, mapping, localization, navigation
  config/                     Tham số SLAM và Nav2
  maps/                       map.yaml và map.pgm
  worlds/                     World hri_lab.sdf
  rviz/                       Cấu hình RViz
  scripts/                    WASD teleop và kiểm tra hệ thống
```

## Nguồn sử dụng

- [TurtleBot 4 User Manual](https://turtlebot.github.io/turtlebot4-user-manual/)
- [Nav2 minimal TurtleBot simulation](https://github.com/ros-navigation/nav2_minimal_turtlebot_simulation)
- [SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox)
- [Navigation2](https://github.com/ros-navigation/navigation2)

`nav2_params.yaml` dựa trên cấu hình mặc định của Nav2 Jazzy cài trên máy.
Các launch file gọi lại simulator và Nav2; phần bổ sung cho bài gồm world,
cấu hình SLAM, teleop WASD và script kiểm tra.
