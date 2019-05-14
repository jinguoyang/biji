# coding: utf-8

from rules.table_rules.base import TableRulesBase


class SettleForRoundRule(TableRulesBase):
    def condition(self, table):
        if table.cur_round > table.conf.max_rounds:
            return True
        else:
            return False

    def action(self, table):
        table.dismiss_room()
