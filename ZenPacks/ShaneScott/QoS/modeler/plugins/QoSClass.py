import Globals
from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin
from Products.DataCollector.plugins.DataMaps import ObjectMap, MultiArgs
from ZenPacks.ShaneScott.QoS.QoS import QoSmodel, AutoVivification
from struct import *
import sys
import string
import subprocess

class QoSClass(PythonPlugin):

    ZENPACKID = 'ZenPacks.ShaneScott.QoS'

    transport = "python"
    maptype = 'QoSMap'
    relname = 'classes'
    compname = "os"
    modname = 'ZenPacks.ShaneScott.QoS.ClassMap'
    deviceProperties = PythonPlugin.deviceProperties + ('zSnmpCommunity', 'zSnmpPort')

    def collect(self, device, log):
        oids = {}
        modeler = QoSmodel()

        oids['cbQosServicePolicyEntry'] = (1,3,6,1,4,1,9,9,166,1,1,1,1)
        oids['ifDescr'] = (1,3,6,1,2,1,2,2,1,2)
        oids['cbQosObjectsEntry'] = (1,3,6,1,4,1,9,9,166,1,5,1,1)
        oids['cbQosPolicyMapCfgEntry'] = (1,3,6,1,4,1,9,9,166,1,6,1,1)
        oids['cbQosCMCfgEntry'] = (1,3,6,1,4,1,9,9,166,1,7,1,1)
        oids['cbQosMatchStmtCfgEntry'] = (1,3,6,1,4,1,9,9,166,1,8,1,1)
        oids['cbQosQueueingCfgEntry'] = (1,3,6,1,4,1,9,9,166,1,9,1,1)
        oids['cbQosPoliceCfgEntry'] = (1,3,6,1,4,1,9,9,166,1,12,1,1)

        policy_traffic_direction_names = {'1': 'INPUT', '2': 'OUTPUT'}
        queueing_bandwidth_units = {'1': 'kbps', '2': '%', '3': '% remaining', '4': 'ratioRemaining'}
        police_rate_types = {'1': 'kbps', '2': '%', '3': 'cps'}

        port =  getattr(device, 'zSnmpPort', 161)
        hostname = device.manageIp
        community = getattr(device, 'zSnmpCommunity', 'public')

        results = ''

        cbQosServicePolicyEntries = modeler.get_table(hostname, port, community, oids['cbQosServicePolicyEntry'])
        cbQosServicePolicyTable = modeler.get_cbQosServicePolicyTable(cbQosServicePolicyEntries)
        ifEntries = modeler.get_table(hostname, port, community, oids['ifDescr'])
        ifEntriesTable = modeler.get_ifEntriesTable(ifEntries)
        cbQosObjectsEntries = modeler.get_table(hostname, port, community, oids['cbQosObjectsEntry'])
        cbQosObjectsTable = modeler.get_cbQosObjectTable(cbQosObjectsEntries)
        cbQosPolicyMapCfgEntries = modeler.get_table(hostname, port, community, oids['cbQosPolicyMapCfgEntry'])
        cbQosPolicyMapCfgTable = modeler.get_cbQosPolicyMapTable(cbQosPolicyMapCfgEntries)        
        cbQosCMCfgEntries = modeler.get_table(hostname, port, community, oids['cbQosCMCfgEntry'])
        cbQosCMCfgTable = modeler.get_cbQosCMCfgTable(cbQosCMCfgEntries)
        cbQosQueueingCfgEntries = modeler.get_table(hostname, port, community, oids['cbQosQueueingCfgEntry'])
        cbQosQueueingCfgTable = modeler.get_cbQosQueueingCfgTable(cbQosQueueingCfgEntries)
        cbQosPoliceCfgEntries = modeler.get_table(hostname, port, community, oids['cbQosPoliceCfgEntry'])
        cbQosPoliceCfgTable = modeler.get_cbQosPoliceCfgTable(cbQosPoliceCfgEntries)

        interfaces = {}
        for cbQosPolicyIndex in cbQosServicePolicyTable.keys():
            interface_idx = cbQosServicePolicyTable[cbQosPolicyIndex]['cbQosIfIndex']
            try:
                interface_name = ifEntriesTable[interface_idx]
                interfaces[interface_idx] = interface_name
            except:
                interfaces[interface_idx] = "controlPlane"

        for interface_idx in interfaces:
            interface_name = interfaces[interface_idx]
            for cbQosPolicyIndex in cbQosServicePolicyTable.keys():
                if cbQosServicePolicyTable[cbQosPolicyIndex]['cbQosIfIndex'] == interface_idx:
                    policy_map_name_1 = cbQosPolicyMapCfgTable[cbQosObjectsTable[cbQosPolicyIndex]['QosObjectsEntry'][cbQosPolicyIndex]['cbQosConfigIndex']]['cbQosPolicyMapName']
                    policy_traffic_direction = cbQosServicePolicyTable[cbQosPolicyIndex]['cbQosPolicyDirection']
                    policy_traffic_direction_name = policy_traffic_direction_names[policy_traffic_direction]

                    for cbQosObjectsIndex_1 in cbQosObjectsTable[cbQosPolicyIndex]['QosObjectsEntry']:
                        if cbQosObjectsTable[cbQosPolicyIndex]['QosObjectsEntry'][cbQosObjectsIndex_1]['cbQosObjectsType'] == '2' and cbQosObjectsTable[cbQosPolicyIndex]['QosObjectsEntry'][cbQosObjectsIndex_1]['cbQosParentObjectsIndex'] == cbQosPolicyIndex:
                            cbQosCMName = cbQosCMCfgTable[cbQosObjectsTable[cbQosPolicyIndex]['QosObjectsEntry'][cbQosObjectsIndex_1]['cbQosConfigIndex']]['cbQosCMName']
                            (bandwidth, units) = modeler.get_bandwidth(cbQosPolicyIndex, cbQosObjectsIndex_1, cbQosObjectsTable, cbQosQueueingCfgTable)
                            results = results + "\nCM1:%s:%s:%s:%s:%s:%s:%s" % (cbQosCMName, bandwidth, queueing_bandwidth_units[str(units)], policy_map_name_1, interface_name, policy_traffic_direction_name, str(cbQosPolicyIndex) + '.' + str(cbQosObjectsIndex_1))

                            for cbQosObjectsIndex_2 in cbQosObjectsTable[cbQosPolicyIndex]['QosObjectsEntry']:
                                if cbQosObjectsTable[cbQosPolicyIndex]['QosObjectsEntry'][cbQosObjectsIndex_2]['cbQosObjectsType'] == '1' \
                                        and cbQosObjectsTable[cbQosPolicyIndex]['QosObjectsEntry'][cbQosObjectsIndex_2]['cbQosParentObjectsIndex'] == cbQosObjectsIndex_1:
                                    policy_map_name_2 = cbQosPolicyMapCfgTable[cbQosObjectsTable[cbQosPolicyIndex]['QosObjectsEntry'][cbQosObjectsIndex_2]['cbQosConfigIndex']]['cbQosPolicyMapName']

                                    for cbQosObjectsIndex_3 in cbQosObjectsTable[cbQosPolicyIndex]['QosObjectsEntry']:
                                        if cbQosObjectsTable[cbQosPolicyIndex]['QosObjectsEntry'][cbQosObjectsIndex_3]['cbQosObjectsType'] == '2' and cbQosObjectsTable[cbQosPolicyIndex]['QosObjectsEntry'][cbQosObjectsIndex_3]['cbQosParentObjectsIndex'] == cbQosObjectsIndex_2:
                                            cbQosCMName = cbQosCMCfgTable[cbQosObjectsTable[cbQosPolicyIndex]['QosObjectsEntry'][cbQosObjectsIndex_3]['cbQosConfigIndex']]['cbQosCMName']
                                            (bandwidth, units) = modeler.get_bandwidth(cbQosPolicyIndex, cbQosObjectsIndex_3, cbQosObjectsTable, cbQosQueueingCfgTable)
                                            results = results + "\nCM3:%s:%s:%s:%s:%s:%s:%s" % (cbQosCMName, bandwidth, queueing_bandwidth_units[str(units)], policy_map_name_2, interface_name, policy_traffic_direction_name, str(cbQosPolicyIndex) + '.' + str(cbQosObjectsIndex_3))

        return results

    def process(self, device, results, log):
        """
        collect QoS class information from host device
        """
        log.info('processing %s for device %s', self.name(), device.id)
        rm = self.relMap()
        entries = str(results)
        for line in entries.split('\n'):
            if ':' in line:
                entry = line.split(':')
                if entry[0] == 'CM1' or  entry[0] == 'CM3':
                    log.info('val %s:%s Bandwidth:%s %s Parent:%s Interface:%s Direction:%s index:%s', entry[0], entry[1], entry[2], entry[3], entry[4], entry[5], entry[6], entry[7])
                    om = self.objectMap()
                    omId = entry[1] + '^' + entry[4] + '^' + entry[5] + '^' + entry[6]
                    omId = omId.replace('\'','')
                    omId = omId.replace('/','_')
                    omId = omId.replace(' ','_')
                    omId = omId.replace('-','_')
                    omId = omId.replace('^','-')
                    om.id = self.prepId(omId)
                    instance = entry[1] + '-' + entry[5]
                    instance = instance.replace('\'','')
                    om.instance = instance
                    allocName = entry[1]
                    allocName = allocName.replace('\'','')
                    om.allocName = allocName
                    interface = entry[5]
                    interface = interface.replace('\'','')
                    om.parentInterface = interface
                    om.direction = entry[6]
                    om.allocBandwidth = entry[2]
                    om.allocType = entry[3]
                    parentServicePolicy = entry[4] 
                    parentServicePolicy = parentServicePolicy.replace('\'','')
                    om.parentServicePolicy = parentServicePolicy
                    om.snmpindex = str(entry[7])
                    rm.append(om)

        log.debug('rm %s', rm)
        return [rm]
