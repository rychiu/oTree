from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import random
import utils


doc = """
The principal offers a contract to the agent, who can decide if to reject or
accept. The agent then chooses an effort level. The implementation is based on
<a href="http://www.nottingham.ac.uk/cedex/documents/papers/2006-04.pdf" target="_blank">
    Gaechter and Koenigstein (2006)
</a>.
"""


class Constants(BaseConstants):
    name_in_url = 'principal_agent'
    players_per_group = 2
    num_rounds = 1

    instructions_template = 'principal_agent/Instructions.html'

    bonus = c(30)
    min_fixed_payment = c(-30)
    max_fixed_payment = c(30)

    # """Amount principal gets if contract is rejected"""
    reject_principal_pay = c(0)

    reject_agent_pay = c(10)

    agent_return_share_choices = [
        [percent / 100, '{}%'.format(percent)]
        for percent in range(10, 100 + 1, 10)]

    EFFORT_TO_RETURN = {
        1: 14,
        2: 28,
        3: 42,
        4: 54,
        5: 70,
        6: 84,
        7: 98,
        8: 112,
        9: 126,
        10: 140}

    EFFORT_TO_COST = {
        1: 0,
        2: 4,
        3: 8,
        4: 12,
        5: 18,
        6: 24,
        7: 32,
        8: 40,
        9: 50,
        10: 60}


def cost_from_effort(effort):
    return c(Constants.EFFORT_TO_COST[effort])


def return_from_effort(effort):
    return c(Constants.EFFORT_TO_RETURN[effort])


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    total_return = models.CurrencyField(
        doc="""Total return from agent's effort = [Return for single unit of
            agent's work effort] * [Agent's work effort]"""
    )

    agent_fixed_pay = models.CurrencyField(
        doc="""Amount offered as fixed pay to agent""",
        min=Constants.min_fixed_payment, max=Constants.max_fixed_payment,
        verbose_name='Fixed Payment (from {} to {})'.format(
            Constants.min_fixed_payment, Constants.max_fixed_payment)
    )

    agent_return_share = models.FloatField(
        choices=Constants.agent_return_share_choices,
        doc="""Agent's share of total return""",
        verbose_name='Return Share',
        widget=widgets.RadioSelectHorizontal()
    )

    agent_work_effort = models.PositiveIntegerField(
        choices=range(1, 10 + 1),
        doc="""Agent's work effort, [1, 10]""",
        widget=widgets.RadioSelectHorizontal(),
    )

    agent_work_cost = models.CurrencyField(
        doc="""Agent's cost of work effort"""
    )

    contract_accepted = models.BooleanField(
        doc="""Whether agent accepts proposal""",
        widget=widgets.RadioSelect(),
        choices=(
            (True, 'Accept'),
            (False, 'Reject'),
        )
    )

    def set_payoffs(self):
        principal = self.get_player_by_role('principal')
        agent = self.get_player_by_role('agent')

        if not self.contract_accepted:
            principal.payoff = Constants.reject_principal_pay
            agent.payoff = Constants.reject_agent_pay
        else:
            self.agent_work_cost = cost_from_effort(self.agent_work_effort)
            self.total_return = return_from_effort(self.agent_work_effort)

            money_to_agent = self.agent_return_share * \
                             self.total_return + self.agent_fixed_pay
            agent.payoff = money_to_agent - self.agent_work_cost
            principal.payoff = self.total_return - money_to_agent
        principal.payoff += Constants.bonus
        agent.payoff += Constants.bonus

    def return_share_as_percentage(self):
        return utils.float_as_percentage(self.agent_return_share)


class Player(BasePlayer):
    def role(self):
        if self.id_in_group == 1:
            return 'principal'
        if self.id_in_group == 2:
            return 'agent'
