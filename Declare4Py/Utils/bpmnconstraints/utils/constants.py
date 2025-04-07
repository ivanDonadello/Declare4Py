"""Constants for the parser"""

ALLOWED_GATEWAYS = [
    "exclusive_databased_gateway",
    "parallelgateway",
    "inclusivegateway",
    "complexgateway",
    "eventbasedgateway",
    "exclusivegateway",
]

DISCARDED_START_GATEWAYS = [
    "exclusive_databased_gateway",
    "exclusivegateway"
]

ALLOWED_ACTIVITIES = [
    "task",
    "event",
    "collapsedsubprocess",
    "businessrole",
    "eventsubprocess",
    "collapsedeventsubprocess",
    "subprocess",
    "process",
    "intermediatemessageeventcatching",
    "intermediatetimerevent",
    "intermediateescalationevent",
    "intermediateconditionalevent",
    "intermediatelinkeventcatching",
    "intermediateerrorevent",
    "intermediatecancelevent",
    "intermediatecompensationeventcatching",
    "intermediatesignaleventcatching",
    "intermediatemultipleeventcatching",
    "intermediateparallelmultipleeventcatching",
    "intermediateevent",
    "intermediatemessageeventthrowing",
    "intermediateescalationeventthrowing",
    "intermediatelinkeventthrowing",
    "intermediatecompensationeventthrowing",
    "intermediatesignaleventthrowing",
    "intermediatemultipleeventthrowing",
]

ALLOWED_START_EVENTS = [
    "startevent",
    "startnoneevent",
    "startmessageevent",
    "starttimerevent",
    "starterrorevent",
    "startcompensationevent",
    "startparallelmultipleevent",
    "startescalationevent",
    "startconditionalevent",
    "startsignalevent",
    "startmultipleevent",
]

ALLOWED_END_EVENTS = [
    "end",
    "endevent",
    "endnoneevent",
    "endescalationevent",
    "endmessageevent",
    "enderrorevent",
    "endcancelevent",
    "endcompensationevent",
    "endsignalevent",
    "endmultipleevent",
    "endterminateevent",
]

ALLOWED_SWIMLANES = [
    "pool",
    "lane",
]

ALLOWED_CONNECTING_OBJECTS = ["sequenceflow"]

GATEWAY_MAPPING = {
    ALLOWED_GATEWAYS[0]: "XOR",
    ALLOWED_GATEWAYS[1]: "AND",
    ALLOWED_GATEWAYS[2]: "OR",
    ALLOWED_GATEWAYS[3]: "COMPLEX",
    ALLOWED_GATEWAYS[4]: "EVENT_BASED",
}

END_EVENT_MAPPING = {
    "endnoneevent": "endnoneevent",
    "endescalationevent": "endescalationevent",
    "endmessageevent": "endmessageevent",
    "enderrorevent": "enderrorevent",
    "endcancelevent": "endcancelevent",
    "endcompensationevent": "endcompensationevent",
    "endsignalevent": "endsignalevent",
    "endmultipleevent": "endmultipleevent",
    "endterminateevent": "endterminateevent",
}

ACTIVITY_MAPPING = {
    "task": "task",
    "event": "event",
    "collapsedsubprocess": "subprocess",
    "eventsubprocess": "subprocess",
    "collapsedeventsubprocess": "subprocess",
    "subprocess": "subprocess",
    "intermediatemessageeventcatching": "catchactivity",
    "intermediatetimerevent": "intermediateevent",
    "intermediateescalationevent": "intermediateevent",
    "intermediateconditionalevent": "intermediateevent",
    "intermediatelinkeventcatching": "catchactivity",
    "intermediateerrorevent": "intermediateevent",
    "intermediatecancelevent": "intermediateevent",
    "intermediatecompensationeventcatching": "catchactivity",
    "intermediatesignaleventcatching": "catchactivity",
    "intermediatemultipleeventcatching": "catchactivity",
    "intermediateparallelmultipleeventcatching": "catchactivity",
    "intermediateevent": "intermediateevent",
    "intermediatemessageeventthrowing": "throwactivity",
    "intermediateescalationeventthrowing": "throwactivity",
    "intermediatelinkeventthrowing": "throwactivity",
    "intermediatecompensationeventthrowing": "throwactivity",
    "intermediatesignaleventthrowing": "throwactivity",
    "intermediatemultipleeventthrowing": "throwactivity",
}

GATEWAY_NAMES = [
    "AND",
    "XOR",
    "OR",
    "COMPLEX",
    "EVENT_BASED",
]

DISCARDED_CONSTRAINTS = [
    "Exactly1",
    "Responded Existence",
    "Absence2",
    "Existence1",
    "Existence2",
    "Exactly2",
]

DISCARDED_START_EVENT_NAMES = ["start", "Start", "START", "AND", "XOR", "OR"]

DISCARDED_END_EVENT_NAMES = [
    "end",
    "End",
    "END",
    "AND",
    "XOR",
    "OR",
]

XOR_GATEWAY = ["exclusive_databased_gateway", "exclusivegateway"]
AND_GATEWAY = "parallelgateway"
OR_GATEWAY = "inclusivegateway"

VALID_NAME_LENGTH = 5

CHILD_SHAPES = "childShapes"
OUTGOING = "outgoing"
ELEMENT_ID = "resourceId"
STENCIL = "stencil"
ID = "id"
PROPERTIES = "properties"
NAME = "name"

DECLARE_CONSTRAINT_REGEX_PATTERN = r"(\w+(?:-\w+)?(?: \w+)?)(?: \w+)?\[(.*?)\]"

DECLARE_GATEWAYS = ["Co-Existence", "Choice", "Exclusive Choice"]

DEFAULT_DIRECTION = "LR"
SEQUENCE_FLOW = "-->"
# END_EVENT_STYLING_DEF = "classDef EndEvent fill:stroke:#000,stroke-width:4px"
# END_EVENT_STYLE = ":::EndEvent"
