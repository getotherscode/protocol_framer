import glob                                                       # for fuzzy file name search
import os

def get_bin_file_path() -> list[str]:
    bin_files = glob.glob("*.bin")
    if not bin_files:
        raise FileNotFoundError("do not find any .bin file !!!")  # raise can terminate the execution
    if len(bin_files) > 1:
        raise RuntimeError(".bin file is not only one !!!")
    
    print(f"find the target bin file {bin_files[0]}")
    return bin_files[0]

def parse_bin_file_size(path: list[str]) -> int:
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} do not exist !!!")
    bin_size = os.path.getsize(path)

    print(f"{path} file size: {bin_size}")
    return bin_size
    
def depacketizer(single_pack_size:int, path: list[str], start_addr: int):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} do not exist !!!")

    with open(path, "rb") as f:                                   # with as is context manager, close file automatically, "rb" read only binary
            f.seek(start_addr)
            pack = f.read(single_pack_size)                       # if left bytes is less than 1024, will return all left bytes
            if not pack: raise RuntimeError(f".bin read from {start_addr} is failed  !!!")
            return pack