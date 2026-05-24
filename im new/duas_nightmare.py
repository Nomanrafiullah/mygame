"""
Dua's Nightmare: Finding Noman
3D Horror Game - Ursina Engine
Single file, no external assets
"""

import sys
import math
import random
import os

# Optional imports
try:
    import tkinter as tk
    from tkinter import filedialog
    TKINTER_OK = True
except ImportError:
    TKINTER_OK = False

try:
    import cv2
    CV2_OK = True
except ImportError:
    CV2_OK = False

try:
    from PIL import Image, ImageDraw
    PIL_OK = True
except ImportError:
    PIL_OK = False

# Ursina imports
from ursina import *

# =============================================================================
# CONSTANTS
# =============================================================================
MISSIONS = [
    {
        'name': 'The Whispering Forest',
        'desc': 'Find 3 notes. Noman is waiting.',
        'notes_required': 3,
        'monster_speed': 2.0,
        'fake_friends': 0,
        'darkness': 0.3,
        'size': 80,
        'weapons': ['flashlight'],
        'trap_count': 0,
    },
    {
        'name': 'The Deceptive Cabin',
        'desc': 'Find 4 notes. Trust no one.',
        'notes_required': 4,
        'monster_speed': 2.5,
        'fake_friends': 1,
        'darkness': 0.4,
        'size': 60,
        'weapons': ['flashlight', 'knife'],
        'trap_count': 2,
    },
    {
        'name': 'The Flooded Sewers',
        'desc': 'Find 5 notes. The water hides secrets.',
        'notes_required': 5,
        'monster_speed': 3.0,
        'fake_friends': 2,
        'darkness': 0.6,
        'size': 70,
        'weapons': ['flashlight', 'knife', 'gun'],
        'trap_count': 4,
    },
    {
        'name': 'The Rotting Hospital',
        'desc': 'Find 6 notes. They pretend to help.',
        'notes_required': 6,
        'monster_speed': 3.5,
        'fake_friends': 3,
        'darkness': 0.7,
        'size': 100,
        'weapons': ['flashlight', 'knife', 'gun', 'medkit'],
        'trap_count': 6,
    },
    {
        'name': "Noman's Lair",
        'desc': 'The final truth awaits.',
        'notes_required': 7,
        'monster_speed': 4.0,
        'fake_friends': 2,
        'darkness': 0.8,
        'size': 90,
        'weapons': ['flashlight', 'knife', 'gun', 'medkit'],
        'trap_count': 8,
    },
]

NOMAN_MESSAGES = [
    "Dua... I'm waiting in the dark...",
    "You shouldn't have come here, Dua.",
    "The forest remembers your name, Dua.",
    "Every step brings you closer to me.",
    "They are not your friends, Dua. Trust only me.",
    "I can hear your heartbeat from here.",
    "The water carries my voice to you.",
    "Look behind you, Dua. No... don't.",
    "You are so close now. So very close.",
    "I saved a place for you here, Dua.",
    "The monster is hungry. But I am patient.",
    "Run if you must. I will always find you.",
    "Your friends want to hurt you, Dua. Come to me.",
    "The light lies. The dark tells truth.",
    "Noman is not a name. It's a promise.",
]

FAKE_FRIEND_DIALOGUE = [
    "Hey Dua! Over here! I found a way out!",
    "Dua, trust me, I know where Noman is.",
    "Come closer, I have something to show you.",
    "Don't be scared, I'm here to help you.",
    "The exit is just past this door, follow me!",
    "I've been looking for you everywhere, Dua.",
]

# =============================================================================
# UTILITIES
# =============================================================================
def lerp(a, b, t):
    return a + (b - a) * t

def dist_2d(x1, z1, x2, z2):
    return math.sqrt((x2-x1)**2 + (z2-z1)**2)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def rand_pos(world_size, margin=5):
    half = world_size / 2 - margin
    return (random.uniform(-half, half), random.uniform(-half, half))

