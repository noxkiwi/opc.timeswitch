import threading
import time

import math
from BaseClient import BaseClient
from TimeSwitchItem import TimeSwitchItem
from DatabaseManager import DatabaseManager
from ConfigManager import ConfigManager
import datetime

configManager = ConfigManager()


# I am the collector service.
class TimeSwitchService:
    namespace = "nox.lightsystem.opc.timeswitch"
    baseClient = None  # I am the opcClient of the opc.base service.
    TimeSwitchItems = {}
    server = None
    tree = {}
    scanThread = None
    scanEnable = False
    count = 0

    def __init__(self, server, servernamespace):
        self.server = server
        self.serverNamespace = servernamespace
        # Register Root node
        self.root = self.server.get_objects_node()
        self.baseClient = BaseClient("opc.tcp://vulpes.home:4911/nox/base")
        self.baseClient.connect()
        self.connectItems()

    # Connect to all groups.
    def connectItems(self):
        dm = DatabaseManager()
        # Load all active timeswitches.
        queryString        = """SELECT 
	`timeswitch`.`timeswitch_id`,
	`timeswitch`.`timeswitch_flags`,
	`timeswitch`.`timeswitch_value_on`,
	`timeswitch`.`timeswitch_value_off`,
	`timeswitch`.`timeswitch_monday`,
	`timeswitch`.`timeswitch_tuesday`,
	`timeswitch`.`timeswitch_wednesday`,
	`timeswitch`.`timeswitch_thursday`,
	`timeswitch`.`timeswitch_friday`,
	`timeswitch`.`timeswitch_saturday`,
	`timeswitch`.`timeswitch_sunday`,
	`autoItem`.`opc_item_address`,
	`writeItem`.`opc_item_address`
FROM
	`timeswitch`
JOIN `opc_item` AS autoItem ON (autoItem.opc_item_id = timeswitch.opc_item_auto)
JOIN `opc_item` AS writeItem ON (writeItem.opc_item_id = timeswitch.opc_item_write)
WHERE TRUE 
	AND `timeswitch`.`timeswitch_flags` &1=1
	AND `autoItem`.`opc_item_flags` &1=1
	AND `writeItem`.`opc_item_flags` &1=1"""
        queryData          = (1,2,3)
        timeswitchItemRows = dm.read(queryString, queryData)

        for timeswitchItemRow in timeswitchItemRows:
            timeSwitchItem = TimeSwitchItem(timeswitchItemRow, self.baseClient)

            # First, connect this stuff base to base.
            self.connect(timeSwitchItem)

            self.TimeSwitchItems[timeSwitchItem.id] = timeSwitchItem

    # I will connect the auto and the write item.
    def connect(self, timeSwitchItem: TimeSwitchItem):
        self.connectAuto(timeSwitchItem)
        self.connectWrite(timeSwitchItem)

    # I will connect the Auto item.
    def connectAuto(self, timeSwitchItem: TimeSwitchItem):
        timeSwitchItem.node_read = timeSwitchItem.baseClient.get_root_node().get_child(self.MakeNodePath(timeSwitchItem.auto_address))

    # I will connect the write item.
    def connectWrite(self, timeSwitchItem: TimeSwitchItem):
        timeSwitchItem.node_write = timeSwitchItem.baseClient.get_root_node().get_child(self.MakeNodePath(timeSwitchItem.write_address))

    # Return last Node name
    def GetEndNode(self, tree):
        return tree.split(".")[-1]

    # Generate Tree Branches and the end node.
    def MakeNode(self, tree):
        return self.GetBranchedNode(tree).add_variable(self.serverNamespace, self.GetEndNode(tree), 1)

    # Create new branches to the end node
    # JG.WHG.OG.LR.SOCKET01.OM.B_VALUE
    def GetBranchedNode(self, tree):
        branches = tree.split(".")  # ["JG", "WHG", "OG", "LR", "SOCKET01", "OM", "B_VALUE"]
        branchAddress = ""  # String to identify existing branches in tree.
        branchIndex = 1  # Index to count through all branches.
        parentNode = self.root  # Forces first branch to branch off the server root node.
        delim = ""
        del branches[-1]
        for branch in branches:
            branchAddress = branchAddress + delim + branch
            if not branchAddress in self.tree:
                parentNode = parentNode.add_object(self.serverNamespace, branch)
                self.tree[branchAddress] = parentNode
            else:
                parentNode = self.tree[branchAddress]
            delim = "."
            branchIndex = branchIndex + 1
        return parentNode

    # Start the server
    def start(self):
        self.server.start()

    # Stop the server
    def stop(self):
        self.server.stop()

    def MakeNodePath(self, address):
        branches = address.split(".")
        ret = []
        ret.append("0:Objects")
        for branch in branches:
            ret.append("2:" + branch)
        return ret

    # Generate Tree Branches and the end node.
    def MakeNode(self, tree):
        return self.GetBranchedNode(tree).add_variable(self.serverNamespace, self.GetEndNode(tree), 1)

    # I will connect the OPC Item and put the remoteNode node in it.
    def connectAddress(self, address):
        return self.MakeNode(address)

    # I will return the array of nodes to the given address.
    def makeNodePath(self, address):
        branches = address.split(".")
        ret = []
        ret.append("0:Objects")
        for branch in branches:
            ret.append("2:" + branch)
        return ret

    def increaseCounter(self):
        self.count = self.count + 1
        return self.getCounter()

    def getCounter(self):
        return self.count

    def getList(self):
        retVal = {}
        return retVal

    def getSetValue(self, timeSwitchItem:TimeSwitchItem):
        weekday = datetime.datetime.today().weekday()
        hour   = 4*datetime.datetime.now().hour + math.ceil(datetime.datetime.now().minute/15)
        return int(timeSwitchItem.tuesday[hour])



    def _scan(self):
        while self.scanEnable:
            for timeSwitchItemKey in self.TimeSwitchItems.keys():
                timeSwitchItem = self.TimeSwitchItems[timeSwitchItemKey]
                autoValue = int(timeSwitchItem.node_read.get_value())
                writeValue = int(timeSwitchItem.node_write.get_value())
                print("Checking TimeSwitchItem:") #└
                print("     ---       ├──────────ID: " + str(timeSwitchItem.id))
                print("     ---       ├────────AUTO: " + str(timeSwitchItem.auto_address))
                print("     ---       ├─────────VAL: " + str(autoValue))
                print("     ---       ├───────WRITE: " + str(timeSwitchItem.write_address))
                print("     ---       ├─────────VAL: " + str(writeValue))
                if autoValue != 1:
                    print("     ---       └─────────RES: Skipping: AUTO is OFF")
                    continue
                print("     ---       ├─────────RES: Continuing: AUTO is ON")

                valueNow =self.getSetValue(timeSwitchItem)
                print("     ---       ├──────────ON: " + str(timeSwitchItem.value_on))
                print("     ---       ├─────────OFF: " + str(timeSwitchItem.value_off))
                print("     ---       ├─────────SET: " + str(valueNow))

                if valueNow == 1:
                    if writeValue == 1:
                        print("     ---       └─────────END: already ON")
                    else:
                        timeSwitchItem.node_write.set_value(int(timeSwitchItem.value_on))
                        print("     ---       └─────────END: Set to ON")
                else:
                    if writeValue == 0:
                        print("     ---       └─────────END: already OFF")
                    else:
                        timeSwitchItem.node_write.set_value(int(timeSwitchItem.value_off))
                        print("     ---       └─────────END: Set to OFF")
            time.sleep(1)

    def scan_on(self):
        self.scanThread = threading.Thread(target=self._scan)
        self.scanEnable = True
        self.scanThread.start()

    def scan_off(self):
        self.scanEnable = False
        self.scanThread.join()
