# coding: utf-8

from state.player_state.base import PlayerStateBase


class PromptDiscardState(PlayerStateBase):

    def enter(self, owner):
        super(PromptDiscardState, self).enter(owner)
        owner.table.player_prompts.append(owner.uuid)
        # owner.send_prompts()
        owner.proto.send()
        # print 'enter prompt discard'

    def next_state(self, owner):
        # print 'prompt discard state enter next'
        owner.machine.to_last_state()

    def execute(self, owner, event, proto=None):
        super(PromptDiscardState, self).execute(owner, event, proto)
        from logic.player_action import action
        if event == "action":
            action(owner, proto)
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
