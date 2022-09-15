import llvmlite.ir as ir
import llvmlite.binding as llvm
import enum

class inst(enum.Enum):
    INCREMENT = '+'
    DECREMENT = '-'
    INCREMENT_POINTER = '>'
    DECREMENT_POINTER = '<'
    OUTPUT = '.'
    INPUT = ','
    LOOP_START = '['
    LOOP_END = ']'
    END = '\0'

i8 = ir.IntType(8)
i32 = ir.IntType(32)
voidptr_type = i8.as_pointer()

def get_pointer_to_array_index(builder: ir.IRBuilder, array: ir.PointerType, index: ir.GlobalVariable):
    return builder.gep(array, [builder.load(index)])

def i_add(builder: ir.IRBuilder, location: ir.PointerType, num: ir.IntType):
    value = builder.load(location)
    increment = builder.add(value, num)
    builder.store(increment, location)

def run(program : str):

    mod = ir.Module()
    
    index_var = ir.GlobalVariable(mod, ir.IntType(32), name='index')
    index_var.initializer = ir.Constant(ir.IntType(32), 0)

    tape_type = ir.ArrayType(ir.IntType(8), 30_000)
    tape: ir.GlobalVariable = ir.GlobalVariable(mod, tape_type, name="tape")
    tape.initializer = ir.Constant(tape_type, [0] * 30_000)

    # Declare printf
    printf_type = ir.FunctionType(ir.IntType(32), [voidptr_type], var_arg=True)
    printf = ir.Function(mod, printf_type, name="printf")

    # Declare scanf
    scanf_type = ir.FunctionType(ir.IntType(32), [voidptr_type, voidptr_type], var_arg=True)
    scanf = ir.Function(mod, scanf_type, name="scanf")

    # Declare putchar
    putchar_type = ir.FunctionType(ir.IntType(32), [i8], var_arg=True)
    putchar = ir.Function(mod, putchar_type, name="putchar")

    # Create an entry function
    entry_type = ir.FunctionType(ir.VoidType(), [])
    entry = ir.Function(mod, entry_type, name="main")
    entry_block = entry.append_basic_block(name="entry")

    builder = ir.IRBuilder(entry_block)
    tape_ptr = builder.bitcast(tape, voidptr_type)

    loop_start = None
    loop_end = None
    branch = None

    zero = ir.Constant(i8, 0)

    i = 0
    while i < len(program):
        instruction = program[i]
        if instruction == inst.INCREMENT.value:
            pointer_to_index = get_pointer_to_array_index(builder, tape_ptr, index_var)
            i_add(builder, pointer_to_index, i8(1))

        elif instruction == inst.DECREMENT.value:
            pointer_to_index = get_pointer_to_array_index(builder, tape_ptr, index_var)
            i_add(builder, pointer_to_index, i8(-1))

        elif instruction == inst.INCREMENT_POINTER.value:
            i_add(builder, index_var, i32(1))

        elif instruction == inst.DECREMENT_POINTER.value:
            i_add(builder, index_var, i32(-1))

        elif instruction == inst.OUTPUT.value:

            pointer_to_index = get_pointer_to_array_index(builder, tape_ptr, index_var)
            value = builder.load(pointer_to_index)
            builder.call(putchar, [value])

        elif instruction == inst.INPUT.value:

            retval = builder.call(scanf, [tape_ptr])
            load_to = get_pointer_to_array_index(builder, tape_ptr, index_var)
            builder.store(retval, load_to)

        elif instruction == inst.LOOP_START.value:

            loop_start = builder.append_basic_block(name="loop_start")
            loop_end = builder.append_basic_block(name="loop_end")

            pointer_to_index = get_pointer_to_array_index(builder, tape_ptr, index_var)
            value = builder.load(pointer_to_index)
            builder.cbranch(builder.icmp_signed('==', value, zero), loop_end, loop_start)
            builder.position_at_start(loop_start)

        elif instruction == inst.LOOP_END.value:

            pointer_to_index = get_pointer_to_array_index(builder, tape_ptr, index_var)
            value = builder.load(pointer_to_index)
            builder.cbranch(builder.icmp_signed('!=', value, zero), loop_start, loop_end)
            builder.position_at_end(loop_end)

        elif instruction == inst.END.value:
            break

        i += 1

    builder.ret_void()

    il = llvm.parse_assembly(str(mod))
    return str(il)