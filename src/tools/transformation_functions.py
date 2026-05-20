from haystack.tools import Tool,Toolset
from typing import Any,Dict,Optional,List,Callable
import itertools
from config.log_config import LoggerConfig
import json

logger = LoggerConfig().get_logger()

def _split_str(field:Any,args:Dict,context:Optional[Dict] = None):
    if field is None:
        return args.get('default',"")
    parts = str(field).split(args.get('delimiter',''))
    if args.get('index',0) < len(parts):
        return parts[args.get('index',0)]
    return args.get('default',"")

def _replace_str(field:Any,args:Dict,context:Optional[Dict] = None):
    if field is None:
        return args.get('default',"")
    if type(field) == list:
        return [f.replace(args.get('str_to_replace',''),args.get('replace_with_str','')) for f in field]
    return str(field).replace(args.get('str_to_replace',''),args.get('replace_with_str',''))

def _strip_str(field:Any,args:Dict,context:Optional[Dict] = None):
    if field is None:
        return args.get('default',"")
    if type(field) == list:
        return [f.strip() for f in field]
    return str(field).strip()

def _map_lambda_function(field:Any,args:Dict,context:Optional[Dict] = None):
    if field is None:
        return args.get('default',[])
    if 'filter_condition' in args:
        if args.get('filter_condition').get('filter_type','') == 'direct':
            return list(map(lambda item: item[args.get('map_column','')],filter(lambda item:item[args.get('filter_condition').get('filter_column','')] == args.get('filter_condition').get('filter_value',''),field)))
        if args.get('filter_condition').get('filter_type','') == 'not_equal':
            return list(map(lambda item: item[args.get('map_column','')],filter(lambda item:item[args.get('filter_condition').get('filter_column','')] != args.get('filter_condition').get('filter_value',''),field)))
        if args.get('filter_condition').get('filter_type','') == 'in':
            return list(map(lambda item: item[args.get('map_column','')],filter(lambda item:args.get('filter_condition').get('filter_value','') in item[args.get('filter_condition').get('filter_column','')],field)))
        if args.get('filter_condition').get('filter_type','') == 'not in':
            return list(map(lambda item: item[args.get('map_column','')],filter(lambda item:args.get('filter_condition').get('filter_value','') not in item[args.get('filter_condition').get('filter_column','')],field)))
        if args.get('filter_condition').get('filter_type','') == 'find':
            return list(map(lambda item: item[args.get('map_column','')],filter(lambda item:item[args.get('filter_condition').get('filter_column','').find(args.get('filter_condition').get('filter_value','')) != -1],field)))
        if args.get('filter_condition').get('filter_type','') == 'not find':
            return list(map(lambda item: item[args.get('map_column','')],filter(lambda item:item[args.get('filter_condition').get('filter_column','').find(args.get('filter_condition').get('filter_value','')) == -1],field)))
    return field


def _map_lambda_with_for_loop(field:Any,args:Dict,context:Optional[Dict] = None):
    if field is None:
        return args.get('default',[])
    if 'filter_condition' in args:
        return list(itertools.chain.from_iterable(map(lambda item: [f for f in item[args.get('map_column','')] ],filter(lambda item:item[args.get('filter_condition').get('filter_column','')] == args.get('filter_condition').get('filter_value',''),field))))
    return field


def _split_list_str(field:Any,args:Dict,context:Optional[Dict] = None):
    if field is None:
        return args.get('default',[])
    return [f.split(args.get('delimiter',''))[args.get('index',0)] for f in field]

def _join_list_to_str(field:Any,args:Dict,context:Optional[Dict] = None):
    if field is None:
        return args.get('default',[])
    return args.get('delimiter','').join(str(item) for item in field)   

def _conditional_extract(field:Any,args:Dict,context:Optional[Dict] = None):
    #logger.info(f"Field:{field}")
    #logger.info(f"Context:{context}")
    if args.get("context_type_field") is not None:
        if context is None or args.get('context_type_field') not in context:
            logger.error(f"Context type field {args.get('context_type_field')} not found in context")
            return args.get('default','')
        elif context[args.get('context_type_field','')] == args.get('context_type_value',''):
            if field is None:
                return args.get('default','')
            if args.get("conditional_field") is not None:
                for key,value in args.get("cases",{}).items():
                    if args.get("conditional_field") not in field:
                        logger.error(f"Conditional field {args.get('conditional_field')} not found in field")
                        return args.get('default','')
                    if field[args.get("conditional_field")] == key:
                        if value is None:
                            return args.get('default','')
                        else:
                            return field[value]                       
    return args.get('default','')   

