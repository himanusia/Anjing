class EnemyInfo:
    BIN: int = 47

    def __init__(self,
                 enemy_id: int,
                 energy: float,
                 direction: float,
                 speed: float,
                 position: tuple[float, float],
                 last_seen: int,
                 distance: float = float('inf'),
                 angular_velocity: float = 0.0,
                 acceleration: float = 0.0,
                 gun_heat: float = 0.0,
                 last_hit_by_time: int = -1
                ) -> None:
        self.id = enemy_id
        self.is_alive = True
        self.energy = energy
        self.direction = direction
        self.speed = speed
        self.position = position
        self.last_seen = last_seen
        self.distance = distance
        self.angular_velocity = angular_velocity
        self.acceleration = acceleration
        self.gun_heat = gun_heat
        self.last_hit_by_time = last_hit_by_time
        self.history: list[EnemyInfo] = []
        self.surf_stat: list[float] = [0.0 for _ in range(EnemyInfo.BIN)]
        
    def __repr__(self) -> str:
        return f"EnemyInfo(id={self.id}, is_alive={self.is_alive}, energy={self.energy}, direction={self.direction}, angular_velocity={self.angular_velocity}, speed={self.speed}, acceleration={self.acceleration}, position={self.position}, last_seen={self.last_seen}, distance={self.distance}, last_hit_by_time={self.last_hit_by_time})"

    def set_is_alive(self, alive: bool) -> None:
        self.is_alive = alive
    
    def set_energy(self, new_energy: float) -> None:
        self.energy = new_energy

    def set_direction(self, new_direction: float) -> None:
        self.angular_velocity = new_direction - self.direction
        self.direction = new_direction

    def set_speed(self, new_speed: float) -> None:
        self.acceleration = new_speed - self.speed
        self.speed = new_speed

    def set_position(self, new_position: tuple[float, float]) -> None:
        self.position = new_position

    def set_last_seen(self, turn_number: int) -> None:
        self.last_seen = turn_number

    def set_distance(self, new_distance: float) -> None:
        self.distance = new_distance

    def set_gun_heat(self, new_gun_heat: float) -> None:
        self.gun_heat = new_gun_heat

    def set_last_hit_by_time(self, turn_number: int) -> None:
        self.last_hit_by_time = turn_number

    def add_history(self, enemy_info: 'EnemyInfo') -> None:
        self.history.append(enemy_info)

    def copy(self) -> 'EnemyInfo':
        return EnemyInfo(
            self.id,
            self.energy,
            self.direction,
            self.speed,
            self.position,
            self.last_seen,
            self.distance,
            self.angular_velocity,
            self.acceleration,
            self.gun_heat,
            self.last_hit_by_time
        )
    
    def on_tick_update(self) -> None:
        pass