# =============================================================================
# AVATAR MANAGER
# =============================================================================
class AvatarManager:
    def __init__(self):
        self.face_texture = None
        self.default_face = None
        self.camera_active = False
        self.cap = None
        self.temp_file = 'dua_face_temp.png'
        self._create_default()

    def _create_default(self):
        if PIL_OK:
            size = 128
            img = Image.new('RGBA', (size, size), (20, 10, 15, 255))
            draw = ImageDraw.Draw(img)
            draw.ellipse([10, 10, size-10, size-10], fill=(240, 220, 210))
            draw.ellipse([25, 40, 55, 70], fill=(10, 5, 8))
            draw.ellipse([73, 40, 103, 70], fill=(10, 5, 8))
            draw.ellipse([35, 48, 45, 58], fill=(200, 50, 50))
            draw.ellipse([83, 48, 93, 58], fill=(200, 50, 50))
            draw.arc([40, 65, 88, 95], 0, 180, fill=(120, 30, 40), width=3)
            draw.polygon([(64, 10), (44, 25), (44, 5)], fill=(255, 20, 147))
            draw.polygon([(64, 10), (84, 25), (84, 5)], fill=(255, 20, 147))
            draw.ellipse([58, 5, 70, 17], fill=(255, 20, 147))
            img.save(self.temp_file)

        if os.path.exists(self.temp_file):
            self.default_face = Texture(self.temp_file)

    def open_gallery(self):
        if not TKINTER_OK:
            return False
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        filepath = filedialog.askopenfilename(
            title="Select Dua's Photo",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")]
        )
        root.destroy()
        if filepath and os.path.exists(filepath):
            return self._process_image(filepath)
        return False

    def open_camera(self):
        if not CV2_OK:
            self.face_texture = self.default_face
            return True
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.face_texture = self.default_face
            return False
        self.camera_active = True
        print("Camera active - press SPACE to capture, ESC to cancel")
        return True

    def update_camera(self):
        if not self.camera_active or not self.cap:
            return
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.flip(frame, 1)
            cv2.imshow('Camera - Press SPACE', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            key = cv2.waitKey(1) & 0xFF
            if key == 32:
                self._capture_frame(frame)
            elif key == 27:
                self.close_camera()

    def _capture_frame(self, frame):
        if PIL_OK:
            from PIL import Image
            h, w = frame.shape[:2]
            size = min(h, w)
            y1 = (h - size) // 2
            x1 = (w - size) // 2
            cropped = frame[y1:y1+size, x1:x1+size]
            resized = cv2.resize(cropped, (128, 128), interpolation=cv2.INTER_LANCZOS4)
            img = Image.fromarray(resized)
            img.save(self.temp_file)
            if os.path.exists(self.temp_file):
                self.face_texture = Texture(self.temp_file)
            self.close_camera()

    def close_camera(self):
        self.camera_active = False
        if self.cap:
            self.cap.release()
            self.cap = None
        if CV2_OK:
            cv2.destroyAllWindows()

    def _process_image(self, filepath):
        if PIL_OK:
            from PIL import Image
            try:
                img = Image.open(filepath).convert('RGBA')
                w, h = img.size
                size = min(w, h)
                x1 = (w - size) // 2
                y1 = (h - size) // 2
                img = img.crop((x1, y1, x1+size, y1+size))
                img = img.resize((128, 128), Image.LANCZOS)
                img.save(self.temp_file)
                if os.path.exists(self.temp_file):
                    self.face_texture = Texture(self.temp_file)
                return True
            except Exception as e:
                print(f"Error: {e}")
                return False
        return False

    def get_face_texture(self):
        if self.face_texture:
            return self.face_texture
        return self.default_face

# =============================================================================
# MONSTER
# =============================================================================
class Monster(Entity):
    def __init__(self, world_size, config, **kwargs):
        super().__init__(**kwargs)
        self.world_size = world_size
        self.speed = config['monster_speed']
        self.can_patrol = config.get('monster_patrol', True)
        self.can_hunt = config.get('monster_hunt', True)

        self.body = Entity(parent=self, model='cube', scale=(0.6, 1.8, 0.4),
                          position=(0, 0.9, 0), color=color.rgb(40, 10, 20), collider='box')
        self.head = Entity(parent=self, model='cube', scale=(0.7, 0.8, 0.6),
                          position=(0, 2.0, 0.1), color=color.rgb(50, 15, 25), rotation=(15, 0, 5))
        self.eye_left = Entity(parent=self.head, model='sphere', scale=(0.12, 0.08, 0.1),
                              position=(-0.15, 0.1, 0.3), color=color.rgb(255, 0, 0))
        self.eye_right = Entity(parent=self.head, model='sphere', scale=(0.12, 0.08, 0.1),
                               position=(0.15, 0.1, 0.3), color=color.rgb(255, 0, 0))
        self.arm_left = Entity(parent=self, model='cube', scale=(0.15, 1.2, 0.15),
                              position=(-0.4, 1.0, 0), color=color.rgb(35, 8, 18), rotation=(0, 0, 20))
        self.arm_right = Entity(parent=self, model='cube', scale=(0.15, 1.2, 0.15),
                               position=(0.4, 1.0, 0), color=color.rgb(35, 8, 18), rotation=(0, 0, -20))

        self.patrol_points = []
        self.current_patrol_idx = 0
        self._generate_patrol()
        self.state = 'patrol'
        self.target_pos = None
        self.last_seen_player = None
        self.search_timer = 0
        self.attack_range = 2.5
        self.vision_range = 25
        self.vision_angle = 60
        self.anim_time = 0
        self.limp_offset = random.uniform(0, 3.14)

    def _generate_patrol(self):
        for _ in range(5):
            self.patrol_points.append(rand_pos(self.world_size, 8))
        self.target_pos = self.patrol_points[0]

    def update(self, dt, player_pos, player_hidden=False):
        self.anim_time += dt
        self.limp_offset += dt * 2
        self.body.rotation_z = math.sin(self.limp_offset) * 8
        self.head.rotation_y = math.sin(self.limp_offset * 0.7) * 15
        self.arm_left.rotation_z = 20 + math.sin(self.limp_offset) * 30
        self.arm_right.rotation_z = -20 - math.sin(self.limp_offset) * 30

        d = dist_2d(self.x, self.z, player_pos.x, player_pos.z)
        can_see = False
        if d < self.vision_range and not player_hidden:
            dir_to_player = Vec3(player_pos.x - self.x, 0, player_pos.z - self.z).normalized()
            forward = Vec3(math.sin(math.radians(self.rotation_y)), 0, math.cos(math.radians(self.rotation_y)))
            angle = math.degrees(math.acos(clamp(dir_to_player.dot(forward), -1, 1)))
            if angle < self.vision_angle:
                can_see = True

        if can_see and self.can_hunt:
            self.state = 'chase'
            self.last_seen_player = Vec3(player_pos.x, 0, player_pos.z)
        elif self.state == 'chase' and d > self.vision_range * 1.5:
            self.state = 'search'
            self.search_timer = 5.0
        elif self.state == 'search':
            self.search_timer -= dt
            if self.search_timer <= 0:
                self.state = 'patrol'

        if self.state == 'patrol':
            self._move_to(self.target_pos, dt, self.speed * 0.5)
            if dist_2d(self.x, self.z, self.target_pos[0], self.target_pos[1]) < 2:
                self.current_patrol_idx = (self.current_patrol_idx + 1) % len(self.patrol_points)
                self.target_pos = self.patrol_points[self.current_patrol_idx]
        elif self.state == 'chase':
            chase_target = Vec3(player_pos.x, 0, player_pos.z)
            self._move_to((chase_target.x, chase_target.z), dt, self.speed)
            if random.random() < 0.01:
                self._move_to((chase_target.x, chase_target.z), dt, self.speed * 2.5)
        elif self.state == 'search':
            if self.last_seen_player:
                self._move_to((self.last_seen_player.x, self.last_seen_player.z), dt, self.speed * 0.7)

        if self.target_pos:
            self.look_at(Vec3(self.target_pos[0], self.y, self.target_pos[1]))

        if d < self.attack_range:
            return 'attack'
        return None

    def _move_to(self, target, dt, speed):
        dx = target[0] - self.x
        dz = target[1] - self.z
        dist = math.sqrt(dx*dx + dz*dz)
        if dist > 0.5:
            self.x += (dx / dist) * speed * dt
            self.z += (dz / dist) * speed * dt
        half = self.world_size / 2 - 3
        self.x = clamp(self.x, -half, half)
        self.z = clamp(self.z, -half, half)

# =============================================================================
# FAKE FRIEND
# =============================================================================
class FakeFriend(Entity):
    def __init__(self, position, world_size, **kwargs):
        super().__init__(position=position, **kwargs)
        self.world_size = world_size
        self.state = 'lure'
        self.lure_range = 15
        self.attack_range = 3
        self.speed = 3.0

        self.body = Entity(parent=self, model='cube', scale=(0.5, 1.6, 0.35),
                          position=(0, 0.8, 0), color=color.rgb(200, 180, 170))
        self.head = Entity(parent=self, model='sphere', scale=(0.4, 0.45, 0.4),
                          position=(0, 1.7, 0), color=color.rgb(220, 200, 190))
        self.mouth = Entity(parent=self.head, model='cube', scale=(0.15, 0.03, 0.05),
                           position=(0, -0.1, 0.2), color=color.rgb(150, 50, 50))
        self.name_tag = Text(text='HELPER', position=(self.x, self.y + 2.2, self.z),
                            scale=1.5, color=color.green, origin=(0, 0))
        self.dialogue = random.choice(FAKE_FRIEND_DIALOGUE)
        self.dialogue_timer = 0
        self.showing_dialogue = False

    def update(self, dt, player_pos):
        d = dist_2d(self.x, self.z, player_pos.x, player_pos.z)
        self.name_tag.position = (self.x, self.y + 2.2, self.z)
        self.name_tag.look_at(camera.position)

        if self.state == 'lure':
            self.head.rotation_y = math.sin(pytime.time() * 3) * 30
            if d < self.lure_range:
                if not self.showing_dialogue:
                    self.showing_dialogue = True
                    self.dialogue_timer = 3.0
                else:
                    self.dialogue_timer -= dt
                    if self.dialogue_timer <= 0:
                        self.state = 'chase'
                        self._transform()
        elif self.state == 'chase':
            dx = player_pos.x - self.x
            dz = player_pos.z - self.z
            dist_to = math.sqrt(dx*dx + dz*dz)
            if dist_to > 0.5:
                self.x += (dx / dist_to) * self.speed * dt
                self.z += (dz / dist_to) * self.speed * dt
            self.look_at(Vec3(player_pos.x, self.y, player_pos.z))
            if d < self.attack_range:
                return 'attack'
        return None

    def _transform(self):
        self.body.color = color.rgb(60, 20, 30)
        self.head.color = color.rgb(40, 10, 20)
        self.head.scale = (0.5, 0.6, 0.5)
        Entity(parent=self.head, model='sphere', scale=(0.1, 0.1, 0.1),
              position=(-0.12, 0.05, 0.2), color=color.red)
        Entity(parent=self.head, model='sphere', scale=(0.1, 0.1, 0.1),
              position=(0.12, 0.05, 0.2), color=color.red)
        self.mouth.scale = (0.25, 0.08, 0.05)
        self.mouth.color = color.rgb(80, 10, 10)
        self.name_tag.text = 'IT LIES'
        self.name_tag.color = color.red
        self.animate_scale((1.2, 1.2, 1.2), duration=0.3)
        self.animate_scale((1, 1, 1), duration=0.3, delay=0.3)

# =============================================================================
# NOTE
# =============================================================================
class Note(Entity):
    def __init__(self, position, message, note_id, **kwargs):
        super().__init__(position=position, **kwargs)
        self.message = message
        self.note_id = note_id
        self.collected = False
        self.paper = Entity(parent=self, model='plane', scale=(0.6, 1, 0.8),
                           rotation=(90, 0, 0), color=color.rgb(255, 250, 240))
        self.glow = Entity(parent=self, model='sphere', scale=(1.5, 1.5, 1.5),
                          color=color.rgb(255, 200, 200), alpha=0.3)
        self.float_offset = random.random() * 6.28

    def update(self, dt, player_pos):
        if self.collected:
            return False
        self.float_offset += dt * 2
        self.y = self.position[1] + math.sin(self.float_offset) * 0.2
        self.rotation_y += dt * 30
        d = dist_2d(self.x, self.z, player_pos.x, player_pos.z)
        if d < 2.5 and abs(self.y - player_pos.y) < 2:
            self.collected = True
            self.paper.enabled = False
            self.glow.enabled = False
            return True
        return False

# =============================================================================
# TRAP
# =============================================================================
class Trap(Entity):
    def __init__(self, position, **kwargs):
        super().__init__(position=position, **kwargs)
        self.triggered = False
        self.floor = Entity(parent=self, model='cube', scale=(2, 0.1, 2),
                           position=(0, 0, 0), color=color.rgb(60, 40, 40))
        self.spikes = Entity(parent=self, model='cone', scale=(0.3, 1.5, 0.3),
                            position=(0, -0.5, 0), color=color.rgb(80, 20, 20), enabled=False)

    def update(self, dt, player_pos):
        if self.triggered:
            return False
        d = dist_2d(self.x, self.z, player_pos.x, player_pos.z)
        if d < 1.5:
            self.triggered = True
            self.spikes.enabled = True
            self.spikes.animate_position((0, 0.8, 0), duration=0.2)
            return True
        return False

# =============================================================================
# WEAPON PICKUP
# =============================================================================
class WeaponPickup(Entity):
    def __init__(self, position, weapon_type, **kwargs):
        super().__init__(position=position, **kwargs)
        self.weapon_type = weapon_type
        self.collected = False
        colors = {
            'flashlight': color.rgb(255, 255, 200),
            'knife': color.rgb(180, 180, 190),
            'gun': color.rgb(50, 50, 60),
            'medkit': color.rgb(255, 50, 50)
        }
        self.mesh = Entity(parent=self, model='cube', scale=(0.4, 0.4, 0.4),
                          color=colors.get(weapon_type, color.white))
        self.glow = Entity(parent=self, model='sphere', scale=(1, 1, 1),
                          color=colors.get(weapon_type, color.white), alpha=0.2)
        self.float_offset = random.random() * 6.28

    def update(self, dt, player_pos):
        if self.collected:
            return None
        self.float_offset += dt * 3
        self.y = self.position[1] + math.sin(self.float_offset) * 0.15
        self.rotation_y += dt * 45
        d = dist_2d(self.x, self.z, player_pos.x, player_pos.z)
        if d < 2:
            self.collected = True
            self.mesh.enabled = False
            self.glow.enabled = False
            return self.weapon_type
        return None

# =============================================================================
# WORLD BUILDER
# =============================================================================
class WorldBuilder:
    def __init__(self):
        self.entities = []
        self.notes = []
        self.traps = []
        self.weapons = []
        self.fake_friends = []
        self.monster = None
        self.ground = None
        self.walls = []

    def build_mission(self, mission_idx):
        config = MISSIONS[mission_idx]
        size = config['size']
        self.cleanup()

        ground_color = color.rgb(30, 20, 25) if config['darkness'] > 0.5 else color.rgb(40, 30, 35)
        self.ground = Entity(model='plane', scale=(size, 1, size), color=ground_color,
                            texture='white_cube', texture_scale=(size/10, size/10), collider='box')
        self.entities.append(self.ground)

        water = Entity(model='plane', scale=(300, 1, 300), position=(0, -0.5, 0),
                      color=color.rgb(255, 182, 193), texture='white_cube', texture_scale=(100, 100))
        self.entities.append(water)

        for _ in range(8):
            x, z = rand_pos(size, 5)
            if abs(x) < 10 and abs(z) < 10:
                continue
            hill = Entity(model='sphere', scale=(random.uniform(4, 8), random.uniform(2, 4), random.uniform(4, 8)),
                         position=(x, 0, z), color=color.rgb(255, 190, 205), collider='box')
            self.entities.append(hill)

        for _ in range(20 + mission_idx * 5):
            x, z = rand_pos(size, 5)
            self._build_dead_tree(x, z)

        for _ in range(10 + mission_idx * 3):
            x, z = rand_pos(size, 3)
            rock = Entity(model='cube', scale=(random.uniform(1, 3), random.uniform(0.5, 2), random.uniform(1, 3)),
                         position=(x, 0.5, z), color=color.rgb(45, 40, 42), collider='box')
            rock.rotation = (random.uniform(-15, 15), random.uniform(0, 360), random.uniform(-15, 15))
            self.entities.append(rock)

        used_messages = set()
        for i in range(config['notes_required']):
            x, z = rand_pos(size, 8)
            available = [m for m in NOMAN_MESSAGES if m not in used_messages]
            if not available:
                available = NOMAN_MESSAGES
            msg = random.choice(available)
            used_messages.add(msg)
            note = Note(position=(x, 1.5, z), message=msg, note_id=i)
            self.notes.append(note)

        for wtype in config['weapons']:
            x, z = rand_pos(size, 5)
            weapon = WeaponPickup(position=(x, 1, z), weapon_type=wtype)
            self.weapons.append(weapon)

        for _ in range(config['trap_count']):
            x, z = rand_pos(size, 5)
            trap = Trap(position=(x, 0, z))
            self.traps.append(trap)

        for _ in range(config['fake_friends']):
            x, z = rand_pos(size, 10)
            ff = FakeFriend(position=(x, 0, z), world_size=size)
            self.fake_friends.append(ff)

        mx, mz = rand_pos(size, 15)
        self.monster = Monster(world_size=size, config=config, position=(mx, 0, mz))

        half = size / 2
        wall_thickness = 1
        walls = [
            (0, 1, -half, size, 3, wall_thickness),
            (0, 1, half, size, 3, wall_thickness),
            (-half, 1, 0, wall_thickness, 3, size),
            (half, 1, 0, wall_thickness, 3, size)
        ]
        for wx, wy, wz, ww, wh, wd in walls:
            w = Entity(model='cube', scale=(ww, wh, wd), position=(wx, wy, wz),
                      color=color.clear, collider='box', visible=False)
            self.walls.append(w)
            self.entities.append(w)

        scene.fog_color = color.rgb(20, 10, 15)
        scene.fog_density = config['darkness'] * 0.03

        return config

    def _build_dead_tree(self, x, z):
        trunk_h = random.uniform(3, 6)
        trunk = Entity(model='cube', scale=(0.4, trunk_h, 0.4),
                      position=(x, trunk_h/2, z), color=color.rgb(35, 25, 20), collider='box')
        self.entities.append(trunk)
        for _ in range(3):
            bx = x + random.uniform(-2, 2)
            bz = z + random.uniform(-2, 2)
            by = trunk_h + random.uniform(-1, 2)
            branch = Entity(model='cube', scale=(0.15, random.uniform(1, 3), 0.15),
                           position=(bx, by, bz), color=color.rgb(30, 20, 15),
                           rotation=(random.uniform(-30, 30), random.uniform(0, 360), random.uniform(-30, 30)))
            self.entities.append(branch)

    def update(self, dt, player_pos):
        results = {
            'note_collected': None,
            'weapon_collected': None,
            'trap_triggered': False,
            'monster_attack': False,
            'fake_friend_attack': False,
        }

        for note in self.notes:
            if note.update(dt, player_pos):
                results['note_collected'] = note.message

        for weapon in self.weapons:
            wtype = weapon.update(dt, player_pos)
            if wtype:
                results['weapon_collected'] = wtype

        for trap in self.traps:
            if trap.update(dt, player_pos):
                results['trap_triggered'] = True

        if self.monster:
            attack = self.monster.update(dt, player_pos)
            if attack:
                results['monster_attack'] = True

        for ff in self.fake_friends:
            attack = ff.update(dt, player_pos)
            if attack:
                results['fake_friend_attack'] = True

        return results

    def get_notes_collected(self):
        return sum(1 for n in self.notes if n.collected)

    def cleanup(self):
        for e in self.entities:
            if e:
                destroy(e)
        self.entities = []
        for note in self.notes:
            destroy(note)
        self.notes = []
        for trap in self.traps:
            destroy(trap)
        self.traps = []
        for weapon in self.weapons:
            destroy(weapon)
        self.weapons = []
        for ff in self.fake_friends:
            destroy(ff)
            if ff.name_tag:
                destroy(ff.name_tag)
        self.fake_friends = []
        if self.monster:
            destroy(self.monster)
        self.monster = None
        self.walls = []

# =============================================================================
# PLAYER
# =============================================================================
class PlayerController(Entity):
    def __init__(self, avatar_manager, **kwargs):
        super().__init__(**kwargs)
        self.avatar_manager = avatar_manager

        self.body = Entity(parent=self, model='cube', scale=(0.5, 1.4, 0.35),
                          position=(0, 0.7, 0), color=color.rgb(80, 60, 70))
        face_tex = self.avatar_manager.get_face_texture()
        self.head = Entity(parent=self, model='cube', scale=(0.4, 0.45, 0.4),
                          position=(0, 1.55, 0),
                          texture=face_tex if face_tex else color.rgb(240, 220, 210))
        self.hair = Entity(parent=self.head, model='cube', scale=(0.45, 0.15, 0.45),
                          position=(0, 0.25, 0), color=color.rgb(40, 20, 10))
        self.arm_left = Entity(parent=self, model='cube', scale=(0.12, 0.7, 0.12),
                              position=(-0.35, 0.9, 0), color=color.rgb(80, 60, 70))
        self.arm_right = Entity(parent=self, model='cube', scale=(0.12, 0.7, 0.12),
                               position=(0.35, 0.9, 0), color=color.rgb(80, 60, 70))
        self.leg_left = Entity(parent=self, model='cube', scale=(0.15, 0.7, 0.15),
                              position=(-0.15, -0.35, 0), color=color.rgb(50, 40, 45))
        self.leg_right = Entity(parent=self, model='cube', scale=(0.15, 0.7, 0.15),
                               position=(0.15, -0.35, 0), color=color.rgb(50, 40, 45))

        self.flashlight = Entity(parent=self, model='cube', scale=(0.08, 0.25, 0.08),
                                position=(0.25, 1.1, 0.2), color=color.rgb(60, 60, 50), enabled=False)
        self.flashlight_light = SpotLight(parent=self.flashlight, position=(0, 0.15, 0),
                                         color=color.rgb(255, 250, 220), intensity=2, range=20, enabled=False)

        self.speed = 4.0
        self.sprint_speed = 6.5
        self.jump_power = 6
        self.velocity_y = 0
        self.gravity = 18
        self.grounded = True
        self.stamina = 100

        self.camera_pivot = Entity(parent=self, position=(0, 2.2, 0))
        camera.parent = self.camera_pivot
        camera.position = (0, 1.5, -5)
        camera.rotation_x = 15
        camera.fov = 75

        self.has_flashlight = False
        self.has_knife = False
        self.has_gun = False
        self.has_medkit = False
        self.flashlight_on = False

        self.health = 100
        self.max_health = 100

        self.walk_anim = 0
        self.breathing = 0

    def update(self):
        self.breathing += time.dt * 2
        self.head.y = 1.55 + math.sin(self.breathing) * 0.02

        self.camera_pivot.rotation_y += mouse.velocity[0] * 40
        self.camera_pivot.rotation_x -= mouse.velocity[1] * 40
        self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -20, 40)

        move_dir = Vec3(0, 0, 0)
        if held_keys['w'] or held_keys['up arrow']:
            move_dir += self.forward
        if held_keys['s'] or held_keys['down arrow']:
            move_dir -= self.forward
        if held_keys['a'] or held_keys['left arrow']:
            move_dir -= self.right
        if held_keys['d'] or held_keys['right arrow']:
            move_dir += self.right

        is_sprinting = held_keys['left shift'] and self.stamina > 0
        current_speed = self.sprint_speed if is_sprinting else self.speed

        if is_sprinting and move_dir.length() > 0:
            self.stamina -= time.dt * 15
        else:
            self.stamina = min(100, self.stamina + time.dt * 8)

        if move_dir.length() > 0:
            move_dir = move_dir.normalized()
            self.position += move_dir * current_speed * time.dt
            self.walk_anim += time.dt * 10
            self.leg_left.rotation_x = math.sin(self.walk_anim) * 25
            self.leg_right.rotation_x = math.sin(self.walk_anim + math.pi) * 25
            self.arm_left.rotation_x = math.sin(self.walk_anim + math.pi) * 15
            self.arm_right.rotation_x = math.sin(self.walk_anim) * 15
            self.body.y = 0.7 + abs(math.sin(self.walk_anim * 2)) * 0.05
        else:
            self.leg_left.rotation_x = lerp(self.leg_left.rotation_x, 0, time.dt * 8)
            self.leg_right.rotation_x = lerp(self.leg_right.rotation_x, 0, time.dt * 8)
            self.arm_left.rotation_x = lerp(self.arm_left.rotation_x, 0, time.dt * 8)
            self.arm_right.rotation_x = lerp(self.arm_right.rotation_x, 0, time.dt * 8)
            self.body.y = lerp(self.body.y, 0.7, time.dt * 5)

        if held_keys['space'] and self.grounded:
            self.velocity_y = self.jump_power
            self.grounded = False

        self.velocity_y -= self.gravity * time.dt
        self.y += self.velocity_y * time.dt

        if self.y < 0:
            self.y = 0
            self.velocity_y = 0
            self.grounded = True

        if held_keys['f'] and self.has_flashlight:
            self.flashlight_on = not self.flashlight_on
            self.flashlight.enabled = self.flashlight_on
            self.flashlight_light.enabled = self.flashlight_on

        current_tex = self.avatar_manager.get_face_texture()
        if current_tex and self.head.texture != current_tex:
            self.head.texture = current_tex

    def take_damage(self, amount):
        self.health -= amount
        self.health = max(0, self.health)
        overlay = Entity(parent=camera.ui, model='quad', scale=(2, 1.2),
                        color=color.rgb(255, 0, 0, 100), z=-1)
        destroy(overlay, delay=0.3)
        camera.shake(duration=0.5, magnitude=0.3)

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

