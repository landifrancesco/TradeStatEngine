class TradeEntry:
    def __init__(self, filename, position_size=None, opened=None, closed=None,
                 opened_raw=None, closed_raw=None, pips_gained_lost=None,
                 profit_loss=None, risk_reward=None, strategy_used=None,
                 open_day=None, open_time=None, trade_outcome=None,
                 trade_duration_minutes=None, killzone=None, open_month=None):
        self.filename = filename
        self.position_size = position_size
        self.opened = opened
        self.closed = closed
        self.opened_raw = opened_raw
        self.closed_raw = closed_raw
        self.pips_gained_lost = pips_gained_lost
        self.profit_loss = profit_loss
        self.risk_reward = risk_reward
        self.strategy_used = strategy_used
        self.open_day = open_day
        self.open_time = open_time
        self.trade_outcome = trade_outcome
        self.trade_duration_minutes = trade_duration_minutes
        self.killzone = killzone
        self.open_month = open_month

    def to_dict(self):
        """
        Convert the entry to a dictionary for database insertion.
        """
        return {
            'filename': self.filename,
            'position_size': self.position_size,
            'opened': self.opened,
            'closed': self.closed,
            'pips_gained_lost': self.pips_gained_lost,
            'profit_loss': self.profit_loss,
            'risk_reward': self.risk_reward,
            'strategy_used': self.strategy_used,
            'open_day': self.open_day,
            'open_time': self.open_time,
            'trade_outcome': self.trade_outcome,
            'open_month': self.open_month,  # Add month
            'trade_duration_minutes': self.trade_duration_minutes,  # Add duration
            'killzone': self.killzone,  # Add Killzone
        }
