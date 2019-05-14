# coding: utf-8
import json


class TableConf(object):
    def __init__(self, kwargs):
        self.kwargs = kwargs
        self.settings = json.loads(kwargs)
        self.chairs = self.settings.get("chairs", 5)
        self.max_rounds = self.settings.get("max_rounds", 20)
        self.game_type = self.settings.get("game_type", 22)
        self.app_id = self.settings.get("app_id", 1)
        self.options = self.settings.get("options")
        self.chips = self.settings.get("chips")
        self.aa = self.settings.get("aa", False)
        # 1-不带大小王 2-带大小王
        self._play_type = self.settings.get('play_types', 1)
        # 奖励分算法 1经典 2固定
        self._reward_type = self.settings.get('reward_type', 1)
        # 倍数 1/2/5/10
        self._base_score = self.settings.get('base_score', 1)
        # 1可以聊天，2不可以
        self._has_chat = self.settings.get('has_chat', 1)

    def is_aa(self):
        return self.aa

    @property
    def has_chat(self):
        return self._has_chat == 1

    @property
    def reward_type(self):
        return self._reward_type

    @property
    def base_score(self):
        return self._base_score

    @property
    def play_type(self):
        return self._play_type

    @property
    def show_card_config(self):
        """ interval_time : (1,发牌前2s) (2,发牌4s) (3,发牌后3s)
            show_card_double : 阶段:倍数
        """
        data = {
            'interval_time': [(1, 2), (2, 4), (3, 3)],
            'double': {11: 5, 21: 5, 22: 4, 23: 3, 24: 2, 31: 2},
        }
        return data