# =============================================================================
# UI
# =============================================================================
class GameUI:
    def __init__(self):
        self.health_bg = Entity(parent=camera.ui, model='quad', scale=(0.3, 0.04),
                               position=(-0.65, 0.45), color=color.rgb(50, 10, 10), origin=(-0.5, 0))
        self.health_bar = Entity(parent=camera.ui, model='quad', scale=(0.3, 0.04),
                                position=(-0.65, 0.45), color=color.rgb(200, 30, 30), origin=(-0.5, 0))
        self.stamina_bg = Entity(parent=camera.ui, model='quad', scale=(0.2, 0.02),
                                position=(-0.65, 0.40), color=color.rgb(30, 30, 30), origin=(-0.5, 0))
        self.stamina_bar = Entity(parent=camera.ui, model='quad', scale=(0.2, 0.02),
                                 position=(-0.65, 0.40), color=color.rgb(255, 200, 50), origin=(-0.5, 0))
        self.note_text = Text(parent=camera.ui, text='Notes: 0/0', position=(-0.85, 0.35),
                             scale=1.5, color=color.rgb(255, 200, 200))
        self.mission_text = Text(parent=camera.ui, text='', position=(0, 0.45),
                                scale=1.8, color=color.rgb(255, 150, 150), origin=(0, 0))
        self.message_bg = Entity(parent=camera.ui, model='quad', scale=(0.8, 0.2),
                                position=(0, -0.35), color=color.rgb(10, 5, 8, 200),
                                origin=(0, 0), enabled=False)
        self.message_text = Text(parent=camera.ui, text='', position=(0, -0.35),
                                scale=2, color=color.rgb(255, 200, 200), origin=(0, 0), enabled=False)
        self.message_timer = 0
        self.inventory_text = Text(parent=camera.ui, text='', position=(0.75, -0.4),
                                  scale=1.2, color=color.rgb(200, 200, 200), origin=(0.5, 0))
        self.warning_flash = Entity(parent=camera.ui, model='quad', scale=(2, 1.2),
                                   color=color.clear, z=-0.5)
        self.death_bg = Entity(parent=camera.ui, model='quad', scale=(2, 1.2),
                              color=color.rgb(0, 0, 0), z=-2, enabled=False)
        self.death_text = Text(parent=camera.ui, text='', position=(0, 0),
                              scale=4, color=color.red, origin=(0, 0), enabled=False)
        self.enabled = False

    def update(self, player, mission_config, notes_collected):
        health_pct = player.health / player.max_health
        self.health_bar.scale_x = 0.3 * health_pct
        if health_pct < 0.3:
            self.health_bar.color = color.rgb(255, 0, 0)
            self.warning_flash.color = color.rgb(255, 0, 0, abs(math.sin(time.time() * 5)) * 50)
        else:
            self.health_bar.color = color.rgb(200, 30, 30)
            self.warning_flash.color = color.clear

        stamina_pct = player.stamina / 100
        self.stamina_bar.scale_x = 0.2 * stamina_pct

        self.note_text.text = f'Notes: {notes_collected}/{mission_config["notes_required"]}'
        self.mission_text.text = mission_config['name']

        inv_items = []
        if player.has_flashlight:
            inv_items.append('FLASHLIGHT' + (' [ON]' if player.flashlight_on else ''))
        if player.has_knife:
            inv_items.append('KNIFE')
        if player.has_gun:
            inv_items.append('GUN')
        if player.has_medkit:
            inv_items.append('MEDKIT')
        self.inventory_text.text = '\n'.join(inv_items) if inv_items else 'No items'

        if self.message_timer > 0:
            self.message_timer -= time.dt
            if self.message_timer <= 0:
                self.message_bg.enabled = False
                self.message_text.enabled = False

    def show_message(self, text, duration=4):
        self.message_text.text = text
        self.message_bg.enabled = True
        self.message_text.enabled = True
        self.message_timer = duration

    def show_death(self, message):
        self.death_bg.enabled = True
        self.death_text.text = message
        self.death_text.enabled = True

    def hide_death(self):
        self.death_bg.enabled = False
        self.death_text.enabled = False

