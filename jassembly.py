import sys

_iota = 0

def iota():
    global _iota
    iota_saved = _iota
    _iota += 1
    return iota_saved

CONSTANT_CLASS = iota()
CONSTANT_UTF8 = iota()
CONSTANT_FIELDREF = iota()
CONSTANT_NAMEANDTYPE = iota()
CONSTANT_METHODREF = iota()
CONSTANT_STRING = iota()
CONSTANT_INTEGER = iota()
_iota = 0

ATTRIBUTE_CODE = iota()
ATTRIBUTE_STACKMAPTABLE = iota()
_iota = 0

ACCESS_STATIC = iota()
ACCESS_PUBLIC = iota()
_iota = 0

INSTRUCTION_RETURN = iota()
INSTRUCTION_GETSTATIC = iota()
INSTRUCTION_INVOKEVIRTUAL = iota()
INSTRUCTION_LDC = iota()
INSTRUCTION_INVOKESTATIC = iota()
INSTRUCTION_ARETURN = iota()
INSTRUCTION_IFEQ = iota()
INSTRUCTION_LABEL = iota()
_iota = 0

class ConstantPool:
    def __init__(self):
        self.data = bytearray()
        self.index = 1

def add_constant(pool, type, *args):
    index_saved = pool.index
    if type == CONSTANT_CLASS:
        pool.data += b'\x07'
        name_saved = len(pool.data)
        pool.data += b'\x00\x00'
        pool.index += 1

        name_index = add_constant(pool, CONSTANT_UTF8, args[0])
        pool.data[name_saved:name_saved + 2] = name_index.to_bytes(2, "big")
    elif type == CONSTANT_UTF8:
        pool.data += b'\x01'
        pool.data += len(args[0]).to_bytes(2, "big")
        pool.data += bytearray(args[0], "utf-8")
        pool.index += 1
    elif type == CONSTANT_FIELDREF:
        pool.data += b'\x09'
        class_saved = len(pool.data)
        pool.data += b'\x00\x00'
        field_saved = len(pool.data)
        pool.data += b'\x00\x00'
        pool.index += 1

        class_index = add_constant(pool, CONSTANT_CLASS, args[0])
        pool.data[class_saved:class_saved + 2] = class_index.to_bytes(2, "big")
        field_index = add_constant(pool, CONSTANT_NAMEANDTYPE, args[1], args[2])
        pool.data[field_saved:field_saved + 2] = field_index.to_bytes(2, "big")
    elif type == CONSTANT_METHODREF:
        pool.data += b'\x0A'
        class_saved = len(pool.data)
        pool.data += b'\x00\x00'
        field_saved = len(pool.data)
        pool.data += b'\x00\x00'
        pool.index += 1

        class_index = add_constant(pool, CONSTANT_CLASS, args[0])
        pool.data[class_saved:class_saved + 2] = class_index.to_bytes(2, "big")
        field_index = add_constant(pool, CONSTANT_NAMEANDTYPE, args[1], args[2])
        pool.data[field_saved:field_saved + 2] = field_index.to_bytes(2, "big")
    elif type == CONSTANT_NAMEANDTYPE:
        pool.data += b'\x0C'
        name_saved = len(pool.data)
        pool.data += b'\x00\x00'
        type_saved = len(pool.data)
        pool.data += b'\x00\x00'
        pool.index += 1

        name_index = add_constant(pool, CONSTANT_UTF8, args[0])
        pool.data[name_saved:name_saved + 2] = name_index.to_bytes(2, "big")
        type_index = add_constant(pool, CONSTANT_UTF8, args[1])
        pool.data[type_saved:type_saved + 2] = type_index.to_bytes(2, "big")
    elif type == CONSTANT_STRING:
        pool.data += b'\x08'
        value_saved = len(pool.data)
        pool.data += b'\x00\x00'
        pool.index += 1

        value_index = add_constant(pool, CONSTANT_UTF8, args[0])
        pool.data[value_saved:value_saved + 2] = value_index.to_bytes(2, "big")
    elif type == CONSTANT_INTEGER:
        pool.data += b'\x03'
        value_saved = len(pool.data)
        pool.data += args[0].to_bytes(4, "big")
        pool.index += 1
    else:
        assert False, "Unsupported constant type '%s'" % type
    return index_saved

class Methods:
    def __init__(self):
        self.data = bytearray()
        self.index = 1

def add_method(methods, constant_pool, name, descriptor, access_in, attributes):
    access = 0
    for access_part in access_in:
        if access_part == ACCESS_PUBLIC:
            access += 1
        elif access_part == ACCESS_STATIC:
            access += 8

    methods.data += access.to_bytes(2, "big")

    index = add_constant(constant_pool, CONSTANT_UTF8, name)
    methods.data += index.to_bytes(2, "big")

    index = add_constant(constant_pool, CONSTANT_UTF8, descriptor)
    methods.data += index.to_bytes(2, "big")

    methods.data += (attributes.index - 1).to_bytes(2, "big")
    methods.data += attributes.data

    methods.index += 1

