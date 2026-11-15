import cv2
import numpy as np
import math

class ShapeRecognizer:
    """
    Geometric Shape Recognition Engine.
    Analyzes raw hand-drawn stroke point paths and snaps them to
    clean mathematical shapes (Straight Line, Circle, Triangle, Rectangle)
    while leaving freehand curves and handwriting untouched.
    """
    @staticmethod
    def recognize(points):
        """
        Analyze a stroke's coordinates.
        :param points: List of (x, y) tuples
        :return: (shape_type, shape_data) or (None, None)
        """
        if not points or len(points) < 8:
            return None, None

        n = len(points)
        p_start = points[0]
        p_end = points[-1]
        
        # 1. Check for Straight Line
        chord_dist = math.hypot(p_end[0] - p_start[0], p_end[1] - p_start[1])
        if chord_dist > 50:
            path_len = sum(math.hypot(points[i+1][0] - points[i][0], 
                                      points[i+1][1] - points[i][1]) for i in range(n - 1))
            linearity = chord_dist / max(1e-5, path_len)
            
            # Check maximum perpendicular distance of points to line segment
            if linearity >= 0.88:
                x1, y1 = p_start
                x2, y2 = p_end
                max_deviation = 0.0
                for px, py in points:
                    dist_to_line = abs((y2 - y1) * px - (x2 - x1) * py + x2 * y1 - y2 * x1) / chord_dist
                    if dist_to_line > max_deviation:
                        max_deviation = dist_to_line
                
                if max_deviation <= 28.0:
                    return "LINE", (p_start, p_end)

        # 2. Check for Closed Geometric Shapes (Circle, Triangle, Rectangle)
        endpoint_dist = math.hypot(p_end[0] - p_start[0], p_end[1] - p_start[1])
        
        contour = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
        perimeter = cv2.arcLength(contour, True)
        area = cv2.contourArea(contour)

        # Must be roughly closed to be a polygon or circle
        if area > 450 and (endpoint_dist < 90 or endpoint_dist / max(1.0, perimeter) < 0.28):
            # A. Polygon Approximation (approxPolyDP)
            epsilon = 0.040 * perimeter
            approx = cv2.approxPolyDP(contour, epsilon, True)
            num_vertices = len(approx)

            # Triangle Check
            if num_vertices == 3:
                triangle_pts = [tuple(approx[i][0]) for i in range(3)]
                return "TRIANGLE", triangle_pts

            # Rectangle / Quad Check
            if num_vertices == 4:
                # Check convexity
                if cv2.isContourConvex(approx):
                    bx, by, bw, bh = cv2.boundingRect(contour)
                    rect_area = bw * bh
                    if (area / max(1.0, rect_area)) >= 0.62:
                        return "RECTANGLE", (bx, by, bx + bw, by + bh)

            # B. Circle Check
            # True circles have high circularity (> 0.80) and fill >= 75% of min enclosing circle
            circularity = 4 * math.pi * area / (perimeter ** 2)
            (cx, cy), radius = cv2.minEnclosingCircle(contour)
            circle_area = math.pi * (radius ** 2)
            area_ratio = area / max(1.0, circle_area)

            if circularity >= 0.78 and area_ratio >= 0.75:
                return "CIRCLE", (int(round(cx)), int(round(cy)), int(round(radius)))

        # Freehand writing / curve
        return None, None