# =============================================================================
# MENUS
# =============================================================================
class MainMenu(Entity):
    def __init__(self, start_callback, avatar_callback, exit_callback):
        super().__init__(parent=camera.ui)

        Entity(parent=self, model='quad', scale=(2, 1.2), color=color.rgb(15, 8, 12), z=1)

        Text(parent=self, text="DUA'S NIGHTMARE", position=(0, 0.25), scale=4,
            color=color.rgb(200, 50, 50), origin=(0, 0))
        Text(parent=self, text='Finding Noman', position=(0, 0.12), scale=2,
            color=color.rgb(150, 80, 80), origin=(0, 0))

        btn_scale = (0.4, 0.08)
        btn_color = color.rgb(80, 30, 30)
        hover = color.rgb(120, 40, 40)

        self.play_btn = Button(parent=self, text='START GAME', position=(0, -0.05),
                              scale=btn_scale, color=btn_color, highlight_color=hover,
                              text_color=color.rgb(255, 200, 200))
        self.play_btn.on_click = start_callback

        self.avatar_btn = Button(parent=self, text='AVATAR', position=(0, -0.18),
                                scale=btn_scale, color=btn_color, highlight_color=hover,
                                text_color=color.rgb(255, 200, 200))
        self.avatar_btn.on_click = avatar_callback

        self.exit_btn = Button(parent=self, text='EXIT', position=(0, -0.31),
                              scale=btn_scale, color=btn_color, highlight_color=hover,
                              text_color=color.rgb(255, 200, 200))
        self.exit_btn.on_click = exit_callback

        self.particles = []
        for _ in range(30):
            p = Entity(parent=self, model='circle', scale=random.uniform(0.01, 0.03),
                      position=(random.uniform(-1, 1), random.uniform(-0.6, 0.6), -0.1),
                      color=color.rgb(100, 20, 20))
            self.particles.append({'entity': p, 'speed': random.uniform(0.05, 0.2), 'sway': random.random() * 6.28})

    def update(self):
        for p in self.particles:
            p['sway'] += time.dt * 1.5
            p['entity'].y += p['speed'] * time.dt * 0.05
            p['entity'].x += math.sin(p['sway']) * time.dt * 0.02
            if p['entity'].y > 0.7:
                p['entity'].y = -0.7
                p['entity'].x = random.uniform(-1, 1)

    def show(self):
        self.enabled = True

    def hide(self):
        self.enabled = False

