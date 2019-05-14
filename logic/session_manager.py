# coding: utf-8

import weakref

import time

from settings import heartbeat
from utils.singleton import Singleton


class SessionMgr(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.player_dict = {}
        self.session_set = set()

    def register(self, player, session):
        self.player_dict[session.uuid] = weakref.proxy(player)  # 在字典中存了player的值p todo
        player.session = session

    def add(self, session):     # 添加session
        self.session_set.add(session)

    def cancel(self, session):
        if session and session.uuid in self.player_dict.keys():
            del self.player_dict[session.uuid]

    def delete(self, session):
        self.session_set.remove(session)

    def player(self, session):
        return self.player_dict.get(session.uuid)

    def heartbeat(self):
        """
        如果十二个小时没有进行操作，那么就直接移除session
        :return:
        """
        now = time.time()
        # print("session total", len(self.session_set), "player total", len(self.player_dict))
        expire_session_set = set()
        for session in self.session_set:
            try:
                if now - session.last_time > heartbeat:     # heartbeat=12
                    session.close()
                    # print("session recycle", session.uuid)
                    expire_session_set.add(session)
            except Exception:
                pass
        map(self.delete, expire_session_set)
