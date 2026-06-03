#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid, Odometry
from geometry_msgs.msg import PoseStamped
from action_msgs.msg import GoalStatus
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
import numpy as np
import math
import tf_transformations

class SmartExplorer(Node):
    def __init__(self):
        super().__init__('smart_explorer_v2')
        
        # المشتركون
        self.sub_map = self.create_subscription(OccupancyGrid, '/map', self.map_callback, 10)
        self.sub_odom = self.create_subscription(Odometry, '/X3/odom', self.odom_callback, 10)
        
        # عميل Nav2
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        self.map_data = None
        self.map_info = None
        self.current_pose = {'x': 0.0, 'y': 0.0, 'yaw': 0.0}
        self.is_navigating = False
        
        # متغير لتخزين الاتجاه السابق (للحفاظ على الزخم)
        self.last_target_yaw = None

        self.timer = self.create_timer(1.0, self.exploration_loop)
        self.get_logger().info('🧭 Smart Explorer V2: Forward Bias Enabled!')

    def odom_callback(self, msg):
        self.current_pose['x'] = msg.pose.pose.position.x
        self.current_pose['y'] = msg.pose.pose.position.y
        
        # تحويل الكواتيرنيون إلى زاوية دوران (Yaw)
        q = msg.pose.pose.orientation
        _, _, yaw = tf_transformations.euler_from_quaternion([q.x, q.y, q.z, q.w])
        self.current_pose['yaw'] = yaw

    def map_callback(self, msg):
        self.map_info = msg.info
        # تحويل البيانات لمصفوفة ثنائية الأبعاد لسهولة المعالجة
        self.map_data = np.array(msg.data).reshape((msg.info.height, msg.info.width))

    def get_best_frontier(self):
        if self.map_data is None: return None
        
        res = self.map_info.resolution
        origin_x = self.map_info.origin.position.x
        origin_y = self.map_info.origin.position.y
        
        # موقع الروبوت الحالى على الشبكة
        robot_grid_x = int((self.current_pose['x'] - origin_x) / res)
        robot_grid_y = int((self.current_pose['y'] - origin_y) / res)
        
        # البحث عن النقاط المجهولة (-1) المجاورة لنقاط حرة (0)
        # لتبسيط الحسابات، نأخذ عينة من النقاط المجهولة
        unknowns = np.argwhere(self.map_data == -1)
        
        if len(unknowns) == 0: return None

        # تقليل عدد النقاط للمعالجة (نأخذ نقطة كل 50 نقطة)
        candidates = unknowns[::50]
        
        best_score = float('inf')
        best_point = None
        
        # اتجاه حركة الروبوت الحالي
        current_yaw = self.current_pose['yaw']

        for pt in candidates:
            r, c = pt # row, col (y, x)
            
            # تحويل الإحداثيات لمتر
            real_x = c * res + origin_x
            real_y = r * res + origin_y
            
            dist = math.sqrt((real_x - self.current_pose['x'])**2 + 
                             (real_y - self.current_pose['y'])**2)
            
            # 1. تجاهل النقاط القريبة جداً (تم استكشافها) أو البعيدة جداً
            if dist < 1.0 or dist > 15.0:
                continue

            # 2. حساب زاوية الهدف بالنسبة للروبوت
            angle_to_target = math.atan2(real_y - self.current_pose['y'], 
                                         real_x - self.current_pose['x'])
            
            # 3. حساب الفرق بين اتجاه الروبوت واتجاه الهدف
            # (كم درجة يجب أن ألتف لأصل للنقطة؟)
            angle_diff = abs(angle_to_target - current_yaw)
            # تطبيع الزاوية لتكون بين 0 و PI
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff
            
            # === المعادلة السحرية (Cost Function) ===
            # التكلفة = المسافة + (عقوبة الالتفاف * الوزن)
            # كلما زاد الوزن (Heading Weight)، زاد إصرار الطائرة على المضي للأمام
            heading_weight = 4.0  # (يمكنك زيادة هذا الرقم لزيادة العناد)
            
            # إذا كانت النقطة خلفي (زاوية > 90)، العقوبة تتضاعف
            if angle_diff > (math.pi / 2):
                heading_weight *= 2.0

            score = dist + (angle_diff * heading_weight)
            
            if score < best_score:
                best_score = score
                best_point = (real_x, real_y)
        
        return best_point

    def send_goal(self, x, y):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.w = 1.0 # لا يهم الدوران النهائي حاليا
        
        self.nav_client.wait_for_server()
        self.is_navigating = True
        
        self.get_logger().info(f'🚀 Going Forward to: ({x:.1f}, {y:.1f})')
        
        send_goal_future = self.nav_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('❌ Goal rejected!')
            self.is_navigating = False
            return

        self.get_goal_result_future = goal_handle.get_result_async()
        self.get_goal_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        self.is_navigating = False
        self.get_logger().info('✅ Reached target or finished!')

    def exploration_loop(self):
        if self.is_navigating:
            return

        # البحث عن هدف جديد
        target = self.get_best_frontier()
        
        if target:
            self.send_goal(target[0], target[1])
        else:
            self.get_logger().info('zzz No good frontiers found (scanning)...')

def main(args=None):
    rclpy.init(args=args)
    node = SmartExplorer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