class PauseMenu(Entity):
    def __init__(self, resume_callback, quit_callback):
        super().__init__(parent=camera.ui)

        Entity(parent=self, model='quad', scale=(2, 1.2), color=color.rgb(0, 0, 0, 180), z=1)
        Text(parent=self, text='PAUSED', position=(0, 0.15), scale=3,
            color=color.rgb(200, 50, 50), origin=(0, 0))

        btn_scale = (0.35, 0.08)
        btn_color = color.rgb(60, 20, 20)

        self.resume_btn = Button(parent=self, text='RESUME', position=(0, -0.05),
                                scale=btn_scale, color=btn_color, text_color=color.rgb(255, 200, 200))
        self.resume_btn.on_click = resume_callback

        self.quit_btn = Button(parent=self, text='QUIT TO MENU', position=(0, -0.18),
                              scale=btn_scale, color=btn_color, text_color=color.rgb(255, 200, 200))
        self.quit_btn.on_click = quit_callback

        self.enabled = False

    def show(self):
        self.enabled = True

    def hide(self):
        self.enabled = False

# =============================================================================
# GAME
# =============================================================================
class Game:
    def __init__(self):
        self.app = Ursina(
            title="Dua's Nightmare: Finding Noman",
            borderless=False,
            fullscreen=False,
            size=(1280, 720),
            vsync=True
        )

        window.color = color.rgb(10, 5, 8)

        self.avatar_manager = AvatarManager()
        self.state = 'menu'
        self.current_mission = 0
        self.player = None
        self.world_builder = WorldBuilder()
        self.ui = None
        self.mission_config = None
        self.sky = None
        self.light = None
        self.escape_held = False

        self.main_menu = MainMenu(
            start_callback=self.start_game,
            avatar_callback=self.show_avatar,
            exit_callback=self.exit_game
        )

        self.pause_menu = None

    def start_game(self):
        self.current_mission = 0
        self._start_mission(0)
        self.main_menu.hide()

    def _start_mission(self, mission_idx):
        self.mission_config = MISSIONS[mission_idx]
        self.world_builder.build_mission(mission_idx)

        if self.player:
            destroy(self.player)

        self.player = PlayerController(avatar_manager=self.avatar_manager, position=(0, 0, 0))

        if not self.ui:
            self.ui = GameUI()
        else:
            self.ui.hide_death()

        self.ui.show_message(
            f'Mission {mission_idx + 1}: {self.mission_config["name"]}\n{self.mission_config["desc"]}',
            duration=5
        )

        self.sky = Sky(color=color.rgb(20, 10, 15))
        self.light = DirectionalLight()
        self.light.look_at((1, -0.5, 1))
        self.light.color = color.rgb(80, 60, 70)

        self.state = 'playing'
        mouse.locked = True

    def show_avatar(self):
        if self.avatar_manager.open_gallery():
            print("Avatar updated!")
        elif self.avatar_manager.open_camera():
            pass
        else:
            self.avatar_manager.face_texture = self.avatar_manager.default_face
            print("Using default avatar")

    def exit_game(self):
        application.quit()

    def resume_game(self):
        self.state = 'playing'
        mouse.locked = True
        if self.pause_menu:
            self.pause_menu.hide()

    def return_to_menu(self):
        self._cleanup()
        self.state = 'menu'
        mouse.locked = False
        self.main_menu.show()
        if self.pause_menu:
            self.pause_menu.hide()

    def _cleanup(self):
        if self.player:
            destroy(self.player)
            self.player = None
        self.world_builder.cleanup()
        if self.sky:
            destroy(self.sky)
            self.sky = None
        if self.light:
            destroy(self.light)
            self.light = None

    def _check_escape(self):
        if held_keys.get('escape'):
            if not self.escape_held:
                self.escape_held = True
                if self.state == 'playing':
                    self.state = 'paused'
                    mouse.locked = False
                    if not self.pause_menu:
                        self.pause_menu = PauseMenu(
                            resume_callback=self.resume_game,
                            quit_callback=self.return_to_menu
                        )
                    self.pause_menu.show()
                elif self.state == 'paused':
                    self.resume_game()
        else:
            self.escape_held = False

    def update(self):
        self._check_escape()

        if self.avatar_manager.camera_active:
            self.avatar_manager.update_camera()

        if self.state != 'playing' or not self.player:
            return

        results = self.world_builder.update(time.dt, self.player.position)

        if results['note_collected']:
            self.ui.show_message(f'Note from Noman:\n"{results["note_collected"]}"')
            notes_collected = self.world_builder.get_notes_collected()
            if notes_collected >= self.mission_config['notes_required']:
                self._complete_mission()

        if results['weapon_collected']:
            wtype = results['weapon_collected']
            if wtype == 'flashlight':
                self.player.has_flashlight = True
                self.ui.show_message('Found: FLASHLIGHT (Press F)')
            elif wtype == 'knife':
                self.player.has_knife = True
                self.ui.show_message('Found: KNIFE')
            elif wtype == 'gun':
                self.player.has_gun = True
                self.ui.show_message('Found: GUN')
            elif wtype == 'medkit':
                self.player.has_medkit = True
                self.player.heal(50)
                self.ui.show_message('Found: MEDKIT (+50 HP)')

        if results['trap_triggered']:
            self.player.take_damage(25)
            self.ui.show_message('TRAP! You stepped on something sharp...')

        if results['monster_attack']:
            self.player.take_damage(35)
            self.ui.show_message('The monster caught you! RUN!')

        if results['fake_friend_attack']:
            self.player.take_damage(30)
            self.ui.show_message('IT WAS A TRAP! Your "friend" attacked!')

        if self.player.health <= 0:
            self._game_over()

        notes_collected = self.world_builder.get_notes_collected()
        self.ui.update(self.player, self.mission_config, notes_collected)

    def _complete_mission(self):
        self.state = 'mission_complete'
        mouse.locked = False

        if self.current_mission < len(MISSIONS) - 1:
            self.ui.show_message(
                f'Mission Complete!\nNoman is still waiting...\nNext: {MISSIONS[self.current_mission + 1]["name"]}',
                duration=5
            )
            invoke(self._next_mission, delay=5)
        else:
            self.ui.show_message(
                'You found all the notes...\nBut Noman was never real.\nThe monster was you all along.',
                duration=8
            )
            invoke(self.return_to_menu, delay=8)

    def _next_mission(self):
        self.current_mission += 1
        self._start_mission(self.current_mission)

    def _game_over(self):
        self.state = 'gameover'
        mouse.locked = False
        self.ui.show_death('YOU DIED\nNoman still waits...')
        invoke(self.return_to_menu, delay=4)

    def run(self):
        self.app.run()

# =============================================================================
# MAIN
# =============================================================================
def main():
    game = Game()
    game.run()

if __name__ == '__main__':
    main()