def _extract_field_value(field:Any,args:Dict,context:Optional[Dict] = None):
    #logger.info(f"Field:{field}")
    #logger.info(f"Context:{context}")
    if args.get('context_type_field') is not None:
        if context is None or args.get('context_type_field') not in context:
            logger.error(f"Context type field {args.get('context_type_field')} not found in context")
            return args.get('default','')
        else:
            if context[args.get('context_type_field','')] == args.get('context_type_value',''):
                if field is None or args.get('field_to_extract','') not in field:
                    logger.error(f"Field {args.get('field_to_extract','')} not found in field")
                    return args.get('default','')
                return field[args.get('field_to_extract','')]
            else:
                return args.get('default','')
    return args.get('default','')
           
def _extract_from_list_dict(field:Any,args:Dict,context:Optional[Dict] = None):
    #logger.info(f"Field:{field}")
    #logger.info(f"Context:{context}")
    if field is None:
        return args.get('default',[])
    if isinstance(field,list) and all(isinstance(item,dict) for item in field):
        return [item[args.get('field_to_extract','')] for item in field if args.get('field_to_extract','') in item]
    return args.get('default',[])


def _convert_to_json(field:Any,args:Dict,context:Optional[Dict] = None):
    #logger.info(f"Field: {field}")
    try:
        if field is None:
            return json.dumps(args.get('default',[]))
        return json.dumps(field)
    except Exception as e:
        logger.error(f"Error converting field to JSON: {e}",exc_info=True)
        return args.get('default',[])   


def _split_join(field:Any,args:Dict,context:Optional[Dict]=None):
    part = []
    try:
        parts = str(field).split(args["delimiter"])
        if type(args["index"]) == int:
            if args["index"]<len(parts):
                part = parts[args["index"]]
            else:
                part = args.get('default',[])
        elif type(args["index"])==list:
            part = [parts[i] for i in args["index"] if i<len(parts)]
        if field is None:
            return args.get('default',[])
        return args['join_with'].join(part)
    except Exception as e:
        logger.error(f"Error joining the split string for given indexes: {e}", exc_info=True)
        return args.get('default',[])

split_str = Tool(function=_split_str,name="split_str",description="Split a string by a delimiter and return a specific part",
parameters={
    "type":"object",
    "properties":{
        "field":{"type": ["string", "array", "object", "number", "boolean"]},
        "args":{"type":"object",
        "properties":{
            "delimiter":{"type":"string"},
            "index":{"type":"integer"},
            "default":{"type":"string"}
        },
        "required":["delimiter","index"]}
    },
    "required":["field","args"]
})
replace_str = Tool(function=_replace_str,name="replace_str",description="Replace a string with another string",parameters={
    "type":"object",
    "properties":{
        "field":{"type": ["string", "array", "object", "number", "boolean"]},
        "args":{"type":"object",
        "properties":{
            "str_to_replace":{"type":"string"},
            "replace_with_str":{"type":"string"},
            "default":{"type":"string"}
        },
        "required":["str_to_replace","replace_with_str"]}
    },
    "required":["field","args"]
})
strip_str = Tool(function=_strip_str,name="strip_str",description="Strip a string of whitespace",parameters={
    "type":"object",
    "properties":{
        "field":{"type": ["string", "array", "object", "number", "boolean"]},
        "args":{"type":"object",
        "properties":{
            "default":{"type":"string"}
        },
        "required":[]}
    },
    "required":["field","args"]
})
map_lambda_function = Tool(function=_map_lambda_function,name="map",description="Map a lambda function to a list",parameters={
    "type":"object",
    "properties":{
        "field":{"type": ["string", "array", "object", "number", "boolean"]},
        "args":{"type":"object",
        "properties":{
            "map_column":{"type":"string"},
            "filter_condition":{"type":"object",
            "properties":{"filter_column":{"type":"string"},
            "filter_value":{"type":"string"}},
            "required":["filter_column","filter_value"]}
        },
        "required":["map_column","filter_condition"]}
    },
    "required":["field","args"]
})
map_lambda_with_for_loop = Tool(function=_map_lambda_with_for_loop,name="map_with_for_loop",description="Map a lambda function to a list with a for loop",parameters={
    "type":"object",
    "properties":{
        "field":{"type": ["string", "array", "object", "number", "boolean"]},
        "args":{"type":"object",
        "properties":{
            "map_column":{"type":"string"},
            "filter_condition":{"type":"object",
            "properties":{"filter_column":{"type":"string"},
            "filter_value":{"type":"string"}},
            "required":["filter_column","filter_value"]}
        },
        "required":["map_column","filter_condition"]}
    },
    "required":["field","args"]
})
split_list_str = Tool(function=_split_list_str,name="split_list_str",description="Split a list of strings by a delimiter and return a specific part of each string",parameters={
    "type":"object",
    "properties":{
        "field":{"type": ["string", "array", "object", "number", "boolean"]},
        "args":{"type":"object",
        "properties":{
            "delimiter":{"type":"string"},
            "index":{"type":"integer"},
            "default":{"type":"string"}
        },
        "required":["delimiter","index"]}
    },
    "required":["field","args"]
})
join_list_to_str = Tool(function=_join_list_to_str,name="join_list_to_str",description="Join a list of strings to a single string",parameters={
    "type":"object",
    "properties":{
        "field":{"type": ["string", "array", "object", "number", "boolean"]},
        "args":{"type":"object",
        "properties":{
            "delimiter":{"type":"string"},
            "default":{"type":"string"}
        },
        "required":["delimiter"]}
    },
    "required":["field","args"]
})

