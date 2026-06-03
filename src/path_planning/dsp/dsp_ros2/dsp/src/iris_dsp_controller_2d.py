#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Path, Odometry
from geometry_msgs.msg import Twist, PoseStamped, Point
from visualization_msgs.msg import Marker
import math
from math import atan2, sqrt, degrees, sin, cos

class TunnelController(Node):
    def __init__(self):
        super().__init__('tunnel_controller')
        
        self.sub_odom = self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.sub_path = self.create_subscription(Path, '/dsp/path', self.path_cb, 10)
        self.sub_goal = self.create_subscription(PoseStamped, '/goal_pose', self.goal_cb, 10)
        
        self.pub_cmd = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pub_dsp_goal = self.create_publisher(Point, '/dsp/set_goal', 10)
        self.pub_debug = self.create_publisher(Marker, '/drone_target_marker', 10)

        self.path = []
        self.x = 0.0; self.y = 0.0; self.z = 0.0; self.yaw = 0.0
        
        # === إعدادات النفق الدقيقة ===
        self.FLY_ALTITUDE = 0.8       # ارتفاع متوسط (ليس قريباً من السقف ولا الأرض)
        self.LOOK_AHEAD_DIST = 1.0    # ننظر مسافة قصيرة (40 سم) لتقليل "قص الزوايا"
        self.MAX_SPEED = 0.8         # سرعة هادئة وآمنة للنفق
        self.LATERAL_GAIN = 2.5       # قوة التصحيح الجانبي (المغناطيس الذي يشدك للمسار)

        self.timer = self.create_timer(0.05, self.control_loop)
        self.get_logger().info("🚇 Tunnel Controller Started: With Lateral Correction!")

    def goal_cb(self, msg):
        p = Point()
        p.x = msg.pose.position.x; p.y = msg.pose.position.y; p.z = self.FLY_ALTITUDE
        self.pub_dsp_goal.publish(p)

    def path_cb(self, msg):
        self.path = msg.poses
        if len(self.path) > 3:
            self.get_logger().info(f"🚀 New Path: {len(self.path)} points")

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
        
        # 1. تثبيت الارتفاع
        cmd.linear.z = (self.FLY_ALTITUDE - self.z) * 1.0

        if not self.path or len(self.path) < 2:
            self.pub_cmd.publish(cmd)
            return

        # 2. البحث عن أقرب نقطة (لنحسب خطأ الانحراف عنها)
        closest_idx = 0
        min_dist = float('inf')
        search_limit = min(len(self.path), 50)
        
        for i in range(search_limit):
            px = self.path[i].pose.position.x
            py = self.path[i].pose.position.y
            dist = (px - self.x)**2 + (py - self.y)**2
            if dist < min_dist:
                min_dist = dist
                closest_idx = i

        # تنظيف المسار القديم
        if closest_idx > 0:
             self.path = self.path[closest_idx:]
             closest_idx = 0

        # 3. تحديد "نقطة الأرنب" (Look Ahead Point)
        # بدلاً من القفز بعدد ثابت من النقاط، نبحث عن نقطة تبعد مسافة محددة بالأمتار
        target_idx = 0
        for i in range(len(self.path)):
            px = self.path[i].pose.position.x
            py = self.path[i].pose.position.y
            dist_to_p = sqrt((px - self.x)**2 + (py - self.y)**2)
            if dist_to_p > self.LOOK_AHEAD_DIST:
                target_idx = i
                break
        
        target = self.path[target_idx].pose.position

        # 4. حساب الأخطاء (Global Frame)
        dx = target.x - self.x
        dy = target.y - self.y
        
        # التوقف عند الوصول
        if sqrt(dx**2 + dy**2) < 0.1:
             self.get_logger().info("✅ Reached local target", throttle_duration_sec=2.0)
             self.pub_cmd.publish(cmd)
             return

        # 5. تحويل الخطأ إلى إحداثيات الطائرة (Body Frame)
        # هذا هو السحر! نحسب الخطأ "أمامك" والخطأ "بجانبك"
        # rotation matrix 2D
        local_x = dx * cos(self.yaw) + dy * sin(self.yaw)
        local_y = -dx * sin(self.yaw) + dy * cos(self.yaw)

        # 6. التوجيه (Angular Z)
        # نستخدم atan2 للخطأ المحلي لتوجيه المقدمة نحو الهدف
        steering_angle = atan2(local_y, local_x)
        cmd.angular.z = max(min(steering_angle * 2.0, 1.0), -1.0)

        # 7. الحركة الأمامية (Linear X)
        # نبطئ كلما كانت الزاوية حادة
        speed_factor = max(0.0, 1.0 - abs(steering_angle) / 1.5)
        cmd.linear.x = self.MAX_SPEED * speed_factor

        # 8. الحركة الجانبية التصحيحية (Linear Y) - "الحماية من الجدران"
        # إذا كانت الطائرة بعيدة يميناً أو يساراً عن الخط، ادفعها للعودة
        # نستخدم local_y كمؤشر للانحراف
        cmd.linear.y = local_y * self.LATERAL_GAIN
        
        # تقييد السرعة الجانبية
        cmd.linear.y = max(min(cmd.linear.y, 0.3), -0.3)

        self.pub_cmd.publish(cmd)
        self.publish_debug_marker(target.x, target.y)

    def publish_debug_marker(self, x, y):
        m = Marker()
        m.header.frame_id = "odom"
        m.header.stamp = self.get_clock().now().to_msg()
        m.type = Marker.SPHERE
        m.action = Marker.ADD
        m.pose.position.x = x; m.pose.position.y = y; m.pose.position.z = self.FLY_ALTITUDE
        m.scale.x = 0.2; m.scale.y = 0.2; m.scale.z = 0.2
        m.color.a = 1.0; m.color.r = 0.0; m.color.g = 1.0; m.color.b = 1.0 # سماوي
        self.pub_debug.publish(m)

def main(args=None):
    rclpy.init(args=args)
    node = TunnelController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
