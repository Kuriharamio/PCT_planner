from .scene import Scene


class SceneMap(Scene):
    def __init__(self) -> None:
        super().__init__()

        self.pcd.file_name = 'map.pcd'

        self.map.resolution = 0.1
        self.map.ground_h = 0.00
        self.map.slice_dh = 0.1

        self.trav.kernel_size = 7
        self.trav.interval_min = 0.50
        self.trav.interval_free = 0.65
        self.trav.slope_max = 0.4
        self.trav.step_max = 0.22
        self.trav.standable_ratio = 0.20
        self.trav.cost_barrier = 50.0
        self.trav.safe_margin = 0.4
        self.trav.inflation = 0.2