class Attributes:
    def __init__(self):
        self.data = bytearray()
        self.index = 1

def add_attribute(attributes, constant_pool, type, *args):
    if type == ATTRIBUTE_CODE:
        index = add_constant(constant_pool, CONSTANT_UTF8, "Code")
        attributes.data += index.to_bytes(2, "big")

        code = args[0]
        attribute_length_location = len(attributes.data)
        attributes.data += b'\x00\x00\x00\x00'

        # Stack
        attributes.data += args[1].to_bytes(2, "big")
        # Locals
        attributes.data += args[2].to_bytes(2, "big")
        # Code Length
        attributes.data += len(code.data).to_bytes(4, "big")
        # Code
        attributes.data += code.data
        # Exceptions
        attributes.data += b'\x00\x00'

        # Attributes
        code_attributes = Attributes()
        add_attribute(code_attributes, constant_pool, ATTRIBUTE_STACKMAPTABLE, code.frames)

        attributes.data += (code_attributes.index - 1).to_bytes(2, "big")
        attributes.data += code_attributes.data

        attributes.data[attribute_length_location:attribute_length_location+4] = (len(attributes.data) - attribute_length_location - 4).to_bytes(4, "big")

        attributes.index += 1
    elif type == ATTRIBUTE_STACKMAPTABLE:
        index = add_constant(constant_pool, CONSTANT_UTF8, "StackMapTable")

        attributes.data += index.to_bytes(2, "big")
        total_size_location = len(attributes.data)
        attributes.data += b'\x00\x00\x00\x00'

        attributes.data += len(args[0]).to_bytes(2, "big")

        for stack_place in args[0]:
            attributes.data += b'\xfb'
            attributes.data += stack_place.to_bytes(2, "big")

        attributes.data[total_size_location:total_size_location+4] = (len(attributes.data) - total_size_location - 4).to_bytes(4, "big")

        attributes.index += 1
    else:
        assert False, "Unsupported attribute type '%s'" % type

class Code:
    def __init__(self):
        self.data = bytearray()
        self.label_references = {}
        self.labels = {}

        self.frames = []

def add_instruction(code, constant_pool, type, *args):
    if type == INSTRUCTION_RETURN:
        code.data += b'\xb1'
    elif type == INSTRUCTION_ARETURN:
        code.data += b'\xb0'
    elif type == INSTRUCTION_GETSTATIC:
        code.data += b'\xb2'
        index = add_constant(constant_pool, CONSTANT_FIELDREF, args[0], args[1], args[2])
        code.data += index.to_bytes(2, "big")
    elif type == INSTRUCTION_INVOKEVIRTUAL:
        code.data += b'\xb6'
        index = add_constant(constant_pool, CONSTANT_METHODREF, args[0], args[1], args[2])
        code.data += index.to_bytes(2, "big")
    elif type == INSTRUCTION_INVOKESTATIC:
        code.data += b'\xb8'
        index = add_constant(constant_pool, CONSTANT_METHODREF, args[0], args[1], args[2])
        code.data += index.to_bytes(2, "big")
    elif type == INSTRUCTION_LDC:
        code.data += b'\x13'

        if isinstance(args[0], str):
            index = add_constant(constant_pool, CONSTANT_STRING, args[0])
            code.data += index.to_bytes(2, "big")
        elif isinstance(args[0], int):
            index = add_constant(constant_pool, CONSTANT_INTEGER, args[0])
            code.data += index.to_bytes(2, "big")
        else:
            assert False, "Unsupported ldc operand '%s'" % args[0]
    elif type == INSTRUCTION_IFEQ:
        code.data += b'\x99'
        data_location = len(code.data)
        code.data += b'\x00\x00'

        if args[0] in code.labels:
            code.data[data_location:data_location + 2] = (code.labels[args[0]] - data_location + 1).to_bytes(2, "big")
        else:
            code.label_references[data_location] = args[0]
    elif type == INSTRUCTION_LABEL:
        id = args[0]
        location = len(code.data)

        for instruction, label in list(code.label_references.items()):
            if label == args[0]:
                code.data[instruction:instruction + 2] = (location - instruction + 1).to_bytes(2, "big")
                del code.label_references[instruction]
                break

        code.labels[args[0]] = location
    else:
        assert False, "Unsupported instruction type '%s'" % type

def get_parameters_returns(descriptor):
    params = []
    returns = []

    buffer = ""

    i = 1
    while not descriptor[i] == ')':
        if descriptor[i] == '[':
            i += 1
        else:
            if descriptor[i] == 'L':
                j = i

                while not descriptor[j] == ';':
                    buffer +=  descriptor[j]
                    j += 1

                i = j + 1
            else:
                buffer += descriptor[i]
                i += 1

            if buffer:
                params.append(buffer)
                buffer = ""


    if buffer:
        params.append(buffer)
        buffer = ""

    i += 1

    if not descriptor[i] == 'V':
        returns.append(descriptor[i:])

    return params, returns

