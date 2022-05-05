# I am the TimeSwitchItem    database item.
class TimeSwitchItem:
    id = None
    flags = None
    value_on = None
    value_off = None
    monday = None
    tuesday = None
    wednesday = None
    thursday = None
    friday = None
    saturday = None
    sunday = None
    auto_address = None
    write_address = None

    # I will create the TimeSwitchItem.
    def __init__(self, timeswitchItemRow, baseClient):
        self.id            = timeswitchItemRow[0]
        self.flags         = timeswitchItemRow[1]
        self.value_on      = timeswitchItemRow[2]
        self.value_off     = timeswitchItemRow[3]
        self.monday        = timeswitchItemRow[4]
        self.tuesday       = timeswitchItemRow[5]
        self.wednesday     = timeswitchItemRow[6]
        self.thursday      = timeswitchItemRow[7]
        self.friday        = timeswitchItemRow[8]
        self.saturday      = timeswitchItemRow[9]
        self.sunday        = timeswitchItemRow[10]
        self.auto_address  = timeswitchItemRow[11]
        self.write_address = timeswitchItemRow[12]
        self.baseClient    = baseClient
