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

def brainfuck(program : str):
    instructions = []
    i = 0
    while i < len(program):
        if program[i] == inst.INCREMENT.value:
            instructions.append(inst.INCREMENT)
        elif program[i] == inst.DECREMENT.value:
            instructions.append(inst.DECREMENT)
        elif program[i] == inst.INCREMENT_POINTER.value:
            instructions.append(inst.INCREMENT_POINTER)
        elif program[i] == inst.DECREMENT_POINTER.value:
            instructions.append(inst.DECREMENT_POINTER)
        elif program[i] == inst.OUTPUT.value:
            instructions.append(inst.OUTPUT)
        elif program[i] == inst.INPUT.value:
            instructions.append(inst.INPUT)
        elif program[i] == inst.LOOP_START.value:
            instructions.append(inst.LOOP_START)
        elif program[i] == inst.LOOP_END.value:
            instructions.append(inst.LOOP_END)
        elif program[i] == inst.END.value:
            instructions.append(inst.END)
        i += 1
    return instructions

def i_increment(builder: ir.IRBuilder, tape: ir.GlobalVariable, tape_pointer: ir.GlobalVariable):
    tape_ptr_cast = builder.bitcast(tape, ir.IntType(8).as_pointer())
    index = builder.load(tape_pointer)
    tape_loc = builder.gep(tape_ptr_cast, [index])
    value = builder.load(tape_loc)
    increment = builder.add(value, ir.IntType(8)(1))
    builder.store(increment, tape_loc)


def i_decrement(builder: ir.IRBuilder, tape: ir.GlobalVariable, tape_pointer: ir.GlobalVariable):
    tape_ptr_cast = builder.bitcast(tape, ir.IntType(8).as_pointer())
    index = builder.load(tape_pointer)
    tape_loc = builder.gep(tape_ptr_cast, [index])
    value = builder.load(tape_loc)
    increment = builder.sub(value, ir.IntType(8)(1))
    builder.store(increment, tape_loc)

def i_move_right(builder: ir.IRBuilder, tape_pointer: ir.GlobalVariable):
    increment = builder.add(builder.load(tape_pointer), ir.IntType(32)(1))
    builder.store(increment, tape_pointer)

def i_move_left(builder: ir.IRBuilder, tape_pointer: ir.GlobalVariable):
    decrement = builder.sub(builder.load(tape_pointer), ir.IntType(32)(1))
    builder.store(decrement, tape_pointer)

def i_output(builder: ir.IRBuilder, putc: ir.FunctionType, tape: ir.GlobalVariable, tape_pointer: ir.GlobalVariable):
    tape_ptr_cast = builder.bitcast(tape, ir.IntType(8).as_pointer())
    tape_ptr = builder.gep(tape_ptr_cast, [builder.load(tape_pointer)])
    builder.call(putc, [builder.load(tape_ptr)])


def i_input(builder: ir.IRBuilder, scanf: ir.FunctionType, tape: ir.GlobalVariable, tape_pointer: ir.GlobalVariable):
    tape_ptr_cast = builder.bitcast(tape, ir.IntType(8).as_pointer())
    tape_ptr = builder.gep(tape_ptr_cast, [builder.load(tape_pointer)])
    builder.call(scanf, [tape_ptr])

def main(instructions):

    # types
    voidptr_type = ir.IntType(8).as_pointer()
    i32_type = ir.IntType(32)
    i8 = ir.IntType(8)

    mod = ir.Module()
    
    pointer = ir.GlobalVariable(mod, ir.IntType(32), name='pointer')
    pointer.initializer = ir.Constant(ir.IntType(32), 0)

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
    putc_type = ir.FunctionType(ir.IntType(32), [i8], var_arg=True)
    putc = ir.Function(mod, putc_type, name="putchar")
    

    # Create an entry function
    entry_type = ir.FunctionType(ir.VoidType(), [])
    entry = ir.Function(mod, entry_type, name="main")
    entry_block = entry.append_basic_block(name="entry")

    builder = ir.IRBuilder(entry_block)

    loop_start = None
    loop_end = None
    branch = None

    zero = ir.Constant(ir.IntType(8), 0)

    for instruction in instructions:
        if instruction == inst.INCREMENT:
            i_increment(builder, tape, pointer)
        elif instruction == inst.DECREMENT:
            i_decrement(builder, tape, pointer)
        elif instruction == inst.INCREMENT_POINTER:
            i_move_right(builder, pointer)
        elif instruction == inst.DECREMENT_POINTER:
            i_move_left(builder, pointer)
        elif instruction == inst.OUTPUT:
            i_output(builder, putc, tape, pointer)
        elif instruction == inst.INPUT:
            i_input(builder, scanf, tape, pointer)
        elif instruction == inst.LOOP_START:

            loop_start = builder.append_basic_block(name="loop_start")
            loop_end = builder.append_basic_block(name="loop_end")

            tape_cast_t = builder.bitcast(tape, ir.IntType(8).as_pointer())
            tape_ptr = builder.gep(tape_cast_t, [builder.load(pointer)])
            value_at_pc = builder.load(tape_ptr)
            builder.cbranch(builder.icmp_signed('==', value_at_pc, zero), loop_end, loop_start)
            builder.position_at_start(loop_start)

        elif instruction == inst.LOOP_END:

            tape_cast_t = builder.bitcast(tape, ir.IntType(8).as_pointer())
            tape_ptr = builder.gep(tape_cast_t, [builder.load(pointer)])
            value_at_pc = builder.load(tape_ptr)

            builder.cbranch(builder.icmp_signed('!=', value_at_pc, zero), loop_start, loop_end)
            builder.position_at_end(loop_end)

        elif instruction == inst.END:
            break

    builder.ret_void()

    il = llvm.parse_assembly(str(mod))
    return str(il)