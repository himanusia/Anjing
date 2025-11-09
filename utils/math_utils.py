import numpy as np

class MathUtils:
    
    @staticmethod
    def max_escape_angle(bullet_speed: float):
        return np.asin(8 / bullet_speed)

    @staticmethod
    def project(location: tuple[float, float], angle_deg: float, distance: float) -> tuple[float, float]:
        """
        Project a point from the given location at a certain angle and distance.
        """
        x = location[0] + np.cos(np.radians(angle_deg)) * distance
        y = location[1] + np.sin(np.radians(angle_deg)) * distance
        return (x, y)

    @staticmethod
    def limit(min_val: float, val: float, max_val: float):
        """
        Limit the value between min_val and max_val.
        """
        return max(min_val, min(val, max_val))
    
    @staticmethod
    def angle_between_points(src: tuple[float, float], dest: tuple[float, float]) -> float:
        """
        Calculate the angle in degrees from src to dest.
        """
        return np.degrees(np.atan2(dest[1] - src[1], dest[0] - src[0]))