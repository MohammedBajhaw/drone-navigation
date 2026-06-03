#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid, Odometry
from geometry_msgs.msg import PoseStamped, Twist
from visualization_msgs.msg import Marker
import numpy as np
import math

class AutoExplorer(Node):
    def __init__(self):
        super().__init__('auto_explorer')
        
        self.sub_map = self.create_subscription(OccupancyGrid, '/projected_map', self.map_cb, 10)
        self.sub_odom = self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        
        self.pub_goal = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.pub_marker = self.create_publisher(Marker, '/explorer_target', 10)
        # نحتاج هذا الناشر لعمل دوران بسيط إذا تهنا (اختياري)
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)

        self.map_data = None
        self.map_info = None
        self.current_x = 0.0
        self.current_y = 0.0
        
        self.is_moving = False
        self.goal_x = 0.0
        self.goal_y = 0.0
        
        # إعدادات الاستكشاف
        # كم بلوك يجب أن يكون فارغاً حول الهدف؟ (8 * 0.15 = 1.2 متر تقريباً)
        self.SAFETY_RADIUS_BLOCKS = 2
        
        # المسافة التي نعتبر عندها أننا وصلنا (Touch and Go)
        self.ACCEPTANCE_RADIUS = 4.0

        # المؤقت سريع لاتخاذ قرارات سلسة
        self.timer = self.create_timer(0.5, self.exploration_loop)
        self.get_logger().info("🛡️ Safe Auto Explorer Started! (Wall Avoidance Active)")

    def odom_cb(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        
        if self.is_moving:
            dist = math.sqrt((self.goal_x - self.current_x)**2 + (self.goal_y - self.current_y)**2)
            if dist < self.ACCEPTANCE_RADIUS:
                self.is_moving = False
                self.get_logger().info(f"⚡ Close enough ({dist:.2f}m)! Next target please...")

    def map_cb(self, msg):
        # تخزين الخريطة كمصفوفة ثنائية الأبعاد للسهولة
        self.map_data = np.array(msg.data, dtype=np.int8).reshape((msg.info.height, msg.info.width))
        self.map_info = msg.info

    def is_location_safe(self, grid_x, grid_y, width, height, check_radius):
        """
        تفحص مربعاً حول النقطة (grid_x, grid_y)
        تعيد False إذا وجدت أي عائق (قيمة > 50) داخل هذا المربع
        """
        # تحديد حدود المربع مع التأكد من عدم الخروج عن حدود المصفوفة
        x_start = max(0, grid_x - check_radius)
        x_end = min(width, grid_x + check_radius)
        y_start = max(0, grid_y - check_radius)
        y_end = min(height, grid_y + check_radius)

        # قص الجزء المراد فحصه من الخريطة
        region = self.map_data[y_start:y_end, x_start:x_end]
        
        # البحث عن أي عائق (100)
        # القيمة 100 تعني جدار مؤكد. -1 مجهول. 0 فارغ.
        # نحن نرفض النقطة إذا كانت قريبة جداً من جدار (100)
        if np.any(region == 100):
            return False
        return True

    def exploration_loop(self):
        if self.map_data is None:
            return
            
        if self.is_moving:
            return 

        self.get_logger().info("🔍 Scanning for SAFE frontiers...")
        
        res = self.map_info.resolution
        ox = self.map_info.origin.position.x
        oy = self.map_info.origin.position.y
        w = self.map_info.width
        h = self.map_info.height

        best_goal = None
        min_dist = float('inf')
        max_dist_found = -1.0

        # قفزات المسح (كل 2 بكسل لتقليل الحمل على المعالج)
        step = 2 
        
        # هوامش المسح (لتجنب أطراف الخريطة)
        margin = self.SAFETY_RADIUS_BLOCKS + 2

        found_something = False

        for y in range(margin, h - margin, step):
            for x in range(margin, w - margin, step):
                
                # 1. هل النقطة نفسها فارغة؟
                if self.map_data[y, x] != 0:
                    continue
                
                # 2. هل هي "حافة" (بجانبها مجهول)؟
                # نفحص الجيران المباشرين
                has_unknown = False
                if (self.map_data[y+1, x] == -1 or self.map_data[y-1, x] == -1 or
                    self.map_data[y, x+1] == -1 or self.map_data[y, x-1] == -1):
                    has_unknown = True
                
                if has_unknown:
                    # 3. الفحص الأمني (هل هي بعيدة عن الجدران؟)
                    # هذا هو الشرط الذي طلبته!
                    if not self.is_location_safe(x, y, w, h, self.SAFETY_RADIUS_BLOCKS):
                        continue  # هذه النقطة خطيرة (قريبة من الجدار)، ارمِها وابحث عن غيرها

                    # إذا نجحت في الاختبار، نحسب مسافتها
                    real_x = x * res + ox
                    real_y = y * res + oy
                    dist = math.sqrt((real_x - self.current_x)**2 + (real_y - self.current_y)**2)
                    
                    # نختار الأقرب بشرط ألا يكون قريباً جداً (أقل من متر ونصف)
                    if 1.5 < dist < 15.0: 
                        if dist > max_dist_found: # نغير الاستراتيجية للأبعد المتاح
                            max_dist_found = dist
                            best_goal = (real_x, real_y)
                            found_something = True

        if best_goal:
            self.goal_x, self.goal_y = best_goal
            self.get_logger().info(f"🛡️ Safe target found ({min_dist:.1f}m away). Radius check passed.")
            self.send_goal(self.goal_x, self.goal_y)
            self.is_moving = True
        else:
            self.get_logger().warn("⚠️ No SAFE frontiers found! Either map is complete or spaces are too tight.")
            # هنا ممكن أن نطلب من الروبوت الدوران قليلاً ليحدث الخريطة
            self.rotate_in_place()

    def rotate_in_place(self):
        # دوران بطيء لتحديث الليزر
        cmd = Twist()
        cmd.angular.z = 0.4
        self.pub_cmd_vel.publish(cmd)

    def send_goal(self, x, y):
        msg = PoseStamped()
        msg.header.frame_id = "odom"
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.position.x = x
        msg.pose.position.y = y
        msg.pose.position.z = 1.0 
        
        self.pub_goal.publish(msg)
        self.publish_marker(x, y)

    def publish_marker(self, x, y):
        m = Marker()
        m.header.frame_id = "odom"
        m.header.stamp = self.get_clock().now().to_msg()
        m.type = Marker.SPHERE
        m.action = Marker.ADD
        m.pose.position.x = x; m.pose.position.y = y; m.pose.position.z = 1.0
        m.scale.x = 0.6; m.scale.y = 0.6; m.scale.z = 0.6
        m.color.a = 0.9; m.color.r = 0.0; m.color.g = 1.0; m.color.b = 0.0 # أخضر
        self.pub_marker.publish(m)

def main():
    rclpy.init()
    node = AutoExplorer()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
