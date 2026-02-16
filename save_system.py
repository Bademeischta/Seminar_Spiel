import json
import os
from constants import SAVE_FILE

class SaveSystem:
    def __init__(self):
        self.data = self.get_default_data()
        self.load()

    def get_default_data(self):
        return {
            "stats": {
                "total_wins": 0,
                "best_time": float('inf'),
                "highest_parry_chain": 0,
                "total_parries": 0,
                "total_damage_dealt": 0,
                "total_distance_moved": 0,
                "total_dashes": 0,
                "total_perfect_parries": 0
            },
            "unlocks": {
                "skins": ["Standard"],
                "ex_attacks": ["Papierflieger"]
            },
            "medals": {
                "no_hit": False,
                "perfect": False
            }
        }

    def load(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r') as f:
                    loaded_data = json.load(f)
                    # Merge loaded data with default to handle schema updates
                    for key in self.data:
                        if key in loaded_data:
                            if isinstance(self.data[key], dict):
                                self.data[key].update(loaded_data[key])
                            else:
                                self.data[key] = loaded_data[key]
            except Exception as e:
                print(f"Error loading save file: {e}")

    def save(self):
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Error saving file: {e}")

    def update_stat(self, stat_name, value, mode="add"):
        if stat_name in self.data["stats"]:
            if mode == "add":
                self.data["stats"][stat_name] += value
            elif mode == "min":
                self.data["stats"][stat_name] = min(self.data["stats"][stat_name], value)
            elif mode == "max":
                self.data["stats"][stat_name] = max(self.data["stats"][stat_name], value)
            elif mode == "set":
                self.data["stats"][stat_name] = value
            self.save()

    def unlock_skin(self, skin_name):
        if skin_name not in self.data["unlocks"]["skins"]:
            self.data["unlocks"]["skins"].append(skin_name)
            self.save()

    def unlock_ex(self, ex_name):
        if ex_name not in self.data["unlocks"]["ex_attacks"]:
            self.data["unlocks"]["ex_attacks"].append(ex_name)
            self.save()