def do_thing(contents, output_file):
    constant_pool = ConstantPool()
    this_class = add_constant(constant_pool, CONSTANT_CLASS, "Main")
    super_class = add_constant(constant_pool, CONSTANT_CLASS, "java/lang/Object")

    methods = Methods()

    current_class = None
    current_method = None
    current_code = None

    stack = 0
    max_stack = 0

    for line in contents.split('\n'):
        line = line.strip()
        line_split = line.split(' ')
        line_start = line_split[0]

        if line_start == "class":
            current_class = line_split[1]
        elif line_start == "method":
            current_method = line_split[1:]
            current_code = Code()
            stack = 0
            max_stack = 0
        elif line_start == "end":
            attributes = Attributes()
            parameters, _ = get_parameters_returns(current_method[2])
            add_attribute(attributes, constant_pool, ATTRIBUTE_CODE, current_code, max_stack, len(parameters))

            access_modifiers = []
            for access_modifier in current_method[0].split('/'):
                if access_modifier == "static":
                    access_modifiers.append(ACCESS_STATIC)
                elif access_modifier == "public":
                    access_modifiers.append(ACCESS_PUBLIC)
                else:
                    assert False, "Unknown access modifier '%s'" % access_modifier

            add_method(methods, constant_pool, current_method[1], current_method[2], access_modifiers, attributes)

            current_method = None
        elif line_start == "push":
            line_rest = " ".join(line_split[1:])

            def is_int(str):
                try:
                    int(str)
                    return True
                except:
                    return False

            if line_rest.startswith('"') and line_rest.endswith('"'):
                add_instruction(current_code, constant_pool, INSTRUCTION_LDC, line_rest[1:-1])
            elif is_int(line_rest):
                add_instruction(current_code, constant_pool, INSTRUCTION_LDC, int(line_rest))
            else:
                assert False, "Unhandled ldc instruction type"

            stack += 1
        elif line_start == "gets":
            add_instruction(current_code, constant_pool, INSTRUCTION_GETSTATIC, line_split[1], line_split[2], line_split[3])
            stack += 1
        elif line_start == "invv":
            add_instruction(current_code, constant_pool, INSTRUCTION_INVOKEVIRTUAL, line_split[1], line_split[2], line_split[3])

            parameters, returns = get_parameters_returns(line_split[3])
            stack += len(returns) - len(parameters) - 1
        elif line_start == "invs":
            add_instruction(current_code, constant_pool, INSTRUCTION_INVOKESTATIC, line_split[1], line_split[2], line_split[3])

            parameters, returns = get_parameters_returns(line_split[3])
            stack += len(returns) - len(parameters)
        elif line_start == "ret":
            _, returns = get_parameters_returns(current_method[2])

            if len(returns) == 0:
                add_instruction(current_code, constant_pool, INSTRUCTION_RETURN)
            elif returns[0][0] == 'L':
                add_instruction(current_code, constant_pool, INSTRUCTION_ARETURN)
            else:
                assert False, "Unhandled return type '%s'" % returns
        elif line_start == "ifeq":
            add_instruction(current_code, constant_pool, INSTRUCTION_IFEQ, line_split[1])

            stack -= 1
        elif line_start == "label":
            add_instruction(current_code, constant_pool, INSTRUCTION_LABEL, line_split[1])
            current_code.frames.append(len(current_code.data))
        elif not line:
            pass
        else:
            assert False, "Unhandled line '%s'" % line

        if stack > max_stack:
            max_stack = stack

    output = bytearray()
    # Magic
    output += b'\xCA\xFE\xBA\xBE'

    # Minor Version
    output += b'\x00\x00'

    # Major Version
    output += b'\x00\x40'

    # Constant Pool
    output += constant_pool.index.to_bytes(2, "big")
    output += constant_pool.data

    # Access Flags
    output += b'\x00\x00'

    # This Class
    output += this_class.to_bytes(2, "big")

    # Super Class
    output += super_class.to_bytes(2, "big")

    # Interfaces Count
    output += b'\x00\x00'

    # Fields Count
    output += b'\x00\x00'

    # Methods
    output += (methods.index - 1).to_bytes(2, "big")
    output += methods.data

    # Attributes Count
    output += b'\x00\x00'

    output_file = open(output_file, "wb")
    output_file.write(output)
    output_file.close()
    
args = sys.argv
if not len(args) == 3:
    print("Usage: jassembly [input] [output]")
    exit(1)

input = open(sys.argv[1], "r")
do_thing(input.read(), sys.argv[2])
