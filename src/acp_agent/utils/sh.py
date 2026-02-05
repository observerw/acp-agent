import aioshutil


async def available_programs(*programs: str) -> str:
    for program in programs:  # check availability in order
        if await aioshutil.which(program):
            return program
    raise RuntimeError(
        f"None of the required programs were found: {', '.join(programs)}"
    )
