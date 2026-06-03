#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Path, Odometry
from geometry_msgs.msg import Twist, PoseStamped, Point
from visualization_msgs.msg import Marker
from math import atan2, sqrt, sin, cos

class TunnelController(Node):
    def __init__(self):
        super().__init__('tunnel_controller')
        
        self.sub_odom = self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.sub_path = self.create_subscription(Path, '/dsp/path', self.path_cb, 10)
        
        self.pub_cmd = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pub_debug = self.create_publisher(Marker, '/drone_target_marker', 10)

        self.path = []
        self.x = 0.0; self.y = 0.0; self.z = 0.0; self.yaw = 0.0
        
        # إعدادات الطيران
        self.DEFAULT_ALTITUDE = 0.8   # الارتفاع المفضل إذا لم يكن هناك عوائق
        self.LOOK_AHEAD_DIST = 1.0    
        self.MAX_SPEED = 0.8         
        self.LATERAL_GAIN = 2.5       
        self.VERTICAL_GAIN = 1.5      # قوة تصحيح الارتفاع (جديد)
        
        self.pos_history = []
        self.evading_counter = 0

        self.timer = self.create_timer(0.05, self.control_loop)
        self.get_logger().info("🦅 3D Tunnel Controller Ready: I can jump over obstacles!")

    def path_cb(self, msg):
        self.path = msg.poses

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
        
        # 0. Evasive Maneuver if Stuck
        if self.evading_counter > 0:
            cmd.linear.x = -1.0      # تراجع للخلف
            cmd.angular.z = 0.5      # دوران لتغيير الزاوية
            cmd.linear.z = (self.DEFAULT_ALTITUDE - self.z) * 1.0 # الحفاظ على الارتفاع
            self.pub_cmd.publish(cmd)
            self.evading_counter -= 1
            return

        # 1. إذا لم يكن هناك مسار، حلق في المكان بارتفاع ثابت
        if not self.path or len(self.path) < 2:
            cmd.linear.z = (self.DEFAULT_ALTITUDE - self.z) * 1.0
            self.pub_cmd.publish(cmd)
            return

        # 2. البحث عن أقرب نقطة وتنظيف المسار القديم
        closest_idx = 0; min_dist = float('inf'); limit = min(len(self.path), 50)
        for i in range(limit):
            d = (self.path[i].pose.position.x - self.x)**2 + (self.path[i].pose.position.y - self.y)**2
            if d < min_dist: min_dist = d; closest_idx = i
        
        if closest_idx > 0: self.path = self.path[closest_idx:]

        # 3. تحديد نقطة الهدف (Look Ahead)
        # نأخذ النقطة التي تبعد مسافة معينة، وهذه النقطة تحتوي على (x, y, z)
        target = self.path[0].pose.position
        for p in self.path:
            if sqrt((p.pose.position.x - self.x)**2 + (p.pose.position.y - self.y)**2) > self.LOOK_AHEAD_DIST:
                target = p.pose.position
                break
        
        # 4. حساب الفروقات (Errors)
        dx = target.x - self.x
        dy = target.y - self.y
        
        # --- التعديل الجوهري هنا: حساب خطأ الارتفاع ---
        # بدلاً من استخدام ارتفاع ثابت، نستخدم ارتفاع الهدف القادم من المخطط
        # إذا كان المخطط رسم مساراً فوق الصخرة، ستكون target.z عالية
        dz = target.z - self.z 

        # 5. التحكم في الارتفاع (Vertical Control)
        # نرسل أمراً للصعود أو النزول بناءً على خطأ الارتفاع
        cmd.linear.z = dz * self.VERTICAL_GAIN

        # 6. التحكم الأفقي (Horizontal Control)
        local_x = dx * cos(self.yaw) + dy * sin(self.yaw)
        local_y = -dx * sin(self.yaw) + dy * cos(self.yaw)

        steering = atan2(local_y, local_x)
        cmd.angular.z = max(min(steering * 2.0, 1.0), -1.0)
        cmd.linear.x = self.MAX_SPEED * max(0.0, 1.0 - abs(steering) / 1.5)
        cmd.linear.y = max(min(local_y * self.LATERAL_GAIN, 0.3), -0.3)

        # 7. كشف الاصطدام/التوقف (Stuck / Collision Detection)
        self.pos_history.append((self.x, self.y))
        if len(self.pos_history) > 40: # تسجيل لمدة ثانيتين تقريباً
            old_x, old_y = self.pos_history.pop(0)
            dist_moved = sqrt((self.x - old_x)**2 + (self.y - old_y)**2)
            # إذا كنا نحاول التحرك للأمام لكن لم نتحرك سوى مسافة ضئيلة جداً
            if cmd.linear.x > 0.2 and dist_moved < 0.2:
                self.get_logger().warn("💥 STUCK! Drone collided with obstacle! Engaging evasion maneuver...")
                self.evading_counter = 30 # التراجع للخلف لمدة 1.5 ثانية لتحرير الطائرة
                self.pos_history.clear()

        self.pub_cmd.publish(cmd)
        self.publish_debug_marker(target.x, target.y, target.z)

    def publish_debug_marker(self, x, y, z):
        m = Marker()
        m.header.frame_id = "odom"; m.header.stamp = self.get_clock().now().to_msg()
        m.type = Marker.SPHERE; m.action = Marker.ADD
        # نرسم الكرة في الارتفاع الحقيقي للهدف لنرى هل ستقفز الطائرة أم لا
        m.pose.position.x = x; m.pose.position.y = y; m.pose.position.z = z
        m.scale.x = 0.3; m.scale.y = 0.3; m.scale.z = 0.3
        m.color.a = 1.0; m.color.r = 1.0; m.color.g = 0.0; m.color.b = 0.0 # أحمر
        self.pub_debug.publish(m)

def main():
    rclpy.init(); node = TunnelController(); rclpy.spin(node); node.destroy_node(); rclpy.shutdown()

if __name__ == '__main__': main()
