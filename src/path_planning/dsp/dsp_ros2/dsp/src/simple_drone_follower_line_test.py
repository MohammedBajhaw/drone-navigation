#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Path, Odometry
from geometry_msgs.msg import Twist, PoseStamped, Point
from visualization_msgs.msg import Marker
import math
from math import atan2, degrees, cos, sin, sqrt

class ForceForwardController(Node):
    def __init__(self):
        super().__init__('force_forward_controller')
        
        self.sub_odom = self.create_subscription(Odometry, '/X3/odom', self.odom_cb, 10)
        self.pub_cmd = self.create_publisher(Twist, '/X3/cmd_vel', 10)
        self.pub_debug = self.create_publisher(Marker, '/drone_target_marker', 10)

        # === المسار ===
        self.path = []
        # 10 متر للأمام
        for i in range(101): 
            p = PoseStamped()
            p.pose.position.x = i * 0.1  
            p.pose.position.y = 0.0      
            self.path.append(p)
        # 5 متر لليمين
        for i in range(51): 
            p = PoseStamped()
            p.pose.position.x = 10.0        
            p.pose.position.y = -(i * 0.1)  
            self.path.append(p)
            
        self.get_logger().info(f"⚠️ TEST MODE: Sharp Turn Path Loaded. Points: {len(self.path)}")

        self.x = 0.0; self.y = 0.0; self.z = 0.0; self.yaw = 0.0
        
        # === تعديلات الدقة ===
        self.FLY_ALTITUDE = 1.3
        self.LOOK_AHEAD_INDEX = 6    # <--- تقليل الرقم ليجعل الطائرة تلتصق بالمسار (زاوية حادة)
        self.MAX_SPEED = 0.5
        
        self.timer = self.create_timer(0.05, self.control_loop)

    def odom_cb(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        self.z = msg.pose.pose.position.z
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.yaw = atan2(siny_cosp, cosy_cosp)

    def control_loop(self):
        cmd = Twist()
        cmd.linear.z = (self.FLY_ALTITUDE - self.z) * 1.0

        if not self.path:
            self.pub_cmd.publish(cmd)
            return

        # البحث عن أقرب نقطة
        closest_idx = 0
        min_dist = float('inf')
        search_limit = min(len(self.path), 150)
        
        for i in range(search_limit):
            px = self.path[i].pose.position.x
            py = self.path[i].pose.position.y
            dist = (px - self.x)**2 + (py - self.y)**2
            if dist < min_dist:
                min_dist = dist
                closest_idx = i
        
        # حذف النقاط القديمة
        if closest_idx > 0:
             self.path = self.path[closest_idx:]

        # تحديد الهدف (قريب جداً الآن)
        target_idx = min(self.LOOK_AHEAD_INDEX, len(self.path) - 1)
        target = self.path[target_idx].pose.position

        # حسابات التوجيه
        dx_global = target.x - self.x
        dy_global = target.y - self.y
        dist_to_target = sqrt(dx_global**2 + dy_global**2)
        
        # حساب زاوية الخطأ
        target_yaw = atan2(dy_global, dx_global)
        yaw_err = target_yaw - self.yaw
        while yaw_err > math.pi: yaw_err -= 2 * math.pi
        while yaw_err < -math.pi: yaw_err += 2 * math.pi
        
        # === التعديل الجوهري: الفرملة الذكية ===
        # إذا كانت زاوية الخطأ كبيرة (أكثر من 20 درجة)، قلل السرعة لتتمكن من اللف بحدة
        current_speed = self.MAX_SPEED
        if abs(degrees(yaw_err)) > 20:
            current_speed = 0.15  # سرعة بطيئة جداً عند المنعطف
        
        # تحويل السرعة للإحداثيات المحلية
        local_x = dx_global * cos(self.yaw) + dy_global * sin(self.yaw)
        local_y = -dx_global * sin(self.yaw) + dy_global * cos(self.yaw)
        
        if dist_to_target > 0.05:
            cmd.linear.x = (local_x / dist_to_target) * current_speed
            cmd.linear.y = (local_y / dist_to_target) * current_speed
        
        # زيادة حدة الدوران (Gain عالي)
        cmd.angular.z = max(min(yaw_err * 4.0, 1.5), -1.5) 

        self.pub_cmd.publish(cmd)
        self.publish_debug_marker(target.x, target.y)

    def publish_debug_marker(self, x, y):
        m = Marker()
        m.header.frame_id = "X3/odom"
        m.header.stamp = self.get_clock().now().to_msg()
        m.type = Marker.SPHERE
        m.action = Marker.ADD
        m.pose.position.x = x; m.pose.position.y = y; m.pose.position.z = self.FLY_ALTITUDE
        m.scale.x = 0.5; m.scale.y = 0.5; m.scale.z = 0.5
        m.color.a = 1.0; m.color.r = 1.0; m.color.g = 0.0; m.color.b = 0.0 
        self.pub_debug.publish(m)

def main(args=None):
    rclpy.init(args=args)
    node = ForceForwardController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