conditional_extract = Tool(function=_conditional_extract,name="conditional_extract",description="Extract a value based on a condition",parameters={
    "type":"object",
    "properties":{
        "field":{"type": ["string", "array", "object", "number", "boolean"]},
        "args":{"type":"object",
        "properties":{
            "conditional_field":{"type":"string"},
            "cases":{"type":"object",
            "properties":{"case1":{"type":"string"},
            "case2":{"type":"string"}},
            "required":["case1","case2"]}
        },
        "required":["conditional_field","cases"]}
    },
    "required":["field","args"]
})

extract_from_list_dict = Tool(function=_extract_from_list_dict,name="extract_from_list_dict",description="Extract a value from a list of dictionaries",parameters={
    "type":"object",
    "properties":{
        "field":{"type": ["string", "array", "object", "number", "boolean"]},
        "args":{"type":"object",
        "properties":{
            "field_to_extract":{"type":"string"}
        },
        "required":["field_to_extract"]}
    },
    "required":["field","args"]
})

extract_field_value = Tool(function=_extract_field_value,name="extract_field_value",description="Extract a value from a field",parameters={
    "type":"object",
    "properties":{
        "field":{"type": ["string", "array", "object", "number", "boolean"]},
        "args":{"type":"object",
        "properties":{
            "field_to_extract":{"type":"string"}
        },
        "required":["field_to_extract"]}
    },
    "required":["field","args"]
})

convert_to_json = Tool(function=_convert_to_json,name="convert_to_json",description="Convert a field to JSON",parameters={
    "type":"object",
    "properties":{
        "field":{"type": ["string", "array", "object", "number", "boolean"]},
        "args":{"type":"object",
        "properties":{
            "default":{"type":"string"}
        },
        "required":[]}
    },
    "required":["field"]
})

split_join = Tool(function =_split_join,name="split_join",description="split the string and join the string for the specified indexes",parameters={
    "type":"object",
    "properties":{
        "field":{"type": ["string", "array", "object", "number", "boolean"]},
        "args":{"type":"object",
        "properties":{
            "delimiter":{"type":"string"},
            "index":{"type":["array","number"]},
            "join_with":{"type":"string"}
        },
        "required":["delimiter","join_with","index"]}
    },
    "required":["field","args"]
})

transformation_toolset = Toolset([split_str,replace_str,strip_str,map_lambda_function,map_lambda_with_for_loop,split_list_str,join_list_to_str,conditional_extract,extract_from_list_dict,extract_field_value,convert_to_json,split_join])

TRANSFORM_REGISTRY: Dict[str,Callable]={tool.name: tool.function for tool in transformation_toolset}
