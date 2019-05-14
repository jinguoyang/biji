# coding: utf-8

from state.table_state.base import TableStateBase


class WaitState(TableStateBase):

    def execute(self, owner, event):
        super(WaitState, self).execute(owner, event)
        from logic.table_action import end
        if event == "end":
            end(owner)
