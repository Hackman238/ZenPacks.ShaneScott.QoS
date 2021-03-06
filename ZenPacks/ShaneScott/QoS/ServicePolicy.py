import copy
import logging
log = logging.getLogger("zen.ZenQoS")

import locale

from Globals import DTMLFile
from Globals import InitializeClass
from Products.ZenModel.OSComponent import OSComponent
from Products.ZenModel.ManagedEntity import ManagedEntity
from Products.ZenUtils.Utils import convToUnits, prepId
from Products.ZenRelations.RelSchema import *
from Products.ZenModel.ZenossSecurity import *
from AccessControl import ClassSecurityInfo

class ServicePolicy(OSComponent): 
    """QoS ServicePolicy Object"""

    ZENPACKID = 'ZenPacks.ShaneScott.QoS'

    portal_type = meta_type = 'ServicePolicy'

    instance = ''
    parentInterface = ''
    direction = ''
    allocName = ''

    _properties = OSComponent._properties + (
        {'id':'instance', 'type':'string', 'mode':'w'},
        {'id':'allocName', 'type':'string', 'mode':'w'},
        {'id':'parentInterface', 'type':'string', 'mode':'w'},
        {'id':'direction', 'type':'string', 'mode':'w'},
        )

    _relations = OSComponent._relations + (
        ("os", ToOne(ToManyCont, "Products.ZenModel.OperatingSystem", "servicepolicies")),
        )

    ServicePolicyTypeMap = ('Parent','Child')

    factory_type_information = (
        {
            'id'         : 'ServicePolicy',
            'meta_type'      : 'ServicePolicy',
            'description'    : """QoS ServicePolicy Object""",
            'icon'       : 'Device_icon.gif',
            'product'    : 'ServicePolicy',
            'factory'    : 'manage_addServicePolicy',
            'immediate_view' : 'ServicePolicyPerformance',
	    'actions'    : '',
        },
    )


    security = ClassSecurityInfo()

    def __init__(self, id, title = None):
        """
        Init OSComponent
        """
        OSComponent.__init__(self, id, title)
        self.buildRelations()

    def deviceId(self):
        """
        The device id, for indexing purposes.
        """
        d = self.device()
        if d: return d.getPrimaryId()
        else: return None

    def getId(self):
        return self.id

    def getInstance(self):
        return self.instance

    def getAllocName(self):
        return self.allocName

    def getParentInterface(self):
        return self.parentInterface

    def getDirection(self):
        return self.direction

    def viewName(self):
        return self.id
    name = primarySortKey = viewName


    def managedDeviceLink(self):
        from Products.ZenModel.ZenModelRM import ZenModelRM
        d = self.getDmdRoot("Devices").findDevice(self.id)
        if d:
            return ZenModelRM.urlLink(d, 'link')
        return None

    def manage_editProperties(self, REQUEST):
        """
        Override from propertiyManager so we can trap errors
        """
        return ConfmonPropManager.manage_editProperties(self, REQUEST)

    def getRRDTemplateName(self):
        """
        Return the interface type as the target type name.
        """
        return self.prepId(self.id or "Unknown")

    def getRRDTemplates(self):
        """
        Return a list containing the appropriate RRDTemplate for this Service Policy.
        """
        templateName = self.getRRDTemplateName()
        default = self.getRRDTemplateByName(templateName)

        if not default:
            default = self.getRRDTemplateByName("Generic_ServicePolicy")

        if default:
            return [default]
        return []

InitializeClass(ServicePolicy)
