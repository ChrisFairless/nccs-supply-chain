def get_output_dir():
    return OUTPUT_DIR


def get_run_dir(run_title):
    return f"{OUTPUT_DIR}/{run_title}"


def get_direct_output_dir(run_title):
    return f"{OUTPUT_DIR}/{run_title}/direct"


def get_indirect_output_dir(run_title):
    return f"{OUTPUT_DIR}/{run_title}/indirect"


OUTPUT_DIR = "../results"
